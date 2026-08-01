# Inputs, automated transformations, and target calibration

The normal public workflow consumes raw upstream outputs. Precomputed `safety_score`, `adme_score`, `binding_score`, or `liability_score` values are **not** required.

## 1. Candidate docking CSV

One row per compound × target × grid center.

Required logical fields:

- `compound`
- `target`
- `pdb_id`
- `grid_id`
- docking affinity (`best_affinity_kcal_mol`, `affinity`, `vina_affinity`, or a mapped equivalent)

The published configuration requires exactly **20 unique grid rows per compound-target block**. SWAN computes best, mean, and median ΔG internally. The **median** enters the primary binding transformation.

Individual grid energies are required to be finite but are not required to be negative: weak/positive individual Vina values can occur. A **reference-calibrated target median must be negative**, otherwise scoring stops with an actionable error.

See `examples/templates/candidate_docking_template.csv`.

## 2. ADME/property CSV

Required raw logical fields:

- compound
- molecular weight
- consensus LogP
- TPSA
- rotatable bonds
- H-bond acceptors
- H-bond donors
- PAINS alert count
- GI absorption (`High` or `Low` in the standard workflow)
- synthetic accessibility

Common SwissADME-style headings are recognized automatically. A JSON `--column-map` can resolve unusual headings.

SWAN converts every raw field to a bounded desirability and computes the nine-term ADME geometric mean. The user never needs to calculate `adme_score`.

See `examples/templates/swissadme_input_template.csv`.

## 3. Toxicity/liability CSV

Required raw logical fields:

- compound
- LD50 (mg/kg)
- toxicity class (integer 1–6)
- hepatotoxicity status + confidence
- neurotoxicity status + confidence
- nephrotoxicity status + confidence
- respiratory-toxicity status + confidence
- cardiotoxicity status + confidence
- BBB status + confidence
- Complex-I status + confidence

A status can be combined with confidence, for example `Inactive (0.82)`, or status and confidence can be placed in separate columns such as `Neurotoxicity` and `Neurotoxicity confidence`. In the strict workflow each endpoint must contain `Active` or `Inactive` and a confidence in **[0.5, 1.0]**. Missing or ambiguous endpoint confidence causes a clear failure rather than silently defaulting.

`--allow-missing-predictors` exists only for explicit historical-reproduction work and should not be used for normal third-party scoring.

See `examples/templates/protox_input_template.csv`.

## 4. Safety automation

SWAN computes:

- log-scaled LD50 desirability using the frozen 50–5000 mg/kg interpolation anchors;
- toxicity-class desirability;
- endpoint desirabilities from confidence-coded Active/Inactive predictions;
- `acute_safety = GM(d_LD50, d_toxicity_class)`;
- `organ_safety = GM(d_hepato, d_neuro, d_nephro, d_respiratory, d_cardio)`;
- `safety_score = GM(acute_safety, organ_safety)`.

For a confidence-coded endpoint:

- `Inactive` → desirability = confidence;
- `Active` → desirability = 1 − confidence.

All locked desirabilities are bounded to [0.01, 1.00].

## 5. ADME automation

The CLI applies the frozen model's MW, LogP, TPSA, rotatable-bond, HBA, HBD, PAINS, GI-absorption, and synthetic-accessibility rules, then takes their geometric mean.

Use:

```bash
swan-mpo explain-model --sources
```

to see both the exact constants and their provenance. The provenance document distinguishes literature-grounded preferred regions from SWAN-MPO outer design anchors.

## 6. Panel-specific liability automation

The same confidence-aware categorical transformation is applied to BBB, neurotoxicity, and Complex-I inputs.

- Colon = GM(BBB, neurotoxicity)
- Prostate = GM(BBB, Complex I, neurotoxicity)
- RCC = GM(BBB, Complex I, neurotoxicity)

The user supplies raw predictions and confidences, not `liability_score`. Neurotoxicity intentionally appears in general safety and panel liability in the frozen primary architecture; that overlap is separately stress-tested in the manuscript.

## 7. New-target reference redocking

For a new target, copy `examples/templates/target_redocking_config_template.json`, supply prepared receptor/native-ligand PDBQT paths plus a justified box. The native-ligand PDBQT must preserve the reference pose coordinates in the receptor frame, and run:

```bash
swan-mpo redock-reference \
  --targets-config target_redocking.json \
  --require-vina-1-2-7 \
  --output-dir redocking_results
```

SWAN runs Vina, parses all generated modes, calculates symmetry-aware fixed-frame heavy-atom RMSD, and applies:

1. mode 1 RMSD ≤ cutoff → strict top-pose reference calibration;
2. otherwise, a generated mode RMSD ≤ cutoff → generated-mode recovery, using the recovered native-like mode energy as `reference_dg`;
3. otherwise → comparative-only, excluded from primary BestNode.

Default cutoff is 2.0 Å.

For the published nine targets, use the bundled audited calibration by default rather than silently regenerating manuscript values with changed docking parameters.

## 8. BestNode

For each target:

```text
candidate grid rows → median ΔG → target reference ΔG → bounded binding desirability
```

For each panel:

```text
eligible reference-calibrated target desirabilities → maximum = BestNode binding
```

The result table also reports the selected BestNode, the second-best eligible node where available, and a best/second-best ratio for interpretability. These audit fields do not change the primary score.

## 9. Final score

```text
SWAN-MPO = GM(safety_score, adme_score, BestNode binding, liability_score)
```

with equal domain weighting through the geometric mean.

## 10. Column mapping

If source exports use different headings, provide a JSON mapping. Only overrides are needed, for example:

```json
{
  "adme": {"compound": "Molecule", "mw": "Molecular Weight"},
  "toxicity": {
    "compound": "Molecule",
    "ld50_mgkg": "LD50 (mg/kg)",
    "neuro_confidence": "Neurotoxicity probability"
  },
  "docking": {"compound": "Ligand", "dg": "Affinity"}
}
```

If required columns are missing, SWAN reports accepted aliases, the columns actually found, and the relevant template path.

## 11. Nonfatal boundary warnings

Values beyond the frozen desirability-anchor ranges are reported in `warnings.csv` and `run_metadata.json`. These are **model-anchor warnings, not a formal applicability-domain assessment**.
