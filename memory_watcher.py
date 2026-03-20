import time
import subprocess
import os

print("Starting Memory Leakage Watchdog (Checking every 60 seconds)...")

MAX_MEMORY_GB = 6.0 # Threshold to alert or take action (e.g. 6 GB)

while True:
    try:
        # Check Total Memory Usage of the system
        free_output = subprocess.run(["free", "-m"], capture_output=True, text=True)
        lines = free_output.stdout.strip().split('\n')
        mem_info = lines[1].split()
        total_mem_mb = int(mem_info[1])
        used_mem_mb = int(mem_info[2])
        used_mem_gb = used_mem_mb / 1024.0
        
        # Check specifically for Chromium processes to see if tabs are piling up
        ps_output = subprocess.run(["ps", "-ef"], capture_output=True, text=True)
        chromium_count = ps_output.stdout.count("chromium")
        
        print(f"[Memory Check] Used: {used_mem_gb:.2f}GB / Tabs: {chromium_count}")
        
        # If memory gets dangerously high (>6GB) or there are way too many zombie chromium processes (>25)
        if used_mem_gb > MAX_MEMORY_GB or chromium_count > 25:
            # We are hitting a severe memory leak from visual browser subagents failing to close tabs
            msg = f"🚨 URGENT SYSTEM ALERT: Memory Leak Detected! 🚨\n\nSystem is currently using {used_mem_gb:.2f}GB of RAM with {chromium_count} active Chromium processes running in the background. The visual subagents are hoarding tabs again.\n\nI am instantly executing a `killall -9 chromium` command to flush the memory and prevent a server crash."
            subprocess.run(["openclaw", "message", "send", "--target", "telegram:1792750225", "--message", msg])
            
            print("Executing emergency memory flush...")
            subprocess.run(["killall", "-9", "chromium"])
            
            # Sleep a bit longer after an emergency flush
            time.sleep(300)
            
    except Exception as e:
        print(f"Memory Watcher Error: {e}")
        
    # Check every 60 seconds
    time.sleep(60)
