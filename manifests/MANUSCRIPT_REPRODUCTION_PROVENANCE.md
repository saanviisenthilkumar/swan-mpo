# Manuscript reproduction provenance: eight-structure revision

The corrected 59-compound deployment excludes PDB 3V3N (bacterial TetX2, not human SRD5A2). No replacement docking structure or modified scoring equation was introduced. The 49-table Online Resource 2 ZIP, including the separately reproducible domain ablation, was checked at SHA-256 `7748ea78bf1374eadd46bb522794fc47f377cbab130cf28a9c62f26d8e52db40`.

## Corrected source identities

- Docking deployment, Table S3: 9,440 rows; SHA-256 `74f4cd4527d4d4a619b3eaec07288145333863339836f63c8967ab8793b44ec0`.
- Expanded panel scores, Table S8B: 177 rows; SHA-256 `3cf353658c5d576776189205d13373d4ddd31f5eca999521085ce14c47a73107`.
- Expanded target-level audit, Table S17D: 472 rows; SHA-256 `772a8e7845528fccd16851156cb0566c414f5ee686a9df98f72197fd700a7e34`.
- Unmodified full SwissADME export: 59 rows; SHA-256 `a1b6339695bba431239def8969d56244cecd978e195e5eaf2a3019ca21ec7ab1`.
- Unmodified ProTox export: 59 rows; SHA-256 `4ef8ea376f89533ad3bd3afb9d810aab9c8fccc3f216179414d6de776b3f08ee`.

## Rebuild checks

- The 9,440-row compact docking CSV matches the corrected, Mac-verified Table S3 energy column for all surviving 472 compound/structure blocks (20 grids each); 770 original extraction values required reconciliation with the source logs.
- The 472-row compact target validation CSV was compared field-by-field against corrected Table S17D, including calibration statuses.
- All 177 primary SWAN-MPO scores, domain values, and primary ranks reproduce corrected Table S8B. The selected BestNode label of prostate Annomuricatin B changed from 5AR2 to mTOR when the invalid structure was removed. Subsequent raw-log energy reconciliation changed 8 colorectal, 12 prostate, and 12 renal-cell-carcinoma rank positions compared with the preceding eight-structure tables; Muricatacin remained rank 1/2/2.
- The bundled calibration CSV contains eight records, with four strict, one generated-mode, and three comparative-only classes.
- The frozen `locked_model.py` hash remains `97799e91f23803de3b9a477aea3bbcfb061f1b1d9abebdecfdadcd1b537f4454`.

The source manifests retain the previous nine-structure hashes as historical provenance. The superseded docking ledger had 10,620 rows (SHA-256 `3eff29c597802a7052a546cdc00012a3445c684fb7726513492ea923daa996c4`) and the original target audit had 531 rows (SHA-256 `b3084e76615c2937a9a4214d9061d803fd735d3d717e3a8a199618f67d8ead28`).
