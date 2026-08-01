# SWAN-MPO CLI v1.3.1 release-candidate validation

## Status

**READY FOR USER TERMINAL / SECOND-AI REVIEW — NOT YET A PUBLIC RELEASE**

The only critical empirical check not executable in the present build environment is a real AutoDock Vina 1.2.7 integration run. The release candidate includes the command and preservation workflow for the user to run on a machine where Vina is installed.

## Frozen artifacts verified

- locked model SHA-256: `97799e91f23803de3b9a477aea3bbcfb061f1b1d9abebdecfdadcd1b537f4454`
- published target-calibration CSV SHA-256: `e7584f10c0f970bb54ddf39cfdacbb6cb061bc6a3d2bd795e2d5f119efc7287c`

Neither frozen artifact was modified.

## Local build verification

- 59 ordinary tests passed.
- 1 real-Vina integration test skipped because no Vina executable/config is available in the build environment.
- `swan-mpo verify`: PASS.
- packaged raw-input demo: PASS.
- installed CLI `--version`: PASS.
- Python compilation: PASS.
- release privacy/path audit: PASS.
- redistribution/structural-file audit: PASS; zero receptor/ligand structure assets bundled.
- published calibration classes normalize to 4 strict top-pose, 2 generated-mode recovery, 3 comparative-only.
- strict ProTox endpoint-confidence validation: PASS.
- separate status/confidence column adapter: PASS.
- exact 20-grid count checks: PASS.
- finite positive/weak individual grid energies accepted; nonnegative **calibrated median** rejected: PASS.
- receptor PDB mismatch rejected: PASS.
- missing target calibration rejected: PASS.
- comparative-only target exclusion from primary BestNode: PASS.
- generated-mode calibration chooses recovered native-like mode energy: PASS.
- symmetry/atom-order RMSD test: PASS.
- fixed-frame RMSD translation is not aligned away: PASS.
- Vina 1.2.7 version parser/enforcement tests: PASS.
- out-of-frozen-anchor warning generation: PASS.
- run metadata/input SHA recording without committed author-machine paths: PASS.
- threshold-source registry: PASS.

## User-machine evidence and v1.3.1 patch status

The immediately preceding v1.3.0 release candidate completed a fresh macOS/Apple-Silicon venv installation on the user's machine: 57 tests passed, the only configured real-Vina test was skipped, `swan-mpo verify` passed, and the installed AutoDock Vina executable reported v1.2.7. That run exposed a release-audit false positive because the audit scanned locally generated `demo_results/` files containing the console-script home path. v1.3.1 fixes both sides of that issue: shareable run metadata now redacts the home prefix and runtime output directories/local configs are git-ignored and excluded from the source-release audit.

The hosted build environment now passes 59 ordinary tests plus both audits. The exact v1.3.1 ZIP still requires a short user-machine regression and the real mTOR Vina integration before public release.

## Public-release blockers still open

1. Run the v1.3.1 regression suite on the user's Mac and confirm the fixed release audit passes after demo generation.
2. Run the real AutoDock Vina 1.2.7 mTOR/4JSP integration using `scripts/make_mtor_real_vina_config.py`.
3. Second-AI adversarial review of this exact v1.3.1 ZIP.
4. Fix any verified findings, rerun tests, then private-GitHub clean clone.
5. Only then tag/public-release and archive.
