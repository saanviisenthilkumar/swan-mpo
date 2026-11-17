# ChEMBL activity/status benchmark reproducibility

This directory provides an offline reproduction package for the SWAN-MPO
ChEMBL activity/status benchmark and its secondary domain decomposition.

## Scope

The benchmark evaluates whether fixed integration of:

- measured ChEMBL target potency used as binding evidence;
- a descriptor-derived ADME proxy; and
- a descriptor-derived structure-liability proxy (historically named the
  safety proxy in the upstream ChEMBL analysis)

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

### Revised target scope

The v1.3.3 analysis tables exclude the 5AR2/SRD5A2 target entirely. Two
5AR2 assay rows were removed from the active primary (190 to 188 records),
secondary (251 to 249 records), and external-status cohort tables. All metric,
target-stratified, bootstrap, and domain-decomposition expected outputs are
recomputed from this reduced cohort. This is a target-scope correction, not a
change to activity thresholds, score definitions, or clinical warning labels.

The upstream descriptor source still contains 514 historical 5AR2 records.
Those records are **not** part of the active v1.3.3 analyses. The source and
the original analysis lock are preserved byte-for-byte for provenance.
`scripts/exclude_5ar2.py` documents and verifies the row-exclusion step.

### Final OR2 nomenclature and BEDROC alignment

The 188-record active primary file has the same fields and data values as OR2
Table S13A (with repository-standard LF line endings).
Its historical fields `d_safety_proxy`, `d_adme_safety_proxy`,
`safety_only`, `binding_safety_gm`, and `adme_safety_gm` were renamed to
`d_structure_derived_liability`, `d_adme_liability_gm`,
`structure_derived_liability`, `binding_liability_gm`, and
`adme_liability_gm`, respectively. All values and row identities are identical
to those in the 188-record pre-rename active benchmark. The secondary 249-row
file uses the same aliases; the untouched upstream descriptor/status sources
retain their historical names for traceability.

BEDROC (alpha = 20) uses the final OR2 *tie-invariant expected-rank* rule:
each positive in a tied-score block receives the average exponential weight
over the ranks occupied by that block. This corrects the older repository's
row-order-sensitive BEDROC outputs while retaining ROC-AUC, PR-AUC,
enrichment-factor, and cohort definitions. OR2 Tables S13B, S13C, and S13D
provide canonical, independently checked values for 80 of these statistics.

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
scripts**. They operate on the revised, target-filtered record tables instead
of querying a live ChEMBL API, so later database updates cannot change the
revised benchmark outputs. Both reproduction scripts reject 5AR2 input rows.

## Reproduce the primary benchmark

From the repository root:

```bash
python reproducibility/chembl_activity_status/scripts/reproduce_activity_status_metrics.py
```

The script recomputes and checks:

- primary and secondary ROC-AUC;
- PR-AUC;
- exact tie-averaged BEDROC (alpha = 20);
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
- RDKit for optional upstream chemistry tasks (the offline metrics scripts
  themselves use NumPy for tie-averaged BEDROC)

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
