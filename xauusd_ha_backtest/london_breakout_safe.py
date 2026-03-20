import csv
from datetime import datetime

def run_london_breakout(csv_file):
    df = []
    with open(csv_file, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            df.append({
                'open_time': row['open_time'],
                'high': float(row['high']),
                'low': float(row['low']),
                'close': float(row['close'])
            })
            
    initial_capital = 10000.0
    capital = initial_capital
    peak_capital = initial_capital
    max_dd = 0.0
    
    position = 0 
    entry_price = 0.0
    stop_loss = 0.0
    take_profit = 0.0
    position_size = 0.0
    
    risk_per_trade_percent = 0.001 
    trades = []
    
    asian_high = -1.0
    asian_low = 99999.0
    trade_taken_today = False
    
    for i in range(1, len(df)):
        curr_high = df[i]['high']
        curr_low = df[i]['low']
        curr_close = df[i]['close']
        
        dt_obj = datetime.strptime(df[i]['open_time'], "%Y-%m-%d %H:%M:%S")
        utc_hour = dt_obj.hour
        utc_minute = dt_obj.minute
        
        # Asian Session Reset at start of day
        if utc_hour == 0 and utc_minute == 0:
            asian_high = -1.0
            asian_low = 99999.0
            trade_taken_today = False
            
        # Build Asian Session Box (00:00 to 07:00 UTC)
        if 0 <= utc_hour < 7:
            if curr_high > asian_high: asian_high = curr_high
            if curr_low < asian_low: asian_low = curr_low
            
        # Check Exits (can happen any time)
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
                
        if capital > peak_capital:
            peak_capital = capital
        current_dd = (peak_capital - capital) / peak_capital
        if current_dd > max_dd:
            max_dd = current_dd
            
        # Entry Logic (London Session Breakout: 07:00 UTC to 14:00 UTC)
        if position == 0 and not trade_taken_today and (7 <= utc_hour < 14) and asian_high > 0:
            box_size = asian_high - asian_low
            
            # Require minimum volatility ($2) but not huge shock ($30)
            if 2.0 < box_size < 30.0:
                risk_amount = capital * risk_per_trade_percent
                
                # Buy breakout
                if curr_close > asian_high:
                    position = 1
                    entry_price = curr_close
                    stop_loss = asian_high - (box_size * 0.5) # Tight stop: half the box
                    take_profit = entry_price + (box_size * 1.5) # 1:3 RR
                    risk_per_oz = entry_price - stop_loss
                    position_size = risk_amount / risk_per_oz if risk_per_oz > 0 else 0
                    trade_taken_today = True
                    
                # Sell breakdown
                elif curr_close < asian_low:
                    position = -1
                    entry_price = curr_close
                    stop_loss = asian_low + (box_size * 0.5)
                    take_profit = entry_price - (box_size * 1.5)
                    risk_per_oz = stop_loss - entry_price
                    position_size = risk_amount / risk_per_oz if risk_per_oz > 0 else 0
                    trade_taken_today = True

    wins = len([t for t in trades if t['Result'] == 'Win'])
    total = len(trades)
    wr = (wins/total*100) if total > 0 else 0
    net_profit = capital - initial_capital
    ret_pct = (net_profit / initial_capital) * 100
    
    print(f"--- Asian Box Breakout Strategy ({csv_file}) ---")
    print(f"Total Trades: {total} | Win Rate: {wr:.2f}%")
    print(f"Net Profit: ${net_profit:.2f} ({ret_pct:.2f}%)")
    print(f"Max Drawdown: {max_dd*100:.4f}%")
    print("----------------------------------\n")

run_london_breakout('xauusd_5m_30days.csv')
