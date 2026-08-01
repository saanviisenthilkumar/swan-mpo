from __future__ import annotations

import json
import tempfile
from importlib.resources import files
from pathlib import Path

from .calibration import calibrate_from_redocking, load_published_calibration
from .config import PUBLISHED_ONCOLOGY
from .errors import InputValidationError
from .io import read_csv, read_json
from .locked_model import model_source_sha256
from .pipeline import score_pipeline
from .provenance import sha256_file, runtime_versions, portable_text
from .vina_redocking import EXPECTED_VINA_VERSION, resolve_vina_executable, vina_version, run_vina_reference_redocking

EXPECTED_LOCKED_SHA256 = "97799e91f23803de3b9a477aea3bbcfb061f1b1d9abebdecfdadcd1b537f4454"
EXPECTED_PUBLISHED_CALIBRATION_SHA256 = "e7584f10c0f970bb54ddf39cfdacbb6cb061bc6a3d2bd795e2d5f119efc7287c"


def run_packaged_demo():
    resources = files("swan_mpo.resources")
    adme_rows, adme_fields = read_csv(resources / "example_adme.csv")
    tox_rows, tox_fields = read_csv(resources / "example_toxicity.csv")
    dock_rows, dock_fields = read_csv(resources / "example_candidate_docking.csv")
    redock_rows, redock_fields = read_csv(resources / "example_reference_redocking.csv")
    config = read_json(resources / "example_config.json")
    calibration = calibrate_from_redocking(redock_rows, redock_fields, None, 2.0)
    scores, target = score_pipeline(
        adme_rows,
        adme_fields,
        tox_rows,
        tox_fields,
        dock_rows,
        dock_fields,
        calibration,
        config,
        selected_panels=["Colon"],
        require_full_panel_coverage=True,
    )
    expected = json.loads((resources / "example_expected.json").read_text(encoding="utf-8"))
    observed = {row["compound"]: row["SWAN_MPO_score"] for row in scores}
    failures = {
        key: {"observed": observed.get(key), "expected": value}
        for key, value in expected.items()
        if key not in observed or abs(observed[key] - value) > 1e-12
    }
    return scores, target, calibration, failures


def verify_installation(*, check_vina=False, vina_executable="vina"):
    resources = files("swan_mpo.resources")
    published_calibration_path = resources / "published_target_redocking_calibration.csv"
    scores, target, calibration, demo_failures = run_packaged_demo()
    published = load_published_calibration()
    classes = [row.get("validation_class") for row in published]
    checks = {
        "locked_model_hash": {
            "status": "PASS" if model_source_sha256() == EXPECTED_LOCKED_SHA256 else "FAIL",
            "observed": model_source_sha256(),
            "expected": EXPECTED_LOCKED_SHA256,
        },
        "published_calibration_hash": {
            "status": "PASS" if sha256_file(published_calibration_path) == EXPECTED_PUBLISHED_CALIBRATION_SHA256 else "FAIL",
            "observed": sha256_file(published_calibration_path),
            "expected": EXPECTED_PUBLISHED_CALIBRATION_SHA256,
        },
        "packaged_demo": {
            "status": "PASS" if not demo_failures else "FAIL",
            "rows": len(scores),
            "failures": demo_failures,
        },
        "published_calibration_classes": {
            "status": "PASS"
            if classes.count("strict_top_pose") == 4
            and classes.count("generated_mode_recovery") == 2
            and classes.count("comparative_only") == 3
            else "FAIL",
            "strict_top_pose": classes.count("strict_top_pose"),
            "generated_mode_recovery": classes.count("generated_mode_recovery"),
            "comparative_only": classes.count("comparative_only"),
        },
    }
    if check_vina:
        try:
            executable = resolve_vina_executable(vina_executable)
            version = vina_version(executable)
            checks["vina_1_2_7"] = {
                "status": "PASS" if version == EXPECTED_VINA_VERSION else "FAIL",
                "executable": Path(executable).name,
                "executable_sha256": sha256_file(executable),
                "observed": version,
                "expected": EXPECTED_VINA_VERSION,
            }
        except Exception as exc:
            checks["vina_1_2_7"] = {"status": "FAIL", "error": str(exc), "expected": EXPECTED_VINA_VERSION}
    overall = "PASS" if all(value.get("status") == "PASS" for value in checks.values()) else "FAIL"
    return {"status": overall, "checks": checks, "runtime_versions": runtime_versions()}


def run_real_vina_integration(config_path, *, vina_executable="vina", output_dir=None):
    if output_dir is None:
        temp = tempfile.TemporaryDirectory(prefix="swan_vina_verify_")
        output_dir = Path(temp.name)
    else:
        temp = None
        output_dir = Path(output_dir)
    rows, calibration, runs = run_vina_reference_redocking(
        config_path,
        output_dir,
        vina_executable=vina_executable,
        enforce_version=True,
    )
    report = {
        "status": "PASS",
        "output_dir": portable_text(output_dir),
        "targets": [row["target"] for row in calibration],
        "modes": len(rows),
        "runs": len(runs),
        "calibration": calibration,
    }
    # Keep temporary directory alive until caller has consumed the report. The CLI
    # always passes an explicit output directory, so this branch is mainly library use.
    report["_temporary_directory"] = temp
    return report
