import requests
import pandas as pd
import time
from datetime import datetime, timedelta
import sys

# We use Binance PAXGUSDT (PAX Gold) as a proxy for spot Gold. It perfectly tracks 1oz Gold and allows downloading exact 3m intervals for 30 days.
symbol = "PAXGUSDT"
interval = "3m"
limit = 1000

end_time = int(time.time() * 1000)
start_time = int((datetime.now() - timedelta(days=30)).timestamp() * 1000)

all_klines = []
current_start = start_time

print("Downloading 30 days of 3m Gold data...")
while current_start < end_time:
    url = f"https://api.binance.com/api/v3/klines?symbol={symbol}&interval={interval}&startTime={current_start}&limit={limit}"
    try:
        res = requests.get(url)
        data = res.json()
        if not data:
            break
        all_klines.extend(data)
        current_start = data[-1][0] + 1
        time.sleep(0.1)
    except Exception as e:
        print("Error fetching data:", e)
        sys.exit(1)

df = pd.DataFrame(all_klines, columns=['open_time', 'open', 'high', 'low', 'close', 'volume', 'close_time', 'qav', 'num_trades', 'taker_base_vol', 'taker_quote_vol', 'ignore'])
df['open_time'] = pd.to_datetime(df['open_time'], unit='ms')
df = df[['open_time', 'open', 'high', 'low', 'close']].astype({'open': float, 'high': float, 'low': float, 'close': float})
df.to_csv('xauusd_3m_30days.csv', index=False)
print(f"Downloaded {len(df)} candles.")

# Calculate HA
ha_close = (df['open'] + df['high'] + df['low'] + df['close']) / 4
ha_open = [ (df['open'].iloc[0] + df['close'].iloc[0]) / 2 ]

for i in range(1, len(df)):
    ha_open.append( (ha_open[i-1] + ha_close.iloc[i-1]) / 2 )

df['ha_close'] = ha_close
df['ha_open'] = ha_open
df['ha_high'] = df[['high', 'ha_open', 'ha_close']].max(axis=1)
df['ha_low'] = df[['low', 'ha_open', 'ha_close']].min(axis=1)

df['ha_color'] = df.apply(lambda row: 'Green' if row['ha_close'] > row['ha_open'] else 'Red', axis=1)

# Strategy rules
MAX_CANDLE_SIZE = 2.5 # Assuming 25 points = 250 pips = $2.5 move in Gold

position = None
entry_price = 0.0
entry_time = None
trades = []

for i in range(1, len(df)):
    prev_color = df['ha_color'].iloc[i-1]
    curr_color = df['ha_color'].iloc[i]

    curr_high = df['high'].iloc[i]
    curr_low = df['low'].iloc[i]
    curr_close = df['close'].iloc[i]
    curr_time = df['open_time'].iloc[i]

    candle_size = curr_high - curr_low

    buy_signal = (prev_color == 'Red') and (curr_color == 'Green')
    sell_signal = (prev_color == 'Green') and (curr_color == 'Red')

    is_oversized = candle_size > MAX_CANDLE_SIZE

    # Check Exits
    if position == 'Long' and sell_signal:
        pnl = curr_close - entry_price
        trades.append({'Type': 'Long', 'Entry_Time': str(entry_time), 'Entry_Price': entry_price, 'Exit_Time': str(curr_time), 'Exit_Price': curr_close, 'PnL': pnl, 'Oversized_Exit': is_oversized})
        position = None

    elif position == 'Short' and buy_signal:
        pnl = entry_price - curr_close
        trades.append({'Type': 'Short', 'Entry_Time': str(entry_time), 'Entry_Price': entry_price, 'Exit_Time': str(curr_time), 'Exit_Price': curr_close, 'PnL': pnl, 'Oversized_Exit': is_oversized})
        position = None

    # Check Entries
    if position is None:
        if buy_signal and not is_oversized:
            position = 'Long'
            entry_price = curr_close
            entry_time = curr_time
        elif sell_signal and not is_oversized:
            position = 'Short'
            entry_price = curr_close
            entry_time = curr_time

# Summary
total_trades = len(trades)
winning_trades = len([t for t in trades if t['PnL'] > 0])
losing_trades = len([t for t in trades if t['PnL'] <= 0])
win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0
total_pnl = sum([t['PnL'] for t in trades])

with open('backtest_results.md', 'w') as f:
    f.write("# XAUUSD 3-Minute Heikin Ashi Strategy Backtest\n\n")
    f.write(f"**Data Period**: Last 30 Days (3-minute candles)\n")
    f.write(f"**Filter applied**: Candle size > 25 points ($2.5) -> Exit but no entry.\n\n")
    f.write("## Performance Summary\n")
    f.write(f"- **Total Trades**: {total_trades}\n")
    f.write(f"- **Winning Trades**: {winning_trades}\n")
    f.write(f"- **Losing Trades**: {losing_trades}\n")
    f.write(f"- **Win Rate**: {win_rate:.2f}%\n")
    f.write(f"- **Net PnL (in USD terms per 1 oz)**: ${total_pnl:.2f}\n\n")
    f.write("## Sample of Last 10 Trades\n")
    f.write("| Type | Entry Time | Entry Price | Exit Time | Exit Price | PnL | Oversized Exit |\n")
    f.write("|---|---|---|---|---|---|---|\n")
    for t in trades[-10:]:
        f.write(f"| {t['Type']} | {t['Entry_Time']} | {t['Entry_Price']:.2f} | {t['Exit_Time']} | {t['Exit_Price']:.2f} | {t['PnL']:.2f} | {t['Oversized_Exit']} |\n")
print("Backtest complete. Results saved to backtest_results.md")

