#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

echo "[1/2] Running BTC alpha research pipeline..."
python3 research.py

echo "[2/3] Strategy leaderboard"
python3 scripts/leaderboard.py

echo "[3/3] Running low-DD track"
python3 research_lowdd.py

echo "[4/4] Running triple-objective track"
python3 research_triple_objective.py
python3 scripts/triple_leaderboard.py

echo "Done. See results/REPORT.md, results/LOWDD_REPORT.md, results/TRIPLE_OBJECTIVE_REPORT.md, and notebooks/triple_objective_research.ipynb"
