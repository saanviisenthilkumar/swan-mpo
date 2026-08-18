from __future__ import annotations

import json
import tempfile
from importlib.resources import files
from pathlib import Path

from .calibration import calibrate_from_redocking, load_published_calibration
from .config import PUBLISHED_ONCOLOGY
from .domain_audit import calculate_domain_audit_tables
from .errors import InputValidationError
from .io import read_csv, read_json
from .locked_model import model_source_sha256
from .pipeline import score_pipeline
from .provenance import sha256_file, runtime_versions, portable_text
from .vina_redocking import EXPECTED_VINA_VERSION, resolve_vina_executable, vina_version, run_vina_reference_redocking

EXPECTED_LOCKED_SHA256 = "97799e91f23803de3b9a477aea3bbcfb061f1b1d9abebdecfdadcd1b537f4454"
EXPECTED_PUBLISHED_CALIBRATION_SHA256 = "e7584f10c0f970bb54ddf39cfdacbb6cb061bc6a3d2bd795e2d5f119efc7287c"

EXPECTED_RUNTIME_PACKAGES = {
    "numpy": "2.3.5",
    "networkx": "3.6.1",
}
EXPECTED_PYTHON_MAJOR_MINOR = "3.13"

EXPECTED_MANUSCRIPT_RESOURCE_SHA256 = {
    "manuscript_source_manifest.json": "8e48007744de8ec50e7ba9941f4b71970161fea31034a8df231ed5502bb45561",
    "manuscript_swissadme_canonical_full.csv": "a1b6339695bba431239def8969d56244cecd978e195e5eaf2a3019ca21ec7ab1",
    "manuscript_swissadme_original_incomplete.csv": "a90b7c3cdee1d9b10257ccdf368dab6bedbe31520031113f6b1255b79deba7ca",
    "manuscript_protox_raw.csv": "4ef8ea376f89533ad3bd3afb9d810aab9c8fccc3f216179414d6de776b3f08ee",
    "manuscript_candidate_docking.csv": "6172ccc65f3ffddf07ce835ab5b5f45803f1b708f36499f5e5260971ed47530b",
    "manuscript_expected_panel_scores.csv": "cd94a21ed3bb9160220ef0d7c4897bba045c7c3eb6fd45ded717f209a073f8ca",
    "manuscript_expected_target_level_binding.csv": "8148755f8085c0d17ca5abde608ef62fd2c8621545e9f03225ef994c29f00641",
}


def manuscript_resource_hash_report():
    resources = files("swan_mpo.resources")
    observed = {}
    failures = []
    import hashlib
    for name, expected in EXPECTED_MANUSCRIPT_RESOURCE_SHA256.items():
        actual = hashlib.sha256((resources / name).read_bytes()).hexdigest()
        observed[name] = {"observed": actual, "expected": expected, "status": "PASS" if actual == expected else "FAIL"}
        if actual != expected:
            failures.append(name)
    return {"status": "PASS" if not failures else "FAIL", "files": observed, "failures": failures}



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


def run_manuscript_reproduction(*, tolerance=1e-10):
    """Recompute the frozen 59-compound expanded screen from exact packaged inputs.

    The reproduction uses the exact canonical 59-row full SwissADME export
    (SHA-256 a1b6339695bba431239def8969d56244cecd978e195e5eaf2a3019ca21ec7ab1),
    the exact 59-row ProTox export, and the scoring-required columns copied row-for-row
    from the canonical 10,620-row docking ledger. It checks all 177 panel rows and all
    531 target-level binding rows against frozen canonical expected outputs.
    """
    resources = files("swan_mpo.resources")
    adme_rows, adme_fields = read_csv(resources / "manuscript_swissadme_canonical_full.csv")
    tox_rows, tox_fields = read_csv(resources / "manuscript_protox_raw.csv")
    dock_rows, dock_fields = read_csv(resources / "manuscript_candidate_docking.csv")
    expected_rows, _ = read_csv(resources / "manuscript_expected_panel_scores.csv")
    expected_target_rows, _ = read_csv(resources / "manuscript_expected_target_level_binding.csv")
    calibration = load_published_calibration()
    scores, target = score_pipeline(
        adme_rows, adme_fields, tox_rows, tox_fields, dock_rows, dock_fields,
        calibration, PUBLISHED_ONCOLOGY, selected_panels=["Colon", "Prostate", "RCC"],
        require_full_panel_coverage=True,
    )
    expected = {(r["panel"], r["Compound"]): r for r in expected_rows}
    observed = {(r["panel"], r["compound"]): r for r in scores}
    failures = []
    for key, ref in expected.items():
        obs = observed.get(key)
        if obs is None:
            failures.append({"key": key, "field": "row", "observed": None, "expected": "present"})
            continue
        numeric_pairs = [
            ("bestnode_binding", "bestnode_binding"),
            ("safety_score", "safety_score"),
            ("adme_score", "adme_score"),
            ("liability_score", "liability_score"),
            ("SWAN_MPO_score", "SWAN_BestNode"),
        ]
        for obs_field, ref_field in numeric_pairs:
            delta = abs(float(obs[obs_field]) - float(ref[ref_field]))
            if delta > tolerance:
                failures.append({"key": key, "field": obs_field, "observed": obs[obs_field], "expected": ref[ref_field], "abs_diff": delta})
        exact_pairs = [
            ("selected_best_node", "selected_best_node"),
            ("SWAN_MPO_rank", "rank_SWAN_BestNode"),
            ("bestnode_binding_rank", "rank_bestnode_binding"),
        ]
        for obs_field, ref_field in exact_pairs:
            oval, rval = str(obs[obs_field]), str(ref[ref_field])
            if oval.endswith('.0') and rval.isdigit(): oval = oval[:-2]
            if rval.endswith('.0') and oval.isdigit(): rval = rval[:-2]
            if oval != rval:
                failures.append({"key": key, "field": obs_field, "observed": oval, "expected": rval})

    expected_target = {(r["Compound"], r["pdb_id"]): r for r in expected_target_rows}
    observed_target = {(r["compound"], r["pdb_id"]): r for r in target}
    for key, ref in expected_target.items():
        obs = observed_target.get(key)
        if obs is None:
            failures.append({"key": key, "field": "target_row", "observed": None, "expected": "present"})
            continue
        for obs_field, ref_field in [
            ("n_grid_centers","n_grid_centers"), ("best_dg","best_dg"),
            ("median_dg","median_dg"), ("mean_dg","mean_dg")
        ]:
            delta=abs(float(obs[obs_field])-float(ref[ref_field]))
            if delta > tolerance:
                failures.append({"key":key,"field":obs_field,"observed":obs[obs_field],"expected":ref[ref_field],"abs_diff":delta})
        ref_binding=str(ref.get("binding_reference_calibrated","")).strip()
        obs_binding=obs.get("binding_reference_calibrated","")
        if ref_binding not in {"", "nan", "NaN"}:
            delta=abs(float(obs_binding)-float(ref_binding))
            if delta > tolerance:
                failures.append({"key":key,"field":"binding_reference_calibrated","observed":obs_binding,"expected":ref_binding,"abs_diff":delta})
        elif obs_binding not in {"", None}:
            failures.append({"key":key,"field":"binding_reference_calibrated","observed":obs_binding,"expected":""})
        expected_status = str(ref.get("binding_calibration_status", "")).strip()
        if obs.get("calibration_status") != expected_status:
            failures.append({"key":key,"field":"calibration_status","observed":obs.get("calibration_status"),"expected":expected_status})

    extras = sorted(set(observed) - set(expected))
    extra_targets = sorted(set(observed_target) - set(expected_target))
    if extras: failures.append({"field":"unexpected_panel_rows","observed":extras[:20],"expected":[]})
    if extra_targets: failures.append({"field":"unexpected_target_rows","observed":extra_targets[:20],"expected":[]})
    resource_hashes = manuscript_resource_hash_report()
    if resource_hashes["status"] != "PASS":
        failures.append({"field": "manuscript_resource_hashes", "observed": resource_hashes["failures"], "expected": []})
    return {
        "status": "PASS" if not failures else "FAIL",
        "resource_hashes": resource_hashes,
        "rows_observed": len(scores),
        "rows_expected": len(expected_rows),
        "target_level_rows": len(target),
        "target_level_rows_expected": len(expected_target_rows),
        "tolerance": tolerance,
        "failures": failures,
        "muricatacin": [
            {"panel":r["panel"],"score":r["SWAN_MPO_score"],"rank":r["SWAN_MPO_rank"],"bestnode":r["selected_best_node"],"binding_rank":r["bestnode_binding_rank"]}
            for r in scores if r["compound"] == "Muricatacin"
        ],
    }

def _strict_runtime_checks(vina_executable="vina"):
    versions = runtime_versions()
    checks = {}
    py = versions.get("python") or ""
    checks["python_3_13"] = {
        "status": "PASS" if py.startswith(EXPECTED_PYTHON_MAJOR_MINOR + ".") else "FAIL",
        "observed": py, "expected": EXPECTED_PYTHON_MAJOR_MINOR + ".x"
    }
    for package, expected in EXPECTED_RUNTIME_PACKAGES.items():
        observed = versions.get(package)
        checks[f"dependency_{package}"] = {
            "status": "PASS" if observed == expected else "FAIL",
            "observed": observed, "expected": expected
        }
    try:
        executable = resolve_vina_executable(vina_executable)
        observed = vina_version(executable)
        checks["vina_exact"] = {
            "status": "PASS" if observed == EXPECTED_VINA_VERSION else "FAIL",
            "observed": observed, "expected": EXPECTED_VINA_VERSION,
            "executable": Path(executable).name, "executable_sha256": sha256_file(executable)
        }
    except Exception as exc:
        checks["vina_exact"] = {"status": "FAIL", "error": str(exc), "expected": EXPECTED_VINA_VERSION}
    return checks


def verify_installation(*, check_vina=False, vina_executable="vina", strict=False, check_manuscript=False):
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
    if check_manuscript or strict:
        manuscript = run_manuscript_reproduction()
        checks["manuscript_resource_hashes"] = manuscript["resource_hashes"]
        checks["manuscript_reproduction"] = {
            "status": manuscript["status"],
            "rows_observed": manuscript["rows_observed"],
            "rows_expected": manuscript["rows_expected"],
            "target_level_rows": manuscript["target_level_rows"],
            "muricatacin": manuscript["muricatacin"],
            "failures": manuscript["failures"][:20],
        }
    if strict:
        checks.update(_strict_runtime_checks(vina_executable))
        from .method_warnings import collect_method_warnings
        method_codes = [w["code"] for w in collect_method_warnings(PUBLISHED_ONCOLOGY, published)]
        checks["published_method_warning_contract"] = {
            "status": "PASS" if method_codes == ["PANEL_SINGLE_NODE_BESTNODE"] else "FAIL",
            "observed": method_codes,
            "expected": ["PANEL_SINGLE_NODE_BESTNODE"],
            "note": "The single-node Colon BestNode warning is an expected structural caveat, not a release failure.",
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
