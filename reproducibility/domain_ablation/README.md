# Frozen domain-ranking ablation reproduction

This folder reproduces Supplementary Table S24 from the locked 177 panel-score
rows. The full four-domain score is independently reconstructed from the fixed
binding, ADME, general safety, and panel-liability components. No new docking,
fitting, outcome labels, or weight tuning are used.

From the repository root, after installing the optional dependencies in
`reproducibility/domain_ablation/requirements.txt`:

```bash
python reproducibility/domain_ablation/run_four_stage_ablation.py --check-expected
```

The script writes its calculations under `reproduced_outputs/` and checks the
three frozen CSVs in `expected_outputs/`. The published Supplementary Table
S24A/S24B/S24C equivalents also ship in Online Resource 2. The four stages
use equal-weight geometric means of the domains present and the frozen
desirability floor of 0.01. Leave-one-domain-out calculations start with the
same four prespecified domains and omit one at a time.

This analysis measures **changes in ranking**, not whether the changes improve
experimental activity or safety prediction. In the current data, selected
BestNode binding is mTOR for every compound and panel; Prostate and RCC use
identical domain values and have identical final rankings. Neurotoxicity enters
both general safety and context liability, so these domains are not fully
independent.
