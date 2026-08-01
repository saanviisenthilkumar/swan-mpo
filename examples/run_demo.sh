#!/usr/bin/env bash
set -euo pipefail
swan-mpo score --demo --output-dir "${1:-demo_results}"
swan-mpo verify
