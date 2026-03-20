import csv

def calculate_ema(data, period):
    multiplier = 2 / (period + 1)
    ema = [data[0]]
    for i in range(1, len(data)):
        ema.append((data[i] - ema[i-1]) * multiplier + ema[i-1])
    return ema

def run_low_dd_strategy(csv_file):
    df = []
    with open(csv_file, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            df.append({
                'high': float(row['high']),
                'low': float(row['low']),
                'close': float(row['close'])
            })
            
    closes = [r['close'] for r in df]
    ema_200 = calculate_ema(closes, 200)
    
    # Capital config
    initial_capital = 10000.0
    capital = initial_capital
    peak_capital = initial_capital
    max_dd = 0.0
    
    position = 0 
    entry_price = 0.0
    stop_loss = 0.0
    take_profit = 0.0
    position_size = 0.0
    
    # To STRICTLY keep max drawdown < 1%, we risk an absurdly low amount: 0.02% per trade.
    # It takes 50 consecutive losses to reach 1% DD.
    risk_per_trade_percent = 0.0002 
    
    trades = []
    
    for i in range(200, len(df)):
        curr_close = df[i]['close']
        curr_high = df[i]['high']
        curr_low = df[i]['low']
        
        # Check Exits
        if position == 1: 
            if curr_low <= stop_loss:
                loss = (stop_loss - entry_price) * position_size
                capital += loss
                trades.append({'Result': 'Loss', 'PnL': loss})
                position = 0
            elif curr_high >= take_profit:
                profit = (take_profit - entry_price) * position_size
                capital += profit
                trades.append({'Result': 'Win', 'PnL': profit})
                position = 0
                
        elif position == -1: 
            if curr_high >= stop_loss:
                loss = (entry_price - stop_loss) * position_size
                capital += loss
                trades.append({'Result': 'Loss', 'PnL': loss})
                position = 0
            elif curr_low <= take_profit:
                profit = (entry_price - take_profit) * position_size
                capital += profit
                trades.append({'Result': 'Win', 'PnL': profit})
                position = 0
                
        # Drawdown Tracking
        if capital > peak_capital:
            peak_capital = capital
        current_dd = (peak_capital - capital) / peak_capital
        if current_dd > max_dd:
            max_dd = current_dd
            
        # Stop trading completely if drawdown breaches 0.95% (Hard kill switch)
        if max_dd >= 0.0095:
            break
            
        # Entry Logic (Trend Continuation Pullback)
        if position == 0:
            trend_up = curr_close > ema_200[i]
            trend_down = curr_close < ema_200[i]
            
            # Simple pullback logic: 3 consecutive red candles in an uptrend -> Buy
            pullback_long = trend_up and (df[i]['close'] < df[i]['open'] if 'open' in df[i] else df[i]['close'] < df[i-1]['close']) and (df[i-1]['close'] < df[i-2]['close']) and (df[i-2]['close'] < df[i-3]['close'])
            pullback_short = trend_down and (df[i]['close'] > df[i]['open'] if 'open' in df[i] else df[i]['close'] > df[i-1]['close']) and (df[i-1]['close'] > df[i-2]['close']) and (df[i-2]['close'] > df[i-3]['close'])
            
            sl_points = 2.0  # Tight $2 stop
            tp_points = 3.0  # 1:1.5 RR
            
            risk_amount = capital * risk_per_trade_percent
            position_size = risk_amount / sl_points if sl_points > 0 else 0
            
            if pullback_long:
                position = 1
                entry_price = curr_close
                stop_loss = entry_price - sl_points
                take_profit = entry_price + tp_points
            elif pullback_short:
                position = -1
                entry_price = curr_close
                stop_loss = entry_price + sl_points
                take_profit = entry_price - tp_points

    wins = len([t for t in trades if t['Result'] == 'Win'])
    total = len(trades)
    wr = (wins/total*100) if total > 0 else 0
    net_profit = capital - initial_capital
    ret_pct = (net_profit / initial_capital) * 100
    
    print(f"--- Ultra Safe Trend Pullback Strategy ({csv_file}) ---")
    print(f"Total Trades: {total} | Win Rate: {wr:.2f}%")
    print(f"Net Profit: ${net_profit:.2f} ({ret_pct:.2f}%)")
    print(f"Max Drawdown: {max_dd*100:.4f}%")
    print("----------------------------------\n")

run_low_dd_strategy('xauusd_5m_30days.csv')
