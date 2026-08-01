# SWAN-MPO v1.3.2 RC2 — Mac + real-Vina + clean-clone release gate

Do not make the repository public or create the paper release until every gate below passes.

## A. Apply RC2 to the existing private repository

The current private Git repository is expected at:

```bash
$HOME/Downloads/SWAN_MPO_PRIVATE_REVIEW_RC1/repository
```

Unzip `SWAN_MPO_PRIVATE_REVIEW_RC2.zip` into Downloads, then run:

```bash
cd "$HOME/Downloads/SWAN_MPO_PRIVATE_REVIEW_RC1/repository"
rm -f Dockerfile
rsync -a \
  --exclude='.git/' \
  --exclude='.venv/' \
  --exclude='.pytest_cache/' \
  "$HOME/Downloads/SWAN_MPO_PRIVATE_REVIEW_RC2/" ./
```

Do not remove `.git/`.

## B. Fresh local RC2 environment

```bash
cd "$HOME/Downloads/SWAN_MPO_PRIVATE_REVIEW_RC1/repository"
rm -rf .venv .pytest_cache demo_results manuscript_reproduction real_vina_verification
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install 'setuptools==80.9.0' 'wheel==0.45.1'
python -m pip install --no-build-isolation -e '.[dev]'

python -m compileall -q src tests scripts
pytest -q
swan-mpo --version
swan-mpo verify --manuscript
swan-mpo reproduce-manuscript --output-dir manuscript_reproduction
python scripts/audit_release.py
python scripts/license_audit.py
```

Expected ordinary suite: **70 passed, 1 skipped**. The only skip should be the optional actual-Vina test until `SWAN_REAL_VINA_CONFIG` is set.

## C. Actual Vina 1.2.7 RC2 gate

```bash
vina --version
swan-mpo verify --check-vina
python scripts/make_mtor_real_vina_config.py

swan-mpo verify \
  --vina-config my_real_vina_mtor.json \
  --output-dir real_vina_verification \
  --report real_vina_verification_report.json

export SWAN_REAL_VINA_CONFIG="$PWD/my_real_vina_mtor.json"
pytest -q -m real_vina
swan-mpo verify --strict
```

Expected mTOR/4JSP classification: `generated_mode_recovery`, recovered mode 13, reference ΔG -6.578 kcal/mol, RMSD < 2.0 Å. The RC2 symmetry-aware RMSD need not be numerically identical to the historical RMSD implementation; the frozen published calibration remains authoritative.

## D. Commit RC2 only after A–C pass

```bash
git status
git add -A
git diff --cached --check
git commit -m "SWAN-MPO v1.3.2 RC2 audit closure"
git tag -a v1.3.2-rc2 -m "Post-adversarial-audit release candidate"
git push origin main
git push origin v1.3.2-rc2
```

Do not commit `.venv`, `my_real_vina_mtor.json`, Vina outputs, or local verification results containing machine-specific paths. Those are ignored by the repository and should remain local.

## E. Clean-clone gate

Clone the private repository into a brand-new directory rather than reusing the development tree:

```bash
cd "$HOME/Downloads"
rm -rf swan-mpo-clean-clone
git clone git@github.com:saanviisenthilkumar/swan-mpo.git swan-mpo-clean-clone
cd swan-mpo-clean-clone
git checkout v1.3.2-rc2

python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install 'setuptools==80.9.0' 'wheel==0.45.1'
python -m pip install --no-build-isolation -e '.[dev]'

pytest -q
swan-mpo verify --manuscript
swan-mpo reproduce-manuscript --output-dir manuscript_reproduction
python scripts/audit_release.py
python scripts/license_audit.py
```

The clean clone must reproduce the same 177 panel rows / 531 target rows without accessing files outside the clone.

## F. Public-access gate

Before JoC submission:

1. Create/freeze the public code release.
2. Create the archival code/data record (OSF/Zenodo as chosen).
3. Confirm required reproducibility inputs are accessible without login.
4. Confirm the GitHub/archival DOI links from an incognito/not-signed-in browser.
5. Insert those exact links into Availability of Data and Materials and the repository README.
