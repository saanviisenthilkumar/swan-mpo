from __future__ import annotations

from .calibration import calibration_index
from .config import normalize_panel


def collect_method_warnings(config, calibration_rows, *, selected_panels=None, allow_missing_predictors=False, primary_only=False):
    """Return non-fatal workflow warnings that affect interpretation, not arithmetic."""
    warnings = []
    calibration = calibration_index(calibration_rows)
    panels = [normalize_panel(p) for p in (selected_panels or list(config.get("panels", {})))]

    for panel in panels:
        panel_targets = config.get("panels", {}).get(panel, [])
        eligible = [
            target for target in panel_targets
            if calibration.get(target, {}).get("calibration_status") == "reference_calibrated"
        ]
        if len(eligible) == 1:
            warnings.append({
                "code": "PANEL_SINGLE_NODE_BESTNODE",
                "compound": "",
                "field": "BestNode",
                "value": eligible[0],
                "message": (
                    f"Panel {panel} has a single reference-calibrated target ({eligible[0]}); "
                    "primary BestNode is therefore a single-node binding summary rather than a multi-target selection."
                ),
            })

    if allow_missing_predictors:
        warnings.append({
            "code": "NONSTANDARD_MODE_ACTIVATED",
            "compound": "",
            "field": "allow_missing_predictors",
            "value": True,
            "message": (
                "--allow-missing-predictors is active. Results use the locked historical missing/default rules, "
                "are outside the standard complete-input workflow, and should be disclosed if reported."
            ),
        })

    if primary_only:
        warnings.append({
            "code": "PRIMARY_ONLY_COVERAGE_MODE",
            "compound": "",
            "field": "primary_only",
            "value": True,
            "message": (
                "--primary-only is active. Candidate docking coverage is required only for reference-calibrated "
                "BestNode targets rather than every configured panel target."
            ),
        })

    return warnings
