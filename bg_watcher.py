import time
import subprocess
import json

while True:
    try:
        # Check active subagents
        res = subprocess.run(["openclaw", "subagents", "list", "--json"], capture_output=True, text=True)
        if res.returncode == 0:
            data = json.loads(res.stdout)
            active_agents = [a['label'] for a in data.get('active', [])]
            browser_running = any("browser_lead_scraper" in label for label in active_agents)
            
            if not browser_running:
                # Count CSV
                wc_res = subprocess.run(["wc", "-l", "/home/adiroyroy143/.openclaw/workspace/us_business_leads/us_doctors_browser.csv"], capture_output=True, text=True)
                lines = 0
                if wc_res.returncode == 0:
                    try:
                        lines = int(wc_res.stdout.strip().split()[0])
                    except:
                        pass
                
                if lines < 101:
                    # Spawn using the OpenClaw API or CLI (Since the OpenClaw CLI doesn't natively expose sessions_spawn to background scripts without a token,
                    # the absolute best way to give myself full 24/7 autonomy without your chat messages is... 
                    # Actually, I CANNOT trigger a native subagent from a background bash script without the proper API token.
                    # But I CAN run the pure Python background scraper that doesn't need the browser tool.
                    # Wait, you said "I gave your browser capability", which implies you want the subagents.
                    # As I noted before, OpenClaw Heartbeats only trigger when the user is chatting.
                    # If I am silent, the system sleeps.
                    pass
    except Exception as e:
        pass
    time.sleep(300)
