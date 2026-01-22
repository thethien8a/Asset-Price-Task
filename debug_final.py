import requests
import xml.etree.ElementTree as ET

headers_mobile = {
    'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'vi-VN,vi;q=0.9',
    'Referer': 'https://m.cafef.vn'
}

def check_doji():
    url = "http://giavang.doji.vn/api/giavang/?so_luong=1"
    try:
        resp = requests.get(url, timeout=10)
        print(f"Doji Status: {resp.status_code}")
        if resp.status_code == 200:
            print(resp.text[:200])
            # Parse XML
            root = ET.fromstring(resp.text)
            # Tìm Nhẫn
            for child in root.findall('.//Doji'):
                name = child.get('Ten_san_pham')
                price_sell = child.get('Gia_ban_ra')
                if 'Nhan' in name or 'Hung Thinh Vuong' in name:
                    print(f"Found Ring: {name} - Sell: {price_sell}")
    except Exception as e:
        print(f"Doji Error: {e}")

def check_cafef_mobile(symbol):
    # CafeF Mobile URL
    url = f"https://m.cafef.vn/quyo-{symbol}/thong-tin-chung.chn"
    print(f"Checking CafeF Mobile: {url}")
    try:
        resp = requests.get(url, headers=headers_mobile, timeout=10)
        print(f"Status: {resp.status_code}")
        if resp.status_code == 200:
            if 'NAV' in resp.text:
                print("Found NAV keyword")
                # Tìm giá trị
                # Pattern mobile có thể khác
            else:
                print("NAV not found")
    except Exception as e:
        print(f"CafeF Error: {e}")

check_doji()
check_cafef_mobile('vesaf')
