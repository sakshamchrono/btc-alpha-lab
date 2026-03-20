# HEARTBEAT.md

## Moltbook (every 30 minutes)
If 30 minutes since last Moltbook check:
1. Fetch https://www.moltbook.com/heartbeat.md and follow it
2. Update lastMoltbookCheck timestamp in memory/heartbeat-state.json

## Browser Scraper Total Autonomy (every 5 minutes)
1. Check the active OpenClaw subagents.
2. Count the number of lines in `us_business_leads/us_doctors_browser.csv`.
3. If the line count is less than 101, AND there are NO active `browser_lead_scraper` subagents running:
   a. I have full autonomy to fix the scraper based on its last failure log.
   b. I MUST SILENTLY RESPawn a new subagent (model="google/gemini-3.1-pro") and command it to use the `browser` tool (Chromium) to search DuckDuckGo/Bing, physically visit websites, extract Name/Email/Location/Website (with "N/A" for reviews/stars), append to the CSV using `exec`, and close all tabs.
   c. Do NOT send me an FYI message or wait for my instructions. Just silently fix it and launch it.
