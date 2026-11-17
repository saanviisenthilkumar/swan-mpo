# Supplementary release provenance and reproducibility alignment

This repository aligns its public offline ChEMBL and descriptor-compatible
comparator reproduction files with the verified 49-table Online Resource 2
(OR2) release candidate:

- OR2 file: `SWAN_OR2_49TABLE_FINAL_SOURCE_VERIFIED_20261117.zip`
- OR2 ZIP SHA-256: `57e828f08cba817c0650482fd96947e6169e8bd46627f60b8b6242d925140993`
- OR2 supplementary tables: 49; archive-level table manifest: 49/49 verified.

## What changed in the GitHub reproduction layer

1. **S13:** The 188-record primary ChEMBL table matches OR2 S13A; historical
   descriptor-safety field names were relabeled as *structure-derived liability*
   without changing the underlying observations. The 249-row secondary table
   uses the same aliases. The BEDROC calculation now averages exponential rank
   weights for tied scores and is independent of input row order. All 80 BEDROC
   values across S13B, S13C, and S13D were independently reconstructed in OR2.
   The historical ChEMBL 37 descriptor source and original generator hash remain
   preserved without rewriting provenance.

2. **S14:** The comparator input is byte-identical to OR2 S14C (3,980 rows:
   995 ChEMBL actives and 2,985 synthetic comparison profiles); the expected
   metrics and DeLong tables are byte-identical to OR2 S14A and S14B.
   The previously shipped 4,388-profile comparator cohort is superseded and
   retained only in documented historical checksums. The paired DeLong 95%
   confidence intervals use the normal 97.5th percentile for consistency with
   OR2. The source-score generation is historical; the public script reproduces
   the evaluation statistics from frozen compound-level scores.

3. **Core model:** The locked panel-specific SWAN-MPO scoring implementation is
   not modified here. The 59-compound, eight-structure deployment covers 9,440
   Vina score records and 177 compound-panel SWAN scores, as in OR2 S3, S8B,
   S17D, and S24.

## Scope and methodological qualifications

- The broad ChEMBL S11/S12 and comparator S14 synthetic profiles are not
  experimentally demonstrated inactive compounds; neutral safety and liability
  placeholder values are shared across the benchmark classes. These are
  exploratory ranking tests, not a claim of prospective clinical or toxicity
  validation.
- The ChEMBL activity/status S13 benchmark is a **distinct** 188-record
  analysis based on ChEMBL potency and structure-derived proxy variables; it
  is not an end-to-end candidate docking re-run.
- The historical global 15-compound S16 model and current 177-score S24
  panel-specific ablations have different scopes and are not interchangeable.
- OR2 separately bundles its own reconstructed S10–S12 and S16 verifiers,
  S22 full-universe checks, S23 hash metadata, and associated provenance.
  This GitHub repository does not claim to contain every original docking
  pose/log, full COCONUT source record, or historical generating script.

No numerical change was made to the locked SWAN-MPO scoring equations in this
alignment. A changed GitHub/Zenodo version label, if later issued, is a
release-management decision and not evidence of a changed scoring model.
