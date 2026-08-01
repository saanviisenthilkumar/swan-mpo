from __future__ import annotations

import math

from .columns import ADME_ALIASES
from .locked_model import SPEC, as_float
from .pipeline import standardize_compound_table, standardize_toxicity_table


def collect_domain_warnings(
    adme_rows,
    adme_fields,
    tox_rows,
    tox_fields,
    *,
    adme_map=None,
    tox_map=None,
):
    """Return non-fatal warnings for values outside frozen desirability anchor ranges."""
    adme = standardize_compound_table(adme_rows, adme_fields, ADME_ALIASES, adme_map, "ADME")
    tox = standardize_toxicity_table(tox_rows, tox_fields, tox_map, "toxicity")
    warnings = []

    def add(compound, field, value, message, code="OUTSIDE_FROZEN_ANCHOR_RANGE"):
        warnings.append(
            {
                "code": code,
                "compound": compound,
                "field": field,
                "value": value,
                "message": message,
            }
        )

    for row in adme:
        c = row["compound"]
        checks = [
            ("mw", as_float(row["mw"]), lambda x: x > SPEC.mw_bad_max,
             f"MW exceeds the frozen upper bad anchor ({SPEC.mw_bad_max:g}); desirability is clipped near the model floor."),
            ("consensus_logp", as_float(row["consensus_logp"]),
             lambda x: x < SPEC.logp_low_bad or x > SPEC.logp_high_bad,
             f"Consensus LogP lies outside the frozen tolerated range [{SPEC.logp_low_bad:g}, {SPEC.logp_high_bad:g}]."),
            ("tpsa", as_float(row["tpsa"]), lambda x: x > SPEC.tpsa_bad_max,
             f"TPSA exceeds the frozen upper bad anchor ({SPEC.tpsa_bad_max:g})."),
            ("rotatable_bonds", as_float(row["rotatable_bonds"]), lambda x: x > SPEC.rot_bonds_bad_max,
             f"Rotatable-bond count exceeds the frozen upper bad anchor ({SPEC.rot_bonds_bad_max:g})."),
            ("hba", as_float(row["hba"]), lambda x: x > SPEC.hba_bad_max,
             f"HBA count exceeds the frozen upper bad anchor ({SPEC.hba_bad_max:g})."),
            ("hbd", as_float(row["hbd"]), lambda x: x > SPEC.hbd_bad_max,
             f"HBD count exceeds the frozen upper bad anchor ({SPEC.hbd_bad_max:g})."),
            ("synthetic_accessibility", as_float(row["synthetic_accessibility"]), lambda x: x > SPEC.sa_bad_max,
             f"Synthetic-accessibility score exceeds the frozen upper bad anchor ({SPEC.sa_bad_max:g})."),
        ]
        for field, value, predicate, message in checks:
            if math.isfinite(value) and predicate(value):
                add(c, field, value, message)

    for row in tox:
        c = row["compound"]
        ld50 = as_float(row["ld50_mgkg"])
        if math.isfinite(ld50) and (ld50 < SPEC.ld50_low_mgkg or ld50 > SPEC.ld50_high_mgkg):
            add(
                c,
                "ld50_mgkg",
                ld50,
                f"LD50 lies outside the frozen logarithmic anchor interval [{SPEC.ld50_low_mgkg:g}, {SPEC.ld50_high_mgkg:g}] mg/kg; the desirability is clipped at a bound.",
            )
    return warnings
