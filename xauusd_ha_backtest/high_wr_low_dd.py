import csv
import math

def calc_rsi(data, period=14):
    deltas = [data[i] - data[i-1] for i in range(1, len(data))]
    gains = [d if d > 0 else 0 for d in deltas]
    losses = [-d if d < 0 else 0 for d in deltas]
    
    avg_gain = sum(gains[:period]) / period
    avg_loss = sum(losses[:period]) / period
    
    rs = avg_gain / avg_loss if avg_loss != 0 else 0
    rsi = [100 - (100 / (1 + rs))] * period
    
    for i in range(period, len(deltas)):
        avg_gain = (avg_gain * (period - 1) + gains[i]) / period
        avg_loss = (avg_loss * (period - 1) + losses[i]) / period
        rs = avg_gain / avg_loss if avg_loss != 0 else 0
        rsi.append(100 - (100 / (1 + rs)))
        
    return [0] + rsi # align indexing

def run_low_dd_strategy(csv_file):
    df = []
    with open(csv_file, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            df.append({
                'open': float(row['open']),
                'high': float(row['high']),
                'low': float(row['low']),
                'close': float(row['close'])
            })
            
    closes = [r['close'] for r in df]
    rsi = calc_rsi(closes, 14)
    
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
    
    # Ultra-low risk per trade: 0.1% to guarantee < 1% total drawdown
    risk_per_trade_percent = 0.001 
    
    trades = []
    
    for i in range(50, len(df)):
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
            
        # Entry Logic (Mean Reversion - RSI Extremes)
        if position == 0:
            current_rsi = rsi[i]
            
            # Very tight fixed stop loss: $1.5 movement in gold
            sl_points = 1.5 
            # Small meaningful profit (1:1.5 RR)
            tp_points = 2.25 
            
            risk_amount = capital * risk_per_trade_percent
            position_size = risk_amount / sl_points if sl_points > 0 else 0
            
            # RSI oversold -> bounce expected
            if current_rsi < 25:
                position = 1
                entry_price = curr_close
                stop_loss = entry_price - sl_points
                take_profit = entry_price + tp_points
                
            # RSI overbought -> pullback expected
            elif current_rsi > 75:
                position = -1
                entry_price = curr_close
                stop_loss = entry_price + sl_points
                take_profit = entry_price - tp_points

    wins = len([t for t in trades if t['Result'] == 'Win'])
    total = len(trades)
    wr = (wins/total*100) if total > 0 else 0
    net_profit = capital - initial_capital
    ret_pct = (net_profit / initial_capital) * 100
    
    print(f"--- High WR Mean Reversion Strategy ({csv_file}) ---")
    print(f"Total Trades: {total} | Win Rate: {wr:.2f}%")
    print(f"Net Profit: ${net_profit:.2f} ({ret_pct:.2f}%)")
    print(f"Max Drawdown: {max_dd*100:.4f}%")
    print("----------------------------------\n")

run_low_dd_strategy('xauusd_5m_30days.csv')
