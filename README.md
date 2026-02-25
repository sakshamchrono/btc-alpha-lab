# btc-alpha-lab

Overnight quant research on BTC market alpha with walk-forward out-of-sample validation.

## What this repo contains
- `research.py` — full research pipeline (stdlib Python, no extra deps required)
- `notebooks/btc_alpha_research.ipynb` — clear notebook report + reproducible analysis summary
- `data/btc_usd_daily_stooq.csv` — ingested historical BTC daily OHLC data
- `results/summary.json` — full output artifacts (metrics, walk-forward parameter logs, OOS returns, sensitivity)
- `results/REPORT.md` — concise findings and caveats

## Strategy families tested
1. Trend-following (SMA crossover)
2. Mean-reversion (RSI threshold)
3. Volatility breakout / regime (Donchian breakout + EMA filter)

## Backtest design
- Signal lag: 1 day (avoid lookahead bias)
- Validation: walk-forward (train 3y, test 1y, step 1y)
- Costs: turnover-based transaction costs (default 5 bps)
- Metrics: CAGR, Sharpe, Max Drawdown, Win Rate, annualized volatility
- Sensitivity: transaction cost stress at 2/5/10/20 bps

## Reproduce
```bash
cd btc-alpha-lab
python3 research.py
```

## Concise progress log
- 2026-02-25 20:12 UTC — Initialized repo structure and research plan.
- 2026-02-25 20:18 UTC — Implemented full walk-forward backtest engine in `research.py`.
- 2026-02-25 20:20 UTC — Ingested BTC daily data and generated OOS metrics + sensitivity outputs.
- 2026-02-25 20:22 UTC — Built notebook report and summarized best strategy with caveats.
- 2026-02-25 20:23 UTC — Prepared git repository for commit/push.
