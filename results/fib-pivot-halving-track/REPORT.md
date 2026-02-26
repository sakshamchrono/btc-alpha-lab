# Fib-Pivot-Halving Track

Data: 2010-07-19 to 2026-02-25 (4039 rows)
Validation: purged walk-forward (train=4y, test=180d, step=180d, purge=7d)
Frictions: 4 bps costs + 2 bps slippage

## Ablation (OOS)

| Variant | CAGR | Total Return | Sharpe | Sortino | MaxDD | Calmar | Win Rate | Monthly Hit | Turnover |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Baseline | 2.84% | 21.29% | 1.38 | 2.57 | -1.89% | 1.50 | 12.46% | 27.38% | 0.92x |
| Baseline + Fibonacci | 5.15% | 41.43% | 1.44 | 2.93 | -2.80% | 1.84 | 15.63% | 30.95% | 1.87x |
| Baseline + Pivots | 2.80% | 20.96% | 1.18 | 2.07 | -2.38% | 1.17 | 14.52% | 41.67% | 2.62x |
| Baseline + Halving | 7.75% | 67.39% | 1.61 | 3.03 | -4.89% | 1.59 | 19.96% | 34.52% | 1.26x |
| Combined (Fib+Pivots+Halving) | 8.33% | 73.79% | 1.52 | 2.86 | -5.29% | 1.57 | 21.43% | 46.43% | 4.12x |

## Combined vs Baseline delta
- CAGR: +5.50%
- Win Rate: +8.97%
- Max Drawdown improvement (less negative is better): -3.41%

## Benchmarks

| Metric | Buy & Hold (same OOS windows) | Combined |
|---|---:|---:|
| CAGR | 117.95% | 8.33% |
| Total Return | 21582.08% | 73.79% |
| Sharpe | 1.39 | 1.52 |
| Sortino | 2.41 | 2.86 |
| Max Drawdown | -82.97% | -5.29% |
| Calmar | 1.42 | 1.57 |
| Win Rate | 52.42% | 21.43% |
| Monthly Hit Rate | 59.52% | 46.43% |
| Turnover | 1.00 | 4.12 |

## Latest recommended strategy reference (lowdd::linear_ml)

| Metric | Latest Recommended | Combined |
|---|---:|---:|
| CAGR | 54.13% | 8.33% |
| Total Return | 2662.24% | 73.79% |
| Sharpe | 2.17 | 1.52 |
| Sortino | 4.14 | 2.86 |
| Max Drawdown | -16.70% | -5.29% |
| Calmar | 3.24 | 1.57 |
| Win Rate | 20.54% | 21.43% |
| Monthly Hit Rate | 46.24% | 46.43% |
| Turnover | 13.10 | 4.12 |