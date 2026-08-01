# RC2 terminal gate

Run after copying RC2 into the private repository working tree.

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install 'setuptools==80.9.0' 'wheel==0.45.1'
python -m pip install --no-build-isolation -e '.[dev]'

pytest -q
# Expected ordinary suite: 70 passed, 1 skipped (optional actual-Vina test)
swan-mpo --version
swan-mpo verify --manuscript
rm -rf manuscript_reproduction
swan-mpo reproduce-manuscript --output-dir manuscript_reproduction
python scripts/audit_release.py
python scripts/license_audit.py
swan-mpo verify --check-vina
```

Then regenerate the local mTOR config and run actual Vina:

```bash
python scripts/make_mtor_real_vina_config.py
rm -rf real_vina_verification
swan-mpo verify --vina-config my_real_vina_mtor.json --output-dir real_vina_verification --report real_vina_verification_report.json
export SWAN_REAL_VINA_CONFIG="$PWD/my_real_vina_mtor.json"
pytest -q -m real_vina
```

Finally run strict verification:

```bash
swan-mpo verify --strict
```

Expected manuscript reproduction: 177 panel rows, 531 target rows, zero failures; Muricatacin Colon 1 / Prostate 2 / RCC 2 and binding rank 47 in all panels.
