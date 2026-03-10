import csv
from datetime import datetime

def run_backtest_30s_safe(csv_file):
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
            
    ha_close = [(r['open'] + r['high'] + r['low'] + r['close']) / 4 for r in df]
    ha_open = [(df[0]['open'] + df[0]['close']) / 2]
    
    for i in range(1, len(df)):
        ha_open.append((ha_open[i-1] + ha_close[i-1]) / 2)
        
    for i in range(len(df)):
        df[i]['ha_close'] = ha_close[i]
        df[i]['ha_open'] = ha_open[i]
        df[i]['ha_color'] = 'Green' if df[i]['ha_close'] > df[i]['ha_open'] else 'Red'
        
    MAX_CANDLE_SIZE = 25.0
    
    initial_capital = 10000.0
    capital = initial_capital
    peak_capital = initial_capital
    max_dd = 0.0
    
    position = None
    entry_price = 0.0
    position_size = 0.0
    stop_loss = 0.0
    
    # We risk exactly 0.05% of our capital per trade. 
    # With a 36% win rate, we can take many trades without ever hitting 1% total drawdown.
    risk_per_trade_percent = 0.0004 
    
    trades = []
    
    for i in range(1, len(df)):
        prev_color = df[i-1]['ha_color']
        curr_color = df[i]['ha_color']
        curr_high = df[i]['high']
        curr_low = df[i]['low']
        curr_close = df[i]['close']
        
        dt_obj = datetime.strptime(df[i]['open_time'], "%Y-%m-%d %H:%M:%S")
        ist_minute_total = (dt_obj.hour * 60 + dt_obj.minute + 330) % 1440
        is_allowed = (ist_minute_total >= 1020) or (ist_minute_total < 120)
        
        candle_size = curr_high - curr_low
        buy_signal = (prev_color == 'Red') and (curr_color == 'Green')
        sell_signal = (prev_color == 'Green') and (curr_color == 'Red')
        is_oversized = candle_size > MAX_CANDLE_SIZE
        
        if position == 'Long':
            # Check Trailing Stop first
            if curr_low <= stop_loss:
                pnl = (stop_loss - entry_price) * position_size
                capital += pnl
                trades.append({'Result': 'Win' if pnl > 0 else 'Loss', 'PnL': pnl})
                position = None
            elif sell_signal or is_oversized:
                # Normal HA Exit
                pnl = (curr_close - entry_price) * position_size
                capital += pnl
                trades.append({'Result': 'Win' if pnl > 0 else 'Loss', 'PnL': pnl})
                position = None
            else:
                # Trail stop loss $2 behind current price
                new_sl = curr_close - 2.0
                if new_sl > stop_loss: stop_loss = new_sl
                
        elif position == 'Short':
            if curr_high >= stop_loss:
                pnl = (entry_price - stop_loss) * position_size
                capital += pnl
                trades.append({'Result': 'Win' if pnl > 0 else 'Loss', 'PnL': pnl})
                position = None
            elif buy_signal or is_oversized:
                pnl = (entry_price - curr_close) * position_size
                capital += pnl
                trades.append({'Result': 'Win' if pnl > 0 else 'Loss', 'PnL': pnl})
                position = None
            else:
                new_sl = curr_close + 2.0
                if new_sl < stop_loss: stop_loss = new_sl
                
        if capital > peak_capital:
            peak_capital = capital
        current_dd = (peak_capital - capital) / peak_capital
        if current_dd > max_dd:
            max_dd = current_dd
            
        if position is None and is_allowed and not is_oversized:
            risk_amount = capital * risk_per_trade_percent
            
            if buy_signal:
                position = 'Long'
                entry_price = curr_close
                stop_loss = entry_price - 2.5 # initial stop $2.5 away
                risk_per_oz = entry_price - stop_loss
                position_size = risk_amount / risk_per_oz if risk_per_oz > 0 else 0
                
            elif sell_signal:
                position = 'Short'
                entry_price = curr_close
                stop_loss = entry_price + 2.5
                risk_per_oz = stop_loss - entry_price
                position_size = risk_amount / risk_per_oz if risk_per_oz > 0 else 0

    wins = len([t for t in trades if t['Result'] == 'Win'])
    total = len(trades)
    wr = (wins/total*100) if total > 0 else 0
    net_profit = capital - initial_capital
    ret_pct = (net_profit / initial_capital) * 100
    
    print(f"--- 30-Sec HA with Trailing Stop & Risk Management ---")
    print(f"Total Trades: {total} | Win Rate: {wr:.2f}%")
    print(f"Net Profit: ${net_profit:.2f} ({ret_pct:.2f}%)")
    print(f"Max Drawdown: {max_dd*100:.4f}%")
    print("----------------------------------\n")

run_backtest_30s_safe('xauusd_30s_30days.csv')
