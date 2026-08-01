# Real AutoDock Vina validation

Validated on the author's macOS ARM machine with Python 3.13.12 and actual AutoDock Vina 1.2.7.

- Vina executable SHA-256: `823c2bbacf26d72183861322345f0a89736aca66c8e81054c66f93af5ad623f1`
- mTOR / 4JSP tight-box config provenance SHA-256: `af0147f5f1b7e516d2612bcd31923fd360f17931461255cb4934a7373ac51506`
- center: 49.224, -1.763, -45.895
- box: 16 × 16 × 16 Å
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
- optional real-Vina pytest: PASS twice (~68.5 s each)

This validates the executable path. Frozen Table S6 remains authoritative for the published analysis; the new run does not overwrite frozen calibration. The exact v1.3.2 RC2 build was rerun after the adversarial-review fixes and passed the real-Vina integration and dedicated real-Vina pytest.
