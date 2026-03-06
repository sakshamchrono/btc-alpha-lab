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

async function fetchInterval(interval) {
    const symbol = "PAXGUSDT"; 
    const limit = 1000;
    const end_time = Date.now();
    let current_start = Date.now() - (30 * 24 * 60 * 60 * 1000);
    let all_klines = [];
    console.log(`Downloading 30 days of ${interval} Gold data...`);
    while (current_start < end_time) {
        let data = await getBinanceData(symbol, interval, current_start, limit);
        if (!data || data.length === 0 || data.code) break;
        all_klines.push(...data);
        current_start = data[data.length - 1][0] + 1;
        await new Promise(r => setTimeout(r, 50)); 
    }
    return all_klines.map(k => ({
        timestamp: k[0],
        open_time: new Date(k[0]).toISOString().replace('T', ' ').substring(0, 19),
        open: parseFloat(k[1]),
        high: parseFloat(k[2]),
        low: parseFloat(k[3]),
        close: parseFloat(k[4])
    }));
}

function runStrategy(df, timeframeLabel) {
    let csvContent = "open_time,open,high,low,close\n" + df.map(row => `${row.open_time},${row.open},${row.high},${row.low},${row.close}`).join("\n");
    fs.writeFileSync(`xauusd_${timeframeLabel}_30days.csv`, csvContent);

    let ha_close = df.map(row => (row.open + row.high + row.low + row.close) / 4);
    let ha_open = [(df[0].open + df[0].close) / 2];
    for (let i = 1; i < df.length; i++) {
        ha_open.push((ha_open[i-1] + ha_close[i-1]) / 2);
    }
    for (let i = 0; i < df.length; i++) {
        df[i].ha_close = ha_close[i];
        df[i].ha_open = ha_open[i];
        df[i].ha_color = df[i].ha_close > df[i].ha_open ? 'Green' : 'Red';
    }

    const MAX_CANDLE_SIZE = 25.0; 
    let position = null;
    let entry_price = 0.0;
    let entry_time = null;
    let trades = [];
    
    for (let i = 1; i < df.length; i++) {
        let prev_color = df[i-1].ha_color;
        let curr_color = df[i].ha_color;
        let curr_high = df[i].high;
        let curr_low = df[i].low;
        let curr_close = df[i].close;
        let curr_time = df[i].open_time; 
        
        let d = new Date(curr_time + "Z");
        let utc_hour = d.getUTCHours();
        let utc_minute = d.getUTCMinutes();
        let ist_minute_total = (utc_hour * 60 + utc_minute + 330) % 1440;
        
        let is_blockout = false;
        if ((ist_minute_total >= 135 && ist_minute_total < 270) || 
            (ist_minute_total >= 555 && ist_minute_total < 660)) {
            is_blockout = true;
        }
        
        let candle_size = curr_high - curr_low;
        let buy_signal = (prev_color === 'Red') && (curr_color === 'Green');
        let sell_signal = (prev_color === 'Green') && (curr_color === 'Red');
        let is_oversized = candle_size > MAX_CANDLE_SIZE;

        if (position === 'Long' && sell_signal) {
            trades.push({Type: 'Long', Entry_Time: entry_time, Entry_Price: entry_price, Exit_Time: curr_time, Exit_Price: curr_close, PnL: curr_close - entry_price, Reason: is_oversized ? "Oversized_Opposite" : "Signal_Opposite"});
            position = null;
        } else if (position === 'Short' && buy_signal) {
            trades.push({Type: 'Short', Entry_Time: entry_time, Entry_Price: entry_price, Exit_Time: curr_time, Exit_Price: curr_close, PnL: entry_price - curr_close, Reason: is_oversized ? "Oversized_Opposite" : "Signal_Opposite"});
            position = null;
        }
        
        if (position === null && !is_blockout && !is_oversized) {
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
    
    let md = `# XAUUSD ${timeframeLabel} HA Strategy (IST Blockout Filtered)\n\n`;
    md += `**Data Period**: Last 30 Days (${timeframeLabel} candles)\n`;
    md += `**Strategy**: Pure Heikin Ashi Color Change (Red to Green = Buy, Green to Red = Sell)\n`;
    md += `**Filter 1**: Candle size > 25 points ($25.0) -> Exit current position, but NO new entry.\n`;
    md += `**Filter 2 (Time)**: NO new entries during IST blockouts (02:15 AM - 04:30 AM AND 09:15 AM - 11:00 AM).\n\n`;
    md += `## Performance Summary\n`;
    md += `- **Total Trades**: ${trades.length}\n`;
    md += `- **Winning Trades**: ${winning_trades}\n`;
    md += `- **Losing Trades**: ${losing_trades}\n`;
    md += `- **Win Rate**: ${win_rate.toFixed(2)}%\n`;
    md += `- **Net PnL (in USD terms per 1 oz)**: $${total_pnl.toFixed(2)}\n\n`;
    
    md += `## Sample of Last 10 Trades\n`;
    md += `| Type | Entry Time (UTC) | Entry Price | Exit Time (UTC) | Exit Price | PnL | Reason |\n|---|---|---|---|---|---|---|\n`;
    trades.slice(-10).forEach(t => {
        md += `| ${t.Type} | ${t.Entry_Time} | ${t.Entry_Price.toFixed(2)} | ${t.Exit_Time} | ${t.Exit_Price.toFixed(2)} | ${t.PnL.toFixed(2)} | ${t.Reason} |\n`;
    });
    
    fs.writeFileSync(`backtest_${timeframeLabel}_results.md`, md);
    console.log(`${timeframeLabel} Backtest complete. Trades: ${trades.length} | Win Rate: ${win_rate.toFixed(2)}% | PnL: $${total_pnl.toFixed(2)}`);
}

async function runAll() {
    // 5m
    let df_5m = await fetchInterval("5m");
    runStrategy(df_5m, "5m");

    // 10m (Synthesize from 5m because Binance API doesn't have native 10m)
    let df_10m = [];
    for (let i = 0; i < df_5m.length - 1; i += 2) {
        let k1 = df_5m[i];
        let k2 = df_5m[i+1];
        df_10m.push({
            timestamp: k1.timestamp,
            open_time: k1.open_time,
            open: k1.open,
            high: Math.max(k1.high, k2.high),
            low: Math.min(k1.low, k2.low),
            close: k2.close
        });
    }
    console.log(`Generated ${df_10m.length} candles for 10m.`);
    runStrategy(df_10m, "10m");

    // 15m
    let df_15m = await fetchInterval("15m");
    runStrategy(df_15m, "15m");
}

runAll();
