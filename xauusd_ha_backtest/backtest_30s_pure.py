import urllib.request
import json
import concurrent.futures
import time
from datetime import datetime, timedelta

def fetch_chunk(start_ts, end_ts):
    all_k = []
    curr = start_ts
    while curr < end_ts:
        url = f"https://api.binance.com/api/v3/klines?symbol=PAXGUSDT&interval=1s&startTime={curr}&limit=1000"
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            res = urllib.request.urlopen(req, timeout=10)
            data = json.loads(res.read().decode())
            if not data or 'code' in data: break
            all_k.extend(data)
            curr = data[-1][0] + 1
        except Exception as e:
            print("Error chunk:", e)
            break
    return all_k

days = 5
end_ts = int(time.time() * 1000)
start_ts = int((datetime.now() - timedelta(days=days)).timestamp() * 1000)

chunk_size = 4 * 60 * 60 * 1000 # 4 hours chunks for more parallel workers
ranges = []
c = start_ts
while c < end_ts:
    nxt = min(c + chunk_size, end_ts)
    ranges.append((c, nxt))
    c = nxt

print(f"Downloading {days} days of 1-sec data in {len(ranges)} parallel chunks...")
results = []
with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
    futures = [executor.submit(fetch_chunk, r[0], r[1]) for r in ranges]
    for future in concurrent.futures.as_completed(futures):
        results.extend(future.result())

print(f"Downloaded {len(results)} 1s candles. Aggregating to 30s...")

# Sort by timestamp
results.sort(key=lambda x: x[0])

df_30s = []
current_group = []
current_30s_start = None

for row in results:
    ts = row[0]
    
    # 30 seconds block = ts // 30000 * 30000
    block_start = (ts // 30000) * 30000
    
    if current_30s_start is None:
        current_30s_start = block_start
        
    if block_start != current_30s_start:
        if current_group:
            open_p = float(current_group[0][1])
            close_p = float(current_group[-1][4])
            high_p = max([float(x[2]) for x in current_group])
            low_p = min([float(x[3]) for x in current_group])
            dt_str = datetime.utcfromtimestamp(current_30s_start / 1000).strftime('%Y-%m-%d %H:%M:%S')
            
            df_30s.append({
                'open_time': dt_str,
                'open': open_p,
                'high': high_p,
                'low': low_p,
                'close': close_p
            })
        current_group = [row]
        current_30s_start = block_start
    else:
        current_group.append(row)

# Last group
if current_group:
    open_p = float(current_group[0][1])
    close_p = float(current_group[-1][4])
    high_p = max([float(x[2]) for x in current_group])
    low_p = min([float(x[3]) for x in current_group])
    dt_str = datetime.utcfromtimestamp(current_30s_start / 1000).strftime('%Y-%m-%d %H:%M:%S')
    
    df_30s.append({
        'open_time': dt_str,
        'open': open_p,
        'high': high_p,
        'low': low_p,
        'close': close_p
    })

print(f"Aggregated into {len(df_30s)} 30-second candles.")

# HA
ha_close = [(r['open'] + r['high'] + r['low'] + r['close']) / 4 for r in df_30s]
ha_open = [(df_30s[0]['open'] + df_30s[0]['close']) / 2]

for i in range(1, len(df_30s)):
    ha_open.append((ha_open[i-1] + ha_close[i-1]) / 2)

for i in range(len(df_30s)):
    df_30s[i]['ha_close'] = ha_close[i]
    df_30s[i]['ha_open'] = ha_open[i]
    df_30s[i]['ha_color'] = 'Green' if ha_close[i] > ha_open[i] else 'Red'

MAX_CANDLE_SIZE = 25.0
position = None
entry_price = 0.0
trades = []

for i in range(1, len(df_30s)):
    prev_color = df_30s[i-1]['ha_color']
    curr_color = df_30s[i]['ha_color']
    curr_high = df_30s[i]['high']
    curr_low = df_30s[i]['low']
    curr_close = df_30s[i]['close']
    
    dt_obj = datetime.strptime(df_30s[i]['open_time'], "%Y-%m-%d %H:%M:%S")
    
    # IST calculation
    ist_minute_total = (dt_obj.hour * 60 + dt_obj.minute + 330) % 1440
    
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
    f.write(f"**Data Period**: Last {days} Days (30-second candles synthesized from 1-second Binance ticks)\n")
    f.write(f"**Strategy**: Pure Heikin Ashi Color Change\n")
    f.write(f"**Filter 1**: Candle size > 25 points ($25.0) -> Exit current position, NO new entry.\n")
    f.write(f"**Filter 2 (Time)**: ONLY trade between **5:00 PM IST and 2:00 AM IST** (New York Session Overlap).\n\n")
    f.write(f"## Performance Summary\n")
    f.write(f"- **Total Trades**: {total_trades}\n")
    f.write(f"- **Winning Trades**: {winning_trades}\n")
    f.write(f"- **Win Rate**: {win_rate:.2f}%\n")
    f.write(f"- **Net PnL (in USD terms per 1 oz)**: ${total_pnl:.2f}\n")

print(f"30s Backtest complete. Trades: {total_trades} | Win Rate: {win_rate:.2f}% | PnL: ${total_pnl:.2f}")

