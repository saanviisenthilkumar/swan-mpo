from __future__ import annotations

import argparse
import hashlib
import json
import sys
from importlib.resources import files
from pathlib import Path

from . import __version__
from .errors import SwanMPOError, InputValidationError
from .io import read_csv, read_json, write_csv, write_json
from .config import load_config
from .calibration import calibrate_from_redocking, load_published_calibration
from .pipeline import score_pipeline
from .validation import validate_pipeline
from .locked_model import MODEL_VERSION, model_source_sha256, model_specification
from .domain_audit import calculate_domain_audit_tables
from .domain_warnings import collect_domain_warnings
from .method_warnings import collect_method_warnings
from .vina_redocking import run_vina_reference_redocking, EXPECTED_VINA_VERSION
from .provenance import base_run_metadata, write_run_log
from .verification import (
    EXPECTED_LOCKED_SHA256,
    run_packaged_demo,
    verify_installation,
    run_real_vina_integration,
    run_manuscript_reproduction,
)


def _maps(path):
    if not path:
        return {}
    data = read_json(path)
    if not isinstance(data, dict):
        raise InputValidationError("Column map must be a JSON object.")
    return data


def _calibration(args):
    if getattr(args, "reference_redocking", None):
        rows, fields = read_csv(args.reference_redocking)
        maps = _maps(getattr(args, "column_map", None))
        return calibrate_from_redocking(
            rows,
            fields,
            maps.get("reference_redocking"),
            getattr(args, "rmsd_cutoff", 2.0),
        )
    if getattr(args, "calibration", None) and args.calibration not in {"published", "published-oncology"}:
        rows, _ = read_csv(args.calibration)
        return rows
    return load_published_calibration()


def _load_inputs(args):
    adme_rows, adme_fields = read_csv(args.adme)
    tox_rows, tox_fields = read_csv(args.toxicity)
    dock_rows, dock_fields = read_csv(args.docking)
    return adme_rows, adme_fields, tox_rows, tox_fields, dock_rows, dock_fields


def _demo_inputs():
    resources = files("swan_mpo.resources")
    adme_rows, adme_fields = read_csv(resources / "example_adme.csv")
    tox_rows, tox_fields = read_csv(resources / "example_toxicity.csv")
    dock_rows, dock_fields = read_csv(resources / "example_candidate_docking.csv")
    redock_rows, redock_fields = read_csv(resources / "example_reference_redocking.csv")
    config = read_json(resources / "example_config.json")
    calibration = calibrate_from_redocking(redock_rows, redock_fields, None, 2.0)
    return adme_rows, adme_fields, tox_rows, tox_fields, dock_rows, dock_fields, config, calibration


def _manuscript_inputs():
    resources = files("swan_mpo.resources")
    adme_rows, adme_fields = read_csv(resources / "manuscript_swissadme_canonical_full.csv")
    tox_rows, tox_fields = read_csv(resources / "manuscript_protox_raw.csv")
    dock_rows, dock_fields = read_csv(resources / "manuscript_candidate_docking.csv")
    config = load_config("published-oncology")
    calibration = load_published_calibration()
    return adme_rows, adme_fields, tox_rows, tox_fields, dock_rows, dock_fields, config, calibration


def _require_locked_hash():
    observed = model_source_sha256()
    if observed != EXPECTED_LOCKED_SHA256:
        raise InputValidationError(
            f"Installed locked_model.py does not match the frozen SHA-256. Observed {observed}; expected {EXPECTED_LOCKED_SHA256}."
        )


def cmd_calibrate(args):
    rows, fields = read_csv(args.reference_redocking)
    maps = _maps(args.column_map)
    result = calibrate_from_redocking(
        rows,
        fields,
        maps.get("reference_redocking"),
        args.rmsd_cutoff,
    )
    write_csv(args.output, result)
    print(f"Wrote {len(result)} target calibration row(s) to {args.output}")


def cmd_validate(args):
    _require_locked_hash()
    adme_rows, adme_fields, tox_rows, tox_fields, dock_rows, dock_fields = _load_inputs(args)
    config = load_config(args.config)
    calibration = _calibration(args)
    maps = _maps(args.column_map)
    report = validate_pipeline(
        adme_rows,
        adme_fields,
        tox_rows,
        tox_fields,
        dock_rows,
        dock_fields,
        calibration,
        config,
        adme_map=maps.get("adme"),
        tox_map=maps.get("toxicity"),
        docking_map=maps.get("docking"),
        allow_missing_predictors=args.allow_missing_predictors,
    )
    warnings = collect_domain_warnings(
        adme_rows,
        adme_fields,
        tox_rows,
        tox_fields,
        adme_map=maps.get("adme"),
        tox_map=maps.get("toxicity"),
    )
    warnings.extend(collect_method_warnings(
        config, calibration, allow_missing_predictors=args.allow_missing_predictors
    ))
    report["locked_model_sha256"] = model_source_sha256()
    report["locked_model_hash_ok"] = True
    report["warnings"] = warnings
    print(json.dumps(report, indent=2))


def _write_score_outputs(
    *,
    output_dir,
    scores,
    target_rows,
    calibration,
    domain_rows,
    liability_rows,
    warnings,
    metadata,
):
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    write_csv(output_dir / "swan_panel_scores.csv", scores)
    write_csv(output_dir / "compound_safety_adme_desirabilities.csv", domain_rows)
    write_csv(output_dir / "panel_liability_desirabilities.csv", liability_rows)
    write_csv(output_dir / "target_level_binding.csv", target_rows)
    write_csv(output_dir / "target_calibration_used.csv", calibration)
    if warnings:
        write_csv(output_dir / "warnings.csv", warnings)
    else:
        write_csv(output_dir / "warnings.csv", [], fieldnames=["code", "compound", "field", "value", "message"])
    metadata["outputs"] = [
        "compound_safety_adme_desirabilities.csv",
        "panel_liability_desirabilities.csv",
        "target_level_binding.csv",
        "target_calibration_used.csv",
        "swan_panel_scores.csv",
        "warnings.csv",
    ]
    write_json(output_dir / "run_metadata.json", metadata)
    # Backward-compatible name retained for the manuscript/repository transition.
    write_json(output_dir / "run_manifest.json", metadata)
    write_run_log(output_dir / "run.log", metadata)
    return output_dir


def cmd_score(args):
    _require_locked_hash()
    if args.demo:
        if any([args.docking, args.adme, args.toxicity, args.reference_redocking]) or args.calibration != "published":
            raise InputValidationError(
                "--demo uses bundled synthetic example inputs and cannot be combined with --docking, --adme, --toxicity, --reference-redocking, or a custom --calibration."
            )
        adme_rows, adme_fields, tox_rows, tox_fields, dock_rows, dock_fields, config, calibration = _demo_inputs()
        maps = {}
        panels = ["Colon"]
        input_paths = []
        config_label = "bundled-demo"
    else:
        missing = [name for name in ("docking", "adme", "toxicity") if not getattr(args, name)]
        if missing:
            raise InputValidationError(
                f"score requires --docking, --adme, and --toxicity unless --demo is used. Missing: {missing}."
            )
        adme_rows, adme_fields, tox_rows, tox_fields, dock_rows, dock_fields = _load_inputs(args)
        config = load_config(args.config)
        calibration = _calibration(args)
        maps = _maps(args.column_map)
        panels = args.panels.split(",") if args.panels else None
        input_paths = [args.docking, args.adme, args.toxicity, args.column_map]
        if args.reference_redocking:
            input_paths.append(args.reference_redocking)
        elif args.calibration not in {"published", "published-oncology"}:
            input_paths.append(args.calibration)
        if args.config not in {"published", "published-oncology"}:
            input_paths.append(args.config)
        config_label = args.config

    scores, target_rows = score_pipeline(
        adme_rows,
        adme_fields,
        tox_rows,
        tox_fields,
        dock_rows,
        dock_fields,
        calibration,
        config,
        adme_map=maps.get("adme"),
        tox_map=maps.get("toxicity"),
        docking_map=maps.get("docking"),
        selected_panels=panels,
        require_full_panel_coverage=not args.primary_only,
        allow_missing_predictors=args.allow_missing_predictors,
    )
    domain_rows, liability_rows = calculate_domain_audit_tables(
        adme_rows,
        adme_fields,
        tox_rows,
        tox_fields,
        config,
        adme_map=maps.get("adme"),
        tox_map=maps.get("toxicity"),
        selected_panels=panels,
        allow_missing=args.allow_missing_predictors,
    )
    warnings = collect_domain_warnings(
        adme_rows,
        adme_fields,
        tox_rows,
        tox_fields,
        adme_map=maps.get("adme"),
        tox_map=maps.get("toxicity"),
    )
    warnings.extend(collect_method_warnings(
        config, calibration, selected_panels=panels,
        allow_missing_predictors=args.allow_missing_predictors,
        primary_only=args.primary_only,
    ))
    metadata = base_run_metadata(
        command="score --demo" if args.demo else "score",
        input_paths=input_paths,
        config=config,
        warnings=warnings,
    )
    config_canonical = json.dumps(config, sort_keys=True, separators=(",", ":")).encode("utf-8")
    calibration_canonical = json.dumps(calibration, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")
    metadata.update(
        {
            "config": config_label,
            "config_sha256": hashlib.sha256(config_canonical).hexdigest(),
            "config_snapshot": config,
            "calibration_source": "bundled-demo"
            if args.demo
            else ("reference_redocking" if args.reference_redocking else args.calibration or "published"),
            "calibration_table_sha256": hashlib.sha256(calibration_canonical).hexdigest(),
            "primary_only": args.primary_only,
            "panels": panels or list(config["panels"]),
            "demo": bool(args.demo),
            "nonstandard_mode": bool(args.allow_missing_predictors),
        }
    )
    output_dir = _write_score_outputs(
        output_dir=args.output_dir,
        scores=scores,
        target_rows=target_rows,
        calibration=calibration,
        domain_rows=domain_rows,
        liability_rows=liability_rows,
        warnings=warnings,
        metadata=metadata,
    )
    print(
        f"Wrote {len(scores)} panel score row(s), explicit safety/ADME/liability audit tables, "
        f"{len(target_rows)} target-level binding row(s), warnings, hashes, and run metadata to {output_dir}"
    )
    if args.demo:
        observed = {row["compound"]: row["SWAN_MPO_score"] for row in scores}
        print("Demo scores:")
        for compound, score in sorted(observed.items()):
            print(f"  {compound}: {score:.12f}")


def cmd_show_calibration(args):
    rows = load_published_calibration()
    if args.output:
        write_csv(args.output, rows)
    else:
        print(json.dumps(rows, indent=2))


def cmd_reproduce(args):
    _require_locked_hash()
    scores, target, calibration, failures = run_packaged_demo()
    report = {
        "status": "PASS" if not failures else "FAIL",
        "locked_model_sha256": model_source_sha256(),
        "rows_checked": len(scores),
        "failures": failures,
        "note": "This packaged regression demo is synthetic and verifies the public raw-input architecture; it is not presented as the manuscript's Muricatacin raw-input reproduction dataset.",
    }
    print(json.dumps(report, indent=2))
    if args.output_dir:
        outdir = Path(args.output_dir)
        outdir.mkdir(parents=True, exist_ok=True)
        write_csv(outdir / "swan_panel_scores.csv", scores)
        write_csv(outdir / "target_level_binding.csv", target)
        write_csv(outdir / "target_calibration_used.csv", calibration)
        write_json(outdir / "reproduction_report.json", report)
    if report["status"] != "PASS":
        raise SystemExit(1)


def cmd_reproduce_manuscript(args):
    _require_locked_hash()
    adme_rows, adme_fields, tox_rows, tox_fields, dock_rows, dock_fields, config, calibration = _manuscript_inputs()
    scores, target_rows = score_pipeline(
        adme_rows, adme_fields, tox_rows, tox_fields, dock_rows, dock_fields,
        calibration, config, selected_panels=["Colon", "Prostate", "RCC"],
        require_full_panel_coverage=True
    )
    domain_rows, liability_rows = calculate_domain_audit_tables(
        adme_rows, adme_fields, tox_rows, tox_fields, config,
        selected_panels=["Colon", "Prostate", "RCC"]
    )
    warnings = collect_domain_warnings(adme_rows, adme_fields, tox_rows, tox_fields)
    warnings.extend(collect_method_warnings(config, calibration, selected_panels=["Colon", "Prostate", "RCC"]))
    report = run_manuscript_reproduction()
    metadata = base_run_metadata(
        command="reproduce-manuscript", config=config, warnings=warnings,
        input_paths=[]
    )
    metadata.update({
        "config": "published-oncology",
        "calibration_source": "published",
        "manuscript_reproduction": True,
        "source_manifest": "manuscript_source_manifest.json",
        "manuscript_adme_source": "manuscript_swissadme_canonical_full.csv",
        "manuscript_toxicity_source": "manuscript_protox_raw.csv",
        "manuscript_docking_source": "manuscript_candidate_docking.csv",
        "verification_status": report["status"],
        "manuscript_resource_hashes": report["resource_hashes"],
        "nonstandard_mode": False,
    })
    output_dir = _write_score_outputs(
        output_dir=args.output_dir, scores=scores, target_rows=target_rows, calibration=calibration,
        domain_rows=domain_rows, liability_rows=liability_rows, warnings=warnings, metadata=metadata
    )
    write_json(Path(output_dir) / "manuscript_reproduction_report.json", report)
    print(json.dumps(report, indent=2))
    if report["status"] != "PASS":
        raise SystemExit(1)


def cmd_redock_reference(args):
    rows, calibration, runs = run_vina_reference_redocking(
        args.targets_config,
        args.output_dir,
        vina_executable=args.vina_executable,
        rmsd_cutoff=args.rmsd_cutoff,
        enforce_version=args.require_vina_1_2_7,
    )
    print(
        f"Completed Vina reference redocking for {len(runs)} target(s). "
        f"Wrote {len(rows)} mode-level rows and {len(calibration)} calibration row(s) to {args.output_dir}"
    )


def cmd_explain_model(args):
    payload = {
        "model_version": MODEL_VERSION,
        "locked_model_sha256": model_source_sha256(),
        "specification": model_specification(),
        "workflow": {
            "ADME": "Raw SwissADME/property fields (complete export required) -> nine bounded desirabilities -> geometric mean adme_score. Consensus Log P is required; incomplete exports are rejected rather than imputed.",
            "Safety": "Raw LD50 + toxicity class -> acute_safety; five confidence-coded organ toxicity endpoints -> organ_safety; geometric mean -> safety_score.",
            "Liability": "Colon uses BBB + neurotoxicity only; Complex I is accepted in the shared toxicity table but explicitly excluded from the Colon liability geometric mean. Prostate and RCC use BBB + Complex I + neurotoxicity.",
            "Binding": "Candidate grid-level docking -> median dG per compound-target -> target-specific reference-redocking calibration -> target desirability -> BestNode across reference-calibrated panel targets.",
            "Final": "Equal-weight geometric mean of safety_score, adme_score, BestNode binding, and liability_score.",
        },
        "important_scope": "The CLI computes SWAN-MPO desirabilities and aggregation from raw predictor/docking outputs. It does not run SwissADME or ProTox. Candidate docking remains upstream. Reference-ligand Vina redocking can be run by redock-reference.",
    }
    if args.sources:
        resources = files("swan_mpo.resources")
        payload["threshold_provenance"] = read_json(resources / "threshold_sources.json")
        payload["threshold_provenance_document"] = "docs/THRESHOLD_PROVENANCE.md"
    if args.output:
        write_json(args.output, payload)
    else:
        print(json.dumps(payload, indent=2))


def cmd_verify(args):
    report = verify_installation(
        check_vina=args.check_vina or args.strict,
        vina_executable=args.vina_executable,
        strict=args.strict,
        check_manuscript=args.manuscript,
    )
    if args.vina_config:
        if not args.output_dir:
            raise InputValidationError("--vina-config requires --output-dir so the real Vina integration artifacts are preserved for review.")
        real = run_real_vina_integration(
            args.vina_config,
            vina_executable=args.vina_executable,
            output_dir=args.output_dir,
        )
        real.pop("_temporary_directory", None)
        report["real_vina_integration"] = real
        if real.get("status") != "PASS":
            report["status"] = "FAIL"
    print(json.dumps(report, indent=2))
    if args.report:
        write_json(args.report, report)
    if report["status"] != "PASS":
        raise SystemExit(1)


def add_raw_inputs(parser, *, required=False):
    parser.add_argument("--docking", required=required, help="Grid-level candidate docking CSV; SWAN computes each compound-target median.")
    parser.add_argument("--adme", required=required, help="Raw ADME/property export (SwissADME-compatible aliases supported).")
    parser.add_argument("--toxicity", required=required, help="Raw ProTox/toxicity export. Endpoint confidence may be embedded in each status or supplied in companion confidence columns.")
    parser.add_argument("--config", default="published-oncology", help="'published-oncology' or a JSON panel/target config.")
    parser.add_argument("--reference-redocking", help="Mode-level native/reference-ligand redocking CSV. If supplied, SWAN derives target calibration from these rows.")
    parser.add_argument("--calibration", default="published", help="Published frozen calibration or a calibration CSV. Ignored when --reference-redocking is supplied.")
    parser.add_argument("--column-map", help="Optional JSON mapping canonical field names to source columns.")
    parser.add_argument("--rmsd-cutoff", type=float, default=2.0, help="Heavy-atom RMSD cutoff used when deriving calibration from existing reference-redocking rows. Default 2.0 Å.")
    parser.add_argument("--allow-missing-predictors", action="store_true", help="Advanced historical-reproduction mode only: allow missing raw predictor cells and use the locked missing/default rules. Strict complete inputs are required by default.")


def build_parser():
    parser = argparse.ArgumentParser(
        prog="swan-mpo",
        description=(
            "SWAN-MPO: raw candidate docking + ADME + toxicity outputs -> automated desirabilities -> "
            "reference-calibrated BestNode -> final ranking. Candidate docking and SwissADME/ProTox prediction remain upstream; "
            "reference-ligand redocking can be executed directly with AutoDock Vina."
        ),
    )
    parser.add_argument("--version", action="version", version=f"swan-mpo {__version__} | model={MODEL_VERSION} | sha256={EXPECTED_LOCKED_SHA256} | expected-vina={EXPECTED_VINA_VERSION}")
    sub = parser.add_subparsers(dest="command", required=True)

    command = sub.add_parser("redock-reference", help="Run AutoDock Vina for configured native/reference ligands and derive target calibration.")
    command.add_argument("--targets-config", required=True, help="JSON containing receptor/native-ligand PDBQT paths and docking box for every target.")
    command.add_argument("--vina-executable", default="vina", help="Vina executable name or full path.")
    command.add_argument("--rmsd-cutoff", type=float, default=None, help="Override RMSD cutoff from config (usually 2.0 Å).")
    command.add_argument("--require-vina-1-2-7", action="store_true", help=f"Fail unless the executable reports AutoDock Vina {EXPECTED_VINA_VERSION}.")
    command.add_argument("--output-dir", required=True)
    command.set_defaults(func=cmd_redock_reference)

    command = sub.add_parser("calibrate-targets", help="Derive per-target reference calibration from an existing mode-level reference-redocking CSV.")
    command.add_argument("--reference-redocking", required=True)
    command.add_argument("--column-map")
    command.add_argument("--rmsd-cutoff", type=float, default=2.0)
    command.add_argument("--output", required=True)
    command.set_defaults(func=cmd_calibrate)

    command = sub.add_parser("explain-model", help="Show frozen transformations and how raw inputs become SWAN-MPO scores.")
    command.add_argument("--sources", action="store_true", help="Also show literature provenance and which outer anchors are SWAN-MPO design choices.")
    command.add_argument("--output")
    command.set_defaults(func=cmd_explain_model)

    command = sub.add_parser("validate", help="Validate candidate docking, ADME, toxicity, and target calibration before scoring.")
    add_raw_inputs(command, required=True)
    command.set_defaults(func=cmd_validate)

    command = sub.add_parser("score", help="Compute all SWAN-MPO domains, BestNode binding, final scores, ranks, warnings, and audit outputs.")
    add_raw_inputs(command, required=False)
    command.add_argument("--demo", action="store_true", help="Run the bundled synthetic raw-input regression example. No external input files are required.")
    command.add_argument("--panels", help="Comma-separated subset of configured panels.")
    command.add_argument("--primary-only", action="store_true", help="Require docking coverage only for reference-calibrated BestNode targets; default requires all configured panel targets.")
    command.add_argument("--output-dir", required=True)
    command.set_defaults(func=cmd_score)

    command = sub.add_parser("show-published-calibration", help="Display/export the frozen published redocking-derived calibration.")
    command.add_argument("--output")
    command.set_defaults(func=cmd_show_calibration)

    command = sub.add_parser("reproduce-example", help="Run the packaged synthetic raw-input end-to-end regression example.")
    command.add_argument("--output-dir")
    command.set_defaults(func=cmd_reproduce)

    command = sub.add_parser("reproduce-manuscript", help="Recompute the frozen 59-compound expanded screen from packaged raw predictor/scoring inputs and compare all 177 panel rows with canonical expected outputs.")
    command.add_argument("--output-dir", required=True)
    command.set_defaults(func=cmd_reproduce_manuscript)

    command = sub.add_parser("verify", help="Verify the locked model, published calibration, packaged demo, and optionally the local Vina installation / real redocking path.")
    command.add_argument("--check-vina", action="store_true", help=f"Require AutoDock Vina {EXPECTED_VINA_VERSION} on this machine.")
    command.add_argument("--vina-executable", default="vina")
    command.add_argument("--vina-config", help="Run an actual end-to-end Vina reference-redocking integration using this target config. Requires Vina 1.2.7.")
    command.add_argument("--output-dir", help="Directory for real Vina integration artifacts when --vina-config is used.")
    command.add_argument("--report", help="Optional JSON path for the verification report.")
    command.add_argument("--manuscript", action="store_true", help="Also run the packaged 59-compound/177-panel-row manuscript reproduction regression.")
    command.add_argument("--strict", action="store_true", help="Strict release verification: manuscript reproduction + exact Vina 1.2.7 + pinned runtime package versions + Python 3.13.x.")
    command.set_defaults(func=cmd_verify)

    return parser


def main(argv=None):
    args = build_parser().parse_args(argv)
    try:
        args.func(args)
    except SwanMPOError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(2)


if __name__ == "__main__":
    main()
