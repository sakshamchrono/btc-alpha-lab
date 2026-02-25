# Triple-Objective Track

Data: 2010-07-19 to 2026-02-25 (4039 rows)
Validation: purged walk-forward (train=4y,test=180d,step=180d,purge=7d)
Costs: 4 bps + 2 bps slippage

## Candidate leaderboard

| Strategy | Objective | CAGR | WinRate | MaxDD | Sharpe | Sortino | Calmar | Turnover | Monthly Hit |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| logistic_l2 | 2.387 | 2.95% | 14.25% | -1.69% | 1.51 | 2.97 | 1.75 | 1.08x | 32.53% |
| hybrid_blend | 2.290 | 11.70% | 26.26% | -9.88% | 1.33 | 2.41 | 1.18 | 8.82x | 40.96% |
| meta_labeled_ensemble | 2.279 | 14.64% | 9.02% | -9.81% | 1.46 | 2.75 | 1.49 | 5.37x | 22.89% |
| boosted_stumps | 2.143 | 4.87% | 22.39% | -4.48% | 1.28 | 2.41 | 1.09 | 5.96x | 55.42% |
| weak_ensemble | 2.063 | 24.90% | 27.69% | -24.84% | 1.20 | 2.11 | 1.00 | 20.29x | 39.76% |

## Explicit comparison vs Buy & Hold (OOS)

| Metric | Buy&Hold | Recommended |
|---|---:|---:|
| CAGR | 243.49% | 24.90% |
| Total Return | 85158192.08% | 360.20% |
| Sharpe | 1.70 | 1.20 |
| Sortino | 3.12 | 2.11 |
| Max Drawdown | -93.07% | -24.84% |
| Calmar | 2.62 | 1.00 |
| Win Rate | 52.19% | 27.69% |
| Monthly Hit Rate | 56.72% | 39.76% |
| Turnover | 1.00 | 20.29 |

## Final selection logic
- Recommended: **weak_ensemble**
- Selection: Pareto-per-fold then weighted triple-objective score.
- Constraint note: No strategy beat buy-and-hold on both CAGR and total return OOS; reporting closest Pareto candidate.

## Baseline references
- Buy&Hold: CAGR 243.49%, Total Return 85158192.08%, MaxDD -93.07%
- Prior repo best vol_breakout: CAGR 78.09%, MaxDD -70.62%, Sharpe 1.33

## Stability
- Bull CAGR 54.10%, Bear CAGR -23.00%
- High-vol MaxDD -20.50%, Low-vol MaxDD -20.50%
- Rolling windows evaluated: 78

## Deployment blueprint
- Size = signal × vol-target (35%) × drawdown de-risk ladder.
- De-risk ladder: DD<-10% => 60% size; DD<-15% => 35%; DD<-20% => flat/kill-switch.
- Alert/kill triggers: 180d Sharpe < 0 for two windows OR DD breach above historical 95th percentile.
- Execution guardrails: long-only, exposure cap=1.0, turnover alert >25x/year.

## Remaining risks
- BTC gap risk, exchange microstructure slippage, and regime decay can degrade live results.
- Carry-like sleeve is proxy signal, not true basis carry.
- Needs quarterly re-validation and conservative capital ramp.