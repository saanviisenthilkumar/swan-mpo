# Licensing and redistribution

## SWAN-MPO source code

The original SWAN-MPO source code in this repository is distributed under the MIT License (`LICENSE`).

## Repository-authored data/configuration/examples

Repository-authored CSV/JSON templates, configuration examples, audit tables, and documentation are designated CC BY 4.0 in `DATA_LICENSE.md`, except where a file explicitly states otherwise.

## Third-party software

SWAN-MPO interoperates with third-party software including AutoDock Vina, RDKit, Open Babel, NumPy, NetworkX, and pytest. Those projects remain governed by their own licenses. Installing or invoking a third-party dependency does not relicense SWAN-MPO's original source code.

Users distributing a container or environment that includes third-party binaries must comply with each included project's license and notice requirements.

## Structural data

This release candidate does **not** bundle receptor PDB/PDBQT files, crystallographic ligand files, or other third-party structural assets. Users provide those files for new-target redocking. This avoids silently redistributing structural or database content under an incompatible license.

## Release audit

`scripts/license_audit.py` checks the repository for structural-file types that should not be bundled and reports the declared license boundary. It is a repository sanity check, not legal advice.
