from __future__ import annotations

import math
import os
import re
import shlex
import shutil
import subprocess
from pathlib import Path
from typing import Any

from .errors import InputValidationError
from .io import read_json, write_csv, write_json
from .config import normalize_target
from .calibration import calibrate_from_redocking
from .rmsd import HeavyAtom, parse_pdbqt_atom, calculate_redocking_rmsd
from .provenance import sha256_file, runtime_versions, portable_text


EXPECTED_VINA_VERSION = "1.2.7"


def _num(value: Any, name: str) -> float:
    try:
        numeric = float(value)
    except Exception as exc:
        raise InputValidationError(f"{name} must be numeric; got {value!r}.") from exc
    if not math.isfinite(numeric):
        raise InputValidationError(f"{name} must be finite; got {value!r}.")
    return numeric


def _resolve_file(base: Path, value: str, label: str) -> Path:
    path = Path(value).expanduser()
    if not path.is_absolute():
        path = (base / path).resolve()
    if not path.is_file():
        raise InputValidationError(f"{label} does not exist: {path}")
    return path


def load_vina_redocking_config(path: str | Path) -> dict[str, Any]:
    config_path = Path(path).expanduser().resolve()
    data = read_json(config_path)
    if not isinstance(data, dict):
        raise InputValidationError("Vina redocking config must be a JSON object.")
    jobs = data.get("targets")
    if not isinstance(jobs, list) or not jobs:
        raise InputValidationError("Vina redocking config requires a non-empty 'targets' list.")
    defaults = data.get("defaults") or {}
    base = config_path.parent
    normalized = []
    seen = set()
    for index, job in enumerate(jobs, start=1):
        if not isinstance(job, dict):
            raise InputValidationError(f"targets[{index}] must be a JSON object.")
        target = normalize_target(job.get("target", ""))
        pdb_id = str(job.get("pdb_id", "")).strip().upper()
        if not target or not pdb_id:
            raise InputValidationError(f"targets[{index}] requires target and pdb_id.")
        if target in seen:
            raise InputValidationError(f"Vina redocking config contains duplicate target {target!r}.")
        seen.add(target)
        receptor = _resolve_file(base, str(job.get("receptor_pdbqt", "")), f"{target} receptor_pdbqt")
        ligand = _resolve_file(base, str(job.get("native_ligand_pdbqt", "")), f"{target} native_ligand_pdbqt")
        center = job.get("center")
        size = job.get("size")
        if not (isinstance(center, list) and len(center) == 3):
            raise InputValidationError(f"{target}: center must be [x,y,z].")
        if not (isinstance(size, list) and len(size) == 3):
            raise InputValidationError(f"{target}: size must be [x,y,z] in Angstrom.")
        center = [_num(value, f"{target} center") for value in center]
        size = [_num(value, f"{target} size") for value in size]
        if any(value <= 0 for value in size):
            raise InputValidationError(f"{target}: all box sizes must be positive.")
        normalized.append(
            {
                "target": target,
                "pdb_id": pdb_id,
                "receptor_pdbqt": str(receptor),
                "native_ligand_pdbqt": str(ligand),
                "center": center,
                "size": size,
                "exhaustiveness": int(job.get("exhaustiveness", defaults.get("exhaustiveness", 12))),
                "num_modes": int(job.get("num_modes", defaults.get("num_modes", 9))),
                "energy_range": _num(job.get("energy_range", defaults.get("energy_range", 3)), f"{target} energy_range"),
                "seed": int(job.get("seed", defaults.get("seed", 2026))),
                "cpu": int(job.get("cpu", defaults.get("cpu", 1))),
                "scoring": str(job.get("scoring", defaults.get("scoring", "vina"))).strip().lower(),
                "rmsd_backend": str(job.get("rmsd_backend", defaults.get("rmsd_backend", data.get("rmsd_backend", "symmetry")))).strip().lower(),
            }
        )
    return {
        "config_path": str(config_path),
        "targets": normalized,
        "rmsd_cutoff_A": float(data.get("rmsd_cutoff_A", 2.0)),
        "required_vina_version": data.get("required_vina_version"),
    }


def resolve_vina_executable(value: str = "vina") -> str:
    path = Path(value).expanduser()
    if path.parent != Path(".") or os.sep in value:
        if not path.is_file():
            raise InputValidationError(f"AutoDock Vina executable not found: {path}")
        return str(path.resolve())
    found = shutil.which(value)
    if not found:
        raise InputValidationError(
            "AutoDock Vina was not found on PATH. Install Vina 1.2.7 or pass "
            "--vina-executable /full/path/to/vina."
        )
    return found


def vina_version(executable: str) -> str | None:
    for flag in ("--version", "-v"):
        try:
            proc = subprocess.run([executable, flag], text=True, capture_output=True, timeout=20)
        except Exception:
            continue
        text = f"{proc.stdout}\n{proc.stderr}"
        match = re.search(r"(?:AutoDock\s+Vina\s+v?|vina\s+v?)(\d+\.\d+\.\d+)", text, re.I)
        if match:
            return match.group(1)
    return None


def require_vina_version(executable: str, expected: str = EXPECTED_VINA_VERSION) -> str:
    observed = vina_version(executable)
    if observed is None:
        raise InputValidationError(
            f"Could not determine AutoDock Vina version from {executable!r}. "
            f"The manuscript workflow requires Vina {expected}."
        )
    if observed != expected:
        raise InputValidationError(
            f"AutoDock Vina version mismatch: observed {observed}, required {expected}. "
            "Use the exact manuscript version for reproduction."
        )
    return observed


def _native_atoms(path: Path) -> list[HeavyAtom]:
    atoms = []
    for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        atom = parse_pdbqt_atom(line)
        if atom:
            atoms.append(atom)
    if not atoms:
        raise InputValidationError(f"No heavy atoms could be parsed from native ligand PDBQT: {path}")
    return atoms


def _vina_models(path: Path):
    text = path.read_text(encoding="utf-8", errors="ignore").splitlines()
    models = []
    current = []
    affinity = None

    def finish():
        nonlocal current, affinity
        if current:
            models.append({"atoms": current, "affinity": affinity})
        current = []
        affinity = None

    for line in text:
        if line.startswith("MODEL"):
            if current:
                finish()
            continue
        if line.startswith("ENDMDL"):
            finish()
            continue
        if "REMARK VINA RESULT:" in line:
            match = re.search(r"REMARK VINA RESULT:\s*([-+]?\d+(?:\.\d+)?)", line)
            if match:
                affinity = float(match.group(1))
        atom = parse_pdbqt_atom(line)
        if atom:
            current.append(atom)
    if current:
        finish()
    if not models:
        raise InputValidationError(f"No docked models could be parsed from Vina output: {path}")
    for index, model in enumerate(models, start=1):
        if model["affinity"] is None:
            raise InputValidationError(
                f"Vina output model {index} has no REMARK VINA RESULT affinity: {path}"
            )
    return models


def run_vina_reference_redocking(
    config_path: str | Path,
    output_dir: str | Path,
    *,
    vina_executable: str = "vina",
    rmsd_cutoff: float | None = None,
    enforce_version: bool = False,
):
    config = load_vina_redocking_config(config_path)
    outdir = Path(output_dir)
    outdir.mkdir(parents=True, exist_ok=True)
    executable = resolve_vina_executable(vina_executable)
    required_version = config.get("required_vina_version")
    observed_version = vina_version(executable)
    if enforce_version or required_version:
        expected = str(required_version or EXPECTED_VINA_VERSION)
        observed_version = require_vina_version(executable, expected)

    cutoff = float(config["rmsd_cutoff_A"] if rmsd_cutoff is None else rmsd_cutoff)
    all_rows = []
    run_rows = []
    warnings = []
    for job in config["targets"]:
        target = job["target"]
        target_dir = outdir / target
        target_dir.mkdir(parents=True, exist_ok=True)
        box = target_dir / "vina_box.txt"
        box.write_text(
            "\n".join(
                [
                    f"center_x = {job['center'][0]}",
                    f"center_y = {job['center'][1]}",
                    f"center_z = {job['center'][2]}",
                    f"size_x = {job['size'][0]}",
                    f"size_y = {job['size'][1]}",
                    f"size_z = {job['size'][2]}",
                ]
            )
            + "\n",
            encoding="utf-8",
        )
        output_pdbqt = target_dir / "reference_redocked.pdbqt"
        stdout_path = target_dir / "vina_stdout.txt"
        stderr_path = target_dir / "vina_stderr.txt"
        command = [
            executable,
            "--receptor",
            job["receptor_pdbqt"],
            "--ligand",
            job["native_ligand_pdbqt"],
            "--config",
            str(box),
            "--scoring",
            job["scoring"],
            "--exhaustiveness",
            str(job["exhaustiveness"]),
            "--num_modes",
            str(job["num_modes"]),
            "--energy_range",
            str(job["energy_range"]),
            "--seed",
            str(job["seed"]),
            "--cpu",
            str(job["cpu"]),
            "--out",
            str(output_pdbqt),
        ]
        proc = subprocess.run(command, text=True, capture_output=True)
        stdout_path.write_text(proc.stdout or "", encoding="utf-8")
        stderr_path.write_text(proc.stderr or "", encoding="utf-8")
        if proc.returncode != 0:
            raise InputValidationError(
                f"Vina redocking failed for {target} (exit {proc.returncode}). See {stderr_path}."
            )
        if not output_pdbqt.is_file():
            raise InputValidationError(
                f"Vina reported success for {target} but did not create {output_pdbqt}."
            )

        native = _native_atoms(Path(job["native_ligand_pdbqt"]))
        models = _vina_models(output_pdbqt)
        for mode, model in enumerate(models, start=1):
            rmsd, method, automorphisms = calculate_redocking_rmsd(
                native,
                model["atoms"],
                backend=job["rmsd_backend"],
            )
            all_rows.append(
                {
                    "target": target,
                    "pdb_id": job["pdb_id"],
                    "mode": mode,
                    "dg_kcal_mol": model["affinity"],
                    "rmsd_A": rmsd,
                    "rmsd_method": method,
                    "symmetry_automorphisms_evaluated": automorphisms,
                }
            )
        run_rows.append(
            {
                "target": target,
                "pdb_id": job["pdb_id"],
                "vina_executable": Path(executable).name,
                "vina_executable_sha256": sha256_file(executable),
                "vina_version": observed_version or "unknown",
                "command": " ".join(
                    shlex.quote(portable_text(value))
                    for value in command
                ),
                "returncode": proc.returncode,
                "receptor_file": Path(job["receptor_pdbqt"]).name,
                "native_ligand_file": Path(job["native_ligand_pdbqt"]).name,
                "receptor_sha256": sha256_file(job["receptor_pdbqt"]),
                "native_ligand_sha256": sha256_file(job["native_ligand_pdbqt"]),
                "output_pdbqt": str(output_pdbqt.relative_to(outdir)),
                "stdout_log": str(stdout_path.relative_to(outdir)),
                "stderr_log": str(stderr_path.relative_to(outdir)),
                "n_modes_parsed": len(models),
                "seed": job["seed"],
                "cpu": job["cpu"],
                "exhaustiveness": job["exhaustiveness"],
                "num_modes": job["num_modes"],
                "energy_range": job["energy_range"],
                "scoring": job["scoring"],
                "rmsd_backend": job["rmsd_backend"],
            }
        )

    calibration = calibrate_from_redocking(all_rows, list(all_rows[0].keys()), None, cutoff)
    write_csv(outdir / "reference_redocking.csv", all_rows)
    write_csv(outdir / "target_calibration.csv", calibration)
    write_csv(outdir / "vina_redocking_runs.csv", run_rows)
    manifest = {
        "config_name": Path(config["config_path"]).name,
        "config_sha256": sha256_file(config["config_path"]),
        "rmsd_cutoff_A": cutoff,
        "vina_executable": Path(executable).name,
        "vina_executable_sha256": sha256_file(executable),
        "vina_version": observed_version or "unknown",
        "required_vina_version": required_version,
        "runtime_versions": runtime_versions(),
        "rmsd_default": "symmetry-corrected fixed-frame heavy-atom RMSD using element-labeled native-ligand graph automorphisms",
        "ordered_rmsd_option": "Available only by explicit rmsd_backend='ordered' configuration; not the recommended default for new targets.",
        "warnings": warnings,
    }
    write_json(outdir / "redocking_manifest.json", manifest)
    return all_rows, calibration, run_rows
