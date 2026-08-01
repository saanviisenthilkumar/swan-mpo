# Changelog

## 1.3.1 - release-candidate hardening after macOS clean-install test

- Sanitized shareable run metadata so local home-directory prefixes are written as `$HOME` and console-script paths are normalized.
- Prevented the source release audit from treating git-ignored runtime output folders as release source.
- Added git-ignore rules for demo results and local real-Vina configurations/reports.
- Added Vina `energy_range` support; this was required for manuscript-faithful redocking protocols.
- Added a canonical mTOR/4JSP tight-native-box template and helper using center (49.224, -1.763, -45.895), 16 Å box, exhaustiveness 64, 20 modes, energy range 4, seed 2026, and CPU=0.
- Added local input hash/size reporting and historical `config_tight.txt` SHA verification for the mTOR integration helper.
- Clarified that JSON configuration files are data files and must be passed to commands rather than executed directly.
- Preserved the locked model byte-for-byte.


## 1.3.0 release candidate

- Preserved the byte-identical frozen SWAN-MPO v1.0 mathematical model.
- Kept raw candidate docking + raw ADME + raw toxicity/liability as the standard public input boundary.
- Automated safety, ADME, panel liability, target-level binding, BestNode, final MPO scoring, and ranks.
- Added optional direct AutoDock Vina reference-ligand redocking for new-target calibration.
- Added symmetry-aware fixed-frame heavy-atom RMSD using graph isomorphism, with an explicit ordered fallback only for controlled cases.
- Added strict endpoint-confidence validation and support for separate ProTox-style confidence columns.
- Added actionable schema errors and exact grid-count validation.
- Added `swan-mpo explain-model --sources`, threshold provenance documentation, and source registry.
- Added `swan-mpo score --demo` and `swan-mpo verify`.
- Added nonfatal frozen-anchor warnings, run metadata, input hashes, structured run log, and runtime-version records.
- Added exact environment manifest, example templates, CI tests, licensing/redistribution documentation, and optional Docker recipe.
- Added real-Vina verification pathway that requires Vina 1.2.7 and preserves integration artifacts.

## 1.2.0 staging — superseded

- Added automated raw-domain scoring and initial Vina reference-redocking runner.
- RMSD implementation was not sufficiently robust to symmetry/atom-order changes and is superseded by 1.3.0.

## 1.1.0 staging — superseded

- Replaced component-score-first workflow with raw upstream inputs.
- Added candidate grid aggregation and target calibration ingestion.

## 1.0.0 staging — superseded

- Initial CLI prototype. Precomputed component-score input was too close to the internal model boundary for the intended public workflow.
