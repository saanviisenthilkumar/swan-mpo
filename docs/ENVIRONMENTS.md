# Environments and exact tool versions

SWAN-MPO separates the **public scoring/redocking runtime** from upstream molecule preparation and predictor services. This avoids pretending that tools not required by the CLI are runtime dependencies.

## Public CLI / reference-redocking environment

`environment.yml` pins the direct release environment:

- Python 3.13.5
- NumPy 2.3.5
- NetworkX 3.6.1
- pytest 9.0.2
- AutoDock Vina 1.2.7
- pip 25.2
- setuptools 80.9.0
- wheel 0.45.1

The core scoring package itself requires NumPy and NetworkX. Vina is needed only for `redock-reference` and real-Vina verification.

## Audited manuscript/upstream tools

The audited manuscript workflow additionally records:

- RDKit 2026.03.2 in the audited ligand-preparation environment;
- Open Babel 3.1.0 in the audited ligand-preparation/conversion workflow;
- AutoDock Vina 1.2.7 for docking/redocking.

RDKit and Open Babel are **not required by the standard SWAN-MPO scoring CLI** and are therefore not silently installed as runtime dependencies. The manuscript used separate computational environments; this release preserves that distinction rather than inventing one combined environment that was never actually used.

SwissADME and ProTox are upstream predictor services and are not called automatically by SWAN-MPO.
