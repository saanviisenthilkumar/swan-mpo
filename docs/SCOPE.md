# Scope and interpretation

## Standard supported workflow
SWAN-MPO accepts candidate grid-level docking, raw ADME/property output, and raw toxicity/liability output, then computes the frozen domain desirabilities, target-calibrated BestNode, final geometric mean, ranks, warnings, and audit tables.

## Reference redocking
For new targets SWAN-MPO can execute AutoDock Vina reference/native-ligand redocking from prepared PDBQT inputs. Candidate-compound docking remains upstream.

## Intentionally unsupported
- automatic SwissADME or ProTox web calls;
- candidate-compound docking automation;
- a GUI;
- runtime modification of frozen desirability thresholds.

## Nonstandard historical mode
`--allow-missing-predictors` is not the standard workflow. It activates locked historical missing/default rules, emits `NONSTANDARD_MODE_ACTIVATED`, and sets `nonstandard_mode: true`. Results generated this way are not directly comparable to standard complete-input outputs without disclosure.


## Interpretation warnings
The published Colon panel has one reference-calibrated primary BestNode target (mTOR), so the software emits `PANEL_SINGLE_NODE_BESTNODE`. This is already disclosed in the manuscript and limits multi-target interpretation; it does not invalidate the arithmetic. Out-of-anchor warnings are screening-context flags, not a formal applicability-domain model.
