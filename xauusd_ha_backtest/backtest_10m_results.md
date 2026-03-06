# XAUUSD 10m HA Strategy (IST Blockout Filtered)

**Data Period**: Last 30 Days (10m candles)
**Strategy**: Pure Heikin Ashi Color Change (Red to Green = Buy, Green to Red = Sell)
**Filter 1**: Candle size > 25 points ($25.0) -> Exit current position, but NO new entry.
**Filter 2 (Time)**: NO new entries during IST blockouts (02:15 AM - 04:30 AM AND 09:15 AM - 11:00 AM).

## Performance Summary
- **Total Trades**: 797
- **Winning Trades**: 291
- **Losing Trades**: 506
- **Win Rate**: 36.51%
- **Net PnL (in USD terms per 1 oz)**: $104.14

## Sample of Last 10 Trades
| Type | Entry Time (UTC) | Entry Price | Exit Time (UTC) | Exit Price | PnL | Reason |
|---|---|---|---|---|---|---|
| Short | 2026-03-06 11:35:00 | 5094.11 | 2026-03-06 12:05:00 | 5100.21 | -6.10 | Signal_Opposite |
| Long | 2026-03-06 12:05:00 | 5100.21 | 2026-03-06 12:45:00 | 5094.53 | -5.68 | Signal_Opposite |
| Short | 2026-03-06 12:45:00 | 5094.53 | 2026-03-06 13:25:00 | 5132.56 | -38.03 | Oversized_Opposite |
| Long | 2026-03-06 14:15:00 | 5115.76 | 2026-03-06 14:35:00 | 5098.98 | -16.78 | Signal_Opposite |
| Short | 2026-03-06 14:35:00 | 5098.98 | 2026-03-06 14:55:00 | 5155.92 | -56.94 | Oversized_Opposite |
| Short | 2026-03-06 15:45:00 | 5151.85 | 2026-03-06 16:45:00 | 5154.04 | -2.19 | Signal_Opposite |
| Long | 2026-03-06 16:45:00 | 5154.04 | 2026-03-06 16:55:00 | 5146.89 | -7.15 | Signal_Opposite |
| Short | 2026-03-06 16:55:00 | 5146.89 | 2026-03-06 17:15:00 | 5155.28 | -8.39 | Signal_Opposite |
| Long | 2026-03-06 17:15:00 | 5155.28 | 2026-03-06 17:45:00 | 5148.15 | -7.13 | Signal_Opposite |
| Short | 2026-03-06 17:45:00 | 5148.15 | 2026-03-06 18:05:00 | 5156.80 | -8.65 | Signal_Opposite |
