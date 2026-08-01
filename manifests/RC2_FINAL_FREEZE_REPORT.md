# SWAN-MPO v1.3.2 RC2 final sandbox freeze report

## Scope
RC2 dispositions every finding from the independent v1.3.1 adversarial audit without changing the locked mathematical model or frozen published target calibration.

## Frozen identities
- locked model SHA-256: `97799e91f23803de3b9a477aea3bbcfb061f1b1d9abebdecfdadcd1b537f4454` — PASS
- published calibration SHA-256: `e7584f10c0f970bb54ddf39cfdacbb6cb061bc6a3d2bd795e2d5f119efc7287c` — PASS
- manuscript source-manifest SHA-256: `8e48007744de8ec50e7ba9941f4b71970161fea31034a8df231ed5502bb45561` — PASS

## Final sandbox gate
- `compileall src tests scripts`: PASS
- pytest: **70 passed, 1 skipped**
- only skip: optional actual-Vina integration requiring a user-supplied verified local config
- `swan-mpo verify --manuscript`: PASS
- packaged manuscript resource SHA-256 checks: PASS
- `swan-mpo reproduce-manuscript`: PASS
- panel rows reproduced: **177/177**
- target-level rows reproduced: **531/531**
- reproduction failures: **0**
- release/privacy audit: PASS
- license/redistribution audit: PASS
- compact manuscript-extract derivation audit: PASS

## Muricatacin canonical regression
- Colon: score `0.7337646613702474`, rank 1, BestNode mTOR, binding rank 47
- Prostate: score `0.6609780531711298`, rank 2, BestNode mTOR, binding rank 47
- RCC: score `0.6609780531711298`, rank 2, BestNode mTOR, binding rank 47

## Audit closures in RC2
- Colon liability verified as BBB + neurotoxicity only; Complex I is explicitly marked excluded in panel-liability audit output while the locked source remains byte-identical.
- Synthetic demo now has numeric golden-score regression protection.
- Exact manuscript SwissADME, exact unchanged ProTox, scoring-required 10,620-row docking extract, and 177/531 canonical expected outputs are packaged and hash-verified.
- A one-command `reproduce-manuscript` workflow reproduces all 177 panel and 531 target rows.
- Historical incomplete SwissADME export is provenance-only and regression-tested to fail standard scoring rather than be imputed.
- Colon single-node BestNode warning added.
- Missing-predictor escape hatch is permanently marked in warnings and run metadata.
- Version output exposes software/model identity/hash and expected Vina 1.2.7.
- Unverified Docker surface removed rather than shipping an untested container claim.
- Exact Vina command echo, strict verifier, CI badge/workflow, broader boundary-warning tests, and cross-platform privacy checks added.
- Exact upstream predictor exports have `.gitattributes` byte-preservation rules so Git cannot silently normalize line endings and invalidate provenance hashes.
- Advertised Python support narrowed to the tested Python 3.13 release line.
- Historical deterministic BestNode tie order reproduces all 177 canonical selected-node labels.
- Manuscript reproduction and public archive/checklist documentation added.

## External gates still required before public JoC release
These are validation/publication-state gates, not unresolved code findings:
1. Run this **exact RC2** on the author's Mac against actual AutoDock Vina 1.2.7 using the canonical mTOR/4JSP reference-redocking setup.
2. Push/tag RC2 privately and repeat install/reproduction/audits from a brand-new clean clone.
3. Create the public archival code/data release and verify all required endpoints are accessible without login.
4. Insert only the final verified public URLs/DOIs into the manuscript.

The prior v1.3.1 actual-Vina run passed and is recorded in `REAL_VINA_VALIDATION_SUMMARY.md`; an RC2 rerun remains required because RC2 contains post-audit release-engineering changes.
