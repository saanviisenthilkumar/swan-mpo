# Changelog

## 1.3.2 — RC2 post-adversarial-audit
- Added an independently checked compact-extract derivation audit plus explicit manuscript-reproduction/public-archive documentation.
- Added the manuscript source-manifest itself to the strict SHA-256 verification contract.
- Preserved byte-identical frozen scoring model and published calibration.
- Packaged exact canonical 59-row full SwissADME export, exact 59-row ProTox export, scoring-required extract of the canonical 10,620-row docking ledger, and frozen expected 177-panel/531-target outputs.
- Added `reproduce-manuscript` full-regression command and `verify --manuscript`; no descriptor imputation is used for manuscript reproduction.
- Reconciled SwissADME provenance: an earlier incomplete export with blank Consensus Log P is provenance-only; canonical analysis used a later full SwissADME export and explicitly prohibited available-model logP averaging.
- Encoded the historical deterministic BestNode tie priorities required to reproduce all 177 canonical selected-node labels exactly: Prostate uses AR > 5AR2 > mTOR > Bcl-2 and RCC uses AKT1 > mTOR > Bcl-2 > PI3Ka. This changes tie resolution only and does not alter the locked SWAN-MPO scoring equations.
- Made Colon Complex-I exclusion explicit in liability audit outputs; locked equation unchanged.
- Added numeric golden-output assertions for synthetic demo.
- Added `PANEL_SINGLE_NODE_BESTNODE`, `NONSTANDARD_MODE_ACTIVATED`, and `PRIMARY_ONLY_COVERAGE_MODE` warnings.
- Added expected Vina 1.2.7 to `--version`, strict verification, exact portable Vina command echo, expanded warning tests, and stronger cross-platform privacy audit.
- Added CI manuscript reproduction and badge.
- Added exact packaged manuscript-resource hash verification to `verify --manuscript`/`--strict`; manuscript reproduction metadata records the verified resource hashes.
- Added regression protection that the historical incomplete SwissADME export is rejected rather than imputed, plus end-to-end persistence tests for nonstandard missing-predictor mode.
- Removed a duplicate ambiguous copy of the historical incomplete SwissADME file; only the explicitly named provenance-only copy remains.
- Added `.gitattributes` byte-preservation rules for exact upstream SwissADME/ProTox exports so Git checkout cannot silently normalize line endings and invalidate their SHA-256 provenance.
- `--version` now exposes software version, locked model identity/hash, and expected Vina 1.2.7.
- Narrowed the advertised Python support to the actually validated 3.13 release line instead of claiming untested 3.10–3.12 compatibility.
- Removed the unverified optional Dockerfile rather than ship an untested container claim.
- Completed the actual AutoDock Vina 1.2.7 RC2 mTOR/4JSP rerun: generated-mode recovery reproduced mode 13, reference ΔG = -6.578 kcal/mol, RMSD = 1.1326525817600657 Å; the dedicated real-Vina pytest and strict verification both passed.

## 1.3.1 — RC1
Private adversarial review candidate pushed as tag `v1.3.1-rc1` / commit `7bdf0d9`.
