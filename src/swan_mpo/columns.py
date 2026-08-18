from __future__ import annotations

from .config import normalize_key
from .errors import InputValidationError

ADME_ALIASES = {
    "compound": ["compound", "compound_name", "name", "molecule", "molecule name"],
    "mw": ["mw", "molecular_weight", "molwt", "molecular weight", "molecular weight (g/mol)"],
    "consensus_logp": ["consensus_logp", "consensus log p", "consensus logp", "logp", "consensus_log_p"],
    "tpsa": ["tpsa", "topological polar surface area", "topological polar surface area (a2)", "topological polar surface area (å²)"],
    "rotatable_bonds": ["rotatable_bonds", "num. rotatable bonds", "num rotatable bonds", "rotatable bonds", "rotatable bond count", "#rotatable bonds"],
    "hba": ["hba", "num. h-bond acceptors", "num h-bond acceptors", "h-bond acceptors", "h bond acceptors", "#h-bond acceptors"],
    "hbd": ["hbd", "num. h-bond donors", "num h-bond donors", "h-bond donors", "h bond donors", "#h-bond donors"],
    "pains_alerts": ["pains_alerts", "pains #alerts", "pains alerts", "pains", "pains alert count"],
    "gi_absorption": ["gi_absorption", "gi absorption", "gastrointestinal absorption", "gi_abs"],
    "synthetic_accessibility": ["synthetic_accessibility", "synthetic accessibility", "sa score", "sascore", "synthetic accessibility score"],
}

TOX_ALIASES = {
    "compound": ["compound", "compound_name", "name", "molecule", "molecule name"],
    "ld50_mgkg": ["ld50_mgkg", "ld50", "predicted ld50", "ld50 (mg/kg)", "ld50 mg/kg", "predicted ld50 (mg/kg)", "LD₅₀ (mg/kg)"],
    "toxicity_class": ["toxicity_class", "toxicity class", "predicted toxicity class", "tox class"],
    "hepato": ["hepato", "hepatotoxicity", "hepatotoxicity prediction"],
    "neuro": ["neuro", "neurotoxicity", "neurotoxicity prediction"],
    "nephro": ["nephro", "nephrotoxicity", "nephrotoxicity prediction"],
    "respi": ["respi", "respiratory toxicity", "respiratory_toxicity", "respiratory toxicity prediction"],
    "cardio": ["cardio", "cardiotoxicity", "cardiotoxicity prediction"],
    "bbb": ["bbb", "blood-brain barrier", "blood brain barrier", "bbb permeability", "bbb prediction"],
    "complex_i": ["complex_i", "complex i", "mitochondrial complex i", "complex1", "complex i toxicity", "complex i prediction", "nadh-qo", "nadh qo", "nadh-quinone oxidoreductase", "nadhox"],
}

# Optional companion columns. If a status cell already embeds a numeric confidence,
# these are not required. If a status cell contains only Active/Inactive, the strict
# workflow requires one of these columns and combines status + confidence internally.
TOX_CONF_ALIASES = {
    "hepato_confidence": ["hepato_confidence", "hepatotoxicity confidence", "hepatotoxicity probability", "hepatotoxicity confidence score"],
    "neuro_confidence": ["neuro_confidence", "neurotoxicity confidence", "neurotoxicity probability", "neurotoxicity confidence score"],
    "nephro_confidence": ["nephro_confidence", "nephrotoxicity confidence", "nephrotoxicity probability", "nephrotoxicity confidence score"],
    "respi_confidence": ["respi_confidence", "respiratory toxicity confidence", "respiratory toxicity probability", "respiratory confidence"],
    "cardio_confidence": ["cardio_confidence", "cardiotoxicity confidence", "cardiotoxicity probability", "cardiotoxicity confidence score"],
    "bbb_confidence": ["bbb_confidence", "bbb confidence", "blood-brain barrier confidence", "bbb probability", "blood brain barrier probability"],
    "complex_i_confidence": ["complex_i_confidence", "complex i confidence", "complex i probability", "mitochondrial complex i confidence"],
}

DOCK_ALIASES = {
    "compound": ["compound", "compound_name", "name", "ligand", "ligand_name"],
    "target": ["target", "target_standard", "protein", "target_name"],
    "pdb_id": ["pdb_id", "pdb", "receptor_pdb_id"],
    "grid_id": ["grid_id", "grid", "center_id", "grid_center", "grid center"],
    "dg": ["best_affinity_kcal_mol", "dg", "docking_energy", "affinity", "vina_affinity", "binding affinity"],
}

REDOCK_ALIASES = {
    "target": ["target", "target_standard"],
    "pdb_id": ["pdb_id", "pdb"],
    "mode": ["mode", "mode_number", "rank"],
    "dg": ["dg_kcal_mol", "docking_energy", "affinity", "vina_affinity", "dg"],
    "rmsd": ["rmsd_a", "rmsd", "heavy_atom_rmsd_a", "heavy atom rmsd"],
}


def _normalized_field_lookup(fieldnames):
    return {normalize_key(c): c for c in fieldnames}


def resolve_optional_column(fieldnames, options):
    normalized = _normalized_field_lookup(fieldnames)
    hits = []
    for option in options:
        key = normalize_key(option)
        if key in normalized:
            hits.append(normalized[key])
    hits = list(dict.fromkeys(hits))
    if len(hits) > 1:
        raise InputValidationError(
            f"Multiple optional columns match the same field: {hits}. Use --column-map to disambiguate."
        )
    return hits[0] if hits else None


def resolve_columns(fieldnames, aliases, explicit=None, *, table="input"):
    explicit = explicit or {}
    normalized = _normalized_field_lookup(fieldnames)
    result = {}
    for canonical, options in aliases.items():
        if canonical in explicit:
            col = explicit[canonical]
            if col not in fieldnames:
                raise InputValidationError(
                    f"{table}: mapped column {col!r} for {canonical!r} does not exist. "
                    f"Available columns: {list(fieldnames)}"
                )
            result[canonical] = col
            continue
        hits = []
        for option in options:
            key = normalize_key(option)
            if key in normalized:
                hits.append(normalized[key])
        hits = list(dict.fromkeys(hits))
        if len(hits) == 1:
            result[canonical] = hits[0]
        elif len(hits) > 1:
            raise InputValidationError(
                f"{table}: multiple columns could map to {canonical}: {hits}. Use --column-map."
            )
        else:
            raise InputValidationError(
                f"{table}: could not find required field {canonical!r}. "
                f"Accepted aliases include: {options}. Available columns: {list(fieldnames)}. "
                "See examples/templates/ for input templates."
            )
    return result
