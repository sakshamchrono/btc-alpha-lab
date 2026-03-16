# BTCUSDT 3-Minute HA Strategy (Doji & Wick Filtered)

**Data Period**: Last 30 Days (3-minute candles)
**Strategy**: Pure Heikin Ashi Color Change
**Filter 1 (Oversized)**: Candle size > $400 -> Exit current position, NO new entry.
**Filter 2 (Doji)**: If HA Body is < 25% of total HA length -> NO entry.
**Filter 3 (Wick)**: If HA opposing wick is > 20% of the HA body -> NO entry.
 *(A strong HA Buy must have a flat bottom, a strong HA Sell must have a flat top)*

## Performance Summary
- **Total Trades**: 1095
- **Winning Trades**: 362
- **Losing Trades**: 733
- **Win Rate**: 33.06%
- **Net PnL (in USD terms per 1 BTC)**: $204.49
