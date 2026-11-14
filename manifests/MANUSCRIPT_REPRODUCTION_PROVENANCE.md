# Manuscript reproduction provenance

The 59-compound deployment uses eight receptor structures and excludes PDB 3V3N (bacterial TetX2, not human SRD5A2). No replacement docking structure or modified scoring equation was introduced. The associated Online Resource 2 ZIP was independently verified at SHA-256 `1904978856fa232f46f2c3fcbf45a9c17ff7db58507f188faab390ab5c3b547a`.

## Source identities

- Docking deployment, Table S3: 9,440 rows; SHA-256 `987269cbcef84be063fa40aa9971e5219bcabc915122ec899139429d3ec0b256`.
- Expanded panel scores, Table S8B: 177 rows; SHA-256 `28fbd6167c15a03f65e02deb46e53889658fc92992cb817bdcd7228767bb13b9`.
- Expanded target-level audit, Table S17D: 472 rows; SHA-256 `16707e45c6fc3851eae8203b43c8f5c7d060dee16442b8a1afc7379fe72b517b`.
- Unmodified full SwissADME export: 59 rows; SHA-256 `a1b6339695bba431239def8969d56244cecd978e195e5eaf2a3019ca21ec7ab1`.
- Unmodified ProTox export: 59 rows; SHA-256 `4ef8ea376f89533ad3bd3afb9d810aab9c8fccc3f216179414d6de776b3f08ee`.

## Rebuild checks

- The 9,440-row compact docking CSV retains the original values for all surviving 472 compound/structure blocks (20 grids each).
- The 472-row compact target validation CSV was compared field-by-field against Table S17D, including calibration statuses.
- All 177 primary SWAN-MPO scores, domain values, and primary ranks match Table S8B; the selected BestNode label of prostate Annomuricatin B is mTOR after the 5AR2 node was excluded. No primary numerical score or rank changes.
- The bundled calibration CSV contains eight records, with four strict, one generated-mode, and three comparative-only classes.
- The frozen `locked_model.py` hash remains `97799e91f23803de3b9a477aea3bbcfb061f1b1d9abebdecfdadcd1b537f4454`.

The source manifests retain the prior nine-structure hashes as historical provenance. That docking ledger had 10,620 rows (SHA-256 `3eff29c597802a7052a546cdc00012a3445c684fb7726513492ea923daa996c4`) and the prior target audit had 531 rows (SHA-256 `b3084e76615c2937a9a4214d9061d803fd735d3d717e3a8a199618f67d8ead28`).
