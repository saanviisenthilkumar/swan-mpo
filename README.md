# SWAN-MPO v1.3.2 — private review candidate RC2

[![tests](https://github.com/saanviisenthilkumar/swan-mpo/actions/workflows/tests.yml/badge.svg)](https://github.com/saanviisenthilkumar/swan-mpo/actions/workflows/tests.yml)

SWAN-MPO is a transparent scoring layer for safety-aware, affinity-normalized multi-parameter optimization. The standard workflow starts from **raw upstream candidate-docking, ADME/property, and toxicity/liability outputs**. Users do **not** calculate SWAN domain scores themselves.

> **Frozen science:** `src/swan_mpo/locked_model.py` remains byte-identical to SHA-256 `97799e91f23803de3b9a477aea3bbcfb061f1b1d9abebdecfdadcd1b537f4454`. The bundled published calibration remains SHA-256 `e7584f10c0f970bb54ddf39cfdacbb6cb061bc6a3d2bd795e2d5f119efc7287c`. RC2 changes release engineering, validation, warnings, provenance, and manuscript reproduction only.

## Scientific automation boundary

Researchers provide candidate **grid-level docking results**, raw SwissADME-compatible physicochemical/ADME output, and raw ProTox-compatible toxicity/liability predictions. For a new target they also provide prepared receptor/native-ligand PDBQT files and a justified reference-redocking box.

SWAN-MPO validates those inputs and calculates safety, ADME, panel-specific liability, the median docking energy for each compound-target block, target-reference-calibrated binding, primary BestNode, the equal-weight four-domain geometric mean, ranks, warnings, hashes, and audit tables. It may launch AutoDock Vina for **reference-ligand redocking** of new targets. It deliberately does **not** call SwissADME/ProTox web services or automate candidate-compound docking.

For the published oncology implementation, Colon liability uses **BBB + neurotoxicity only**; Complex I is intentionally excluded because Complex I is an intended colorectal docking target. Prostate/RCC liability use BBB + Complex I + neurotoxicity. The audit output records the endpoint set used for every panel.

## Install and verify

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
pytest -q
swan-mpo verify
```

The tested macOS ARM validation used Python 3.13.12 and AutoDock Vina 1.2.7. See `docs/ENVIRONMENTS.md`.

## Reproduce the manuscript expanded screen

The exact canonical scoring inputs needed for the 59-compound expanded screen are now packaged under `src/swan_mpo/resources/`. Run:

```bash
swan-mpo reproduce-manuscript --output-dir manuscript_reproduction
```

The command recomputes **531 target-level rows and 177 panel rows** and compares them to frozen canonical expected outputs. It must reproduce Muricatacin as Colon rank 1, Prostate rank 2, RCC rank 2, with binding-only/BestNode binding rank 47 in all three panels. `manuscript_source_manifest.json` records the exact source hashes.

The required ADME file is the exact full SwissADME batch export used by the frozen analysis (`expanded_acetogenins_swissadme_CANONICAL_FULL.csv`, SHA-256 `a1b6339695bba431239def8969d56244cecd978e195e5eaf2a3019ca21ec7ab1`). An earlier incomplete export with blank Consensus Log P is retained only as provenance and is **not** used for reproduction. No logP imputation occurs in `reproduce-manuscript`.

## Synthetic installation demo

```bash
swan-mpo score --demo --output-dir demo_results
```

This independent synthetic regression example checks the public raw-input architecture. Its Alpha/Beta golden scores are asserted numerically by the test suite.

## Standard scoring

```bash
swan-mpo validate \
  --docking candidate_docking.csv \
  --adme swissadme.csv \
  --toxicity protox.csv \
  --config published-oncology

swan-mpo score \
  --docking candidate_docking.csv \
  --adme swissadme.csv \
  --toxicity protox.csv \
  --config published-oncology \
  --output-dir results
```

`--allow-missing-predictors` is an explicit nonstandard historical-reproduction mode. When used, SWAN writes `NONSTANDARD_MODE_ACTIVATED` to `warnings.csv` and `nonstandard_mode: true` to `run_metadata.json`.

## New-target reference redocking

```bash
swan-mpo redock-reference \
  --targets-config configs/my_target_redocking.json \
  --require-vina-1-2-7 \
  --output-dir redocking_results
```

Before each run the CLI echoes the exact portable Vina command. The redocking package retains mode energies, symmetry-aware fixed-frame heavy-atom RMSDs, calibration decisions, Vina version/hash, input hashes, and logs. Comparative-only targets can never enter primary BestNode.

## Verification

```bash
swan-mpo verify
swan-mpo verify --manuscript
swan-mpo verify --check-vina
swan-mpo verify --strict
```

`--strict` checks the locked model and calibration hashes, synthetic golden values, the full manuscript reproduction, Python 3.13.x, pinned NumPy/NetworkX versions, exact Vina 1.2.7, and the expected published single-node Colon warning contract.

## Score outputs

Every score run writes `compound_safety_adme_desirabilities.csv`, `panel_liability_desirabilities.csv`, `target_level_binding.csv`, `target_calibration_used.csv`, `swan_panel_scores.csv`, `warnings.csv`, `run_metadata.json`, `run_manifest.json`, and `run.log`. These expose raw values, transformed desirabilities, domain scores, node selection, final score, warnings, versions, hashes, and input provenance.

Under the published calibration, **Colon has one reference-calibrated target (mTOR)**, so the CLI writes `PANEL_SINGLE_NODE_BESTNODE`. This is an interpretive warning, not an arithmetic failure.

## Model transparency

```bash
swan-mpo explain-model
swan-mpo explain-model --sources
swan-mpo show-published-calibration
```

## Published calibration classes

- strict top-pose: Bcl-2, AR, PI3Kα, AKT1
- generated-mode recovery: mTOR, 5AR2
- comparative-only / excluded from primary BestNode: EGFR, Caspase-3, Complex I

Ties in the frozen expanded-screen BestNode implementation are broken deterministically using the historical target/PDB ordering encoded in `bestnode_tie_priority`; this reproduces all 177 canonical selected-node labels.

## Real-Vina validation already completed

The v1.3.1 code path immediately preceding RC2 was tested on the author's Mac against an actual AutoDock Vina 1.2.7 executable using the canonical mTOR/4JSP tight-box setup. It reproduced `generated_mode_recovery`, selected mode 13, ΔG = -6.578 kcal/mol, and symmetry-aware fixed-frame RMSD = 1.1326525817600657 Å. The optional real-Vina pytest passed twice. RC2 must be rerun on the same machine after review fixes before public release.

## Documentation

- `docs/INPUTS_AND_CALIBRATION.md` — schemas, panel liability, manuscript data
- `docs/VINA_REFERENCE_REDOCKING.md` — Vina/RMSD workflow
- `docs/THRESHOLD_PROVENANCE.md` — frozen anchor provenance
- `docs/SCOPE.md` — supported/nonstandard operations
- `docs/ENVIRONMENTS.md` — tested/pinned runtime information
- `docs/LICENSE_AND_REDISTRIBUTION.md` — licensing and data provenance
- `docs/MANUSCRIPT_REPRODUCTION.md` — exact 59-compound/177-panel/531-target reproduction workflow
- `docs/ARCHIVAL_RELEASE_CHECKLIST.md` — public no-login archival and manuscript-link gate
- `examples/templates/` — user input templates

## Licensing

Source code is MIT licensed. Repository-authored data/docs are CC BY 4.0 unless file-specific upstream terms apply. The bundled SwissADME exports are attributed under SwissADME's CC BY 4.0 Licensed Materials terms. The exact unchanged ProTox raw export is marked under the upstream CC BY-ND 4.0 notice linked by ProTox and is not relicensed by SWAN-MPO. No receptor/native-ligand structure files are redistributed.
