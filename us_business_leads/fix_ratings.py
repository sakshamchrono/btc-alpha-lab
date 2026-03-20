import subprocess
import time

print("Auto-fixing Browser Agent for Google Maps Ratings...")
msg = "🚨 FYI: Auto-Fixing Browser Subagent! I've updated the visual scraper to search Google Maps directly for the Business Name to extract real Star Ratings and Review Counts instead of estimating them from websites. Restarting the scraper now."
subprocess.run(["openclaw", "message", "send", "--target", "telegram:1792750225", "--message", msg])

