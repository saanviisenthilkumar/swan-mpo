from __future__ import annotations

from .pipeline import (
    standardize_compound_table,
    standardize_toxicity_table,
    aggregate_candidate_docking,
    validate_predictor_values,
    build_target_binding,
)
from .columns import ADME_ALIASES
from .calibration import calibration_index
from .errors import InputValidationError


def validate_pipeline(
    adme_rows,
    adme_fields,
    tox_rows,
    tox_fields,
    docking_rows,
    docking_fields,
    calibration_rows,
    config,
    *,
    adme_map=None,
    tox_map=None,
    docking_map=None,
    allow_missing_predictors=False,
):
    adme = standardize_compound_table(adme_rows, adme_fields, ADME_ALIASES, adme_map, "ADME")
    tox = standardize_toxicity_table(tox_rows, tox_fields, tox_map, "toxicity")
    validate_predictor_values(adme, tox, allow_missing=allow_missing_predictors)

    dock_summary = aggregate_candidate_docking(
        docking_rows,
        docking_fields,
        column_map=docking_map,
        expected_grids=config.get("expected_grid_centers", 20),
        require_exact_grids=True,
    )
    calibration = calibration_index(calibration_rows)

    if {row["compound_key"] for row in adme} != {row["compound_key"] for row in tox}:
        raise InputValidationError("ADME and toxicity compound sets do not match.")
    if {row["compound_key"] for row in adme} != {row["compound_key"] for row in dock_summary}:
        raise InputValidationError("Property and docking compound sets do not match.")

    targets = sorted({row["target"] for row in dock_summary})
    configured_targets = sorted({target for targets_ in config["panels"].values() for target in targets_})
    missing_calibration = sorted(target for target in configured_targets if target not in calibration)
    if missing_calibration:
        raise InputValidationError(
            f"Configured target(s) lack redocking/calibration records: {missing_calibration}."
        )

    # This also catches calibrated targets with non-negative candidate medians.
    build_target_binding(dock_summary, calibration_rows)

    calibrated = sorted(
        target
        for target in targets
        if calibration.get(target, {}).get("calibration_status") == "reference_calibrated"
    )
    comparative = sorted(
        target
        for target in targets
        if calibration.get(target, {}).get("calibration_status") != "reference_calibrated"
    )
    unconfigured = sorted(set(targets) - set(configured_targets))
    return {
        "status": "PASS",
        "compounds": len(adme),
        "docking_target_blocks": len(dock_summary),
        "targets": targets,
        "reference_calibrated_targets": calibrated,
        "comparative_or_uncalibrated_targets": comparative,
        "unconfigured_docking_targets": unconfigured,
        "expected_grid_centers": config.get("expected_grid_centers", 20),
    }
