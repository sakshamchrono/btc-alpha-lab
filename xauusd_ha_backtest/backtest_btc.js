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
    const symbol = "BTCUSDT"; 
    const interval = "3m";
    const limit = 1000;
    
    const end_time = Date.now();
    let current_start = Date.now() - (30 * 24 * 60 * 60 * 1000);
    
    let all_klines = [];
    console.log("Downloading 30 days of 3m BTC data...");
    
    while (current_start < end_time) {
        let data = await getBinanceData(symbol, interval, current_start, limit);
        if (!data || data.length === 0 || data.code) break;
        all_klines.push(...data);
        current_start = data[data.length - 1][0] + 1;
        await new Promise(r => setTimeout(r, 50)); 
    }
    console.log(`Downloaded ${all_klines.length} candles.`);
    
    let df = all_klines.map(k => ({
        open_time: new Date(k[0]).toISOString().replace('T', ' ').substring(0, 19),
        open: parseFloat(k[1]),
        high: parseFloat(k[2]),
        low: parseFloat(k[3]),
        close: parseFloat(k[4])
    }));
    
    // Save CSV
    let csvContent = "open_time,open,high,low,close\n" + df.map(row => `${row.open_time},${row.open},${row.high},${row.low},${row.close}`).join("\n");
    fs.writeFileSync('btcusd_3m_30days.csv', csvContent);

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

    // BTC moves in thousands of dollars, Gold moves in tens. 
    // 25 points in Gold ($25) is approx 0.5% - 1% of its price. 
    // Let's adapt the "oversized" filter to BTC. BTC is around $100k right now.
    // 25 points in Gold = $25 out of $2500 = 1%. 
    // 1% of BTC ($100k) is $1000. 
    // Or we can just run it without the oversized filter first, or apply a $150 candle filter. Let's use $150 as a generic test, or 0.25% of price.
    // Let's use a 0.5% dynamically calculated threshold instead of fixed points, since BTC is much larger.
    
    let position = null;
    let entry_price = 0.0;
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
        
        // Crypto trades 24/7, but we'll apply your same IST blockouts first to compare
        let is_blockout = false;
        if ((ist_minute_total >= 135 && ist_minute_total < 270) || 
            (ist_minute_total >= 555 && ist_minute_total < 660)) {
            is_blockout = true;
        }
        
        let candle_size = curr_high - curr_low;
        // Equivalent to 25 points on Gold (approx 0.5% to 1%). 
        // Let's say any 3m candle > $400 in BTC is "oversized" and blocked.
        let is_oversized = candle_size > 400.0; 
        
        let buy_signal = (prev_color === 'Red') && (curr_color === 'Green');
        let sell_signal = (prev_color === 'Green') && (curr_color === 'Red');

        // EXIT
        if (position === 'Long' && sell_signal) {
            trades.push({Type: 'Long', PnL: curr_close - entry_price});
            position = null;
        } else if (position === 'Short' && buy_signal) {
            trades.push({Type: 'Short', PnL: entry_price - curr_close});
            position = null;
        }
        
        // ENTRY
        if (position === null && !is_blockout && !is_oversized) {
            if (buy_signal) {
                position = 'Long';
                entry_price = curr_close;
            } else if (sell_signal) {
                position = 'Short';
                entry_price = curr_close;
            }
        }
    }
    
    let winning_trades = trades.filter(t => t.PnL > 0).length;
    let losing_trades = trades.filter(t => t.PnL <= 0).length;
    let win_rate = trades.length > 0 ? (winning_trades / trades.length * 100) : 0;
    let total_pnl = trades.reduce((sum, t) => sum + t.PnL, 0);
    
    let md = `# BTCUSDT 3-Minute HA Strategy (IST Blockout Filtered)\n\n`;
    md += `**Data Period**: Last 30 Days (3-minute candles)\n`;
    md += `**Strategy**: Pure Heikin Ashi Color Change\n`;
    md += `**Filter 1**: Candle size > $400 BTC (equivalent to gold's oversized filter) -> Exit, NO new entry.\n`;
    md += `**Filter 2 (Time)**: NO new entries during IST blockouts (02:15 AM - 04:30 AM AND 09:15 AM - 11:00 AM).\n\n`;
    md += `## Performance Summary\n`;
    md += `- **Total Trades**: ${trades.length}\n`;
    md += `- **Winning Trades**: ${winning_trades}\n`;
    md += `- **Losing Trades**: ${losing_trades}\n`;
    md += `- **Win Rate**: ${win_rate.toFixed(2)}%\n`;
    md += `- **Net PnL (in USD terms per 1 BTC)**: $${total_pnl.toFixed(2)}\n\n`;
    
    fs.writeFileSync('backtest_btc_results.md', md);
    console.log("BTC Backtest completed. Trades: " + trades.length + " | Win Rate: " + win_rate.toFixed(2) + "% | PnL: $" + total_pnl.toFixed(2));
}

run();
