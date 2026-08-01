#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip setuptools wheel
python -m pip install -e ".[dev]"
pytest -q
swan-mpo verify
rm -rf demo_results
swan-mpo score --demo --output-dir demo_results
python scripts/audit_release.py
python scripts/license_audit.py
echo "LOCAL BOOTSTRAP: PASS"
