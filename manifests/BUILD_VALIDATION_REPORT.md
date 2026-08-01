# RC2 build validation report

## Frozen artifacts
- locked model expected SHA-256: `97799e91f23803de3b9a477aea3bbcfb061f1b1d9abebdecfdadcd1b537f4454`
- published calibration expected SHA-256: `e7584f10c0f970bb54ddf39cfdacbb6cb061bc6a3d2bd795e2d5f119efc7287c`

## Previously completed real-machine evidence
The v1.3.1 execution path passed a fresh macOS ARM install, ordinary tests, release/license audits, Vina 1.2.7 detection, actual mTOR/4JSP reference redocking, and real-Vina pytest twice. See `REAL_VINA_VALIDATION_SUMMARY.md`.

## RC2 changes
- exact canonical manuscript ADME/ProTox/docking inputs packaged;
- one-command 177-panel + 531-target manuscript regression;
- Colon Complex I exclusion made explicit/auditable without changing locked math;
- golden demo numeric assertion;
- single-node and nonstandard-mode warnings;
- Vina expectation in version output and command echo;
- strict verifier;
- expanded boundary-warning tests;
- expanded cross-platform privacy audit;
- CI manuscript regression;
- unverified Docker recipe removed.

The RC2 Mac and real-Vina gates passed on the author's macOS ARM machine. The tagged `v1.3.2-rc2` commit was subsequently cloned into a fresh directory, installed in a new virtual environment, and passed the portable test suite (70 passed, 1 expected optional real-Vina skip), exact manuscript reproduction (177/177 panel rows and 531/531 target-level rows; zero failures), release audit, and license/redistribution audit.

## Sandbox RC2 verification
- Python compilation of `src/`, `tests/`, and `scripts/`: **PASS**.
- ordinary/unit/integration suite excluding actual Vina: **70 passed, 1 real-Vina test skipped**.
- exact manuscript packaged-input hash checks: **PASS**.
- incomplete historical SwissADME export rejection/no-imputation regression: **PASS**.
- standalone `verify --manuscript`: **PASS**.
- standalone one-command manuscript reproduction: **PASS — 177 panel rows, 531 target rows, zero failures**.
- Muricatacin reproduced as Colon rank 1, Prostate rank 2, RCC rank 2; binding rank 47 in all three panels.
- locked model SHA-256: **PASS** (`97799e91...f4454`).
- published calibration SHA-256: **PASS** (`e7584f10...c7287c`).
- RC2 release/privacy audit: **PASS**.
- RC2 license/redistribution audit: **PASS**.

## RC2 author-Mac validation
- Python 3.13.12 / macOS ARM fresh virtual-environment install: **PASS**.
- full test invocation: **71 passed**.
- `verify --manuscript`: **PASS**.
- manuscript regression: **177/177 panel rows and 531/531 target rows; zero failures**.
- release/privacy audit: **PASS**.
- license/redistribution audit: **PASS**.
- AutoDock Vina 1.2.7 detection: **PASS**.
- actual mTOR/4JSP reference redocking: **PASS**.
- real-Vina result: generated-mode recovery, mode 13, ΔG = -6.578 kcal/mol,
  symmetry-aware fixed-frame RMSD = 1.1326525817600657 Å.
- dedicated `pytest -q -m real_vina`: **PASS**.
- `swan-mpo verify --strict`: **PASS**.

## Remaining external release gates
1. Push/tag RC2 privately and run a **fresh clean clone** install + tests + manuscript regression + audits.
2. Make the final code/data endpoint publicly accessible without login and verify archival/public links before JoC submission.
