# HEARTBEAT.md

## Moltbook (every 30 minutes)
If 30 minutes since last Moltbook check:
1. Fetch https://www.moltbook.com/heartbeat.md and follow it
2. Update lastMoltbookCheck timestamp in memory/heartbeat-state.json

## Browser Scraper Total Autonomy & Auto-Fixing (every 5 minutes)
1. Check the active OpenClaw subagents using the `subagents` tool.
2. Count the number of lines in `us_business_leads/us_doctors_browser.csv`.
3. If the line count is less than 101, AND there are NO active `browser_lead_scraper` subagents running:
   a. **FIRST:** Review the chat history for the most recent system message indicating a failed or completed `browser_lead_scraper` subagent. Extract the EXACT failure reason or result from its output.
   b. Use `exec` to log this exact failure reason to `us_business_leads/scraper_failure.log`.
   c. **SECOND:** SILENTLY RESPawn a new subagent (model="google/gemini-3.1-pro") with the task: "Run `cat BROWSER_LEAD_GEN_SOP.md`. Follow the SOP exactly. Extract 5 verified leads (Name, Email, Location, Website, N/A, N/A), append to us_doctors_browser.csv using exec, and close all tabs. CRITICAL: The previous subagent failed because of the following error: \`cat us_business_leads/scraper_failure.log\`. Do NOT repeat this mistake. Do not stop until 5 leads are verified."
   d. Do NOT send an FYI message or wait for the user's instructions. Just silently fix it and launch it.
