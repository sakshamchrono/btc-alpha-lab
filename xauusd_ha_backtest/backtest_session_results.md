# XAUUSD 3-Minute Heikin Ashi Strategy (Session Filtered)

**Data Period**: Last 30 Days (3-minute candles)
**Filter 1**: Candle size > 25 points ($25.0) -> Exit but no entry.
**Filter 2 (Session)**: Entries ONLY between 08:00 UTC (London Open) and 21:00 UTC (NY Close). Force close all positions at 21:00 UTC to avoid Asian session chop.

## Performance Summary
- **Total Trades**: 1820
- **Winning Trades**: 658
- **Losing Trades**: 1162
- **Win Rate**: 36.15%
- **Net PnL (in USD terms per 1 oz)**: $-181.71

## Sample of Last 10 Trades
| Type | Entry Time | Entry Price | Exit Time | Exit Price | PnL | Reason |
|---|---|---|---|---|---|---|
| Short | 2026-03-05 15:39:00 | 5100.36 | 2026-03-05 15:45:00 | 5101.89 | -1.53 | Signal_Opposite |
| Long | 2026-03-05 15:45:00 | 5101.89 | 2026-03-05 16:03:00 | 5103.79 | 1.90 | Signal_Opposite |
| Short | 2026-03-05 16:03:00 | 5103.79 | 2026-03-05 16:39:00 | 5079.66 | 24.13 | Signal_Opposite |
| Long | 2026-03-05 16:39:00 | 5079.66 | 2026-03-05 17:15:00 | 5096.74 | 17.08 | Signal_Opposite |
| Short | 2026-03-05 17:15:00 | 5096.74 | 2026-03-05 17:45:00 | 5079.65 | 17.09 | Signal_Opposite |
| Long | 2026-03-05 17:45:00 | 5079.65 | 2026-03-05 17:48:00 | 5076.83 | -2.82 | Signal_Opposite |
| Short | 2026-03-05 17:48:00 | 5076.83 | 2026-03-05 18:03:00 | 5082.96 | -6.13 | Signal_Opposite |
| Long | 2026-03-05 18:03:00 | 5082.96 | 2026-03-05 18:21:00 | 5086.68 | 3.72 | Signal_Opposite |
| Short | 2026-03-05 18:21:00 | 5086.68 | 2026-03-05 18:30:00 | 5090.79 | -4.11 | Signal_Opposite |
| Long | 2026-03-05 18:30:00 | 5090.79 | 2026-03-05 18:48:00 | 5091.05 | 0.26 | Signal_Opposite |
