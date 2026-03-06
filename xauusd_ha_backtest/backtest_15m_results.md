# XAUUSD 15m HA Strategy (IST Blockout Filtered)

**Data Period**: Last 30 Days (15m candles)
**Strategy**: Pure Heikin Ashi Color Change (Red to Green = Buy, Green to Red = Sell)
**Filter 1**: Candle size > 25 points ($25.0) -> Exit current position, but NO new entry.
**Filter 2 (Time)**: NO new entries during IST blockouts (02:15 AM - 04:30 AM AND 09:15 AM - 11:00 AM).

## Performance Summary
- **Total Trades**: 545
- **Winning Trades**: 192
- **Losing Trades**: 353
- **Win Rate**: 35.23%
- **Net PnL (in USD terms per 1 oz)**: $-183.98

## Sample of Last 10 Trades
| Type | Entry Time (UTC) | Entry Price | Exit Time (UTC) | Exit Price | PnL | Reason |
|---|---|---|---|---|---|---|
| Short | 2026-03-06 11:45:00 | 5088.69 | 2026-03-06 12:15:00 | 5099.87 | -11.18 | Signal_Opposite |
| Long | 2026-03-06 12:15:00 | 5099.87 | 2026-03-06 12:45:00 | 5092.82 | -7.05 | Signal_Opposite |
| Short | 2026-03-06 12:45:00 | 5092.82 | 2026-03-06 13:30:00 | 5127.77 | -34.95 | Oversized_Opposite |
| Short | 2026-03-06 14:00:00 | 5106.58 | 2026-03-06 14:15:00 | 5113.92 | -7.34 | Signal_Opposite |
| Long | 2026-03-06 14:15:00 | 5113.92 | 2026-03-06 15:45:00 | 5151.77 | 37.85 | Signal_Opposite |
| Short | 2026-03-06 15:45:00 | 5151.77 | 2026-03-06 16:15:00 | 5154.66 | -2.89 | Signal_Opposite |
| Long | 2026-03-06 16:15:00 | 5154.66 | 2026-03-06 16:30:00 | 5153.60 | -1.06 | Signal_Opposite |
| Short | 2026-03-06 16:30:00 | 5153.60 | 2026-03-06 17:30:00 | 5150.05 | 3.55 | Signal_Opposite |
| Long | 2026-03-06 17:30:00 | 5150.05 | 2026-03-06 17:45:00 | 5151.99 | 1.94 | Signal_Opposite |
| Short | 2026-03-06 17:45:00 | 5151.99 | 2026-03-06 18:00:00 | 5156.80 | -4.81 | Signal_Opposite |
