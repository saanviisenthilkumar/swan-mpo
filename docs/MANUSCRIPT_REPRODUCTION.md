# Manuscript reproduction

The public release is designed so a third party can reproduce the frozen 59-compound expanded SWAN-MPO screen without manually calculating any SWAN domain score.

## Inputs bundled with the release

The package contains:

- the exact canonical 59-row full SwissADME export used by the frozen analysis;
- the exact unchanged 59-row ProTox export used by the frozen analysis;
- a 10,620-row five-column docking extract copied row-for-row from the canonical complete docking ledger, retaining every compound/target/PDB/grid/affinity value required for scoring while omitting local filesystem paths and runtime-only fields;
- the frozen 177-row panel-score validation extract;
- the frozen 531-row target-level binding validation extract;
- the frozen nine-target redocking/calibration resource.

Exact original-source and packaged-file SHA-256 values are recorded in `src/swan_mpo/resources/manuscript_source_manifest.json`.

## One-command reproduction

```bash
swan-mpo reproduce-manuscript --output-dir manuscript_reproduction
```

The command recomputes:

1. raw ADME desirabilities and the ADME domain score;
2. raw safety desirabilities and the safety domain score;
3. panel-specific liability, including explicit exclusion of Complex I from Colon liability;
4. the median docking energy for each of 531 compound-target blocks from 20 grid values per block;
5. target-reference-calibrated binding for eligible targets;
6. primary BestNode selection;
7. the four-domain SWAN-MPO score and within-panel ranks.

It then compares all 177 panel records and all 531 target-level records against the frozen canonical outputs. A nonzero mismatch causes the command to report `FAIL` and exit nonzero.

Expected Muricatacin regression:

- Colon: score 0.7337646613702474, rank 1, BestNode mTOR, binding rank 47;
- Prostate: score 0.6609780531711298, rank 2, BestNode mTOR, binding rank 47;
- RCC: score 0.6609780531711298, rank 2, BestNode mTOR, binding rank 47.

## Predictor provenance and licensing

SwissADME Licensed Materials are described by SIB as CC BY 4.0; the repository retains the exact canonical export and attribution. The ProTox site links its Creative Commons notice to CC BY-ND 4.0; the repository therefore distributes only the exact unchanged ProTox raw export and does not relicense it as repository-authored data. See `DATA_LICENSE.md` and `THIRD_PARTY_NOTICES.md`.

The CLI does not automate SwissADME or ProTox web requests. It consumes their already-generated outputs.

## Public-access requirement

Before journal submission, the tagged release and archival record must be tested from an incognito/not-signed-in browser. A reviewer must be able to obtain the required reproduction inputs without registration or private-repository access.
