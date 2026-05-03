#!/usr/bin/env bash
# Amazon Linux 2023 — minimal venv for Session 1 (no PyTorch).
set -euo pipefail
cd "$(dirname "$0")/.."
# Prefer 3.12 on AL2023: sudo dnf install -y python3.12 python3.12-pip
PYTHON="${PYTHON:-python3.12}"
"$PYTHON" -m venv .venv
# shellcheck disable=SC1091
source .venv/bin/activate
python -m pip install -U pip
pip install -r requirements-ec2-inference.txt
echo "Done. Activate with: source .venv/bin/activate"
echo "Check env:   SESSION0_EC2=1 python scripts/check_env.py"
echo "Run triage:  python scripts/run_session1.py"
