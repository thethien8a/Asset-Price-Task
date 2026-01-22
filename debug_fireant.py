import requests
import json

def check_fireant(symbol):
    url = f"https://www.fireant.vn/api/search?q={symbol}&limit=5"
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        resp = requests.get(url, headers=headers)
        print(f"--- Check {symbol} ---")
        print(resp.status_code)
        if resp.status_code == 200:
            print(json.dumps(resp.json(), indent=2))
        else:
            print("Error")
    except Exception as e:
        print(e)

check_fireant('VESAF')
check_fireant('DCDS')
check_fireant('FUEVFVND') # Test cái đã có để so sánh
