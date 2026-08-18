# Descriptor-compatible MPO comparator reproducibility

This directory provides an offline reproduction package for the frozen
4,388-profile descriptor-compatible MPO comparison reported with SWAN-MPO.

## Scope

The benchmark compares the publication-facing compound-level scores for:

- Descriptor-compatible SWAN variant
- CNS-MPO-inspired oncology proxy
- LE–QED composite proxy
- QED
- QEPPI-inspired proxy

The public reproduction script does **not** regenerate molecular descriptors or
recalculate the framework scores. It starts from the frozen compound-level score
table used for the reported comparator analysis and reproduces the reported
evaluation statistics.

## Frozen population

Use the publication-facing compound-level table as:

`inputs/comparator_compound_scores.csv`

Expected SHA-256:

`5995ca74424861f3dfb5d2aefa6dd1736cb61c8760d9d63fd9e8551d9a0e7dfb`

The upstream 4,388-profile population used before publication-facing relabeling
had SHA-256:

`44ef4bbca5bffb6e196daf364fb20370ad5d52cd701e47962971d0233593e377`

The two tables are row-for-row and value-for-value identical after two column
renames:

- `pfizer_mpo` → `cns_mpo_inspired_oncology_proxy`
- `az_gse` → `le_qed_composite_proxy`

No compound scores, labels, rows, or ordering changed during that relabeling.

## Expected outputs

The archived comparator tables are stored as:

- `expected_outputs/comparator_metrics.csv`
- `expected_outputs/comparator_delong.csv`

Expected source-table SHA-256 values from the finalized supplementary package:

- comparator metrics: `7ac170a4c4b155eac416a8814f66d790e4bb7043064b147ee8488aca68d04e3d`
- paired DeLong comparisons: `7aef391096b57bc9c659d33da436f302d8e8d012db152cb0b565ad9db1c61521`

## Reproduce

From the repository root:

```bash
python reproducibility/mpo_comparator/scripts/reproduce_mpo_comparator.py
```

The script reproduces:

- ROC-AUC;
- exact tie-averaged BEDROC (alpha = 20);
- tie-averaged EF@1% and EF@5%;
- paired DeLong AUC comparisons of the descriptor-compatible SWAN variant
  against each comparator.

A successful run prints:

`MPO COMPARATOR REPRODUCTION: PASS`

The input SHA-256 is checked automatically before reproduction.

## Tie handling

BEDROC and enrichment factors use exact averaging over tied-score blocks rather
than arbitrary row order. This prevents tie blocks from inheriting label order
from the input table.

## Dependencies

The script requires Python, NumPy, pandas, SciPy, and scikit-learn.

`reproduced_outputs/` is generated locally when the script runs and should not
be committed.
