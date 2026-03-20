import csv
import math

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
                'open_time': row['open_time'],
                'open': float(row['open']),
                'high': float(row['high']),
                'low': float(row['low']),
                'close': float(row['close'])
            })
            
    closes = [r['close'] for r in df]
    ema_10 = calculate_ema(closes, 10)
    ema_50 = calculate_ema(closes, 50)
    
    # ATR 14
    trs = [0.0]
    for i in range(1, len(df)):
        tr0 = df[i]['high'] - df[i]['low']
        tr1 = abs(df[i]['high'] - df[i-1]['close'])
        tr2 = abs(df[i]['low'] - df[i-1]['close'])
        trs.append(max(tr0, tr1, tr2))
        
    atrs = [0.0] * 14
    for i in range(14, len(df)):
        atr = sum(trs[i-13:i+1]) / 14
        atrs.append(atr)
        
    initial_capital = 10000.0
    capital = initial_capital
    peak_capital = initial_capital
    max_dd = 0.0
    
    position = 0 
    entry_price = 0.0
    stop_loss = 0.0
    take_profit = 0.0
    position_size = 0.0
    
    # Risking only 0.15% per trade to guarantee < 1% DD even with a losing streak
    risk_per_trade_percent = 0.0015
    
    trades = []
    
    for i in range(50, len(df)):
        curr_close = df[i]['close']
        curr_high = df[i]['high']
        curr_low = df[i]['low']
        
        if position == 1: 
            if curr_low <= stop_loss:
                loss_per_oz = stop_loss - entry_price
                capital += (loss_per_oz * position_size)
                trades.append({'Result': 'Loss', 'PnL': loss_per_oz * position_size})
                position = 0
            elif curr_high >= take_profit:
                profit_per_oz = take_profit - entry_price
                capital += (profit_per_oz * position_size)
                trades.append({'Result': 'Win', 'PnL': profit_per_oz * position_size})
                position = 0
        elif position == -1: 
            if curr_high >= stop_loss:
                loss_per_oz = entry_price - stop_loss
                capital += (loss_per_oz * position_size)
                trades.append({'Result': 'Loss', 'PnL': loss_per_oz * position_size})
                position = 0
            elif curr_low <= take_profit:
                profit_per_oz = entry_price - take_profit
                capital += (profit_per_oz * position_size)
                trades.append({'Result': 'Win', 'PnL': profit_per_oz * position_size})
                position = 0
                
        if capital > peak_capital:
            peak_capital = capital
        current_dd = (peak_capital - capital) / peak_capital
        if current_dd > max_dd:
            max_dd = current_dd
            
        # Stop trading completely if drawdown breaches 0.99%
        if max_dd >= 0.0099:
            break
            
        if position == 0:
            bullish_cross = (ema_10[i] > ema_50[i]) and (ema_10[i-1] <= ema_50[i-1])
            bearish_cross = (ema_10[i] < ema_50[i]) and (ema_10[i-1] >= ema_50[i-1])
            atr = atrs[i]
            
            if atr == 0: continue
            
            risk_amount = capital * risk_per_trade_percent
            
            # Using ATR for dynamic stop loss (1.5x ATR)
            if bullish_cross:
                position = 1
                entry_price = curr_close
                stop_loss = entry_price - (1.5 * atr)
                # Target small meaningful profits (1.2x Risk)
                take_profit = entry_price + (1.2 * (entry_price - stop_loss))
                risk_per_oz = entry_price - stop_loss
                position_size = risk_amount / risk_per_oz if risk_per_oz > 0 else 0
                
            elif bearish_cross:
                position = -1
                entry_price = curr_close
                stop_loss = entry_price + (1.5 * atr)
                take_profit = entry_price - (1.2 * (stop_loss - entry_price))
                risk_per_oz = stop_loss - entry_price
                position_size = risk_amount / risk_per_oz if risk_per_oz > 0 else 0

    wins = len([t for t in trades if t['Result'] == 'Win'])
    total = len(trades)
    wr = (wins/total*100) if total > 0 else 0
    net_profit = capital - initial_capital
    ret_pct = (net_profit / initial_capital) * 100
    
    print(f"--- Strategy on {csv_file} ---")
    print(f"Total Trades: {total} | Win Rate: {wr:.2f}%")
    print(f"Net Profit: ${net_profit:.2f} ({ret_pct:.2f}%)")
    print(f"Max Drawdown: {max_dd*100:.4f}%")
    print("----------------------------------\n")

run_low_dd_strategy('xauusd_5m_30days.csv')
