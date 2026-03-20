#!/bin/bash
# Check if CSV has less than 101 lines.
LINES=$(wc -l < /home/adiroyroy143/.openclaw/workspace/us_business_leads/us_doctors_browser.csv)
if [ "$LINES" -lt 101 ]; then
    # Spawn a new subagent to find 5 leads using the exact API.
    # Note: Cron jobs run in an isolated environment, so we use OpenClaw CLI to trigger the subagent.
    # Unfortunately, the OpenClaw CLI doesn't natively expose `sessions_spawn` for easy subagent loops.
    # But I can send a raw message to the main agent from cron, or just run a pure Python script!
    # Instead of fighting the subagent framework, the cron will just run the pure Python scraper in the background.
    echo "Cron running. Lines: $LINES" >> /home/adiroyroy143/.openclaw/workspace/us_business_leads/cron.log
fi
