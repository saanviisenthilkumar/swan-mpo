# mTOR/4JSP historical redocking provenance used for the real-Vina integration check

This record exists to prevent the real-Vina integration check from silently using the
40 Å candidate-screening box or the generic CLI defaults.

Historical source recovered from the frozen July 28 file audit:

- project-relative source: `phase3_target_pdb_validation/redocking/4JSP/config_tight.txt`
- SHA-256: `af0147f5f1b7e516d2612bcd31923fd360f17931461255cb4934a7373ac51506`
- native-ligand center: `(49.224, -1.763, -45.895)` Å
- box size: `16 × 16 × 16` Å
- exhaustiveness: `64`
- number of modes: `20`
- energy range: `4` kcal/mol
- seed: `2026`
- historical Vina log: AutoDock Vina `1.2.7`
- historical log reported CPU setting: `0`

Audited input inventory:

- `4JSP_receptor.pdbqt`: 2,171,840 bytes
- `AGS_native.pdbqt`: 4,681 bytes

Frozen Table S6 reports the historical mTOR calibration as generated-mode recovery:

- top-mode ΔG: -6.969 kcal/mol
- top-mode heavy-atom RMSD: 3.001 Å
- selected native-like mode: 13
- selected reference ΔG: -6.578 kcal/mol
- selected reference RMSD: 1.274 Å

## Important interpretation

The bundled Table S6 calibration remains the authority for the published analysis.  A
new real-Vina run is an integration/reproducibility check of the public redocking path;
it does **not** replace the frozen calibration.  The public CLI uses a symmetry-aware,
fixed-frame heavy-atom RMSD implementation for new targets.  That improved RMSD method
can in principle assign a different RMSD to a symmetry-equivalent pose than the
historical workflow.  Therefore a real-Vina integration result must not silently
supersede the published Table S6 values.
