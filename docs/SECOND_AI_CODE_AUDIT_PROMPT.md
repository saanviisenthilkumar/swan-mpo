# Independent adversarial code-review prompt

Review this SWAN-MPO release candidate as if you were a Journal of Cheminformatics reproducibility reviewer. Do not assume README claims are true. Inspect and test them.

Check, at minimum:

- whether raw candidate docking + raw ADME + raw toxicity inputs truly flow into SWAN-calculated safety, ADME, liability, target binding, BestNode, and final MPO scores;
- whether the locked model SHA is unchanged and the public adapters alter no frozen equation or constant;
- whether every configured target has an explicit calibration state and comparative-only targets are excluded from primary BestNode;
- whether generated-mode recovery uses the validated native-like mode's energy, not automatically mode 1;
- whether candidate 20-grid medians are calculated correctly and exact grid-count/receptor identity checks fail safely;
- whether separate ProTox status/confidence columns and common SwissADME aliases work;
- whether malformed/missing inputs fail loudly without silent score fabrication;
- whether symmetry-aware fixed-frame RMSD is scientifically correct for atom reordering/symmetry and does not superimpose away redocking displacement;
- whether actual AutoDock Vina 1.2.7 integration is tested independently rather than inferred from mocks;
- whether every run records input hashes, versions, seeds, command, warnings, and audit outputs without leaking author-machine paths;
- whether threshold provenance is accurately distinguished from SWAN-specific design anchors;
- whether examples, licenses, environment pinning, CI, and clean-clone instructions are sufficient for a third party;
- whether any README/manuscript-facing claim exceeds what the code actually does.

Return blockers, major issues, minor issues, and exact reproducible tests for each finding. Treat any discrepancy between frozen manuscript methodology and implementation as a release blocker.
