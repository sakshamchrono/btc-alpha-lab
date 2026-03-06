import csv
from datetime import datetime

def run_backtest_10m(csv_file):
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
    
    position = None
    entry_price = 0.0
    trades = []
    
    for i in range(1, len(df)):
        prev_color = df[i-1]['ha_color']
        curr_color = df[i]['ha_color']
        curr_high = df[i]['high']
        curr_low = df[i]['low']
        curr_close = df[i]['close']
        
        dt_obj = datetime.strptime(df[i]['open_time'], "%Y-%m-%d %H:%M:%S")
        ist_minute_total = (dt_obj.hour * 60 + dt_obj.minute + 330) % 1440
        
        is_blockout = False
        if (135 <= ist_minute_total < 270) or (555 <= ist_minute_total < 660):
            is_blockout = True
            
        candle_size = curr_high - curr_low
        buy_signal = (prev_color == 'Red') and (curr_color == 'Green')
        sell_signal = (prev_color == 'Green') and (curr_color == 'Red')
        is_oversized = candle_size > MAX_CANDLE_SIZE
        
        if position == 'Long':
            if sell_signal:
                trades.append(curr_close - entry_price)
                position = None
        elif position == 'Short':
            if buy_signal:
                trades.append(entry_price - curr_close)
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
    
    print(f"[10m IST Blockout] Python Validation - Trades: {total_trades} | Win Rate: {win_rate:.2f}% | PnL: ${total_pnl:.2f}")

run_backtest_10m('xauusd_10m_30days.csv')
