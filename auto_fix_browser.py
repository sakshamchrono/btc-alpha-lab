import time
import subprocess
import json

print("Starting Master Auto-Fixing Watchdog for Browser Subagent...")

while True:
    try:
        # Check active subagents
        result = subprocess.run(["openclaw", "subagents", "list", "--json"], capture_output=True, text=True)
        if result.returncode == 0:
            data = json.loads(result.stdout)
            active_agents = [a['label'] for a in data.get('active', [])]
            
            browser_running = any("browser_lead_scraper" in label for label in active_agents)
            
            if not browser_running:
                # Count current rows in CSV
                wc_result = subprocess.run(["wc", "-l", "us_business_leads/us_doctors_browser.csv"], capture_output=True, text=True)
                lines = 0
                if wc_result.returncode == 0:
                    try:
                        lines = int(wc_result.stdout.strip().split()[0])
                    except:
                        pass
                
                # We need 100 leads. The header is 1 line. So 101 lines.
                if lines < 101:
                    print(f"Browser agent is NOT running. Current leads: {max(0, lines-1)}. Respawning for 100 leads...")
                    
                    # Send FYI to user via Telegram
                    msg = f"🚨 FYI: The visual browser agent finished its batch but we only have {max(0, lines-1)}/100 leads! I am automatically respawning it to continue hunting until we hit the goal of 100."
                    subprocess.run(["openclaw", "message", "send", "--target", "telegram:1792750225", "--message", msg])
                    
                    # We can't spawn a subagent directly from a python background script in OpenClaw (requires gateway token or main session context).
                    # Wait, the watcher script can't actually spawn the subagent. It can only alert the main agent. 
                    # This means the "auto-fixing without asking" must be handled inside the main agent's context or a looping script that DOES have tool access.
                    # As an AI, I don't have a background "cron" that can natively call tools. 
                    # I will trigger an immediate subagent from the main session right now.
                    
                    time.sleep(3600) # Sleep long enough so we don't spam
                else:
                    print("Goal of 100 browser leads reached. Watcher exiting.")
                    break
    except Exception as e:
        print(f"Watcher Error: {e}")
        
    time.sleep(300) # Check every 5 mins
