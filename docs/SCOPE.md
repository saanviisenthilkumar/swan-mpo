# Scope and automation boundary

SWAN-MPO is the **scoring and target-calibration layer**, not a complete virtual-screening platform.

## SWAN-MPO performs

- schema/value validation of raw candidate-docking, ADME, and toxicity/liability inputs;
- frozen safety, ADME, and panel-specific liability transformations;
- grid-level candidate-docking aggregation to compound-target medians;
- target-specific reference-normalized binding;
- BestNode selection from reference-calibrated panel targets;
- final equal-weight geometric MPO integration and ranking;
- reference/native-ligand AutoDock Vina redocking for **new-target calibration** when the user supplies prepared receptor/ligand PDBQT files and a justified box;
- symmetry-aware fixed-receptor-frame heavy-atom RMSD for that redocking path;
- audit tables, warnings, version records, input hashes, and run logs.

## SWAN-MPO does not perform

- candidate-compound docking or receptor/ligand preparation;
- binding-site discovery or automatic box selection;
- SwissADME prediction/retrieval;
- ProTox prediction/retrieval;
- experimental target validation;
- molecular dynamics, free-energy calculations, or wet-lab validation.

The user remains responsible for the scientific validity and provenance of upstream docking, ADME, and toxicity predictions. The CLI makes their downstream SWAN-MPO treatment deterministic, inspectable, and reproducible.
