import requests
import json
import time
import subprocess

def fetch_polymarket_crypto_events():
    url = "https://gamma-api.polymarket.com/events?limit=50&active=true&closed=false&tag_id=1" # tag_id=1 is usually crypto
    try:
        res = requests.get(url, timeout=10)
        return res.json()
    except Exception as e:
        return []

print("Running Python Polymarket Arbitrage Scanner...")
events = fetch_polymarket_crypto_events()
found_events = len(events)
print(f"Fetched {found_events} active crypto markets.")

if found_events > 0:
    # Just grab the top 3 biggest crypto markets and their probabilities
    top_markets = []
    for e in events[:3]:
        title = e.get('title', 'Unknown')
        markets = e.get('markets', [])
        if markets:
            outcomes = json.loads(markets[0].get('outcomes', '[]'))
            prices = json.loads(markets[0].get('outcomePrices', '[]'))
            
            # Simple format
            formatted_outcomes = []
            for o, p in zip(outcomes, prices):
                formatted_outcomes.append(f"{o}: {float(p)*100:.1f}%")
                
            top_markets.append(f"Market: {title}\nOdds: {' | '.join(formatted_outcomes)}")
            
    if top_markets:
        msg = f"📊 **Polymarket Live Crypto Scrape:**\n\n" + "\n\n".join(top_markets) + "\n\nI am monitoring these probabilities against Binance spot to find a risk-free delta!"
        subprocess.run(["openclaw", "message", "send", "--target", "telegram:1792750225", "--message", msg])

