# Manuscript extract derivation audit

The compact reproduction files were independently compared against the canonical source files used to build them.

## Canonical source identities

- complete docking ledger: 10,620 rows; SHA-256 `3eff29c597802a7052a546cdc00012a3445c684fb7726513492ea923daa996c4`
- canonical expanded panel scores: 177 rows; SHA-256 `750a5d0ef13ceeccb6def1fd1c9d148eb35a5cc3a7ddb3f4d59af92973286cb5`
- canonical expanded target-level binding: 531 rows; SHA-256 `b3084e76615c2937a9a4214d9061d803fd735d3d717e3a8a199618f67d8ead28`
- canonical full SwissADME export: 59 rows; SHA-256 `a1b6339695bba431239def8969d56244cecd978e195e5eaf2a3019ca21ec7ab1`
- canonical ProTox export: 59 rows; SHA-256 `4ef8ea376f89533ad3bd3afb9d810aab9c8fccc3f216179414d6de776b3f08ee`

## Independent comparison result

- `manuscript_swissadme_canonical_full.csv`: byte-identical to the canonical 59-row source — PASS.
- `manuscript_protox_raw.csv`: byte-identical to the canonical 59-row source — PASS.
- `manuscript_candidate_docking.csv`: all 10,620 rows are exact row-order-preserving copies of the five scoring-required columns (`compound_name`, `target`, `pdb_id`, `grid_id`, `best_affinity_kcal_mol`) from the canonical complete ledger — PASS.
- `manuscript_expected_panel_scores.csv`: all 177 rows are exact row-order-preserving copies of the packaged validation columns from the canonical expanded panel table — PASS.
- `manuscript_expected_target_level_binding.csv`: all 531 rows are exact row-order-preserving copies of the packaged validation columns from the canonical target-level table — PASS.

The compact files deliberately omit machine-local path/runtime fields that are not inputs to SWAN scoring. Their derivation does not alter any retained scientific value.
