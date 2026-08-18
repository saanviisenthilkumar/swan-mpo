# AutoDock Vina reference-redocking runner

`redock-reference` calibrates **reference/native ligands for targets**. It is not a candidate virtual-screening engine.

## Prerequisites

- AutoDock Vina 1.2.7 for manuscript-faithful verification;
- a prepared receptor PDBQT;
- a prepared crystallographic/native or otherwise justified reference-ligand PDBQT **whose heavy-atom coordinates remain in the receptor/crystallographic frame**;
- a scientifically justified docking box;
- identical receptor/PDB identity between calibration and subsequent candidate docking.

SWAN-MPO does not prepare structures or infer binding sites. Reference-ligand preparation must preserve the experimental/native heavy-atom pose used for RMSD comparison; re-embedding or independently optimizing the reference ligand before redocking would invalidate the pose-reproduction RMSD.

## Run

```bash
swan-mpo redock-reference \
  --targets-config configs/my_redocking.json \
  --require-vina-1-2-7 \
  --output-dir redocking_results
```

The runner records Vina version, exact command, seed, CPU, exhaustiveness, number of modes, scoring function, receptor/native-ligand hashes, stdout/stderr, docked PDBQT, mode energies, mode RMSDs, and the derived calibration.

## Symmetry-aware RMSD

The default `symmetry` backend calculates **fixed-receptor-frame heavy-atom RMSD** without structural superposition. Atom matching is minimized across element-preserving molecular-graph isomorphisms so symmetry-equivalent atoms and atom-order changes do not silently inflate RMSD.

Connectivity is perceived independently for the native and docked ligand from heavy-atom coordinates using covalent radii plus a conservative tolerance. This is intentionally transparent and testable, but automatic connectivity perception is still a heuristic. The RMSD method and number of graph isomorphisms evaluated are written to `reference_redocking.csv`.

An explicit `ordered` backend exists only for controlled cases where PDBQT heavy-atom identity/order is independently known to be preserved. It is not the recommended default for new targets.

The 2.0 Å decision cutoff is applied to the fixed-frame heavy-atom RMSD.

## Calibration decision

1. top-ranked Vina mode within cutoff → `strict_top_pose`;
2. otherwise, a generated mode within cutoff → `generated_mode_recovery`, and the recovered native-like mode's energy becomes `reference_dg`;
3. otherwise → `comparative_only`, with no primary reference-calibrated BestNode eligibility.

This is especially important for the published generated-mode-recovery targets: primary calibration uses the validated native-like generated-mode energy rather than automatically using Vina mode 1.

## Independent real-Vina verification

Before public release, run at least one actual target end to end:

```bash
vina --version
swan-mpo verify --check-vina
swan-mpo verify \
  --vina-config my_verified_target_redocking.json \
  --output-dir real_vina_verification
```

The last command requires Vina 1.2.7 and preserves the integration artifacts for review. A mocked/fake-Vina unit test is useful for software control flow but does not substitute for this real integration test.

## Published targets

The repository bundles the frozen, audited calibration table used for the manuscript. Normal reproduction of published scoring uses that table rather than regenerating calibration under possibly changed conditions.


## Energy range and manuscript-faithful mTOR check

The redocking runner accepts `energy_range` in the defaults or per-target record and passes it to Vina as `--energy_range`. The frozen mTOR/4JSP tight-native-box redocking used 16 × 16 × 16 Å, exhaustiveness 64, 20 modes, energy range 4 kcal/mol, seed 2026, and the native-ligand center (49.224, -1.763, -45.895). These are distinct from the 40 Å candidate-screening boxes.
