# Changelog

## Unreleased — final OR2 source alignment (November 2026)

- Synchronized the descriptor-compatible comparator's 3,980-profile input and
  expected S14A/S14B results with the final 49-table Online Resource 2 package.
  The previously distributed 4,388-profile cohort is retained by historical
  checksum rather than presented as the final S14 cohort.
- Corrected the ChEMBL activity/status reproduction scripts to calculate
  tie-averaged, input-order-invariant BEDROC and updated the active
  S13-compatible expected results; adopted final S13 structure-liability names
  without altering the numerical record-level inputs.
- Added regression tests and a provenance crosswalk identifying the frozen
  OR2 archive checksum, benchmark populations, and methodological limits.
- Did not change the locked SWAN-MPO scoring equations or calibration classes.

## v1.3.3 eight-structure correction (November 2026)

- Removed the PDB 3V3N structure from the oncology screen because it was incorrectly attributed to human SRD5A2; no substitute receptor was introduced.
- Excluded 1,180 PDB 3V3N docking rows, retaining 9,440 existing observations; updated the 472 target-level and 177 panel reference records without changing the locked scoring equations.
- Recorded the superseded nine-structure source filenames and SHA-256 values as historical provenance and synchronized the tests, hashes, and documentation.
- Excluded the two 5AR2 assay records from the active ChEMBL activity/status cohort and recomputed benchmark and domain-decomposition outputs (188 primary records and 249 secondary records). The original hash-locked ChEMBL descriptor source remains available solely as historical provenance.
- Reconciled 9,440 expanded-screen docking energies with the Mac-verified raw-log ledger and regenerated the frozen 472 target-level/177 panel-level expected results. The scoring equations remain unchanged.
- Added a reproducible four-stage and leave-one-domain-out ablation of the 177 panel-level rankings; its three machine-readable tables are designated Supplementary Table S24A–C.

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
