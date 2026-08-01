# Independent-review implementation matrix

| Requested item | v1.3.1 implementation | Status before user test |
|---|---|---|
| Real Vina integration | `verify --check-vina`, `verify --vina-config`, exact 1.2.7 enforcement, artifact preservation | Code complete; actual Vina execution pending user machine |
| Symmetry-aware RMSD | Fixed-frame heavy-atom graph-isomorphism RMSD; native and pose connectivity perceived independently; tests for equivalent-atom reorder and translation | Implemented/tested |
| Threshold provenance | `docs/THRESHOLD_PROVENANCE.md`, machine-readable registry, `explain-model --sources` | Implemented/tested |
| Clear input validation | Missing columns, ambiguous aliases, missing confidence, bad confidence, grid counts, PDB mismatch, missing calibration, nonfinite inputs | Implemented/tested |
| Example inputs / demo | SwissADME/ProTox/docking/redocking templates; `score --demo`; full audit outputs | Implemented/tested; synthetic demo deliberately not mislabeled as Muricatacin |
| Exact version records | `environment.yml`, exact package requirements, `docs/ENVIRONMENTS.md`, runtime version capture | Implemented; environment solve to be tested locally |
| Run metadata | timestamp, command, model/version, config/calibration hashes, seeds, runtime versions, input SHA-256, warnings | Implemented/tested |
| License compatibility | MIT code, CC BY 4.0 authored data/docs, third-party notices, structural-file audit | Implemented/audited |
| `swan-mpo verify` | frozen model hash, calibration hash, calibration-class counts, demo, optional Vina checks | Implemented/tested |
| Structured logging | `run.log` plus JSON metadata | Implemented/tested |
| Out-of-domain/anchor warnings | `warnings.csv` + metadata; explicitly labeled frozen-anchor warnings, not formal AD validation | Implemented/tested |
| CITATION.cff | top-level CFF, no fake repository DOI/URL | Implemented |
| Docker recipe | Micromamba recipe based on pinned release environment | Implemented; build pending release-machine test |
| Do not automate SwissADME/ProTox | No web-service calls | Preserved |
| Do not automate candidate docking | Candidate grid-level docking remains upstream | Preserved |
| No GUI | CLI only | Preserved |
| No runtime-configurable frozen desirability thresholds | Frozen model remains byte-identical | Preserved |
