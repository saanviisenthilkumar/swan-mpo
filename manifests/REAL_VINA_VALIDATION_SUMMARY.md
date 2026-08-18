# AutoDock Vina integration validation

The public SWAN-MPO reference-redocking pathway was validated with Python 3.13.12 and AutoDock Vina 1.2.7 using the canonical mTOR/4JSP reference-redocking configuration.

- Vina executable SHA-256: `823c2bbacf26d72183861322345f0a89736aca66c8e81054c66f93af5ad623f1`
- mTOR/4JSP configuration SHA-256: `af0147f5f1b7e516d2612bcd31923fd360f17931461255cb4934a7373ac51506`
- center: 49.224, -1.763, -45.895
- box size: 16 × 16 × 16 Å
- exhaustiveness: 64
- modes: 20
- energy range: 4 kcal/mol
- seed: 2026
- result: PASS
- validation class: generated-mode recovery
- selected mode: 13
- selected reference ΔG: -6.578 kcal/mol
- symmetry-aware fixed-frame RMSD: 1.1326525817600657 Å
- RMSD cutoff: 2.0 Å
- dedicated real-Vina integration test: PASS

This validation confirms execution of the public reference-redocking pathway. The frozen published target-calibration resource remains authoritative for reproduction of the reported SWAN-MPO analysis; an integration run does not overwrite the published calibration.
