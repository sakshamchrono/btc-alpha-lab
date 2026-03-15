const fs = require('fs');

function runBTCCustom() {
    let csvData = fs.readFileSync('btcusd_3m_30days.csv', 'utf8').trim().split('\n');
    let df = [];
    for (let i = 1; i < csvData.length; i++) {
        let parts = csvData[i].split(',');
        df.push({
            open_time: parts[0],
            open: parseFloat(parts[1]),
            high: parseFloat(parts[2]),
            low: parseFloat(parts[3]),
            close: parseFloat(parts[4])
        });
    }

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

    let position = null;
    let entry_price = 0.0;
    let entry_time = null;
    let trades = [];
    
    const MAX_CANDLE_SIZE = 200.0; 
    
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
        
        // 6:00 AM IST = 360 mins
        // 9:45 AM IST = 585 mins
        // 6:00 PM IST = 1080 mins
        // 9:45 PM IST = 1305 mins
        
        let is_blockout = false;
        if ((ist_minute_total >= 360 && ist_minute_total < 585) || 
            (ist_minute_total >= 1080 && ist_minute_total < 1305)) {
            is_blockout = true;
        }
        
        let buy_signal = (prev_color === 'Red') && (curr_color === 'Green');
        let sell_signal = (prev_color === 'Green') && (curr_color === 'Red');
        let is_oversized = (curr_high - curr_low) > MAX_CANDLE_SIZE;

        if (position === 'Long' && sell_signal) {
            trades.push({Type: 'Long', PnL: curr_close - entry_price});
            position = null;
        } else if (position === 'Short' && buy_signal) {
            trades.push({Type: 'Short', PnL: entry_price - curr_close});
            position = null;
        }
        
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
    let win_rate = trades.length > 0 ? (winning_trades / trades.length * 100) : 0;
    let total_pnl = trades.reduce((sum, t) => sum + t.PnL, 0);
    
    let md = `# BTCUSDT 3-Minute HA Strategy (Custom $200 + 6-9:45 Blockouts)\n\n`;
    md += `**Data Period**: Last 30 Days (3-minute candles)\n`;
    md += `**Strategy**: Pure Heikin Ashi Color Change\n`;
    md += `**Filter 1**: Candle size > $200 -> Exit current position, NO new entry.\n`;
    md += `**Filter 2 (Time)**: NO new entries during IST blockouts (06:00 AM - 09:45 AM AND 06:00 PM - 09:45 PM).\n\n`;
    md += `## Performance Summary\n`;
    md += `- **Total Trades**: ${trades.length}\n`;
    md += `- **Winning Trades**: ${winning_trades}\n`;
    md += `- **Win Rate**: ${win_rate.toFixed(2)}%\n`;
    md += `- **Net PnL (in USD terms per 1 BTC)**: $${total_pnl.toFixed(2)}\n\n`;
    
    fs.writeFileSync('backtest_btc_custom_results.md', md);
    console.log("BTC Custom Backtest completed. Trades: " + trades.length + " | Win Rate: " + win_rate.toFixed(2) + "% | PnL: $" + total_pnl.toFixed(2));
}

runBTCCustom();
