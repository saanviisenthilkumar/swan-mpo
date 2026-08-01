# Adversarial audit closure — RC2

This file maps every finding from the independent v1.3.1 adversarial audit to its RC2 disposition.

| Finding | RC2 disposition | Evidence |
|---|---|---|
| BUG-1 Colon liability composition | **Closed.** Locked model already uses BBB + neuro only for Colon; Complex I is deliberately excluded. Shared raw ProTox input remains accepted, but audit output explicitly marks exclusion. | `test_colon_liability_is_invariant_to_complex_i_by_design`; `complex_i_included_in_liability`; manuscript already states Complex I is not penalized in colorectal panel. |
| BUG-2 demo golden values | **Closed.** Demo test now asserts Alpha/Beta numeric scores against `example_expected.json` at 1e-12. | `tests/test_verify_and_demo.py` |
| BLOCK-1 real Vina | **Closed for v1.3.1 execution path.** Actual Vina 1.2.7 mTOR/4JSP run passed; mode 13, -6.578, RMSD 1.13265 Å; real-Vina pytest passed twice. RC2 rerun required before public tag. | `REAL_VINA_VALIDATION_SUMMARY.md` |
| BLOCK-2 manuscript raw/scoring inputs | **Closed at the repository-payload level.** Exact canonical full SwissADME, exact unchanged ProTox, canonical 10,620-ledger scoring extract, and canonical expected 177/531 outputs are packaged and hash-verified. One-command regression checks all rows. Public no-login accessibility is a release/archival gate and must be verified after RC2 is pushed/publicly archived. | `swan-mpo reproduce-manuscript`; `verify --manuscript`; `manuscript_source_manifest.json` |
| DOC-1 Colon single-node BestNode | **Closed.** `PANEL_SINGLE_NODE_BESTNODE` warning emitted. Manuscript already explicitly states only mTOR is eligible. | `method_warnings.py`; regression test |
| DOC-2 allow-missing escape hatch | **Closed.** `NONSTANDARD_MODE_ACTIVATED` warning + `nonstandard_mode: true`. | CLI metadata + test |
| DOC-3 version/Vina visibility | **Closed.** `--version` exposes expected Vina 1.2.7. | CLI + test |
| DOC-4 unverified Docker | **Closed by removal.** Unverified optional Dockerfile removed rather than presenting an untested reproducibility surface. | repository tree / changelog |
| ENH-1 echo Vina command | **Implemented.** Exact portable command printed before execution and retained in run artifacts. | `vina_redocking.py` |
| ENH-2 strict verify | **Implemented.** Frozen hashes + demo golden values + manuscript 177/531 regression + exact runtime/Vina + expected method-warning contract. | `swan-mpo verify --strict` |
| ENH-3 CI badge | **Implemented.** | README + Actions workflow |
| Out-of-anchor warning coverage | **Closed.** Regression test covers MW, LogP, TPSA, rotatable bonds, HBA, HBD, SA, LD50. | `test_warnings_and_provenance.py` |
| Cross-platform path audit | **Strengthened.** macOS, Linux, and Windows home-directory patterns, local Mac hostnames, local-network domain suffixes, and placeholder repository URLs are scanned. | `scripts/audit_release.py` |

No audit disposition changes the locked mathematical model.
