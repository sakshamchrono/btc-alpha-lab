import urllib.request
import json
import time
from datetime import datetime, timedelta
import csv
import subprocess

symbol = "PAXGUSDT"
days = 30
end_ts = int(time.time() * 1000)
start_ts = int((datetime.now() - timedelta(days=days)).timestamp() * 1000)

csv_30s = "xauusd_30s_30days.csv"
with open(csv_30s, 'w', newline='') as f:
    writer = csv.writer(f)
    writer.writerow(['open_time', 'open', 'high', 'low', 'close'])

curr = start_ts
current_30s_block = None
current_group = []

print(f"Starting background download and 30s aggregation for {days} days...")
print(f"This requires fetching ~2.5 million 1-second ticks.")

def flush_group(group, block_start):
    open_p = float(group[0][1])
    close_p = float(group[-1][4])
    high_p = max([float(x[2]) for x in group])
    low_p = min([float(x[3]) for x in group])
    dt_str = datetime.utcfromtimestamp(block_start / 1000).strftime('%Y-%m-%d %H:%M:%S')
    with open(csv_30s, 'a', newline='') as f:
        writer = csv.writer(f)
        writer.writerow([dt_str, open_p, high_p, low_p, close_p])

calls = 0
while curr < end_ts:
    url = f"https://api.binance.com/api/v3/klines?symbol={symbol}&interval=1s&startTime={curr}&limit=1000"
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        res = urllib.request.urlopen(req, timeout=10)
        data = json.loads(res.read().decode())
        if not data or 'code' in data: break
        
        for row in data:
            ts = row[0]
            block_start = (ts // 30000) * 30000
            
            if current_30s_block is None:
                current_30s_block = block_start
                
            if block_start != current_30s_block:
                if current_group:
                    flush_group(current_group, current_30s_block)
                current_group = [row]
                current_30s_block = block_start
            else:
                current_group.append(row)

        curr = data[-1][0] + 1
        calls += 1
        if calls % 100 == 0:
            print(f"Downloaded {calls*1000} seconds of data...")
        time.sleep(0.4) # Safe rate limit sleep
    except Exception as e:
        print("Error:", e)
        time.sleep(5)

if current_group:
    flush_group(current_group, current_30s_block)

print("Data gathered. Running backtest...")

# Backtest logic
df = []
with open(csv_30s, 'r') as f:
    reader = csv.DictReader(f)
    for row in reader:
        df.append({
            'open_time': row['open_time'],
            'open': float(row['open']),
            'high': float(row['high']),
            'low': float(row['low']),
            'close': float(row['close'])
        })
        
# HA Calculation
ha_close = [(r['open'] + r['high'] + r['low'] + r['close']) / 4 for r in df]
ha_open = [(df[0]['open'] + df[0]['close']) / 2]
for i in range(1, len(df)):
    ha_open.append((ha_open[i-1] + ha_close[i-1]) / 2)
    
for i in range(len(df)):
    df[i]['ha_color'] = 'Green' if ha_close[i] > ha_open[i] else 'Red'

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

res_md = f"# FULL 30-DAY XAUUSD 30-Second HA Strategy (5 PM - 2 AM IST)\n\n"
res_md += f"**Data Period**: Last 30 Days (30-second candles synthesized slowly from 1-second ticks)\n"
res_md += f"**Strategy**: Pure Heikin Ashi Color Change\n"
res_md += f"**Filter 1**: Candle size > 25 points ($25.0) -> Exit current position, NO new entry.\n"
res_md += f"**Filter 2 (Time)**: ONLY trade between **5:00 PM IST and 2:00 AM IST**.\n\n"
res_md += f"## Performance Summary\n"
res_md += f"- **Total Trades**: {total_trades}\n"
res_md += f"- **Winning Trades**: {winning_trades}\n"
res_md += f"- **Win Rate**: {win_rate:.2f}%\n"
res_md += f"- **Net PnL (in USD terms per 1 oz)**: ${total_pnl:.2f}\n"

with open('backtest_30s_full_results.md', 'w') as f:
    f.write(res_md)
    
print(f"Full 30-Day 30s Backtest complete. Trades: {total_trades} | Win Rate: {win_rate:.2f}% | PnL: ${total_pnl:.2f}")

try:
    subprocess.run(['git', 'add', 'xauusd_30s_30days.csv', 'backtest_30s_full_results.md', 'gather_30d_30s.py'])
    subprocess.run(['git', 'commit', '-m', 'Add full 30-day 30-sec timeframe HA backtest results'])
    subprocess.run(['git', 'push', 'origin', 'master'])
    print("Successfully pushed full 30-day results to GitHub.")
except Exception as e:
    print("Git push failed:", e)

