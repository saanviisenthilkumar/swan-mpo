from __future__ import annotations

import math
import statistics
from collections import defaultdict

from .columns import (
    ADME_ALIASES,
    TOX_ALIASES,
    TOX_CONF_ALIASES,
    DOCK_ALIASES,
    resolve_columns,
    resolve_optional_column,
)
from .config import normalize_target, normalize_panel
from .errors import InputValidationError
from .locked_model import (
    calculate_adme,
    calculate_safety,
    calculate_liability,
    calculate_swan,
    reference_calibrated_binding,
    as_float,
    parse_status,
    parse_confidence,
)
from .calibration import calibration_index


def _compound_key(value):
    return "".join(ch for ch in str(value).lower() if ch.isalnum())


def _rank_min_desc(values):
    ordered = sorted(set(values), reverse=True)
    pos = 1
    ranks = {}
    for value in ordered:
        ranks[value] = pos
        pos += values.count(value)
    return [ranks[value] for value in values]


def standardize_compound_table(rows, fields, aliases, column_map, table_name):
    mapping = resolve_columns(fields, aliases, column_map, table=table_name)
    out = []
    seen = set()
    for row_number, row in enumerate(rows, start=2):
        compound = str(row[mapping["compound"]]).strip()
        key = _compound_key(compound)
        if not compound:
            raise InputValidationError(f"{table_name} row {row_number}: compound is blank.")
        if key in seen:
            raise InputValidationError(
                f"{table_name} row {row_number}: duplicate compound {compound!r}. "
                "Each compound must appear once in each predictor table."
            )
        seen.add(key)
        normalized = {"compound": compound, "compound_key": key}
        for canonical, column in mapping.items():
            if canonical != "compound":
                normalized[canonical] = row.get(column, "")
        out.append(normalized)
    if not out:
        raise InputValidationError(f"{table_name} contains no rows.")
    return out


def _status_with_optional_confidence(status_value, confidence_value):
    """Return a single confidence-coded endpoint string without changing locked math.

    The locked model consumes strings such as ``Inactive (0.84)``. Public inputs may
    supply either that combined representation or separate status/confidence columns.
    This adapter only combines raw fields; it does not alter the scoring equation.
    """
    status = str(status_value).strip()
    existing = parse_confidence(status)
    separate = as_float(confidence_value)
    if math.isfinite(existing):
        if math.isfinite(separate) and abs(existing - separate) > 1e-9:
            raise InputValidationError(
                f"Endpoint contains confidence {existing:g} but companion confidence column contains {separate:g}. "
                "Provide one unambiguous confidence value."
            )
        return status
    if math.isfinite(separate):
        return f"{status} ({separate:g})"
    return status


def standardize_toxicity_table(rows, fields, column_map=None, table_name="toxicity"):
    """Standardize toxicity inputs and merge optional separate confidence columns."""
    column_map = column_map or {}
    core_map = resolve_columns(fields, TOX_ALIASES, column_map, table=table_name)

    confidence_columns = {}
    for canonical, aliases in TOX_CONF_ALIASES.items():
        if canonical in column_map:
            col = column_map[canonical]
            if col not in fields:
                raise InputValidationError(
                    f"{table_name}: mapped confidence column {col!r} for {canonical!r} does not exist."
                )
            confidence_columns[canonical] = col
        else:
            confidence_columns[canonical] = resolve_optional_column(fields, aliases)

    endpoint_to_conf = {
        "hepato": "hepato_confidence",
        "neuro": "neuro_confidence",
        "nephro": "nephro_confidence",
        "respi": "respi_confidence",
        "cardio": "cardio_confidence",
        "bbb": "bbb_confidence",
        "complex_i": "complex_i_confidence",
    }

    out = []
    seen = set()
    for row_number, row in enumerate(rows, start=2):
        compound = str(row[core_map["compound"]]).strip()
        key = _compound_key(compound)
        if not compound:
            raise InputValidationError(f"{table_name} row {row_number}: compound is blank.")
        if key in seen:
            raise InputValidationError(f"{table_name} row {row_number}: duplicate compound {compound!r}.")
        seen.add(key)
        normalized = {"compound": compound, "compound_key": key}
        for canonical, column in core_map.items():
            if canonical == "compound":
                continue
            value = row.get(column, "")
            if canonical in endpoint_to_conf:
                conf_col = confidence_columns.get(endpoint_to_conf[canonical])
                conf_value = row.get(conf_col, "") if conf_col else ""
                try:
                    value = _status_with_optional_confidence(value, conf_value)
                except InputValidationError as exc:
                    raise InputValidationError(f"{compound}: {canonical}: {exc}") from exc
            normalized[canonical] = value
        out.append(normalized)
    if not out:
        raise InputValidationError(f"{table_name} contains no rows.")
    return out


def validate_predictor_values(adme_rows, tox_rows, *, allow_missing=False):
    def missing(value):
        return value is None or str(value).strip().lower() in {"", "na", "nan", "none", "null"}

    for row in adme_rows:
        compound = row["compound"]
        numeric = [
            "mw",
            "consensus_logp",
            "tpsa",
            "rotatable_bonds",
            "hba",
            "hbd",
            "pains_alerts",
            "synthetic_accessibility",
        ]
        for field in numeric:
            if missing(row.get(field)):
                if allow_missing:
                    continue
                raise InputValidationError(
                    f"{compound}: ADME field {field!r} is missing. "
                    "See examples/templates/swissadme_input_template.csv. "
                    "Use --allow-missing-predictors only to reproduce the locked historical missing-value rule."
                )
            value = as_float(row.get(field))
            if not math.isfinite(value):
                raise InputValidationError(
                    f"{compound}: ADME field {field!r} is not numeric: {row.get(field)!r}."
                )
        if not allow_missing:
            if as_float(row["mw"]) <= 0 or as_float(row["synthetic_accessibility"]) <= 0:
                raise InputValidationError(f"{compound}: MW and synthetic accessibility must be positive.")
            for field in ["tpsa", "rotatable_bonds", "hba", "hbd", "pains_alerts"]:
                if as_float(row[field]) < 0:
                    raise InputValidationError(f"{compound}: ADME field {field!r} cannot be negative.")
            gi = str(row.get("gi_absorption", "")).strip().lower()
            if gi not in {"high", "low"}:
                raise InputValidationError(
                    f"{compound}: GI absorption must be 'High' or 'Low' in the standard workflow; "
                    f"got {row.get('gi_absorption')!r}. See examples/templates/swissadme_input_template.csv."
                )

    for row in tox_rows:
        compound = row["compound"]
        for field in ["ld50_mgkg", "toxicity_class"]:
            if missing(row.get(field)):
                if allow_missing:
                    continue
                raise InputValidationError(
                    f"{compound}: toxicity field {field!r} is missing. "
                    "See examples/templates/protox_input_template.csv."
                )
            value = as_float(row.get(field))
            if not math.isfinite(value):
                raise InputValidationError(
                    f"{compound}: toxicity field {field!r} is not numeric: {row.get(field)!r}."
                )
        if not allow_missing:
            if as_float(row["ld50_mgkg"]) <= 0:
                raise InputValidationError(f"{compound}: LD50 must be positive.")
            toxicity_class = as_float(row["toxicity_class"])
            if toxicity_class < 1 or toxicity_class > 6 or int(toxicity_class) != toxicity_class:
                raise InputValidationError(
                    f"{compound}: toxicity class must be an integer in the 1–6 ProTox range; got {row['toxicity_class']!r}."
                )

        for field in ["hepato", "neuro", "nephro", "respi", "cardio", "bbb", "complex_i"]:
            if missing(row.get(field)):
                if allow_missing:
                    continue
                raise InputValidationError(
                    f"{compound}: toxicity endpoint {field!r} is missing. "
                    "Each endpoint requires Active/Inactive status plus prediction confidence. "
                    "See examples/templates/protox_input_template.csv."
                )
            status = parse_status(row.get(field))
            if status is None and not allow_missing:
                raise InputValidationError(
                    f"{compound}: toxicity endpoint {field!r} must include Active or Inactive status; "
                    f"got {row.get(field)!r}."
                )
            confidence = parse_confidence(row.get(field))
            if not allow_missing:
                if not math.isfinite(confidence):
                    raise InputValidationError(
                        f"{compound}: toxicity endpoint {field!r} has no prediction confidence. "
                        "Provide a combined value such as 'Inactive (0.82)' or a companion confidence column "
                        f"such as '{field}_confidence'. See examples/templates/protox_input_template.csv."
                    )
                if confidence < 0.5 or confidence > 1.0:
                    raise InputValidationError(
                        f"{compound}: toxicity endpoint {field!r} confidence must be in [0.5, 1.0] "
                        f"for the locked standard workflow; got {confidence:g}."
                    )
    return True


def aggregate_candidate_docking(rows, fields, *, column_map=None, expected_grids=20, require_exact_grids=True):
    mapping = resolve_columns(fields, DOCK_ALIASES, column_map, table="candidate docking")
    groups = defaultdict(list)
    names = {}
    for row_number, row in enumerate(rows, start=2):
        compound = str(row[mapping["compound"]]).strip()
        key = _compound_key(compound)
        target = normalize_target(row[mapping["target"]])
        pdb_id = str(row[mapping["pdb_id"]]).strip().upper()
        grid_id = str(row[mapping["grid_id"]]).strip()
        dg = as_float(row[mapping["dg"]])
        if not compound or not target or not pdb_id or not grid_id:
            raise InputValidationError(
                f"Candidate docking row {row_number}: compound, target, pdb_id, and grid_id are required."
            )
        # Individual Vina grid values may be weak or even positive. The primary model
        # evaluates the median and only requires a negative median for a calibrated target.
        if not math.isfinite(dg):
            raise InputValidationError(
                f"Candidate docking row {row_number}: docking affinity must be finite; got {row[mapping['dg']]!r}."
            )
        groups[(key, target, pdb_id)].append((grid_id, float(dg)))
        names[key] = compound

    out = []
    for (key, target, pdb_id), values in sorted(groups.items()):
        grid_ids = [value[0] for value in values]
        if len(grid_ids) != len(set(grid_ids)):
            raise InputValidationError(f"Duplicate grid_id detected for {names[key]} / {target}.")
        if require_exact_grids and expected_grids is not None and len(values) != int(expected_grids):
            raise InputValidationError(
                f"{names[key]} / {target}: found {len(values)} unique grid rows; expected exactly {expected_grids}. "
                "The published workflow requires one row per prespecified grid center. "
                "See examples/templates/candidate_docking_template.csv."
            )
        energies = [value[1] for value in values]
        out.append(
            {
                "compound": names[key],
                "compound_key": key,
                "target": target,
                "pdb_id": pdb_id,
                "n_grid_centers": len(values),
                "best_dg": min(energies),
                "median_dg": statistics.median(energies),
                "mean_dg": statistics.fmean(energies),
                "n_nonnegative_grid_energies": sum(value >= 0 for value in energies),
            }
        )
    if not out:
        raise InputValidationError("Candidate docking input contains no scorable rows.")
    return out


def build_target_binding(dock_summary, calibration_rows):
    calibration = calibration_index(calibration_rows)
    out = []
    for row in dock_summary:
        cal = calibration.get(row["target"])
        if cal:
            cal_pdb = str(cal.get("pdb_id", "")).strip().upper()
            dock_pdb = str(row.get("pdb_id", "")).strip().upper()
            if cal_pdb and dock_pdb and cal_pdb != dock_pdb:
                raise InputValidationError(
                    f"{row['compound']} / {row['target']}: candidate docking PDB {dock_pdb} "
                    f"does not match calibration PDB {cal_pdb}."
                )
        reference_dg = as_float(cal.get("reference_dg")) if cal else float("nan")
        status = cal.get("calibration_status", "missing_calibration") if cal else "missing_calibration"
        if status == "reference_calibrated" and math.isfinite(reference_dg) and row["median_dg"] >= 0:
            raise InputValidationError(
                f"{row['compound']} / {row['target']}: median docking energy is {row['median_dg']:.4g} kcal/mol. "
                "Reference-calibrated binding requires a finite negative median energy; inspect the candidate docking run."
            )
        binding = (
            reference_calibrated_binding(row["median_dg"], reference_dg)
            if math.isfinite(reference_dg)
            else float("nan")
        )
        combined = dict(row)
        combined["calibration_status"] = status
        combined["validation_class"] = cal.get("validation_class", "") if cal else ""
        combined["reference_dg"] = reference_dg if math.isfinite(reference_dg) else ""
        combined["binding_reference_calibrated"] = binding if math.isfinite(binding) else ""
        out.append(combined)
    return out


def _panel_coverage(target_binding, config, selected_panels=None, require_full_panel_coverage=True):
    selected = [normalize_panel(panel) for panel in (selected_panels or list(config["panels"]))]
    present = defaultdict(set)
    compounds = {}
    for row in target_binding:
        present[row["compound_key"]].add(row["target"])
        compounds[row["compound_key"]] = row["compound"]
    if require_full_panel_coverage:
        for key in present:
            for panel in selected:
                required = set(config["panels"].get(panel, []))
                missing = required - present[key]
                if missing:
                    raise InputValidationError(
                        f"{compounds[key]}: docking is missing target(s) {sorted(missing)} required by panel {panel}. "
                        "Use --primary-only only when you intentionally want to require coverage of reference-calibrated BestNode targets rather than every configured panel target."
                    )
    return selected


def bestnode_by_panel(
    target_binding,
    config,
    calibration_rows,
    selected_panels=None,
    require_full_panel_coverage=True,
):
    selected = _panel_coverage(target_binding, config, selected_panels, require_full_panel_coverage)
    calibration = calibration_index(calibration_rows)
    configured_targets = sorted({target for panel in selected for target in config["panels"].get(panel, [])})
    missing_cal = [target for target in configured_targets if target not in calibration]
    if missing_cal:
        raise InputValidationError(
            f"Configuration target(s) lack a redocking/calibration record: {missing_cal}. "
            "Every configured target must be explicitly reference-calibrated or marked comparative-only."
        )

    by_compound = defaultdict(list)
    names = {}
    for row in target_binding:
        by_compound[row["compound_key"]].append(row)
        names[row["compound_key"]] = row["compound"]

    out = []
    for key, rows in sorted(by_compound.items()):
        by_target = {row["target"]: row for row in rows}
        for panel in selected:
            panel_targets = config["panels"].get(panel)
            if not panel_targets:
                raise InputValidationError(f"Unknown panel {panel!r} in configuration.")
            eligible = [
                target
                for target in panel_targets
                if calibration.get(target, {}).get("calibration_status") == "reference_calibrated"
            ]
            available = []
            for target in eligible:
                row = by_target.get(target)
                if row and row.get("binding_reference_calibrated") != "":
                    available.append(row)
            if not available:
                raise InputValidationError(
                    f"{names[key]} / {panel}: no reference-calibrated target is available for primary BestNode binding."
                )
            priority = config.get("bestnode_tie_priority", {}).get(panel, eligible)
            priority_index = {target: index for index, target in enumerate(priority)}
            available.sort(
                key=lambda row: (
                    -float(row["binding_reference_calibrated"]),
                    priority_index.get(row["target"], 10**6),
                    row["target"],
                )
            )
            best = available[0]
            second = available[1] if len(available) > 1 else None
            best_value = float(best["binding_reference_calibrated"])
            second_value = float(second["binding_reference_calibrated"]) if second else float("nan")
            ratio = best_value / second_value if second and second_value > 0 else float("nan")
            out.append(
                {
                    "compound": names[key],
                    "compound_key": key,
                    "panel": panel,
                    "n_total_panel_targets": len(panel_targets),
                    "n_calibrated_panel_targets": len(eligible),
                    "selected_best_node": best["target"],
                    "selected_best_node_pdb": best["pdb_id"],
                    "bestnode_binding": best_value,
                    "second_best_node": second["target"] if second else "",
                    "second_bestnode_binding": second_value if second else "",
                    "best_to_second_ratio": ratio if math.isfinite(ratio) else "",
                    "selected_node_median_dg": best["median_dg"],
                    "selected_node_reference_dg": best["reference_dg"],
                }
            )
    return out


def score_pipeline(
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
    selected_panels=None,
    require_full_panel_coverage=True,
    allow_missing_predictors=False,
):
    adme = standardize_compound_table(adme_rows, adme_fields, ADME_ALIASES, adme_map, "ADME")
    tox = standardize_toxicity_table(tox_rows, tox_fields, tox_map, "toxicity")
    validate_predictor_values(adme, tox, allow_missing=allow_missing_predictors)
    adme_index = {row["compound_key"]: row for row in adme}
    tox_index = {row["compound_key"]: row for row in tox}
    if set(adme_index) != set(tox_index):
        only_adme = sorted(set(adme_index) - set(tox_index))
        only_tox = sorted(set(tox_index) - set(adme_index))
        raise InputValidationError(
            f"ADME/toxicity compound sets do not match. ADME-only keys={only_adme[:10]}; toxicity-only keys={only_tox[:10]}."
        )

    dock_summary = aggregate_candidate_docking(
        docking_rows,
        docking_fields,
        column_map=docking_map,
        expected_grids=config.get("expected_grid_centers", 20),
        require_exact_grids=True,
    )
    dock_keys = {row["compound_key"] for row in dock_summary}
    if dock_keys != set(adme_index):
        raise InputValidationError(
            "Docking compound set does not match ADME/toxicity compound set. "
            f"Docking-only={sorted(dock_keys-set(adme_index))[:10]}; "
            f"properties-only={sorted(set(adme_index)-dock_keys)[:10]}."
        )

    target_binding = build_target_binding(dock_summary, calibration_rows)
    bestnodes = bestnode_by_panel(
        target_binding,
        config,
        calibration_rows,
        selected_panels,
        require_full_panel_coverage,
    )

    outputs = []
    for best in bestnodes:
        adme_row = adme_index[best["compound_key"]]
        tox_row = tox_index[best["compound_key"]]
        adme_result = calculate_adme(
            mw=adme_row["mw"],
            consensus_logp=adme_row["consensus_logp"],
            tpsa=adme_row["tpsa"],
            rotatable_bonds=adme_row["rotatable_bonds"],
            hba=adme_row["hba"],
            hbd=adme_row["hbd"],
            pains_alerts=adme_row["pains_alerts"],
            gi_absorption=adme_row["gi_absorption"],
            synthetic_accessibility=adme_row["synthetic_accessibility"],
        )
        safety_result = calculate_safety(
            ld50_mgkg=tox_row["ld50_mgkg"],
            toxicity_class=tox_row["toxicity_class"],
            hepato=tox_row["hepato"],
            neuro=tox_row["neuro"],
            nephro=tox_row["nephro"],
            respi=tox_row["respi"],
            cardio=tox_row["cardio"],
        )
        liability_result = calculate_liability(
            panel=best["panel"],
            bbb=tox_row["bbb"],
            complex_i=tox_row["complex_i"],
            neuro=tox_row["neuro"],
        )
        score = calculate_swan(
            safety_score=safety_result["safety_score"],
            adme_score=adme_result["adme_score"],
            binding_score=best["bestnode_binding"],
            liability_score=liability_result["liability_score"],
        )
        if not math.isfinite(score):
            raise InputValidationError(
                f"{best['compound']} / {best['panel']}: final score is missing; inspect raw inputs and target calibration."
            )
        combined = {
            **best,
            "safety_score": safety_result["safety_score"],
            "adme_score": adme_result["adme_score"],
            "liability_score": liability_result["liability_score"],
            "SWAN_MPO_score": score,
            **{
                key: value
                for key, value in safety_result.items()
                if key.startswith("d_") or key in {"acute_safety", "organ_safety"}
            },
            **{key: value for key, value in adme_result.items() if key.startswith("d_")},
            **{key: value for key, value in liability_result.items() if key.startswith("d_")},
        }
        outputs.append(combined)

    panel_groups = defaultdict(list)
    for index, row in enumerate(outputs):
        panel_groups[row["panel"]].append(index)
    for indexes in panel_groups.values():
        score_ranks = _rank_min_desc([outputs[index]["SWAN_MPO_score"] for index in indexes])
        binding_ranks = _rank_min_desc([outputs[index]["bestnode_binding"] for index in indexes])
        for index, rank, binding_rank in zip(indexes, score_ranks, binding_ranks):
            outputs[index]["SWAN_MPO_rank"] = rank
            outputs[index]["bestnode_binding_rank"] = binding_rank
    return outputs, target_binding
