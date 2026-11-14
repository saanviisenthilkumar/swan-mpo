# SWAN-MPO v1.3.3

**SWAN-MPO (Target-Calibrated Multi-Parameter Optimization)** is a reproducible framework for **multi-domain natural-product scaffold triage**. It integrates receptor-specific binding evidence with ADME, general safety, and context-dependent liability on a common bounded desirability scale, then combines those domains using an equal-weight geometric mean.

The framework was developed and evaluated in oncology-focused natural-product screening, with *Annona muricata* as the primary deployment case. Its methodological contribution is the integration architecture: median multi-grid docking is calibrated to target-specific references before panel-level binding aggregation, while binding and nonbinding domains remain separately auditable throughout scoring.

> **Frozen scoring implementation:** `src/swan_mpo/locked_model.py`
> SHA-256: `97799e91f23803de3b9a477aea3bbcfb061f1b1d9abebdecfdadcd1b537f4454`
>
> **Oncology target-calibration resource:**
> SHA-256: `1c4d9b17a745792a38fd0b6a0fe3793730a991c3e621b0b5e10535297ea1f88e`
>
> The bundled oncology configuration covers eight receptor structures. The locked scoring equations remain unchanged.

## What SWAN-MPO does

For candidate-library scoring, researchers provide candidate docking results, SwissADME-compatible ADME/property outputs, ProTox-compatible toxicity predictions, and a prespecified panel-liability configuration.

SWAN-MPO:

- summarizes candidate docking across grid centers using the median docking energy;
- converts docking energies to target-specific calibrated binding desirabilities;
- restricts primary cross-target aggregation to eligible calibrated targets;
- calculates panel-level BestNode binding and associated node/calibration diagnostics;
- transforms ADME, general-safety, and context-dependent-liability inputs to bounded desirabilities;
- combines binding, ADME, safety, and liability using an equal-weight geometric mean;
- returns ranked scaffold outputs together with component scores, warnings, hashes, and audit tables.

SWAN-MPO does **not** call SwissADME or ProTox web services and does not automatically generate the candidate-library docking campaign. Those upstream outputs are supplied as inputs.

## Install and verify

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
pytest -q
swan-mpo verify
```

On Windows PowerShell:

```powershell
.venv\Scripts\Activate.ps1
```

The validated core-software environment uses Python 3.13.x. Reference-redocking validation used AutoDock Vina 1.2.7. See `docs/ENVIRONMENTS.md` for environment details.

## Candidate-library scoring

Validate inputs:

```bash
swan-mpo validate \
  --docking candidate_docking.csv \
  --adme swissadme.csv \
  --toxicity protox.csv \
  --config published-oncology
```

Score a candidate library:

```bash
swan-mpo score \
  --docking candidate_docking.csv \
  --adme swissadme.csv \
  --toxicity protox.csv \
  --config published-oncology \
  --output-dir results
```

The bundled `published-oncology` configuration reproduces the eight-structure oncology implementation. Custom configurations can be supplied by path; see `examples/templates/` and `docs/INPUTS_AND_CALIBRATION.md`.

## Frozen scoring reproduction

The exact canonical upstream predictor inputs required for the 59-compound expanded *A. muricata* deployment are packaged with the repository resources.

```bash
swan-mpo reproduce-manuscript --output-dir manuscript_reproduction
```

This command deterministically recomputes the **candidate-library SWAN-MPO scoring outputs** and verifies them against the packaged reference results. It reproduces 472 target-level summaries and 177 panel-level scores from the 59-compound × 8-structure deployment, with 9,440 expanded docking observations.

It does **not** rerun docking or regenerate SwissADME/ProTox predictions. Paper-specific external validation analyses are reproduced separately from dedicated offline analysis scripts rather than exposed as core CLI commands.

## ChEMBL activity/status benchmark reproduction

The frozen ChEMBL activity/status benchmark and its secondary domain decomposition are packaged under `reproducibility/chembl_activity_status/`.

Install its validated reproduction environment:

```bash
python -m pip install -r reproducibility/chembl_activity_status/requirements.txt
```

Reproduce the primary benchmark:

```bash
python reproducibility/chembl_activity_status/scripts/reproduce_activity_status_metrics.py
```

Reproduce the secondary domain decomposition:

```bash
python reproducibility/chembl_activity_status/scripts/reproduce_domain_decomposition.py
```

The packaged benchmark uses 188 primary and 249 secondary records, excluding 5AR2-target assay records. Activity/status metrics and domain-decomposition outputs correspond to these inputs. The original ChEMBL descriptor source and its analysis lock are retained as provenance. No live ChEMBL API is used during reproduction.

## Descriptor-compatible MPO comparator reproduction

The frozen 4,388-profile descriptor-compatible comparator analysis is packaged under `reproducibility/mpo_comparator/`.

Install its validated reproduction environment:

```bash
python -m pip install -r reproducibility/mpo_comparator/requirements.txt
```

Reproduce the reported comparator metrics and paired DeLong comparisons:

```bash
python reproducibility/mpo_comparator/scripts/reproduce_mpo_comparator.py
```

This reproduction starts from the frozen publication-facing compound-level score table and recomputes the reported tie-averaged ROC-AUC, BEDROC, enrichment factors, and paired DeLong statistics. It does not regenerate molecular descriptors or framework scores.

## New-target reference calibration

For a new target, SWAN-MPO can evaluate a prepared reference-ligand redocking setup:

```bash
swan-mpo redock-reference \
  --targets-config configs/my_target_redocking.json \
  --require-vina-1-2-7 \
  --output-dir redocking_results
```

The redocking package records mode energies, symmetry-aware heavy-atom RMSDs, calibration decisions, Vina version information, hashes, and logs. Comparative-only targets do not enter primary BestNode aggregation.

## Published calibration classes

- **Strict top-pose:** Bcl-2, AR, PI3Kα, AKT1
- **Generated-mode recovery:** mTOR
- **Comparative-only / excluded from primary BestNode:** EGFR, Caspase-3, mitochondrial Complex I

Under the published calibration, mTOR is the only eligible calibrated target in the colorectal panel. The CLI therefore reports the corresponding single-node BestNode warning rather than treating the panel as a multi-node calibrated aggregation.

## Real-Vina integration validation

The public reference-redocking pathway was validated with AutoDock Vina 1.2.7 using the canonical mTOR/4JSP configuration. The integration run recovered the published generated-mode classification and selected mode 13 with ΔG = -6.578 kcal/mol; the public symmetry-aware fixed-frame implementation gave an RMSD of 1.1326525817600657 Å. The frozen published target-calibration resource remains authoritative for reproduction of the reported analysis.

## Score outputs

A standard scoring run writes machine-readable outputs exposing transformed desirabilities, target-level binding, calibration provenance, panel-level scores, warnings, run metadata, and hashes. Core outputs include:

- `compound_safety_adme_desirabilities.csv`
- `panel_liability_desirabilities.csv`
- `target_level_binding.csv`
- `target_calibration_used.csv`
- `swan_panel_scores.csv`
- `warnings.csv`
- `run_metadata.json`
- `run_manifest.json`
- `run.log`

## Model transparency

```bash
swan-mpo explain-model
swan-mpo explain-model --sources
swan-mpo show-published-calibration
```

## Reproducibility resources

Key documentation and analysis packages include:

- `docs/INPUTS_AND_CALIBRATION.md`
- `docs/VINA_REFERENCE_REDOCKING.md`
- `docs/THRESHOLD_PROVENANCE.md`
- `docs/ENVIRONMENTS.md`
- `docs/LICENSE_AND_REDISTRIBUTION.md`
- `docs/MANUSCRIPT_REPRODUCTION.md`
- `reproducibility/chembl_activity_status/`
- `reproducibility/mpo_comparator/`
- `examples/templates/`

## Citation

**Current software:** *SWAN-MPO v1.3.3*. See `CITATION.cff` for citation metadata. The version-specific archival DOI will be added after the v1.3.3 Zenodo record is available.

**Previous archived version:** Senthilkumar S. *SWAN-MPO v1.3.2* [Computer software]. DOI: https://doi.org/10.5281/zenodo.21988306

**Study data and reproducibility materials**
Open Science Framework: `10.17605/OSF.IO/35QF2`

## Licensing

Source code is distributed under the MIT License. Repository-authored data and documentation use CC BY 4.0 unless file-specific upstream terms apply. Upstream resources remain subject to their original licensing and redistribution terms.
