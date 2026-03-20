const fs = require('fs');
const https = require('https');

function getBinanceData(symbol, interval, startTime, limit) {
    return new Promise((resolve, reject) => {
        const url = `https://api.binance.com/api/v3/klines?symbol=${symbol}&interval=${interval}&startTime=${startTime}&limit=${limit}`;
        https.get(url, (res) => {
            let data = '';
            res.on('data', chunk => data += chunk);
            res.on('end', () => {
                try { resolve(JSON.parse(data)); } 
                catch(e) { resolve([]); }
            });
        }).on('error', reject);
    });
}

async function run() {
    const symbol = "PAXGUSDT"; 
    const interval = "1s"; // We will fetch 1s and aggregate to 30s
    const limit = 1000;
    
    // 7 days of 1-second data = 604,800 rows (605 API calls). 30 days is 2,592 calls. 
    // To respect rate limits and memory, let's do 7 days.
    const days = 7;
    const end_time = Date.now();
    let current_start = Date.now() - (days * 24 * 60 * 60 * 1000);
    
    let all_klines = [];
    console.log(`Downloading ${days} days of 1s Gold data to synthesize 30s candles...`);
    
    let call_count = 0;
    while (current_start < end_time) {
        let data = await getBinanceData(symbol, interval, current_start, limit);
        if (!data || data.length === 0 || data.code) break;
        all_klines.push(...data);
        current_start = data[data.length - 1][0] + 1;
        
        call_count++;
        if (call_count % 100 === 0) console.log(`Downloaded ${all_klines.length} 1-second candles...`);
        
        await new Promise(r => setTimeout(r, 20)); // Prevent 429 Too Many Requests
    }
    console.log(`Finished downloading ${all_klines.length} 1s candles.`);
    
    // Aggregate 1s into 30s
    let df_30s = [];
    for (let i = 0; i < all_klines.length; i += 30) {
        let chunk = all_klines.slice(i, i + 30);
        if (chunk.length === 0) continue;
        
        let open = parseFloat(chunk[0][1]);
        let close = parseFloat(chunk[chunk.length - 1][4]);
        let high = -Infinity;
        let low = Infinity;
        
        for (let j = 0; j < chunk.length; j++) {
            let h = parseFloat(chunk[j][2]);
            let l = parseFloat(chunk[j][3]);
            if (h > high) high = h;
            if (l < low) low = l;
        }
        
        df_30s.push({
            open_time: new Date(chunk[0][0]).toISOString().replace('T', ' ').substring(0, 19),
            timestamp: chunk[0][0],
            open: open,
            high: high,
            low: low,
            close: close
        });
    }
    
    console.log(`Aggregated into ${df_30s.length} 30-second candles.`);

    // HA Calculation
    let ha_close = df_30s.map(row => (row.open + row.high + row.low + row.close) / 4);
    let ha_open = [(df_30s[0].open + df_30s[0].close) / 2];
    
    for (let i = 1; i < df_30s.length; i++) {
        ha_open.push((ha_open[i-1] + ha_close[i-1]) / 2);
    }
    
    for (let i = 0; i < df_30s.length; i++) {
        df_30s[i].ha_close = ha_close[i];
        df_30s[i].ha_open = ha_open[i];
        df_30s[i].ha_color = df_30s[i].ha_close > df_30s[i].ha_open ? 'Green' : 'Red';
    }

    const MAX_CANDLE_SIZE = 25.0; 
    let position = null;
    let entry_price = 0.0;
    let entry_time = null;
    let trades = [];
    
    for (let i = 1; i < df_30s.length; i++) {
        let prev_color = df_30s[i-1].ha_color;
        let curr_color = df_30s[i].ha_color;
        let curr_high = df_30s[i].high;
        let curr_low = df_30s[i].low;
        let curr_close = df_30s[i].close;
        let curr_time = df_30s[i].open_time; 
        
        let d = new Date(curr_time + "Z");
        let utc_hour = d.getUTCHours();
        let utc_minute = d.getUTCMinutes();
        let ist_minute_total = (utc_hour * 60 + utc_minute + 330) % 1440;
        
        // 5 PM IST (17:00) = 1020 mins
        // 2 AM IST (02:00) = 120 mins
        // Trading ONLY allowed between 5 PM and 2 AM IST.
        // This means it crosses midnight.
        // So allowed if ist_minute_total >= 1020 OR ist_minute_total < 120.
        let is_allowed_session = (ist_minute_total >= 1020 || ist_minute_total < 120);
        
        let candle_size = curr_high - curr_low;
        let buy_signal = (prev_color === 'Red') && (curr_color === 'Green');
        let sell_signal = (prev_color === 'Green') && (curr_color === 'Red');
        let is_oversized = candle_size > MAX_CANDLE_SIZE;

        if (position === 'Long') {
            if (sell_signal) {
                trades.push({Type: 'Long', Entry_Time: entry_time, Entry_Price: entry_price, Exit_Time: curr_time, Exit_Price: curr_close, PnL: curr_close - entry_price, Reason: is_oversized ? "Oversized_Opposite" : "Signal_Opposite"});
                position = null;
            }
        } else if (position === 'Short') {
            if (buy_signal) {
                trades.push({Type: 'Short', Entry_Time: entry_time, Entry_Price: entry_price, Exit_Time: curr_time, Exit_Price: curr_close, PnL: entry_price - curr_close, Reason: is_oversized ? "Oversized_Opposite" : "Signal_Opposite"});
                position = null;
            }
        }
        
        // Entry only during 5 PM to 2 AM IST
        if (position === null && is_allowed_session && !is_oversized) {
            if (buy_signal) {
                position = 'Long';
                entry_price = curr_close;
                entry_time = curr_time;
            } else if (sell_signal) {
                position = 'Short';
                entry_price = curr_close;
                entry_time = curr_time;
            }
        }
    }
    
    let winning_trades = trades.filter(t => t.PnL > 0).length;
    let losing_trades = trades.filter(t => t.PnL <= 0).length;
    let win_rate = trades.length > 0 ? (winning_trades / trades.length * 100) : 0;
    let total_pnl = trades.reduce((sum, t) => sum + t.PnL, 0);
    
    let md = `# XAUUSD 30-Second HA Strategy\n\n`;
    md += `**Data Period**: Last ${days} Days (30-second candles, synthesized from 1-second ticks)\n`;
    md += `**Strategy**: Pure Heikin Ashi Color Change\n`;
    md += `**Filter 1**: Candle size > 25 points ($25.0) -> Exit current position, NO new entry.\n`;
    md += `**Filter 2 (Time)**: ONLY trade between **5:00 PM IST and 2:00 AM IST** (New York Session Overlap).\n\n`;
    md += `## Performance Summary\n`;
    md += `- **Total Trades**: ${trades.length}\n`;
    md += `- **Winning Trades**: ${winning_trades}\n`;
    md += `- **Losing Trades**: ${losing_trades}\n`;
    md += `- **Win Rate**: ${win_rate.toFixed(2)}%\n`;
    md += `- **Net PnL (in USD terms per 1 oz)**: $${total_pnl.toFixed(2)}\n\n`;
    
    fs.writeFileSync(`backtest_30s_results.md`, md);
    console.log(`30s Backtest complete. Trades: ${trades.length} | Win Rate: ${win_rate.toFixed(2)}% | PnL: $${total_pnl.toFixed(2)}`);
}

run();
