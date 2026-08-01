# Frozen desirability anchors: provenance and status

SWAN-MPO v1.0 uses fixed desirability functions. This document distinguishes **literature-grounded preferred-region anchors** from **SWAN-MPO framework design anchors** that define a graded decline to the model floor. The latter are prespecified engineering choices and should not be misrepresented as universal medicinal-chemistry cutoffs.

## ADME / physicochemical anchors

| Input | Frozen SWAN-MPO anchor(s) | Provenance status | Rationale / source |
|---|---:|---|---|
| Molecular weight | good ≤ 500; floor by ≥ 800 | 500 literature-grounded; 800 SWAN design anchor | Lipinski et al. describe MW 500 as a widely used oral drug-likeness boundary. The 800 value is a prespecified SWAN-MPO tolerated-range endpoint used to grade rather than hard-exclude larger natural products. |
| Consensus LogP | good 1–5; floor at ≤ −2 or ≥ 8 | upper good boundary literature-grounded; lower-good and floor anchors are SWAN design choices | Lipinski et al. support logP ≲ 5 as a common oral drug-likeness boundary. SWAN uses a broad two-sided graded range to avoid a binary exclusion rule. |
| H-bond acceptors | good ≤ 10; floor by ≥ 15 | 10 literature-grounded; 15 SWAN design anchor | Lipinski et al. |
| H-bond donors | good ≤ 5; floor by ≥ 8 | 5 literature-grounded; 8 SWAN design anchor | Lipinski et al. |
| TPSA | good ≤ 140 Å²; floor by ≥ 220 Å² | 140 literature-grounded; 220 SWAN design anchor | Veber et al. identified polar surface area and flexibility as important oral-bioavailability determinants; ~140 Å² is a commonly used permeability/oral-bioavailability boundary. |
| Rotatable bonds | good ≤ 10; floor by ≥ 28 | 10 literature-grounded; 28 SWAN design anchor | Veber et al. |
| Synthetic accessibility | good ≤ 4; floor by ≥ 8 | metric literature-grounded; both SWAN desirability anchors are framework choices | Ertl & Schuffenhauer introduced the synthetic-accessibility score. SWAN maps this metric to a graded desirability; 4 and 8 are not claimed as universal thresholds. |
| PAINS alerts | 0 alerts → 1.00; ≥1 alert → 0.25; missing → 0.50 | PAINS concept literature-grounded; numeric desirability mapping is SWAN design | Baell & Holloway introduced PAINS substructure filters. SWAN treats PAINS as a graded warning rather than a hard exclusion. |
| GI absorption | High → 1.00; Low → 0.35; unknown → 0.50 | predictor category literature-grounded; numeric mapping is SWAN design | SwissADME/BOILED-Egg literature supports categorical GI-absorption interpretation; SWAN's desirability values are fixed framework mappings. |

## Safety anchors

| Input | Frozen SWAN-MPO anchor(s) | Provenance status | Rationale / source |
|---|---:|---|---|
| Predicted LD50 | logarithmic mapping from 50 to 5000 mg/kg | boundary values align with ProTox/GHS toxicity-class breakpoints; use as SWAN interpolation anchors is a framework choice | ProTox defines six acute-toxicity classes from GHS-aligned LD50 boundaries including 50 and 5000 mg/kg. SWAN uses those values as the low/high anchors of a bounded log desirability. |
| Toxicity class | classes 1–6 mapped linearly | class definition literature/tool-grounded; linear desirability mapping is SWAN design | ProTox acute toxicity uses six ordered classes. SWAN maps class 1 to the low end and class 6 to the high end of desirability. |
| Confidence-coded toxicity endpoints | Inactive(c) → c; Active(c) → 1−c, c∈[0.5,1.0] | SWAN design rule applied to ProTox model confidence | The transformation preserves both predicted class and model confidence. It is an explicit SWAN-MPO scoring rule, not a ProTox-native score. |

## Liability anchors

BBB, neurotoxicity, and Complex I use the same confidence-coded endpoint transform as the safety domain. Their **panel-specific inclusion** is a SWAN-MPO design choice. Complex I is not penalized in the colorectal panel because Complex I is an intended docking target there; it is treated as an off-panel liability in prostate and RCC.

## Binding anchors

Binding desirability uses the candidate compound's **median docking energy across the prespecified grid centers** and a target-specific reference energy derived from validated reference/native-ligand redocking. A target is reference-calibrated when the top pose is within 2.0 Å heavy-atom RMSD or when a later generated mode recovers a native-like pose within 2.0 Å. Comparative-only targets are excluded from the primary BestNode calculation.

The 2.0 Å redocking convention is a standard pose-reproduction criterion used in docking validation; in SWAN-MPO it is fixed before candidate scoring.

## Primary references

1. Lipinski CA, Lombardo F, Dominy BW, Feeney PJ. Experimental and computational approaches to estimate solubility and permeability in drug discovery and development settings. *Advanced Drug Delivery Reviews*. 2001;46:3–26. doi:10.1016/S0169-409X(00)00129-0.
2. Veber DF, Johnson SR, Cheng H-Y, Smith BR, Ward KW, Kopple KD. Molecular properties that influence the oral bioavailability of drug candidates. *Journal of Medicinal Chemistry*. 2002;45:2615–2623. doi:10.1021/jm020017n.
3. Ertl P, Schuffenhauer A. Estimation of synthetic accessibility score of drug-like molecules based on molecular complexity and fragment contributions. *Journal of Cheminformatics*. 2009;1:8. doi:10.1186/1758-2946-1-8.
4. Daina A, Michielin O, Zoete V. SwissADME: a free web tool to evaluate pharmacokinetics, drug-likeness and medicinal chemistry friendliness of small molecules. *Scientific Reports*. 2017;7:42717. doi:10.1038/srep42717.
5. Daina A, Zoete V. A BOILED-Egg to predict gastrointestinal absorption and brain penetration of small molecules. *ChemMedChem*. 2016;11:1117–1121. doi:10.1002/cmdc.201600182.
6. Baell JB, Holloway GA. New substructure filters for removal of pan assay interference compounds (PAINS) from screening libraries and for their exclusion in bioassays. *Journal of Medicinal Chemistry*. 2010;53:2719–2740. doi:10.1021/jm901137j.
7. Banerjee P, et al. ProTox 3.0: a webserver for the prediction of toxicity of chemicals. *Nucleic Acids Research*. 2024;52:W513–W520. doi:10.1093/nar/gkae303.

## Interpretation rule

The exact frozen values above are part of the versioned SWAN-MPO method. Some preferred-region boundaries are directly motivated by established drug-likeness literature, while several outer tolerated-range endpoints and categorical penalties are deliberately broader **SWAN-MPO design anchors** chosen to permit graded triage of natural-product scaffolds. They must not be described as universal biological safety or developability thresholds.
