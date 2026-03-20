import requests
import pandas as pd
from datetime import datetime, timedelta
import concurrent.futures
import time

def fetch_chunk(start_time, end_time):
    # Fetch 1m data instead since 1m gives 1000 candles per call
    # WAIT: User wants 30 SECOND data. We MUST fetch 1s data and group by 30s.
    # 1s limit is 1000 per call = 1000 seconds = 16.6 minutes per API call.
    # 7 days = 604,800 seconds = 605 calls.
    all_k = []
    curr = start_time
    while curr < end_time:
        url = f"https://api.binance.com/api/v3/klines?symbol=PAXGUSDT&interval=1s&startTime={curr}&limit=1000"
        try:
            res = requests.get(url, timeout=10)
            data = res.json()
            if not data or 'code' in data: break
            all_k.extend(data)
            curr = data[-1][0] + 1
        except:
            pass
    return all_k

# Parallel download
end_ts = int(time.time() * 1000)
# Let's do 5 days of 30-second data
start_ts = int((datetime.now() - timedelta(days=5)).timestamp() * 1000)

chunk_size = 12 * 60 * 60 * 1000 # 12 hours chunks
ranges = []
c = start_ts
while c < end_ts:
    nxt = min(c + chunk_size, end_ts)
    ranges.append((c, nxt))
    c = nxt

print(f"Downloading 5 days of 1-sec data in {len(ranges)} parallel chunks...")
results = []
with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
    futures = [executor.submit(fetch_chunk, r[0], r[1]) for r in ranges]
    for future in concurrent.futures.as_completed(futures):
        results.extend(future.result())

df = pd.DataFrame(results, columns=['open_time', 'open', 'high', 'low', 'close', 'v', 'ct', 'q', 'n', 'tb', 'tq', 'i'])
df['open_time'] = pd.to_datetime(df['open_time'], unit='ms')
df = df[['open_time', 'open', 'high', 'low', 'close']].astype(float)

df.set_index('open_time', inplace=True)
print(f"Downloaded {len(df)} 1s candles.")

# Group by 30 seconds
df_30s = df.resample('30S').agg({
    'open': 'first',
    'high': 'max',
    'low': 'min',
    'close': 'last'
}).dropna()

df_30s.reset_index(inplace=True)
print(f"Aggregated into {len(df_30s)} 30-second candles.")

# HA
ha_close = (df_30s['open'] + df_30s['high'] + df_30s['low'] + df_30s['close']) / 4
ha_open = [(df_30s['open'].iloc[0] + df_30s['close'].iloc[0]) / 2]
for i in range(1, len(df_30s)):
    ha_open.append((ha_open[i-1] + ha_close.iloc[i-1]) / 2)

df_30s['ha_close'] = ha_close
df_30s['ha_open'] = ha_open
df_30s['ha_color'] = df_30s.apply(lambda row: 'Green' if row['ha_close'] > row['ha_open'] else 'Red', axis=1)

MAX_CANDLE_SIZE = 25.0
position = None
entry_price = 0.0
trades = []

for i in range(1, len(df_30s)):
    prev_color = df_30s['ha_color'].iloc[i-1]
    curr_color = df_30s['ha_color'].iloc[i]
    curr_high = df_30s['high'].iloc[i]
    curr_low = df_30s['low'].iloc[i]
    curr_close = df_30s['close'].iloc[i]
    curr_time = df_30s['open_time'].iloc[i]
    
    ist_minute_total = (curr_time.hour * 60 + curr_time.minute + 330) % 1440
    
    # TRADING SESSION: 5:00 PM (1020 mins) to 2:00 AM (120 mins) IST
    is_allowed = (ist_minute_total >= 1020) or (ist_minute_total < 120)
    
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
            
    if position is None and is_allowed and not is_oversized:
        if buy_signal:
            position = 'Long'
            entry_price = curr_close
        elif sell_signal:
            position = 'Short'
            entry_price = curr_close

winning_trades = len([t for t in trades if t > 0])
total_trades = len(trades)
win_rate = (winning_trades / total_trades * 100) if total_trades else 0
total_pnl = sum(trades)

with open('backtest_30s_results.md', 'w') as f:
    f.write(f"# XAUUSD 30-Second HA Strategy (5 PM - 2 AM IST)\n\n")
    f.write(f"**Data Period**: Last 5 Days (30-second candles synthesized from 1-second Binance ticks)\n")
    f.write(f"**Strategy**: Pure Heikin Ashi Color Change\n")
    f.write(f"**Filter 1**: Candle size > 25 points ($25.0) -> Exit current position, NO new entry.\n")
    f.write(f"**Filter 2 (Time)**: ONLY trade between **5:00 PM IST and 2:00 AM IST** (New York Session Overlap).\n\n")
    f.write(f"## Performance Summary\n")
    f.write(f"- **Total Trades**: {total_trades}\n")
    f.write(f"- **Winning Trades**: {winning_trades}\n")
    f.write(f"- **Win Rate**: {win_rate:.2f}%\n")
    f.write(f"- **Net PnL (in USD terms per 1 oz)**: ${total_pnl:.2f}\n")

print(f"30s Backtest complete. Trades: {total_trades} | Win Rate: {win_rate:.2f}% | PnL: ${total_pnl:.2f}")

