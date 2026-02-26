# ServiceNow (NOW) Deep-Dive Analysis
**Date:** 2026-02-26 (UTC)  
**Ticker:** NOW  
**Price reference:** $104.23 (Stooq close, 2026-02-25)

## Executive View
ServiceNow remains a high-quality enterprise software compounder (strong revenue growth, high gross margin, large and expanding RPO base), but the stock is in a cyclical de-rating phase with weak trend/momentum and elevated volatility. Near-term setup is mixed: fundamentals remain structurally strong, while technicals still indicate distribution/risk-off behavior.

---

## 1) Fundamental Analysis

## Growth profile
- FY2025 revenue reported around **$13.278B**, up roughly **~21% YoY**.
- RPO/cRPO growth remained robust through 2025 (Q4 cRPO ~25% YoY; RPO ~26.5% YoY per cited summaries), signaling durable backlog and enterprise demand.
- Market narrative remains AI/workflow-led platform expansion, supporting multi-year growth durability.

## Profitability and margins
- Gross profit margin is still strong for SaaS (reported around **~77–78%** range in 2025 references).
- Operating leverage visible on non-GAAP basis (around **~31%** non-GAAP operating margin cited), while GAAP operating margin remains lower (low/mid teens range in cited data).
- Net income (2025) reported near **$1.748B**, indicating increasing GAAP earnings scale.

## Balance sheet and cash generation
- Cash and equivalents cited near **$3.7B** (end-2025 references).
- Total debt cited in the low-single-digit billions (roughly **$2–3B** depending on source currency framing).
- Free cash flow around **$4.58B** in 2025 references, with strong FCF margin profile.

### Fundamental takeaway
- **Strengths:** durable growth, high gross margin, strong FCF conversion, expanding contracted backlog.
- **Watch items:** valuation sensitivity, macro IT budget cyclicality, and execution risk as AI monetization scales.

---

## 2) Valuation vs Peers (Relative)
Using late-Feb-2026 referenced market multiples:
- **NOW:** P/E ~60x+, EV/Sales ~7.6–8.2x
- **CRM (Salesforce):** P/E ~24–25x, EV/Sales ~4.2x
- **WDAY (Workday):** P/E ~54–58x, EV/Sales ~3.7x
- **TEAM (Atlassian):** EV/Sales ~3.8–3.9x, P/E often distorted/negative in some datasets

Interpretation:
- NOW still trades at a **premium EV/Sales multiple** vs large-cap workflow/application peers.
- Premium is justified only if mid/high-teens+ growth and superior margin/cash conversion persist.
- If growth compresses faster than expected, multiple downside can dominate earnings growth in the next 12 months.

---

## 3) Technical Analysis (Price/Trend/Momentum)
**Data source:** Stooq daily OHLCV (`NOW_stooq_daily.csv`) through 2026-02-25.

### Trend
- Spot: **$104.23**
- 50D MA: **$130.48**
- 200D MA: **$172.57**
- Structure: price is below both 50D and 200D MAs → **primary downtrend**.

### Momentum
- RSI(14): **36.66** (weak momentum; not deeply oversold but still bearish-leaning)
- MACD(12,26): **-7.92**
- MACD signal(9): **-9.11**
- MACD above signal but below zero line: possible early stabilization bounce, not yet full trend reversal confirmation.

### Support/Resistance (6M quantile-based)
- Support zone: ~**$105**
- Resistance zone: ~**$190**

### Volatility
- 30-day annualized realized volatility: **~55.3%** (high)
- Regime currently riskier than a typical large-cap software steady-state volatility band.

---

## 4) Quant/Statistical Scenario Modeling (12M Target)
### Method
Hybrid framework:
1. **Historical analog distribution** from full Stooq history using rolling 1-year returns.
2. **Fundamental overlay** (growth durability + valuation mean reversion risk).
3. **Technical regime adjustment** (downtrend state increases downside tail risk).

### Historical 1Y return analogs (rolling windows)
- P10: **-14.2%**
- P50: **+36.8%**
- P90: **+75.4%**

### Scenario assumptions
- **Bear:** valuation compresses further + growth deceleration + weak macro IT spend.
- **Base:** growth remains healthy, valuation partially normalizes, trend stabilizes over 2H.
- **Bull:** AI-driven re-acceleration, strong enterprise demand, multiple re-expansion.

### 12M price targets (from $104.23)
- **Bear:** **$78**  (−25.2%)
- **Base:** **$122** (+17.0%)
- **Bull:** **$155** (+48.7%)

### Probabilities
- Bear: **30%**
- Base: **50%**
- Bull: **20%**

**Probability-weighted expected value:**
- EV target = 0.30×78 + 0.50×122 + 0.20×155 = **$115.4**
- Implied expected return: **+10.7%** over 12M

---

## 5) Max Drawdown Risk (Next 12M)
### Historical analog (rolling 1Y max drawdowns)
- Median 1Y max drawdown: **-25.7%**
- 25th percentile: **-34.4%**
- 10th percentile (stress): **-46.5%**
- Worst observed 1Y window: **-51.9%**

### Scenario-based forward estimate
- Bear-case peak-to-trough assumption: **-45% to -50%**
- Base-case: **-25% to -35%**
- Bull-case: **-15% to -22%**

**Estimated max drawdown risk (next 12M):** **~35% central estimate**, with stress tail approaching **~50%**.

---

## 6) Key Risks, Assumptions, and Limitations
## Key risks
1. **Multiple compression risk**: premium valuation can de-rate quickly if growth misses.
2. **Enterprise IT budget cyclicality**: delayed deal cycles affect cRPO/revenue conversion.
3. **Competition/platform substitution**: pressure from CRM/WDAY/TEAM and broader AI-native workflows.
4. **Execution risk in AI monetization**: monetization pace may lag expectations.

## Core assumptions
- No severe balance-sheet stress event.
- Growth remains positive and above mature software averages.
- Market regime remains volatile but not systemic crisis-level.

## Limitations
- Direct SEC/company IR pages were intermittently blocked via fetch (403/rate-limit/anti-bot), so some fundamental inputs are triangulated from indexed financial aggregators and search-grounded summaries.
- Technicals are based on Stooq EOD data and may differ slightly from exchange/terminal-calculated indicators.
- Scenario model is probabilistic and not investment advice.

---

## Sources
1. Stooq historical data (NOW): https://stooq.com/q/d/l/?s=now.us&i=d  
2. ServiceNow 2025 filing/IR references (search-indexed): https://investor.servicenow.com/financial-resources/sec-filings/default.aspx  
3. ServiceNow FY2025 release reference (search-indexed): https://newsroom.servicenow.com/press-releases/details/2026/ServiceNow-Reports-Fourth-Quarter-and-Full-Year-2025-Financial-Results-Board-of-Directors-Authorizes-Additional-5B-for-Share-Repurchase-Program/default.aspx  
4. Market cap/revenue/margin snapshots: https://companiesmarketcap.com/servicenow/marketcap/  
5. Revenue history context: https://www.macrotrends.net/stocks/charts/NOW/servicenow/revenue  
6. Free cash flow context: https://www.macrotrends.net/stocks/charts/NOW/servicenow/free-cash-flow  
7. Relative EV/Sales (NOW): https://www.financecharts.com/stocks/NOW/value/ev-to-sales  
8. Relative EV/Sales (CRM): https://www.financecharts.com/stocks/CRM/value/ev-to-sales  
9. Relative EV/Sales (WDAY): https://www.financecharts.com/stocks/WDAY/value/ev-to-sales  
10. Relative valuation cross-check: https://multiples.vc/public-comps/servicenow-valuation-multiples
