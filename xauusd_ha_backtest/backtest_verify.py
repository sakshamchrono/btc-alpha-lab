import csv
from datetime import datetime

def run_backtest_python(csv_file, timeframe_label):
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
            
    # Calculate HA exactly as JS does
    ha_close = [(r['open'] + r['high'] + r['low'] + r['close']) / 4 for r in df]
    
    ha_open = [(df[0]['open'] + df[0]['close']) / 2]
    for i in range(1, len(df)):
        ha_open.append((ha_open[i-1] + ha_close[i-1]) / 2)
        
    for i in range(len(df)):
        df[i]['ha_close'] = ha_close[i]
        df[i]['ha_open'] = ha_open[i]
        df[i]['ha_color'] = 'Green' if df[i]['ha_close'] > df[i]['ha_open'] else 'Red'
        
    MAX_CANDLE_SIZE = 25.0
    
    position = None
    entry_price = 0.0
    entry_time = None
    trades = []
    
    for i in range(1, len(df)):
        prev_color = df[i-1]['ha_color']
        curr_color = df[i]['ha_color']
        
        curr_high = df[i]['high']
        curr_low = df[i]['low']
        curr_close = df[i]['close']
        
        # Parse UTC time
        # Format: "2026-02-03 19:00:00"
        dt_obj = datetime.strptime(df[i]['open_time'], "%Y-%m-%d %H:%M:%S")
        utc_hour = dt_obj.hour
        utc_minute = dt_obj.minute
        ist_minute_total = (utc_hour * 60 + utc_minute + 330) % 1440
        
        is_blockout = False
        if (135 <= ist_minute_total < 270) or (555 <= ist_minute_total < 660):
            is_blockout = True
            
        candle_size = curr_high - curr_low
        
        buy_signal = (prev_color == 'Red') and (curr_color == 'Green')
        sell_signal = (prev_color == 'Green') and (curr_color == 'Red')
        
        is_oversized = candle_size > MAX_CANDLE_SIZE
        
        if position == 'Long':
            if sell_signal:
                pnl = curr_close - entry_price
                trades.append(pnl)
                position = None
        elif position == 'Short':
            if buy_signal:
                pnl = entry_price - curr_close
                trades.append(pnl)
                position = None
                
        if position is None and not is_blockout and not is_oversized:
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
    
    print(f"[{timeframe_label}] Python Validation - Trades: {total_trades} | Win Rate: {win_rate:.2f}% | PnL: ${total_pnl:.2f}")

print("Verifying backtest logic across all timeframes (JS vs Python)...")
run_backtest_python('xauusd_1m_30days.csv', '1m')
run_backtest_python('xauusd_3m_30days.csv', '3m')
run_backtest_python('xauusd_5m_30days.csv', '5m')
run_backtest_python('xauusd_10m_30days.csv', '10m')
run_backtest_python('xauusd_15m_30days.csv', '15m')
