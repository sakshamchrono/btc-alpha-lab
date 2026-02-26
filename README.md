# btc-alpha-lab

Overnight quant research on BTC market alpha with walk-forward out-of-sample validation.

## Strategy leaderboard (OOS, net of 5 bps costs)

| Rank | Strategy | CAGR | Sharpe | Max Drawdown | Win Rate |
|---|---|---:|---:|---:|---:|
| 1 | `vol_breakout` | 78.09% | 1.33 | -70.62% | 25.82% |
| 2 | `trend_following` | 27.81% | 0.74 | -69.50% | 22.33% |
| 3 | `mean_reversion` | 3.99% | 0.29 | -51.66% | 8.22% |

> Current best alpha in this repo: **volatility breakout/regime**. Still requires strict risk controls before live deployment.

## What this repo contains
- `research.py` — full research pipeline (stdlib Python, no extra deps required)
- `notebooks/btc_alpha_research.ipynb` — clear notebook report + reproducible analysis summary
- `data/btc_usd_daily_stooq.csv` — ingested historical BTC daily OHLC data
- `results/summary.json` — full output artifacts (metrics, walk-forward parameter logs, OOS returns, sensitivity)
- `results/REPORT.md` — concise findings and caveats
- `scripts/leaderboard.py` — prints strategy ranking from latest results
- `run.sh` — one-command execution pipeline

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

## One-command run
```bash
cd btc-alpha-lab
./run.sh
python3 research_lowdd.py
```

## Low-DD Track

A dedicated downside-first research track now lives in:
- `research_lowdd.py`
- `notebooks/lowdd_research.ipynb`
- `results/lowdd_summary.json`
- `results/LOWDD_REPORT.md`

### Strategy families (Low-DD)
1. Volatility-targeted trend with adaptive sizing
2. Regime filter + momentum (explicit risk-off)
3. Statistical linear model with handcrafted features and strict walk-forward OOS

### Validation & constraints
- Purged walk-forward: train 3y, test 180d, step 180d, purge 5d
- Costs: 4 bps transaction + 2 bps slippage
- Objective: downside-priority (Calmar, Sortino, MaxDD, Ulcer, smoothness)
- Constraints: target annual vol, turnover cap, leverage cap=1

### Current Low-DD best (latest run)
- **linear_ml**: CAGR **54.13%**, Sharpe **2.17**, Sortino **4.14**, MaxDD **-16.70%**, Calmar **3.24**, Monthly hit **46.24%**, Turnover **13.10x**
- Prior repo best (`vol_breakout`) had higher raw CAGR but much deeper drawdown (**-70.62%**), making low-DD track more deployable for risk-controlled operation.

## Triple-Objective Track (CAGR + WinRate + MaxDD)

New artifacts:
- `research_triple_objective.py`
- `notebooks/triple_objective_research.ipynb`
- `results/triple_objective_summary.json`
- `results/TRIPLE_OBJECTIVE_REPORT.md`
- `scripts/triple_leaderboard.py`

Methodology:
- Purged walk-forward OOS (train 4y, test 180d, step 180d, purge 7d)
- Ensemble of weak sleeves (trend, mean-reversion, breakout, regime, carry-like proxy)
- ML families: regularized logistic regression + boosted decision stumps
- Meta-labeling overlay and risk-first sizing (vol targeting + drawdown-aware de-risk ladder)
- Multi-objective ranking: Pareto frontier + weighted score with Sharpe/Sortino guardrails

**Buy-and-hold hard constraint status (latest run):**
- No triple-objective candidate beat buy-and-hold on both OOS CAGR and total return.
- Closest Pareto candidate is selected and explicitly reported in `TRIPLE_OBJECTIVE_REPORT.md`.

## Fib-Pivot-Halving Track (feature-extension ablation)

New artifacts:
- `research_fib_pivot_halving_track.py`
- `notebooks/fib_pivot_halving_track.ipynb`
- `results/fib-pivot-halving-track/summary.json`
- `results/fib-pivot-halving-track/REPORT.md`

Methodology:
- Purged walk-forward OOS (train 4y, test 180d, step 180d, purge 7d)
- Frictions: 4 bps transaction cost + 2 bps slippage
- Leakage-safe ablation: baseline vs +fib vs +pivots vs +halving vs combined
- Metrics reported: CAGR, total return, Sharpe, Sortino, MaxDD, Calmar, win rate, monthly hit rate, turnover

Latest findings (OOS):
- Baseline: CAGR **2.84%**, Win **12.46%**, MaxDD **-1.89%**
- +Fib: CAGR **5.15%**, Win **15.63%**, MaxDD **-2.80%**
- +Pivots: CAGR **2.80%**, Win **14.52%**, MaxDD **-2.38%**
- +Halving: CAGR **7.75%**, Win **19.96%**, MaxDD **-4.89%**
- Combined: CAGR **8.33%**, Win **21.43%**, MaxDD **-5.29%**

Interpretation:
- These features improved **CAGR** and **win rate** versus the same baseline, led by halving-cycle features.
- Improvement was **not material** against the repo's latest recommended strategy (`lowdd::linear_ml`, CAGR **54.13%**) or against buy-and-hold return levels; gains are mainly in smoother risk profile / lower drawdown.

## Manual run
```bash
cd btc-alpha-lab
python3 research.py
python3 scripts/leaderboard.py
python3 research_lowdd.py
python3 research_triple_objective.py
python3 scripts/triple_leaderboard.py
python3 research_fib_pivot_halving_track.py
```

## Auto re-run (GitHub Actions)
Workflow: `.github/workflows/backtest.yml`
- Triggers:
  - weekly schedule (`cron`)
  - manual trigger (`workflow_dispatch`)
  - pushes to `main`
- Actions:
  - runs `research.py`
  - uploads `results/`, `data/`, and notebook as artifacts

## Concise progress log
- 2026-02-25 20:12 UTC — Initialized repo structure and research plan.
- 2026-02-25 20:18 UTC — Implemented full walk-forward backtest engine in `research.py`.
- 2026-02-25 20:20 UTC — Ingested BTC daily data and generated OOS metrics + sensitivity outputs.
- 2026-02-25 20:22 UTC — Built notebook report and summarized best strategy with caveats.
- 2026-02-25 20:23 UTC — Prepared git repository for commit/push.
- 2026-02-25 20:35 UTC — Added leaderboard section, one-command runner, and GitHub Actions workflow.
