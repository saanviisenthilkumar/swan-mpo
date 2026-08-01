# Inputs, automated transformations, and target calibration

The normal workflow consumes upstream raw outputs. Precomputed `safety_score`, `adme_score`, `binding_score`, or `liability_score` values are **not required**.

## Candidate docking CSV
One row per compound × target × grid center with compound, target, PDB ID, grid ID, and Vina affinity. The published configuration requires exactly 20 unique grid rows per compound-target block. SWAN computes the median internally; that median enters target-reference calibration. Duplicate/incomplete grids, nonfinite values, receptor/PDB mismatch, or missing calibration fail with actionable errors.

## ADME/property CSV
Required logical fields: compound, MW, Consensus Log P, TPSA, rotatable bonds, HBA, HBD, PAINS alerts, GI absorption, and synthetic accessibility. Common SwissADME headings (including `#Rotatable bonds`, `#H-bond acceptors`, and `#H-bond donors`) are recognized. The standard workflow requires Consensus Log P. Incomplete exports are rejected rather than imputed.

## Toxicity/liability CSV
Required logical fields: compound, LD50, toxicity class, hepatotoxicity, neurotoxicity, nephrotoxicity, respiratory toxicity, cardiotoxicity, BBB, and Complex I. Common ProTox headings including Unicode `LD₅₀ (mg/kg)` and `NADH-QO` are recognized. Active/Inactive endpoints require prediction confidence in [0.5,1.0] in the standard workflow.

## Automated domains
Safety: LD50 + toxicity class -> acute safety; hepato/neuro/nephro/respi/cardio -> organ safety; acute + organ -> safety. Inactive confidence `c` maps to `c`; Active confidence `c` maps to `1-c`.

ADME: nine frozen property desirabilities -> geometric-mean ADME score.

Liability: **Colon = BBB + neurotoxicity**. Complex I is accepted in the shared compound-level raw ProTox table but is intentionally excluded from Colon liability because it is an intended colorectal docking target. **Prostate/RCC = BBB + Complex I + neurotoxicity.** `panel_liability_desirabilities.csv` records `complex_i_included_in_liability` and `liability_inputs_used` explicitly.

Binding: 20 candidate grid energies -> median ΔG per compound-target -> target-specific reference normalization -> calibrated target desirability. Comparative-only targets remain in target-level audit output but cannot enter primary BestNode.

BestNode: highest eligible reference-calibrated target desirability within the panel. The published expanded analysis uses deterministic historical target/PDB tie ordering encoded in the config; this is regression-tested against all 177 canonical panel rows. Under the published calibration Colon has only mTOR eligible, so `PANEL_SINGLE_NODE_BESTNODE` is emitted.

## Nonstandard modes
`--allow-missing-predictors` activates the locked historical missing/default rules. It writes `NONSTANDARD_MODE_ACTIVATED` and `nonstandard_mode: true`; outputs should not be represented as standard complete-input results without disclosure.

## Exact manuscript reproduction data
`src/swan_mpo/resources/` contains the exact canonical scoring inputs needed for the 59-compound expanded screen: full SwissADME export, raw ProTox export, scoring-required docking columns, and frozen expected 177-panel/531-target outputs. Run `swan-mpo reproduce-manuscript --output-dir manuscript_reproduction`. Source hashes and derivations are in `manuscript_source_manifest.json`. The earlier SwissADME export with missing Consensus Log P is provenance-only and is not used.
