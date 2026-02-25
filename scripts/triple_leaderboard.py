#!/usr/bin/env python3
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
summary = json.loads((ROOT / 'results' / 'triple_objective_summary.json').read_text())
metrics = summary['final_metrics']
buy = summary['baselines']['buy_and_hold']

rows = []
for name, m in metrics.items():
    rows.append({
        'Strategy': name,
        'Objective': m['Objective Score'],
        'CAGR': m['CAGR'],
        'Total': m['Total Return'],
        'WinRate': m['Win Rate'],
        'MaxDD': m['Max Drawdown'],
        'Sharpe': m['Sharpe'],
        'Sortino': m['Sortino'],
        'Turnover': m['Turnover'],
    })
rows.sort(key=lambda r: r['Objective'], reverse=True)

print('\n=== Triple-Objective Leaderboard (OOS) ===')
print(f"{'Strategy':23s} {'Obj':>7s} {'CAGR':>10s} {'Total':>10s} {'Win':>8s} {'MaxDD':>9s} {'Sh':>6s} {'So':>6s} {'Turn':>8s}")
for r in rows:
    print(f"{r['Strategy']:23s} {r['Objective']:7.3f} {r['CAGR']*100:9.2f}% {r['Total']*100:9.2f}% {r['WinRate']*100:7.2f}% {r['MaxDD']*100:8.2f}% {r['Sharpe']:6.2f} {r['Sortino']:6.2f} {r['Turnover']:8.2f}")

print('\nBuy & Hold reference:')
print(f"CAGR={buy['CAGR']*100:.2f}% Total={buy['Total Return']*100:.2f}% Win={buy['Win Rate']*100:.2f}% MaxDD={buy['Max Drawdown']*100:.2f}% Sharpe={buy['Sharpe']:.2f} Sortino={buy['Sortino']:.2f}")
