const fs = require('fs');

function runISTBlockoutBacktest() {
    let csvData = fs.readFileSync('xauusd_3m_30days.csv', 'utf8').trim().split('\n');
    let df = [];
    let headers = csvData[0].split(',');
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
        let curr_time = df[i].open_time; // UTC string
        
        // Convert current candle open time to IST minutes since midnight
        // curr_time is like "2026-02-03 19:00:00"
        let d = new Date(curr_time + "Z");
        let utc_hour = d.getUTCHours();
        let utc_minute = d.getUTCMinutes();
        
        // IST is UTC + 5:30 (330 minutes)
        let ist_minute_total = (utc_hour * 60 + utc_minute + 330) % 1440;
        
        // Blockout 1: 02:15 AM to 04:30 AM IST -> (135 mins to 270 mins)
        // Blockout 2: 09:15 AM to 11:00 AM IST -> (555 mins to 660 mins)
        let is_blockout = false;
        if ((ist_minute_total >= 135 && ist_minute_total < 270) || 
            (ist_minute_total >= 555 && ist_minute_total < 660)) {
            is_blockout = true;
        }
        
        let candle_size = curr_high - curr_low;
        
        // Pure HA Strategy Logic
        let buy_signal = (prev_color === 'Red') && (curr_color === 'Green');
        let sell_signal = (prev_color === 'Green') && (curr_color === 'Red');
        
        // Filter: > 25 points
        let is_oversized = candle_size > MAX_CANDLE_SIZE;

        // EXIT LOGIC
        if (position === 'Long') {
            if (sell_signal) {
                let pnl = curr_close - entry_price;
                trades.push({Type: 'Long', Entry_Time: entry_time, Entry_Price: entry_price, Exit_Time: curr_time, Exit_Price: curr_close, PnL: pnl, Reason: is_oversized ? "Oversized_Opposite" : "Signal_Opposite"});
                position = null;
            }
        } else if (position === 'Short') {
            if (buy_signal) {
                let pnl = entry_price - curr_close;
                trades.push({Type: 'Short', Entry_Time: entry_time, Entry_Price: entry_price, Exit_Time: curr_time, Exit_Price: curr_close, PnL: pnl, Reason: is_oversized ? "Oversized_Opposite" : "Signal_Opposite"});
                position = null;
            }
        }
        
        // ENTRY LOGIC (Only if we are flat, not in a blockout window, and the signal candle isn't > 25 points)
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
    
    let md = `# XAUUSD 3-Minute HA Strategy (IST Blockout Filtered)\n\n`;
    md += `**Data Period**: Last 30 Days (3-minute candles)\n`;
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
    md += `| Type | Entry Time (UTC) | Entry Price | Exit Time (UTC) | Exit Price | PnL | Reason |\n`;
    md += `|---|---|---|---|---|---|---|\n`;
    trades.slice(-10).forEach(t => {
        md += `| ${t.Type} | ${t.Entry_Time} | ${t.Entry_Price.toFixed(2)} | ${t.Exit_Time} | ${t.Exit_Price.toFixed(2)} | ${t.PnL.toFixed(2)} | ${t.Reason} |\n`;
    });
    
    fs.writeFileSync('backtest_ist_blockout_results.md', md);
    console.log("Backtest with IST blockouts completed.");
}

runISTBlockoutBacktest();
