const fs = require('fs');

function runSessionBacktest() {
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

    const MAX_CANDLE_SIZE = 25.0; // 25 points
    
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
        
        // Parse time for session filter
        let dtParts = curr_time.split(' ')[1].split(':');
        let hour = parseInt(dtParts[0]);
        let minute = parseInt(dtParts[1]);
        let timeInMinutes = hour * 60 + minute;
        
        // London opens at 08:00 UTC, NY closes at 21:00 UTC
        let is_active_session = timeInMinutes >= 480 && timeInMinutes < 1260;
        
        let candle_size = curr_high - curr_low;
        let buy_signal = (prev_color === 'Red') && (curr_color === 'Green');
        let sell_signal = (prev_color === 'Green') && (curr_color === 'Red');
        let is_oversized = candle_size > MAX_CANDLE_SIZE;
        
        // Force close at end of NY session (21:00 UTC) to avoid overnight holding
        let force_close = position !== null && timeInMinutes >= 1260 && timeInMinutes < 1265;

        if (position === 'Long' && (sell_signal || force_close)) {
            let pnl = curr_close - entry_price;
            let exit_reason = force_close ? "Session_Close" : (is_oversized ? "Oversized_Opposite" : "Signal_Opposite");
            trades.push({Type: 'Long', Entry_Time: entry_time, Entry_Price: entry_price, Exit_Time: curr_time, Exit_Price: curr_close, PnL: pnl, Reason: exit_reason});
            position = null;
        } else if (position === 'Short' && (buy_signal || force_close)) {
            let pnl = entry_price - curr_close;
            let exit_reason = force_close ? "Session_Close" : (is_oversized ? "Oversized_Opposite" : "Signal_Opposite");
            trades.push({Type: 'Short', Entry_Time: entry_time, Entry_Price: entry_price, Exit_Time: curr_time, Exit_Price: curr_close, PnL: pnl, Reason: exit_reason});
            position = null;
        }
        
        if (position === null && is_active_session) {
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
    
    let md = `# XAUUSD 3-Minute Heikin Ashi Strategy (Session Filtered)\n\n`;
    md += `**Data Period**: Last 30 Days (3-minute candles)\n`;
    md += `**Filter 1**: Candle size > 25 points ($25.0) -> Exit but no entry.\n`;
    md += `**Filter 2 (Session)**: Entries ONLY between 08:00 UTC (London Open) and 21:00 UTC (NY Close). Force close all positions at 21:00 UTC to avoid Asian session chop.\n\n`;
    md += `## Performance Summary\n`;
    md += `- **Total Trades**: ${trades.length}\n`;
    md += `- **Winning Trades**: ${winning_trades}\n`;
    md += `- **Losing Trades**: ${losing_trades}\n`;
    md += `- **Win Rate**: ${win_rate.toFixed(2)}%\n`;
    md += `- **Net PnL (in USD terms per 1 oz)**: $${total_pnl.toFixed(2)}\n\n`;
    
    md += `## Sample of Last 10 Trades\n`;
    md += `| Type | Entry Time | Entry Price | Exit Time | Exit Price | PnL | Reason |\n`;
    md += `|---|---|---|---|---|---|---|\n`;
    trades.slice(-10).forEach(t => {
        md += `| ${t.Type} | ${t.Entry_Time} | ${t.Entry_Price.toFixed(2)} | ${t.Exit_Time} | ${t.Exit_Price.toFixed(2)} | ${t.PnL.toFixed(2)} | ${t.Reason} |\n`;
    });
    
    fs.writeFileSync('backtest_session_results.md', md);
    console.log("Session Backtest complete. Results saved to backtest_session_results.md");
}

runSessionBacktest();
