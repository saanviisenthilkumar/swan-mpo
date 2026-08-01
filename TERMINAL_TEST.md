# Terminal test for SWAN-MPO v1.3.1 release candidate

Run these from the unzipped repository root.

## A. Core clean installation and regression suite

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install 'setuptools==80.9.0' 'wheel==0.45.1'
python -m pip install --no-build-isolation -e '.[dev]'
pytest -q
swan-mpo --version
swan-mpo verify
rm -rf demo_results
swan-mpo score --demo --output-dir demo_results
python scripts/audit_release.py
python scripts/license_audit.py
```

Expected core result: all ordinary tests pass, the one `real_vina` test is skipped unless you explicitly configure it, `swan-mpo verify` reports PASS, and the demo produces the full audit package.

## B. Verify the actual Vina executable

```bash
vina --version
swan-mpo verify --check-vina
```

For manuscript-faithful redocking this must report AutoDock Vina 1.2.7.

## C. Actual mTOR real-Vina integration using the historical tight-box parameters

The JSON files under `configs/` are configuration data, **not executable commands**. To inspect one, use `cat configs/canonical_mtor_redocking_template.json`.

For the mTOR/4JSP integration test using the historical manuscript parameters, generate a local config automatically from the audited project files:

```bash
python scripts/make_mtor_real_vina_config.py
cat my_real_vina_mtor.json
```

The helper searches for the original `4JSP_receptor.pdbqt` and `AGS_native.pdbqt`, verifies the historical `config_tight.txt` SHA-256 when present, checks the audited file sizes, and writes the exact tight-box parameters: center `(49.224, -1.763, -45.895)`, 16 Å box, exhaustiveness 64, 20 modes, energy range 4, seed 2026.

Then run:

```bash
swan-mpo verify \
  --vina-config my_real_vina_mtor.json \
  --output-dir real_vina_verification \
  --report real_vina_verification_report.json
```

That command requires Vina 1.2.7, performs a real reference-ligand redocking run, computes symmetry-aware fixed-frame RMSD, derives target calibration, and preserves the Vina logs/output for audit.

To also execute the pytest integration marker after the config is verified:

```bash
export SWAN_REAL_VINA_CONFIG="$PWD/my_real_vina_mtor.json"
pytest -q -m real_vina
```

## D. Send back

Upload or paste:

- the final `pytest -q` line;
- `swan-mpo verify` output;
- `swan-mpo verify --check-vina` output;
- if Section C is run, `real_vina_verification_report.json` and the `real_vina_verification/` folder or ZIP.
