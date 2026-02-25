#!/usr/bin/env python3
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
summary = json.loads((ROOT / "results" / "summary.json").read_text())
metrics = summary["metrics_oos"]

rows = []
for name, m in metrics.items():
    rows.append(
        {
            "Strategy": name,
            "CAGR": m["CAGR"],
            "Sharpe": m["Sharpe"],
            "MaxDD": m["Max Drawdown"],
            "WinRate": m["Win Rate"],
        }
    )

rows.sort(key=lambda r: r["Sharpe"], reverse=True)

print("\n=== OOS Leaderboard (sorted by Sharpe) ===")
print(f"{'Strategy':18s} {'CAGR':>10s} {'Sharpe':>8s} {'MaxDD':>10s} {'WinRate':>10s}")
for r in rows:
    print(
        f"{r['Strategy']:18s} {r['CAGR']*100:9.2f}% {r['Sharpe']:8.2f} {r['MaxDD']*100:9.2f}% {r['WinRate']*100:9.2f}%"
    )
