import requests
import json

url = "https://api.fmarket.vn/res/product/get-search-product"
params = {'keyword': 'VESAF'}
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Origin': 'https://fmarket.vn',
    'Referer': 'https://fmarket.vn/'
}

try:
    resp = requests.get(url, params=params, headers=headers)
    print(resp.status_code)
    print(resp.text)
except Exception as e:
    print(e)
