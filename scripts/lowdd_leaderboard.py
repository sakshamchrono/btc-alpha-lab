#!/usr/bin/env python3
import json
from pathlib import Path

p = Path(__file__).resolve().parents[1] / "results" / "lowdd_summary.json"
obj = json.loads(p.read_text())

print("Low-DD leaderboard (OOS):")
for i, row in enumerate(obj["ranked"], 1):
    m = obj["metrics_oos"][row["strategy"]]
    print(
        f"{i}. {row['strategy']}: CAGR={m['CAGR']:.2%} Sharpe={m['Sharpe']:.2f} "
        f"Sortino={m['Sortino']:.2f} MaxDD={m['Max Drawdown']:.2%} Calmar={m['Calmar']:.2f} "
        f"Win={m['Win Rate']:.2%} MonthlyHit={m['Monthly Hit Rate']:.2%} Turnover={m['Turnover']:.2f}x"
    )
