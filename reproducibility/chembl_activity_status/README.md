# ChEMBL activity/status benchmark reproducibility

This directory provides an offline reproduction package for the SWAN-MPO
ChEMBL activity/status benchmark and its secondary domain decomposition.

## Scope

The benchmark evaluates whether fixed integration of:

- measured ChEMBL target potency used as binding evidence;
- a descriptor-derived ADME proxy; and
- a descriptor-derived safety proxy

ranks target-active compounds with favorable external ChEMBL clinical status
above complementary activity/status negatives.

This is **not** a full end-to-end four-domain SWAN-MPO run. It does not rerun
candidate docking, target-reference calibration, SwissADME, ProTox, panel
liability, or BestNode.

The primary endpoint is:

- **A:** active + approved/no recorded serious warning
- **B:** active + serious warning
- **C:** weak/inactive + approved/no recorded serious warning
- primary comparison: **A vs (B + C)**

A secondary all-groups table additionally contains group D
(weak/inactive + serious warning).

## Frozen ChEMBL provenance

The benchmark was generated against **ChEMBL 37**, release date 2026-05-01.
The original analysis lock is retained in:

`provenance/original_analysis_lock.json`

The frozen descriptor source distributed here is byte-identical to the source
used by the original analysis:

`inputs/chembl37_descriptor_source.csv`

Expected SHA-256:

`1467e09f92e6d6c57d2f10f8b1a537c0c344221a0f86dc0683b0c4f33be19d98`

The original generating-script SHA-256 recorded by the analysis lock is:

`450f011e3ec3a53977e5b1fe7eab7277a1652aa34a834e0df97a29f4488a82a3`

The public scripts in this directory are separate **offline reproduction
scripts**. They intentionally operate on the frozen record tables instead of
querying a live ChEMBL API, so later database updates cannot change the
manuscript-facing results.

## Reproduce the primary benchmark

From the repository root:

```bash
python reproducibility/chembl_activity_status/scripts/reproduce_activity_status_metrics.py
```

The script recomputes and checks:

- primary and secondary ROC-AUC;
- PR-AUC;
- BEDROC (alpha = 20);
- tie-aware EF@1% and EF@5%;
- parent-clustered bootstrap delta-AUC (2,000 replicates, seed 2026);
- activity/status group counts;
- target-stratified descriptive metrics.

A successful run prints:

`ACTIVITY/STATUS REPRODUCTION: PASS`

## Reproduce the secondary domain decomposition

```bash
python reproducibility/chembl_activity_status/scripts/reproduce_domain_decomposition.py
```

The decomposition reports:

- A vs B;
- A vs C;
- a B/C-balanced sensitivity;
- parent-clustered bootstrap delta-AUC (5,000 replicates, seed 2026).

This decomposition was performed after inspection of the primary benchmark.
It is retained as a secondary mechanism/sensitivity analysis and does not
replace the primary A-vs-(B+C) endpoint.

A successful run prints:

`DOMAIN DECOMPOSITION REPRODUCTION: PASS`

## Dependencies

The offline benchmark scripts require:

- Python 3.13
- NumPy
- pandas
- scikit-learn
- RDKit

Install the validated reproduction environment with:

```bash
python -m pip install -r reproducibility/chembl_activity_status/requirements.txt
```

## File organization

- `inputs/` contains frozen descriptor/status/benchmark record tables.
- `expected_outputs/` contains the archived numerical results.
- `provenance/` contains the original analysis lock.
- `scripts/` contains journal-independent offline reproduction scripts.
- `reproduced_outputs/` is created locally when the scripts are run and should
  not be committed.

The 125 MB molecule API cache used during the original live ChEMBL retrieval is
not required for offline numerical reproduction and is therefore not included
in this software package.
