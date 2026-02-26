# Experiment Results Ledger (All Tracks)

This file documents all major BTC strategy experiment tracks run so far, with clear differences in objective, methodology, and outcomes.

---

## 0) Common setup across tracks

- **Asset/Data:** BTCUSD daily OHLC (Stooq source)
- **Execution assumptions:** close-to-close daily bars, 1-day signal lag
- **Costs/slippage:** transaction costs and/or slippage included in each track (details per track)
- **Bias controls:** out-of-sample walk-forward style validation; no intentional lookahead

> Note: metrics are from each track’s own OOS setup, so numbers are not always perfectly apples-to-apples unless noted.

---

## 1) Baseline Track — `research.py`

### Goal
Find simple alpha across 3 classic families.

### Methods
1. Trend-following (SMA crossover)
2. Mean-reversion (RSI)
3. Volatility breakout/regime (Donchian + EMA filter)

### Validation
- Walk-forward OOS
- Cost model: 5 bps

### Best in track
**`vol_breakout`**

| Strategy | CAGR | Sharpe | MaxDD | Win Rate | Total Return |
|---|---:|---:|---:|---:|---:|
| trend_following | 27.81% | 0.74 | -69.50% | 22.33% | 612.10% |
| mean_reversion | 3.99% | 0.29 | -51.66% | 8.22% | 36.71% |
| **vol_breakout** | **78.09%** | **1.33** | **-70.62%** | **25.82%** | **10019.04%** |

### Key takeaway
Strong headline CAGR, but drawdown is too deep for most real-money deployment.

Source: `results/summary.json`

---

## 2) Low Drawdown Track — `research_lowdd.py`

### Goal
Prioritize **deployability** via lower drawdown and smoother risk profile.

### Methods
1. Vol-targeted trend (adaptive sizing)
2. Regime + momentum risk-off logic
3. Linear statistical/ML model with handcrafted features

### Validation
- Purged walk-forward OOS (train 3y / test 180d / step 180d / purge)
- Costs + slippage included (4 bps + 2 bps)
- Added downside metrics: Sortino, Calmar, Ulcer index, stability checks

### Best in track
**`linear_ml`**

| Strategy | CAGR | Sharpe | Sortino | MaxDD | Calmar | Win Rate | Total Return |
|---|---:|---:|---:|---:|---:|---:|---:|
| vol_target_trend | 5.08% | 0.45 | 0.65 | -27.56% | 0.18 | 7.39% | 46.25% |
| regime_momentum | 46.89% | 1.73 | 3.46 | -22.41% | 2.09 | 22.00% | 1809.89% |
| **linear_ml** | **54.13%** | **2.17** | **4.14** | **-16.70%** | **3.24** | **20.54%** | **2662.24%** |

### Key takeaway
Major drawdown compression vs baseline while maintaining strong risk-adjusted returns.

Source: `results/lowdd_summary.json`

---

## 3) Triple-Objective Track — `research_triple_objective.py`

### Goal
Jointly optimize **CAGR + Win Rate + MaxDD** with robust constraints.

### Methods
- Ensemble sleeves (trend, MR, breakout, regime, carry-like proxy)
- ML families: logistic L2 + boosted stumps
- Meta-labeling overlay and blended variants
- Drawdown-aware risk sizing, vol targeting, de-risk ladder/kill-switch
- Pareto + weighted objective selection

### Validation
- Purged walk-forward OOS (train 4y / test 180d / step 180d / purge 7d)
- Costs + slippage included
- Regime and rolling-window stability checks

### Best in track
**`weak_ensemble`**

| Strategy | CAGR | Sharpe | Sortino | MaxDD | Calmar | Win Rate | Monthly Hit | Turnover | Total Return |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| **weak_ensemble** | **24.90%** | **1.20** | **2.11** | **-24.84%** | **1.00** | **27.69%** | **39.76%** | **20.29x/yr** | **360.20%** |

### Buy-and-hold comparison (same track output)
| Benchmark | CAGR | Sharpe | Sortino | MaxDD | Calmar | Win Rate | Monthly Hit | Total Return |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Buy & Hold | 243.49% | 1.70 | 3.12 | -93.07% | 2.62 | 52.19% | 56.72% | 85158192.08% |

### Key takeaway
No candidate in this track beat buy-and-hold on raw OOS return, but risk was far better controlled.

Source: `results/triple_objective_summary.json`

---

## 4) Fibonacci + Pivot + Halving Track — `research_fib_pivot_halving_track.py`

### Goal
Explicitly test whether adding **Fibonacci**, **Pivot levels**, and **4-year halving cycle** improves performance.

### Methods
- Ablations:
  - baseline
  - +fib
  - +pivots
  - +halving
  - combined

### Validation
- Purged walk-forward OOS (train 4y / test 180d / step 180d / purge 7d)
- Costs + slippage included (4 bps + 2 bps)

### Ablation results
| Variant | CAGR | Win Rate | MaxDD | Sharpe | Sortino | Calmar | Turnover | Total Return |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| baseline | 2.84% | 12.46% | -1.89% | 1.38 | 2.57 | 1.50 | 0.92x/yr | 21.29% |
| plus_fib | 5.15% | 15.63% | -2.80% | 1.44 | 2.93 | 1.84 | 1.87x/yr | 41.43% |
| plus_pivots | 2.80% | 14.52% | -2.38% | 1.18 | 2.07 | 1.17 | 2.62x/yr | 20.96% |
| plus_halving | 7.75% | 19.96% | -4.89% | 1.61 | 3.03 | 1.59 | 1.26x/yr | 67.39% |
| **combined** | **8.33%** | **21.43%** | **-5.29%** | **1.52** | **2.86** | **1.57** | **4.12x/yr** | **73.79%** |

### Key takeaway
These features helped versus that track baseline (especially halving), but did not surpass the stronger low-DD model (`linear_ml`) on overall profile.

Source: `results/fib-pivot-halving-track/summary.json`

---

## Cross-track differences at a glance

| Track | Primary objective | Best model | Strength | Main weakness |
|---|---|---|---|---|
| Baseline | Raw alpha discovery | vol_breakout | High CAGR | Very high drawdown |
| Low-DD | Deployability/risk control | linear_ml | Best risk-adjusted + low DD balance | Win rate still modest |
| Triple-objective | CAGR + win + DD jointly | weak_ensemble | Better win rate than low-DD | Couldn’t beat buy-hold return |
| Fib/Pivot/Halving | Feature-specific hypothesis test | combined | Improved baseline and win/DD balance | Absolute return remains moderate |

---

## Practical conclusion so far

- If priority is **capital survival + smoother risk**, `lowdd::linear_ml` remains strongest deployable candidate.
- If priority is **higher win rate with controlled DD**, triple-objective ensemble improved win rate but sacrificed return vs buy-and-hold.
- Fib/pivot/halving features are useful as enhancers, but not a silver bullet on their own.

---

## Pointers to raw artifacts

- Baseline: `results/summary.json`, `results/REPORT.md`
- Low-DD: `results/lowdd_summary.json`, `results/LOWDD_REPORT.md`
- Triple objective: `results/triple_objective_summary.json`, `results/TRIPLE_OBJECTIVE_REPORT.md`
- Fib/Pivot/Halving: `results/fib-pivot-halving-track/summary.json`, `results/fib-pivot-halving-track/REPORT.md`
