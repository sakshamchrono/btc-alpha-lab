import csv

def run_btc_wicks(csv_file):
    df = []
    with open(csv_file, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            df.append({
                'open_time': row['open_time'],
                'open': float(row['open']),
                'high': float(row['high']),
                'low': float(row['low']),
                'close': float(row['close'])
            })
            
    # Calculate HA values exactly
    ha_close = [(r['open'] + r['high'] + r['low'] + r['close']) / 4 for r in df]
    ha_open = [(df[0]['open'] + df[0]['close']) / 2]
    
    for i in range(1, len(df)):
        ha_open.append((ha_open[i-1] + ha_close[i-1]) / 2)
        
    for i in range(len(df)):
        df[i]['ha_close'] = ha_close[i]
        df[i]['ha_open'] = ha_open[i]
        # In HA, high is max of high, ha_open, ha_close
        df[i]['ha_high'] = max(df[i]['high'], df[i]['ha_open'], df[i]['ha_close'])
        # In HA, low is min of low, ha_open, ha_close
        df[i]['ha_low'] = min(df[i]['low'], df[i]['ha_open'], df[i]['ha_close'])
        df[i]['ha_color'] = 'Green' if df[i]['ha_close'] > df[i]['ha_open'] else 'Red'
        
    MAX_CANDLE_SIZE = 400.0 # Standard oversized filter we used earlier for BTC
    
    position = None
    entry_price = 0.0
    trades = []
    
    for i in range(1, len(df)):
        prev_color = df[i-1]['ha_color']
        curr_color = df[i]['ha_color']
        
        curr_high = df[i]['high']
        curr_low = df[i]['low']
        curr_close = df[i]['close']
        
        ha_o = df[i]['ha_open']
        ha_c = df[i]['ha_close']
        ha_h = df[i]['ha_high']
        ha_l = df[i]['ha_low']
        
        buy_signal = (prev_color == 'Red') and (curr_color == 'Green')
        sell_signal = (prev_color == 'Green') and (curr_color == 'Red')
        
        # Filter 1: Oversized normal candle
        candle_size = curr_high - curr_low
        is_oversized = candle_size > MAX_CANDLE_SIZE
        
        # Filter 2: Doji or Long Wicks on the HA Signal Candle
        ha_body = abs(ha_c - ha_o)
        ha_length = ha_h - ha_l
        
        # Doji: Body is less than 25% of the total candle length
        is_doji = ha_length > 0 and (ha_body / ha_length) < 0.25
        
        # Long Wicks: 
        # A strong HA Green candle should have NO (or very small) lower wick.
        # A strong HA Red candle should have NO (or very small) upper wick.
        # We reject the entry if the opposing wick is larger than 20% of the body.
        lower_wick = ha_o - ha_l if curr_color == 'Green' else ha_c - ha_l
        upper_wick = ha_h - ha_c if curr_color == 'Green' else ha_h - ha_o
        
        bad_wick_buy = (curr_color == 'Green') and (lower_wick > (0.2 * ha_body))
        bad_wick_sell = (curr_color == 'Red') and (upper_wick > (0.2 * ha_body))
        
        skip_entry = is_doji or bad_wick_buy or bad_wick_sell
        reason = "Oversized" if is_oversized else ("Doji/LongWick" if skip_entry else "Valid")

        # EXIT LOGIC
        if position == 'Long':
            if sell_signal:
                trades.append(curr_close - entry_price)
                position = None
        elif position == 'Short':
            if buy_signal:
                trades.append(entry_price - curr_close)
                position = None
                
        # ENTRY LOGIC
        if position is None and not is_oversized and not skip_entry:
            if buy_signal:
                position = 'Long'
                entry_price = curr_close
            elif sell_signal:
                position = 'Short'
                entry_price = curr_close

    winning_trades = len([pnl for pnl in trades if pnl > 0])
    total_trades = len(trades)
    win_rate = (winning_trades / total_trades * 100) if total_trades else 0
    total_pnl = sum(trades)
    
    # Save Results
    with open('backtest_btc_wicks_results.md', 'w') as f:
        f.write("# BTCUSDT 3-Minute HA Strategy (Doji & Wick Filtered)\n\n")
        f.write("**Data Period**: Last 30 Days (3-minute candles)\n")
        f.write("**Strategy**: Pure Heikin Ashi Color Change\n")
        f.write("**Filter 1 (Oversized)**: Candle size > $400 -> Exit current position, NO new entry.\n")
        f.write("**Filter 2 (Doji)**: If HA Body is < 25% of total HA length -> NO entry.\n")
        f.write("**Filter 3 (Wick)**: If HA opposing wick is > 20% of the HA body -> NO entry.\n")
        f.write(" *(A strong HA Buy must have a flat bottom, a strong HA Sell must have a flat top)*\n\n")
        f.write("## Performance Summary\n")
        f.write(f"- **Total Trades**: {total_trades}\n")
        f.write(f"- **Winning Trades**: {winning_trades}\n")
        f.write(f"- **Losing Trades**: {total_trades - winning_trades}\n")
        f.write(f"- **Win Rate**: {win_rate:.2f}%\n")
        f.write(f"- **Net PnL (in USD terms per 1 BTC)**: ${total_pnl:.2f}\n")

    print(f"BTC Wick Filter Backtest -> Trades: {total_trades} | Win Rate: {win_rate:.2f}% | PnL: ${total_pnl:.2f}")

run_btc_wicks('btcusd_3m_30days.csv')
