#!/usr/bin/env python3
"""SWAN-MPO v1.0 locked mathematical model.

Canonical specification:
- Safety, ADME, and liability component equations reproduce the SWAN-MPO v3
  component outputs used by the accepted internal discovery rerun.
- Binding is reference-redocking calibrated BestNode binding.
- Final aggregation is an equal-weight geometric mean.
- The old nonlinear safety gate, CRITIC weighting, entropy weighting, and old
  hybrid binding implementation are intentionally excluded.

Dataset adapters may rename columns and select a panel. They must not redefine
any constants or scoring equations contained in this module.
"""

from __future__ import annotations

import hashlib
import math
import re
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Iterable, Mapping, Any

import numpy as np


MODEL_VERSION = "SWAN-MPO-v1.0-locked"
MODEL_FLOOR = 0.01
MODEL_CEILING = 1.00


@dataclass(frozen=True)
class ModelSpecification:
    version: str = MODEL_VERSION
    floor: float = MODEL_FLOOR
    ceiling: float = MODEL_CEILING

    # ADME desirability anchors
    mw_good_max: float = 500.0
    mw_bad_max: float = 800.0
    logp_low_bad: float = -2.0
    logp_low_good: float = 1.0
    logp_high_good: float = 5.0
    logp_high_bad: float = 8.0
    tpsa_good_max: float = 140.0
    tpsa_bad_max: float = 220.0
    rot_bonds_good_max: float = 10.0
    rot_bonds_bad_max: float = 28.0
    hba_good_max: float = 10.0
    hba_bad_max: float = 15.0
    hbd_good_max: float = 5.0
    hbd_bad_max: float = 8.0
    sa_good_max: float = 4.0
    sa_bad_max: float = 8.0
    pains_present: float = 0.25
    pains_missing: float = 0.50
    gi_high: float = 1.00
    gi_low: float = 0.35
    gi_unknown: float = 0.50

    # Toxicity handling
    toxicity_default_confidence: float = 0.50
    ld50_low_mgkg: float = 50.0
    ld50_high_mgkg: float = 5000.0


SPEC = ModelSpecification()


def model_source_sha256() -> str:
    return hashlib.sha256(Path(__file__).read_bytes()).hexdigest()


def model_specification() -> dict[str, Any]:
    return asdict(SPEC)


def _is_missing(value: Any) -> bool:
    if value is None:
        return True
    try:
        return bool(np.isnan(value))
    except Exception:
        text = str(value).strip().lower()
        return text in {"", "nan", "na", "none", "null"}


def as_float(value: Any) -> float:
    if _is_missing(value):
        return float("nan")
    try:
        return float(value)
    except Exception:
        match = re.search(r"-?\d+(?:\.\d+)?(?:[eE][+-]?\d+)?", str(value).replace(",", ""))
        return float(match.group(0)) if match else float("nan")


def clip01(value: Any, floor: float = MODEL_FLOOR, ceiling: float = MODEL_CEILING) -> float:
    value = as_float(value)
    if math.isnan(value):
        return float("nan")
    return min(max(value, floor), ceiling)


def geometric_mean(values: Iterable[Any], floor: float = MODEL_FLOOR) -> float:
    """Canonical missing-value rule: omit missing terms, then average log desirabilities."""
    clean: list[float] = []
    for value in values:
        numeric = as_float(value)
        if not math.isnan(numeric):
            clean.append(clip01(numeric, floor=floor))
    if not clean:
        return float("nan")
    return math.exp(sum(math.log(max(value, floor)) for value in clean) / len(clean))


def parse_status(value: Any) -> str | None:
    text = str(value).lower()
    if "inactive" in text:
        return "Inactive"
    if "active" in text:
        return "Active"
    return None


def parse_confidence(value: Any) -> float:
    if _is_missing(value):
        return float("nan")
    match = re.search(r"\d*\.?\d+", str(value))
    return float(match.group(0)) if match else float("nan")


def toxicity_endpoint_desirability(value: Any, default_confidence: float = SPEC.toxicity_default_confidence) -> float:
    status = parse_status(value)
    confidence = parse_confidence(value)
    if math.isnan(confidence):
        confidence = default_confidence
    if status == "Inactive":
        desirability = confidence
    elif status == "Active":
        desirability = 1.0 - confidence
    else:
        desirability = default_confidence
    return clip01(desirability)


def ld50_desirability(ld50_mgkg: Any) -> float:
    value = as_float(ld50_mgkg)
    if math.isnan(value) or value <= 0:
        return float("nan")
    desirability = (
        math.log10(value) - math.log10(SPEC.ld50_low_mgkg)
    ) / (
        math.log10(SPEC.ld50_high_mgkg) - math.log10(SPEC.ld50_low_mgkg)
    )
    return clip01(desirability)


def toxicity_class_desirability(toxicity_class: Any) -> float:
    value = as_float(toxicity_class)
    if math.isnan(value):
        return float("nan")
    return clip01((value - 1.0) / 5.0)


def linear_decrease(value: Any, good_max: float, bad_max: float, floor: float = MODEL_FLOOR) -> float:
    value = as_float(value)
    if math.isnan(value):
        return float("nan")
    if value <= good_max:
        return 1.0
    if value >= bad_max:
        return floor
    return clip01(1.0 - ((value - good_max) / (bad_max - good_max)) * (1.0 - floor), floor=floor)


def linear_range(
    value: Any,
    low_good: float,
    high_good: float,
    low_bad: float,
    high_bad: float,
    floor: float = MODEL_FLOOR,
) -> float:
    value = as_float(value)
    if math.isnan(value):
        return float("nan")
    if low_good <= value <= high_good:
        return 1.0
    if value <= low_bad or value >= high_bad:
        return floor
    if value < low_good:
        return clip01(floor + ((value - low_bad) / (low_good - low_bad)) * (1.0 - floor), floor=floor)
    return clip01(1.0 - ((value - high_good) / (high_bad - high_good)) * (1.0 - floor), floor=floor)


def calculate_safety(
    *,
    ld50_mgkg: Any,
    toxicity_class: Any,
    hepato: Any,
    neuro: Any,
    nephro: Any,
    respi: Any,
    cardio: Any,
) -> dict[str, float]:
    d_ld50 = ld50_desirability(ld50_mgkg)
    d_tox_class = toxicity_class_desirability(toxicity_class)
    d_hepato = toxicity_endpoint_desirability(hepato)
    d_neuro = toxicity_endpoint_desirability(neuro)
    d_nephro = toxicity_endpoint_desirability(nephro)
    d_respi = toxicity_endpoint_desirability(respi)
    d_cardio = toxicity_endpoint_desirability(cardio)

    acute_safety = geometric_mean([d_ld50, d_tox_class])
    organ_safety = geometric_mean([d_hepato, d_neuro, d_nephro, d_respi, d_cardio])
    safety_score = geometric_mean([acute_safety, organ_safety])

    return {
        "d_ld50": d_ld50,
        "d_tox_class": d_tox_class,
        "d_hepato": d_hepato,
        "d_neuro": d_neuro,
        "d_nephro": d_nephro,
        "d_respi": d_respi,
        "d_cardio": d_cardio,
        "acute_safety": acute_safety,
        "organ_safety": organ_safety,
        "safety_score": safety_score,
    }


def calculate_liability(*, panel: str, bbb: Any, complex_i: Any, neuro: Any) -> dict[str, float]:
    d_bbb = toxicity_endpoint_desirability(bbb)
    d_complex_i = toxicity_endpoint_desirability(complex_i)
    d_neuro = toxicity_endpoint_desirability(neuro)

    panel_key = re.sub(r"[^a-z0-9]+", "", str(panel).lower())
    if panel_key in {"colon", "colorectal", "crc"}:
        liability_score = geometric_mean([d_bbb, d_neuro])
    elif panel_key in {"prostate", "rcc", "renalcellcarcinoma", "kidney"}:
        liability_score = geometric_mean([d_bbb, d_complex_i, d_neuro])
    else:
        raise ValueError(
            f"Unsupported panel {panel!r}. Canonical liability requires one of Colon, Prostate, or RCC."
        )

    return {
        "d_bbb": d_bbb,
        "d_complex_i": d_complex_i,
        "d_neuro_liability": d_neuro,
        "liability_score": liability_score,
    }


def calculate_adme(
    *,
    mw: Any,
    consensus_logp: Any,
    tpsa: Any,
    rotatable_bonds: Any,
    hba: Any,
    hbd: Any,
    pains_alerts: Any,
    gi_absorption: Any,
    synthetic_accessibility: Any,
) -> dict[str, float]:
    d_mw = linear_decrease(mw, SPEC.mw_good_max, SPEC.mw_bad_max)
    d_logp = linear_range(
        consensus_logp,
        SPEC.logp_low_good,
        SPEC.logp_high_good,
        SPEC.logp_low_bad,
        SPEC.logp_high_bad,
    )
    d_tpsa = linear_decrease(tpsa, SPEC.tpsa_good_max, SPEC.tpsa_bad_max)
    d_rot_bonds = linear_decrease(rotatable_bonds, SPEC.rot_bonds_good_max, SPEC.rot_bonds_bad_max)
    d_hba = linear_decrease(hba, SPEC.hba_good_max, SPEC.hba_bad_max)
    d_hbd = linear_decrease(hbd, SPEC.hbd_good_max, SPEC.hbd_bad_max)

    pains_value = as_float(pains_alerts)
    if math.isnan(pains_value):
        d_pains = SPEC.pains_missing
    elif pains_value == 0:
        d_pains = 1.0
    else:
        d_pains = SPEC.pains_present

    gi_text = str(gi_absorption).strip().lower()
    if gi_text == "high":
        d_gi = SPEC.gi_high
    elif gi_text == "low":
        d_gi = SPEC.gi_low
    else:
        d_gi = SPEC.gi_unknown

    d_sa = linear_decrease(synthetic_accessibility, SPEC.sa_good_max, SPEC.sa_bad_max)

    adme_score = geometric_mean([
        d_mw,
        d_logp,
        d_tpsa,
        d_rot_bonds,
        d_hba,
        d_hbd,
        d_pains,
        d_gi,
        d_sa,
    ])

    return {
        "d_mw": d_mw,
        "d_logp": d_logp,
        "d_tpsa": d_tpsa,
        "d_rot_bonds": d_rot_bonds,
        "d_hba": d_hba,
        "d_hbd": d_hbd,
        "d_pains": d_pains,
        "d_gi": d_gi,
        "d_sa": d_sa,
        "adme_score": adme_score,
    }


def reference_calibrated_binding(median_dg: Any, reference_dg: Any) -> float:
    median_value = as_float(median_dg)
    reference_value = as_float(reference_dg)
    if math.isnan(median_value) or math.isnan(reference_value):
        return float("nan")
    if median_value >= 0 or reference_value >= 0:
        return float("nan")
    reference_strength = -reference_value
    if reference_strength <= 0:
        return float("nan")
    return clip01(min(1.0, (-median_value) / reference_strength))


def calculate_swan(
    *,
    safety_score: Any,
    adme_score: Any,
    binding_score: Any,
    liability_score: Any,
) -> float:
    return geometric_mean([safety_score, adme_score, binding_score, liability_score])
