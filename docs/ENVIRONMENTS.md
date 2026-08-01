# Environments

SWAN-MPO deliberately separates the scoring CLI runtime from upstream chemical-preparation environments.

## Tested scoring/reference-redocking runtime
The release-candidate Mac validation used:
- Python 3.13.12
- NumPy 2.3.5
- NetworkX 3.6.1
- pytest 9.0.2 (test-only)
- AutoDock Vina 1.2.7 (optional reference-redocking executable)

`environment.yml` pins Python to the tested 3.13 series and pins numerical/test/Vina packages. `swan-mpo verify --strict` requires Python 3.13.x, exact NumPy/NetworkX, exact Vina 1.2.7, the manuscript reproduction, and frozen hashes.

## Upstream audited environments
RDKit 2026.03.2 and Open Babel 3.1.0 were used in audited upstream ligand preparation/descriptor workflows. They are **not required** by ordinary SWAN scoring and therefore may appear as `null` in runtime metadata. The CLI invokes the external Vina executable, so the Python `vina` package is also not required.

The repository does not claim that one environment performed every historical stage.

## Supported Python line
Python 3.13 is the supported release line for the manuscript software. `pyproject.toml` intentionally requires `>=3.13,<3.14` rather than advertising untested Python versions. The author Mac validation used Python 3.13.12; CI uses Python 3.13 on Ubuntu.
