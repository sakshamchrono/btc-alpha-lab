#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

echo "[1/2] Running BTC alpha research pipeline..."
python3 research.py

echo "[2/2] Strategy leaderboard"
python3 scripts/leaderboard.py

echo "Done. See results/REPORT.md and notebooks/btc_alpha_research.ipynb"
