# XAUUSD 1-Minute HA Strategy (IST Blockout Filtered)

**Data Period**: Last 30 Days (1-minute candles)
**Strategy**: Pure Heikin Ashi Color Change (Red to Green = Buy, Green to Red = Sell)
**Filter 1**: Candle size > 25 points ($25.0) -> Exit current position, but NO new entry.
**Filter 2 (Time)**: NO new entries during IST blockouts (02:15 AM - 04:30 AM AND 09:15 AM - 11:00 AM).

## Performance Summary
- **Total Trades**: 8154
- **Winning Trades**: 2933
- **Losing Trades**: 5221
- **Win Rate**: 35.97%
- **Net PnL (in USD terms per 1 oz)**: $-96.42

## Sample of Last 10 Trades
| Type | Entry Time (UTC) | Entry Price | Exit Time (UTC) | Exit Price | PnL | Reason |
|---|---|---|---|---|---|---|
| Long | 2026-03-06 17:57:00 | 5149.62 | 2026-03-06 18:04:00 | 5154.08 | 4.46 | Signal_Opposite |
| Short | 2026-03-06 18:04:00 | 5154.08 | 2026-03-06 18:06:00 | 5155.14 | -1.06 | Signal_Opposite |
| Long | 2026-03-06 18:06:00 | 5155.14 | 2026-03-06 18:10:00 | 5155.92 | 0.78 | Signal_Opposite |
| Short | 2026-03-06 18:10:00 | 5155.92 | 2026-03-06 18:12:00 | 5155.75 | 0.17 | Signal_Opposite |
| Long | 2026-03-06 18:12:00 | 5155.75 | 2026-03-06 18:15:00 | 5156.82 | 1.07 | Signal_Opposite |
| Short | 2026-03-06 18:15:00 | 5156.82 | 2026-03-06 18:20:00 | 5157.81 | -0.99 | Signal_Opposite |
| Long | 2026-03-06 18:20:00 | 5157.81 | 2026-03-06 18:27:00 | 5159.28 | 1.47 | Signal_Opposite |
| Short | 2026-03-06 18:27:00 | 5159.28 | 2026-03-06 18:29:00 | 5161.24 | -1.96 | Signal_Opposite |
| Long | 2026-03-06 18:29:00 | 5161.24 | 2026-03-06 18:35:00 | 5160.00 | -1.24 | Signal_Opposite |
| Short | 2026-03-06 18:35:00 | 5160.00 | 2026-03-06 18:37:00 | 5163.73 | -3.73 | Signal_Opposite |
