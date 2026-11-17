# Descriptor-compatible MPO comparator reproducibility

This directory provides an offline reproduction package for the corrected
3,980-profile descriptor-compatible MPO comparison in final Online Resource 2,
Tables S14A–S14C (995 ChEMBL actives and 2,985 synthetic comparison profiles).

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

`71fd4a0b39e0e7f4ad4aadf7cd1e4328203bd853434ef94f520e9cc79923a974`

The preceding repository version contained a **different historical
4,388-profile cohort**, now superseded for the final OR2 comparator results.
Its archived input SHA-256 was:

`5995ca74424861f3dfb5d2aefa6dd1736cb61c8760d9d63fd9e8551d9a0e7dfb`

That older file was itself the publication-facing relabeling of an earlier
4,388-profile source (`44ef4bbca5bffb6e196daf364fb20370ad5d52cd701e47962971d0233593e377`),
with the two historical column-name changes:

- `pfizer_mpo` → `cns_mpo_inspired_oncology_proxy`
- `az_gse` → `le_qed_composite_proxy`

The old relabeling did not change its own scores, labels, rows, or order;
**it did not convert the 4,388-profile cohort into the corrected 3,980-profile
cohort**. The final input is copied byte-for-byte from OR2 Table S14C.

## Expected outputs

The archived comparator tables are stored as:

- `expected_outputs/comparator_metrics.csv`
- `expected_outputs/comparator_delong.csv`

Expected source-table SHA-256 values from the finalized supplementary package:

- comparator metrics (OR2 S14A): `cb83f6da8fff793c7a162b013431c363702b37e866b7c1440c1cddaabf750f5a`
- paired DeLong comparisons (OR2 S14B): `b64e09fb9ffd5c67516dd47c11cc7178009382ab0c6f0aeef962afc8bf0ad97a`

The comparison cohort includes **synthetic profiles**, not experimentally
confirmed inactives. Neutral safety (0.50) and liability (0.60) placeholders
are used for both classes, so these statistics are exploratory ranking
comparisons rather than prospective toxicity or clinical validation.

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
