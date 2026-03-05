const fs = require('fs');
const https = require('https');

function getBinanceData(symbol, interval, startTime, limit) {
    return new Promise((resolve, reject) => {
        const url = `https://api.binance.com/api/v3/klines?symbol=${symbol}&interval=${interval}&startTime=${startTime}&limit=${limit}`;
        https.get(url, (res) => {
            let data = '';
            res.on('data', chunk => data += chunk);
            res.on('end', () => resolve(JSON.parse(data)));
        }).on('error', reject);
    });
}

async function run() {
    const symbol = "PAXGUSDT"; // Proxy for Gold since it tracks 1oz Gold 1:1 and has exact 3m intervals
    const interval = "3m";
    const limit = 1000;
    
    const end_time = Date.now();
    let current_start = Date.now() - (30 * 24 * 60 * 60 * 1000);
    
    let all_klines = [];
    console.log("Downloading 30 days of 3m Gold data...");
    
    while (current_start < end_time) {
        let data = await getBinanceData(symbol, interval, current_start, limit);
        if (!data || data.length === 0) break;
        all_klines.push(...data);
        current_start = data[data.length - 1][0] + 1;
        await new Promise(r => setTimeout(r, 100)); // Sleep
    }
    console.log(`Downloaded ${all_klines.length} candles.`);
    
    // Create DataFrame equivalent
    let df = all_klines.map(k => ({
        open_time: new Date(k[0]).toISOString().replace('T', ' ').substring(0, 19),
        open: parseFloat(k[1]),
        high: parseFloat(k[2]),
        low: parseFloat(k[3]),
        close: parseFloat(k[4])
    }));
    
    // HA Calculation
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
    
    // Save to CSV
    let csvContent = "open_time,open,high,low,close\n" + df.map(row => `${row.open_time},${row.open},${row.high},${row.low},${row.close}`).join("\n");
    fs.writeFileSync('xauusd_3m_30days.csv', csvContent);
    
    const MAX_CANDLE_SIZE = 25.0; // 25 points = $25.0
    
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
        
        let candle_size = curr_high - curr_low;
        
        let buy_signal = (prev_color === 'Red') && (curr_color === 'Green');
        let sell_signal = (prev_color === 'Green') && (curr_color === 'Red');
        let is_oversized = candle_size > MAX_CANDLE_SIZE;
        
        if (position === 'Long' && sell_signal) {
            let pnl = curr_close - entry_price;
            trades.push({Type: 'Long', Entry_Time: entry_time, Entry_Price: entry_price, Exit_Time: curr_time, Exit_Price: curr_close, PnL: pnl, Oversized_Exit: is_oversized});
            position = null;
        } else if (position === 'Short' && buy_signal) {
            let pnl = entry_price - curr_close;
            trades.push({Type: 'Short', Entry_Time: entry_time, Entry_Price: entry_price, Exit_Time: curr_time, Exit_Price: curr_close, PnL: pnl, Oversized_Exit: is_oversized});
            position = null;
        }
        
        if (position === null) {
            if (buy_signal && !is_oversized) {
                position = 'Long';
                entry_price = curr_close;
                entry_time = curr_time;
            } else if (sell_signal && !is_oversized) {
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
    
    let md = `# XAUUSD 3-Minute Heikin Ashi Strategy Backtest\n\n`;
    md += `**Data Period**: Last 30 Days (3-minute candles)\n`;
    md += `**Filter applied**: Candle size > 25 points ($25.0) -> Exit but no entry.\n\n`;
    md += `## Performance Summary\n`;
    md += `- **Total Trades**: ${trades.length}\n`;
    md += `- **Winning Trades**: ${winning_trades}\n`;
    md += `- **Losing Trades**: ${losing_trades}\n`;
    md += `- **Win Rate**: ${win_rate.toFixed(2)}%\n`;
    md += `- **Net PnL (in USD terms per 1 oz)**: $${total_pnl.toFixed(2)}\n\n`;
    
    md += `## Sample of Last 10 Trades\n`;
    md += `| Type | Entry Time | Entry Price | Exit Time | Exit Price | PnL | Oversized Exit |\n`;
    md += `|---|---|---|---|---|---|---|\n`;
    trades.slice(-10).forEach(t => {
        md += `| ${t.Type} | ${t.Entry_Time} | ${t.Entry_Price.toFixed(2)} | ${t.Exit_Time} | ${t.Exit_Price.toFixed(2)} | ${t.PnL.toFixed(2)} | ${t.Oversized_Exit} |\n`;
    });
    
    fs.writeFileSync('backtest_results.md', md);
    console.log("Backtest complete. Results saved to backtest_results.md");
}

run();
