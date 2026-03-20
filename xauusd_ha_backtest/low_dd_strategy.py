import pandas as pd
import numpy as np

def run_low_dd_strategy(csv_file):
    df = pd.read_csv(csv_file)
    df['open_time'] = pd.to_datetime(df['open_time'])
    df.set_index('open_time', inplace=True)
    
    # Calculate indicators
    # Using a fast moving average crossover with ATR for stop loss, but optimized for absolute safety
    df['EMA_10'] = df['close'].ewm(span=10, adjust=False).mean()
    df['EMA_50'] = df['close'].ewm(span=50, adjust=False).mean()
    
    # ATR for volatility-adjusted stop loss
    df['tr0'] = abs(df['high'] - df['low'])
    df['tr1'] = abs(df['high'] - df['close'].shift())
    df['tr2'] = abs(df['low'] - df['close'].shift())
    df['tr'] = df[['tr0', 'tr1', 'tr2']].max(axis=1)
    df['ATR'] = df['tr'].rolling(window=14).mean()
    
    # Initial Capital
    initial_capital = 10000.0
    capital = initial_capital
    peak_capital = initial_capital
    max_dd = 0.0
    
    position = 0 # 1 for Long, -1 for Short
    entry_price = 0.0
    stop_loss = 0.0
    take_profit = 0.0
    
    # We will risk exactly 0.1% of capital per trade to keep DD under 1% total
    risk_per_trade_percent = 0.001
    
    trades = []
    
    for i in range(50, len(df)):
        curr_close = df['close'].iloc[i]
        curr_high = df['high'].iloc[i]
        curr_low = df['low'].iloc[i]
        
        # Check active position exits (Intraday execution simulation)
        if position == 1: # Long
            if curr_low <= stop_loss:
                # Hit Stop Loss
                loss_per_oz = stop_loss - entry_price
                capital += (loss_per_oz * position_size)
                trades.append({'Type': 'Long', 'Result': 'Loss', 'PnL': loss_per_oz * position_size})
                position = 0
            elif curr_high >= take_profit:
                # Hit Take Profit
                profit_per_oz = take_profit - entry_price
                capital += (profit_per_oz * position_size)
                trades.append({'Type': 'Long', 'Result': 'Win', 'PnL': profit_per_oz * position_size})
                position = 0
        elif position == -1: # Short
            if curr_high >= stop_loss:
                # Hit Stop Loss
                loss_per_oz = entry_price - stop_loss
                capital += (loss_per_oz * position_size)
                trades.append({'Type': 'Short', 'Result': 'Loss', 'PnL': loss_per_oz * position_size})
                position = 0
            elif curr_low <= take_profit:
                # Hit Take Profit
                profit_per_oz = entry_price - take_profit
                capital += (profit_per_oz * position_size)
                trades.append({'Type': 'Short', 'Result': 'Win', 'PnL': profit_per_oz * position_size})
                position = 0
                
        # Update Drawdown
        if capital > peak_capital:
            peak_capital = capital
        current_dd = (peak_capital - capital) / peak_capital
        if current_dd > max_dd:
            max_dd = current_dd
            
        # Entry Logic (Only if flat and avoiding massive volatility)
        if position == 0:
            ema10 = df['EMA_10'].iloc[i]
            ema50 = df['EMA_50'].iloc[i]
            ema10_prev = df['EMA_10'].iloc[i-1]
            ema50_prev = df['EMA_50'].iloc[i-1]
            atr = df['ATR'].iloc[i]
            
            # Very tight spread condition - avoid entering during high chop
            if pd.isna(atr): continue
            
            # Trend following crossover
            bullish_cross = (ema10 > ema50) and (ema10_prev <= ema50_prev)
            bearish_cross = (ema10 < ema50) and (ema10_prev >= ema50_prev)
            
            risk_amount = capital * risk_per_trade_percent
            
            if bullish_cross:
                position = 1
                entry_price = curr_close
                # Tight Stop Loss: 1.5 * ATR
                stop_loss = entry_price - (1.5 * atr)
                # Take profit: 1.5 Reward/Risk
                take_profit = entry_price + (1.5 * (entry_price - stop_loss))
                # Calculate size to risk exactly the risk_amount
                risk_per_oz = entry_price - stop_loss
                position_size = risk_amount / risk_per_oz if risk_per_oz > 0 else 0
                
            elif bearish_cross:
                position = -1
                entry_price = curr_close
                stop_loss = entry_price + (1.5 * atr)
                take_profit = entry_price - (1.5 * (stop_loss - entry_price))
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
    print(f"Max Drawdown: {max_dd*100:.2f}%")
    print("----------------------------------\n")

run_low_dd_strategy('xauusd_5m_30days.csv')
