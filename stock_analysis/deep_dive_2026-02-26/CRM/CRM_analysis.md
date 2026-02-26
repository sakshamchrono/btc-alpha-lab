# Salesforce (CRM) Deep-Dive Analysis
**Date:** 2026-02-26 (UTC)  
**Ticker:** CRM  
**Spot price used:** **$191.75** (NYSE close, 2026-02-25)

---

## 1) Fundamental analysis

## Business quality and growth
- Salesforce remains a scaled mission-critical enterprise software platform (Sales, Service, Marketing, Data/AI cloud layers).
- Reported **FY2025 revenue: $37.9B (+9% YoY)** and **FY2025 FCF: ~$12.4B (+31% YoY)**, showing a transition from pure growth to profitable growth/cash discipline.
- Recent trailing data (TTM, market-data aggregator) indicates **revenue ~$41.53B**, implying growth has remained positive but moderated vs earlier hypergrowth years.

## Profitability & margins
Using the latest available trailing snapshot (stock statistics source):
- **Gross margin:** 77.68%
- **Operating margin:** 21.47%
- **Net margin:** 17.96%
- **EBITDA margin:** 30.22%
- **FCF margin:** 34.68%

Interpretation:
- Margin profile is strong for large-cap software and supports a durable FCF story.
- Key question is durability of margin expansion if Salesforce re-accelerates AI/product investment.

## Balance sheet and financial resilience
- **Cash:** $9.57B
- **Total debt:** $17.18B
- **Net debt:** about **$7.61B** (modest relative to FCF generation)
- **Debt/Equity:** 0.29
- **Current ratio:** 0.76 (not unusual for subscription software, but worth tracking)

Interpretation:
- Balance sheet is manageable rather than pristine; leverage is not the core risk.
- Core risk is execution + multiple compression, not near-term solvency.

## Valuation and peer context
### CRM current multiples (trailing snapshot)
- **P/E:** 24.58
- **Forward P/E:** 14.58
- **P/S:** 4.33
- **EV/EBITDA:** 14.93
- **P/FCF:** 12.48

### Peer comparison (same source family, point-in-time snapshot)
- **Adobe (ADBE):** P/E 15.44, EV/EBITDA 11.46, P/S 4.45
- **Oracle (ORCL):** P/E 27.76, EV/EBITDA 20.45, P/S 6.97
- **Microsoft (MSFT):** P/E 25.07, EV/EBITDA 17.17, P/S 9.74
- **SAP:** P/E 27.06, EV/EBITDA 16.54, P/S 5.31

Relative read:
- CRM screens **cheaper than mega-cap premium SaaS/platform peers** (MSFT, SAP on P/S and EV/EBITDA) and **cheaper than ORCL on EV/EBITDA/P/S**.
- CRM is **not deep value** if growth decelerates further; valuation still assumes durable mid/high-single-digit growth + stable margins.

---

## 2) Technical analysis (daily, Stooq data through 2026-02-25)

## Trend
- **Price:** $191.75
- **50DMA:** $228.15
- **200DMA:** $248.02
- Price is below both key moving averages and 50DMA < 200DMA → **primary trend still bearish**.

## Momentum
- **RSI(14): 43.53** → weak-to-neutral; not deeply oversold.
- **MACD:** -12.11
- **Signal:** -13.59
- **Histogram:** +1.49 (early positive momentum inflection while still below zero line).

Read: short-term selling pressure has eased, but trend confirmation requires recovery above ~228 first.

## Support / resistance (heuristic levels)
- **Near support:** ~$178 (recent swing zone)
- **Deeper support:** ~$170–175 (near 52-week low cluster)
- **Near resistance:** ~$220–230 (50DMA zone)
- **Major resistance:** ~$248–266 (200DMA and prior breakdown region)

## Volatility / regime
- **Annualized realized volatility (1Y): ~34.8%**
- **Beta (5Y source snapshot): ~1.28**
- **52-week range:** $174.57 to $313.70
- Current price is ~**38.9% below** 52-week high.

Regime takeaway: high-volatility downtrend with potential for sharp bear-market rallies.

---

## 3) Quant/statistical modeling (1-year target framework)

## Method
I combined:
1. **Market-implied path intuition** from realized volatility (not used blindly because trailing drift is extremely negative),
2. **Fundamental-multiple scenario analysis** (growth + margin + multiple re-rating/de-rating),
3. **Technical regime filter** (downtrend increases left-tail probability).

A pure trailing-drift GBM calibration gives overly bearish medians due to 2025–26 trend damage, so I re-centered scenarios with fundamental assumptions.

## Scenario assumptions
- **Bear case (30%)**: growth slips to low single digits, AI monetization lag, multiple de-rates to lower-teens earnings/low-4x sales neighborhood.
- **Base case (50%)**: mid/high-single-digit growth, margins stable-to-slightly higher, valuation normalizes near historical mid-band.
- **Bull case (20%)**: better AI/cross-cloud attach, double-digit EPS growth realization, multiple expansion back toward prior premium range.

## 1-year price targets
- **Bear:** **$145**
- **Base:** **$245**
- **Bull:** **$320**

Probability-weighted expected value:
- `0.30*145 + 0.50*245 + 0.20*320 = $230.0`
- Implied expected upside vs $191.75: **+19.9%**

Upside/downside from spot:
- Bear: **-24.4%**
- Base: **+27.8%**
- Bull: **+66.9%**

Confidence in target set: **Medium (0.58/1.00)** due to mixed source quality and regime uncertainty.

---

## 4) Max drawdown risk estimate (next 12 months)

## Historical analog anchor
- Approx. **5-year max drawdown:** **-58.6%** (daily close series computation)
- Recent cycle drawdown from 52w high to low: roughly **-44.3%**

## Forward scenario drawdown assumptions
- **Bull environment:** peak-to-trough around **-22%** (normal high-beta software correction)
- **Base environment:** around **-30%**
- **Bear environment:** around **-45%**

Probability-weighted forward max drawdown estimate:
- `0.20*(-22%) + 0.50*(-30%) + 0.30*(-45%) ≈ -32.9%`

**Estimated 1-year max drawdown risk:** **~33% expected**, with stressed left-tail **~45%** possible in risk-off/multiple-compression conditions.

---

## 5) Key thesis, risks, assumptions, limitations

## Core thesis
CRM is a high-quality cash-generating software franchise that currently trades below premium mega-cap software multiples, creating upside if execution on growth + AI monetization stabilizes while margins remain disciplined.

## Primary risks
1. **Sustained growth deceleration** (seat expansion/enterprise budget caution).
2. **AI monetization disappointment** vs market expectations.
3. **Multiple compression** in higher real-rate or risk-off regimes.
4. **Competitive pressure** from MSFT platform bundling and other cloud vendors.
5. **Technical overhang**: still below major moving averages; failed rallies possible.

## Assumptions
- No severe balance-sheet shock or major M&A balance-sheet stress.
- Software demand remains positive, not recession-collapse.
- Market valuation framework for profitable SaaS remains broadly intact.

## Limitations
- Some valuation/fundamental fields are from aggregator snapshots (not fully audited filings line-by-line in this run).
- Salesforce IR pages have anti-bot protections in lightweight fetch mode; when blocked, I used corroborating public sources and marked confidence accordingly.
- Price-target scenarios are model outputs, not certainty forecasts.

---

## Sources
1. Stooq historical daily data (CRM): https://stooq.com/q/d/l/?s=crm.us&i=d  
2. Salesforce FY2025 results press release / IR reference: https://investor.salesforce.com/news/news-details/2025/Salesforce-Announces-Fourth-Quarter-and-Fiscal-Year-2025-Results/default.aspx  
3. Salesforce FY25 release mirror/news page: https://www.salesforce.com/news/press-releases/2025/02/26/fy25-q4-earnings/  
4. CRM valuation/statistics snapshot: https://stockanalysis.com/stocks/crm/statistics/  
5. ADBE valuation/statistics snapshot: https://stockanalysis.com/stocks/adbe/statistics/  
6. ORCL valuation/statistics snapshot: https://stockanalysis.com/stocks/orcl/statistics/  
7. MSFT valuation/statistics snapshot: https://stockanalysis.com/stocks/msft/statistics/  
8. SAP valuation/statistics snapshot: https://stockanalysis.com/stocks/sap/statistics/
