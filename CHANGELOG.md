# Changelog

## v1.3.3 eight-structure correction (November 2026)

- Removed the PDB 3V3N structure from the oncology screen because it was incorrectly attributed to human SRD5A2; no substitute receptor was introduced.
- Excluded 1,180 PDB 3V3N docking rows, retaining 9,440 existing observations; updated the 472 target-level and 177 panel reference records without changing the locked scoring equations.
- Recorded the superseded nine-structure source filenames and SHA-256 values as historical provenance and synchronized the tests, hashes, and documentation.
- Excluded the two 5AR2 assay records from the active ChEMBL activity/status cohort and recomputed benchmark and domain-decomposition outputs (188 primary records and 249 secondary records). The original hash-locked ChEMBL descriptor source remains available solely as historical provenance.

## 1.3.2

- Added deterministic manuscript-scoring reproduction through `swan-mpo reproduce-manuscript`.
- Added `verify --manuscript` and expanded strict verification of frozen model, calibration, runtime, and manuscript-reproduction resources.
- Packaged the canonical 59-compound SwissADME and ProTox inputs, the scoring-required 10,620-row docking extract, and frozen 177-panel / 531-target expected outputs.
- Added exact SHA-256 verification for manuscript-reproduction resources.
- Preserved the frozen SWAN-MPO mathematical model and published target-calibration resource.
- Added deterministic BestNode tie priorities required for exact reproduction of the published expanded-screen outputs.
- Added explicit workflow warnings for single-node calibrated panels, nonstandard missing-predictor mode, and primary-only coverage mode.
- Added regression testing for predictor validation, calibration behavior, manuscript reproduction, provenance, and warning generation.
- Added AutoDock Vina 1.2.7 reference-redocking verification and symmetry-aware heavy-atom RMSD support.
- Added reproducibility, licensing, provenance, and cross-platform privacy checks.
- Added continuous-integration testing for installation, scoring, verification, and manuscript reproduction.
- Restricted documented Python support to the validated Python 3.13 release line.
