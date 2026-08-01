from __future__ import annotations

import hashlib
import json
import os
import platform
import shlex
import sys
from datetime import datetime, timezone
from importlib import metadata
from pathlib import Path
from typing import Iterable

from . import __version__
from .locked_model import MODEL_VERSION, model_source_sha256


def sha256_file(path: str | Path) -> str:
    p = Path(path)
    h = hashlib.sha256()
    with p.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def package_version(name: str) -> str | None:
    try:
        return metadata.version(name)
    except metadata.PackageNotFoundError:
        return None


def runtime_versions() -> dict[str, str | None]:
    return {
        "python": platform.python_version(),
        "platform": platform.platform(),
        "numpy": package_version("numpy"),
        "networkx": package_version("networkx"),
        "pytest": package_version("pytest"),
        "rdkit": package_version("rdkit"),
        "openbabel": package_version("openbabel-wheel") or package_version("openbabel"),
        "vina_python_package": package_version("vina"),
    }


def input_hashes(paths: Iterable[str | Path | None]) -> list[dict[str, str]]:
    """Hash inputs without persisting author-machine absolute paths.

    The SHA-256 identifies the exact input bytes. Only the basename is written to
    portable run artifacts so sharing a results directory does not expose a home
    directory or workstation path.
    """
    rows = []
    seen = set()
    for value in paths:
        if not value:
            continue
        p = Path(value).expanduser().resolve()
        if p in seen or not p.is_file():
            continue
        seen.add(p)
        rows.append({"name": p.name, "sha256": sha256_file(p)})
    return rows




def portable_text(value: str | Path) -> str:
    """Replace the current user's home-directory prefix with ``$HOME``.

    Run artifacts are intended to be shareable.  They preserve enough path
    context to reproduce a command without publishing a workstation username
    or absolute home directory.
    """
    text = str(value)
    home = str(Path.home())
    if home and home in text:
        return text.replace(home, "$HOME")
    return text


def portable_argv(argv: list[str] | None = None) -> list[str]:
    values = list(argv if argv is not None else sys.argv)
    if not values:
        return []
    # Console-script argv[0] is commonly an absolute .venv path.  The package
    # command is the reproducible identity; the installation path is not.
    first = Path(str(values[0])).name
    if first in {"swan-mpo", "swan_mpo", "__main__.py"} or "swan" in first.lower():
        values[0] = "swan-mpo"
    else:
        values[0] = portable_text(values[0])
    return [portable_text(v) for v in values]

def base_run_metadata(
    *,
    command: str,
    input_paths: Iterable[str | Path | None] = (),
    config: dict | None = None,
    warnings: list[dict] | None = None,
    argv: list[str] | None = None,
) -> dict:
    cfg = config or {}
    return {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "command": command,
        "argv": portable_argv(argv),
        "command_line": " ".join(shlex.quote(str(x)) for x in portable_argv(argv)),
        "swan_mpo_version": __version__,
        "model_version": MODEL_VERSION,
        "locked_model_sha256": model_source_sha256(),
        "scoring_is_deterministic": True,
        "scoring_random_seed": None,
        "candidate_docking_seed": cfg.get("candidate_docking_seed", "not_provided"),
        "published_redocking_seed": cfg.get("reference_redocking_seed", 2026 if cfg.get("name") == "published-oncology" else "not_provided"),
        "runtime_versions": runtime_versions(),
        "input_files": input_hashes(input_paths),
        "warnings": warnings or [],
    }


def write_run_log(path: str | Path, metadata: dict) -> Path:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "SWAN-MPO RUN LOG",
        f"timestamp_utc: {metadata.get('timestamp_utc')}",
        f"command_line: {metadata.get('command_line')}",
        f"swan_mpo_version: {metadata.get('swan_mpo_version')}",
        f"model_version: {metadata.get('model_version')}",
        f"locked_model_sha256: {metadata.get('locked_model_sha256')}",
        f"candidate_docking_seed: {metadata.get('candidate_docking_seed')}",
        "runtime_versions:",
    ]
    for key, value in (metadata.get("runtime_versions") or {}).items():
        lines.append(f"  {key}: {value}")
    lines.append("input_files:")
    for row in metadata.get("input_files") or []:
        lines.append(f"  {row['sha256']}  {row['name']}")
    warnings = metadata.get("warnings") or []
    lines.append(f"warnings: {len(warnings)}")
    for warning in warnings:
        lines.append(
            f"  [{warning.get('code','WARNING')}] {warning.get('compound','')} {warning.get('field','')}: {warning.get('message','')}"
        )
    p.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return p
