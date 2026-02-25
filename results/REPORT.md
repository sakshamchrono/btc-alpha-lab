# BTC Alpha Lab Results

Data: 2010-07-19 to 2026-02-25 (4039 daily rows)

## OOS Metrics (walk-forward)
- **vol_breakout**: CAGR=78.09%, Sharpe=1.33, MaxDD=-70.62%, WinRate=25.82%
- **trend_following**: CAGR=27.81%, Sharpe=0.74, MaxDD=-69.50%, WinRate=22.33%
- **mean_reversion**: CAGR=3.99%, Sharpe=0.29, MaxDD=-51.66%, WinRate=8.22%

## Best strategy: vol_breakout
- CAGR=78.09%, Sharpe=1.33, MaxDD=-70.62%, WinRate=25.82%

## Caveats
- Regime shifts can invalidate historical edges.
- Daily bars miss intraday slippage/liquidity shocks.
- Live execution frictions may reduce realized Sharpe.
- No guaranteed profits.