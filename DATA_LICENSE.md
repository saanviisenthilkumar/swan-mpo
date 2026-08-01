# Data and documentation licenses

Licensing is file-specific where upstream prediction outputs are bundled.

## Repository-authored material — CC BY 4.0
Unless an individual file below states otherwise, repository-authored documentation, examples, configuration files, project-created docking extracts, canonical validation extracts, and other tabular metadata are released under the Creative Commons Attribution 4.0 International license (CC BY 4.0).

## SwissADME prediction exports — CC BY 4.0 upstream material
The exact SwissADME exports bundled as:
- `src/swan_mpo/resources/manuscript_swissadme_canonical_full.csv`
- `src/swan_mpo/resources/manuscript_swissadme_original_incomplete.csv`

are redistributed with attribution under SwissADME/SIB's published CC BY 4.0 Licensed Materials terms. The canonical full export is byte-identical to the project source (SHA-256 `a1b6339695bba431239def8969d56244cecd978e195e5eaf2a3019ca21ec7ab1`). Cite Daina A, Michielin O, Zoete V. *SwissADME: a free web tool to evaluate pharmacokinetics, drug-likeness and medicinal chemistry friendliness of small molecules.* Scientific Reports. 2017;7:42717.

SwissADME terms: https://www.swissadme.ch/termsofuse.php
CC BY 4.0: https://creativecommons.org/licenses/by/4.0/

## ProTox prediction export — upstream CC BY-ND 4.0 material
`src/swan_mpo/resources/manuscript_protox_raw.csv` is an **unchanged byte-for-byte copy** of the project's downloaded ProTox result table (SHA-256 `4ef8ea376f89533ad3bd3afb9d810aab9c8fccc3f216179414d6de776b3f08ee`). ProTox 3.0 links its Creative Commons notice to CC BY-ND 4.0. The raw table is therefore not relicensed by the repository. SWAN-MPO consumes the reported predictions as analytical inputs and computes its own safety desirabilities and integrated scores separately; the repository does not distribute a modified ProTox source export.

ProTox 3.0: https://tox.charite.de/protox3/
CC BY-ND 4.0: https://creativecommons.org/licenses/by-nd/4.0/

Cite the ProTox 3.0 publication associated with the predictions.

## No structural-file redistribution
No receptor/native-ligand PDBQT, PDB, MOL/SDF, CIF, or other third-party structural asset is distributed in this repository.

Copyright in repository-authored material (c) 2026 Saanvii Senthilkumar. Upstream rights remain with their respective licensors.
