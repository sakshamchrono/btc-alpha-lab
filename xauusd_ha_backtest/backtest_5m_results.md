# XAUUSD 5m HA Strategy (IST Blockout Filtered)

**Data Period**: Last 30 Days (5m candles)
**Strategy**: Pure Heikin Ashi Color Change (Red to Green = Buy, Green to Red = Sell)
**Filter 1**: Candle size > 25 points ($25.0) -> Exit current position, but NO new entry.
**Filter 2 (Time)**: NO new entries during IST blockouts (02:15 AM - 04:30 AM AND 09:15 AM - 11:00 AM).

## Performance Summary
- **Total Trades**: 1690
- **Winning Trades**: 606
- **Losing Trades**: 1084
- **Win Rate**: 35.86%
- **Net PnL (in USD terms per 1 oz)**: $195.00

## Sample of Last 10 Trades
| Type | Entry Time (UTC) | Entry Price | Exit Time (UTC) | Exit Price | PnL | Reason |
|---|---|---|---|---|---|---|
| Long | 2026-03-06 14:50:00 | 5112.50 | 2026-03-06 15:35:00 | 5166.62 | 54.12 | Signal_Opposite |
| Short | 2026-03-06 15:35:00 | 5166.62 | 2026-03-06 16:00:00 | 5159.91 | 6.71 | Signal_Opposite |
| Long | 2026-03-06 16:00:00 | 5159.91 | 2026-03-06 16:10:00 | 5154.66 | -5.25 | Signal_Opposite |
| Short | 2026-03-06 16:10:00 | 5154.66 | 2026-03-06 16:15:00 | 5160.97 | -6.31 | Signal_Opposite |
| Long | 2026-03-06 16:15:00 | 5160.97 | 2026-03-06 16:25:00 | 5154.66 | -6.31 | Signal_Opposite |
| Short | 2026-03-06 16:25:00 | 5154.66 | 2026-03-06 16:45:00 | 5155.11 | -0.45 | Signal_Opposite |
| Long | 2026-03-06 16:45:00 | 5155.11 | 2026-03-06 16:55:00 | 5152.77 | -2.34 | Signal_Opposite |
| Short | 2026-03-06 16:55:00 | 5152.77 | 2026-03-06 17:15:00 | 5154.30 | -1.53 | Signal_Opposite |
| Long | 2026-03-06 17:15:00 | 5154.30 | 2026-03-06 17:40:00 | 5150.05 | -4.25 | Signal_Opposite |
| Short | 2026-03-06 17:40:00 | 5150.05 | 2026-03-06 18:00:00 | 5154.08 | -4.03 | Signal_Opposite |
