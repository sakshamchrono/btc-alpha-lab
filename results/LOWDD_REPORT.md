# Low-DD BTC Research Report

Data range: 2010-07-19 to 2026-02-25 (4039 rows)

## OOS Ranking (downside-priority)
- **linear_ml**: CAGR 54.13%, Sharpe 2.17, Sortino 4.14, MaxDD -16.70%, Calmar 3.24, Win 20.54%, Monthly Hit 46.24%, Turnover 13.10x
- **regime_momentum**: CAGR 46.89%, Sharpe 1.73, Sortino 3.46, MaxDD -22.41%, Calmar 2.09, Win 22.00%, Monthly Hit 38.71%, Turnover 12.40x
- **vol_target_trend**: CAGR 5.08%, Sharpe 0.45, Sortino 0.65, MaxDD -27.56%, Calmar 0.18, Win 7.39%, Monthly Hit 11.83%, Turnover 2.17x

## Baseline comparison
- Buy & Hold: CAGR 243.49%, MaxDD -93.07%, Calmar 2.62
- Prior repo best (`vol_breakout`): CAGR 78.09%, Sharpe 1.33, MaxDD -70.62%

## Deployability recommendation
- Recommended: **linear_ml**
- Position sizing: daily vol-target, cap leverage at 1.0
- Kill-switch: drawdown and high-volatility cutoffs to force risk-off
- Confidence: moderate; strategy is more stable on DD profile but still regime-sensitive

## Parameter stability
- Full per-window score tables are saved in `results/lowdd_summary.json` under `stability_tables`.
- Use these tables as sensitivity surfaces (score, MaxDD, Calmar, Sortino, turnover) across parameter grids.