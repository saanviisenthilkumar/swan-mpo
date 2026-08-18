# Canonical mTOR/4JSP reference-redocking provenance

This record documents the canonical mTOR/4JSP reference-redocking configuration associated with the published SWAN-MPO target calibration and the public real-Vina integration check.

## Canonical configuration

- configuration SHA-256: `af0147f5f1b7e516d2612bcd31923fd360f17931461255cb4934a7373ac51506`
- native-ligand center: `(49.224, -1.763, -45.895)` Å
- box size: `16 × 16 × 16` Å
- exhaustiveness: `64`
- number of modes: `20`
- energy range: `4` kcal/mol
- seed: `2026`
- AutoDock Vina version: `1.2.7`

Canonical structural-input inventory:

- `4JSP_receptor.pdbqt`: 2,171,840 bytes
- `AGS_native.pdbqt`: 4,681 bytes

## Published calibration

The frozen published mTOR calibration is classified as generated-mode recovery:

- top-mode ΔG: -6.969 kcal/mol
- top-mode heavy-atom RMSD: 3.001 Å
- selected native-like mode: 13
- selected reference ΔG: -6.578 kcal/mol
- selected reference RMSD: 1.274 Å

The published calibration resource remains the authority for reproduction of the reported SWAN-MPO analysis.

## Public real-Vina integration check

The public CLI can independently execute prepared reference-ligand redocking with AutoDock Vina 1.2.7. Its symmetry-aware, fixed-frame heavy-atom RMSD implementation may yield a different RMSD for symmetry-equivalent poses than the historical calibration workflow.

Accordingly, a new real-Vina integration run validates the public redocking pathway but does not replace or silently modify the frozen published calibration.
