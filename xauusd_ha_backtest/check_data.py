import requests

def check_binance_1s():
    # Binance supports 1s klines but only for the very recent past or very limited limits.
    url = "https://api.binance.com/api/v3/klines?symbol=PAXGUSDT&interval=1s&limit=5"
    try:
        res = requests.get(url)
        print("Binance 1s response:", res.status_code)
        if res.status_code == 200:
            print(res.json()[0])
    except Exception as e:
        print(e)

check_binance_1s()
