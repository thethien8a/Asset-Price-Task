import requests
import re

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8'
}

def check_url(url, name):
    print(f"\n--- Checking {name}: {url} ---")
    try:
        resp = requests.get(url, headers=headers, timeout=10)
        print(f"Status: {resp.status_code}")
        if resp.status_code == 200:
            html = resp.text
            print(f"Content Length: {len(html)}")
            # Thử tìm NAV (keyword thông dụng)
            if 'NAV' in html or 'nav' in html:
                print("Found 'NAV' keyword")
            # In ra 500 ký tự chứa NAV để soi
            idx = html.lower().find('nav')
            if idx != -1:
                print(f"Context: {html[idx:idx+200]}")
            else:
                print("NAV keyword not found")
            return html
        else:
            print("Failed")
            return None
    except Exception as e:
        print(f"Error: {e}")
        return None

# Test VinaCapital
html_vina = check_url("https://vinacapital.com/investment-solutions/onshore-funds/vesaf/", "VinaCapital VESAF")

# Test Dragon Capital
html_dragon = check_url("https://dragoncapital.com.vn/en/funds/dcds/", "Dragon Capital DCDS")

# Test Webgia (Gold)
html_gold = check_url("https://webgia.com/gia-vang/sjc/", "Webgia Gold")
if html_gold:
    # In ra đoạn chứa "Nhẫn" để debug regex
    print("\n--- Gold Ring Debug ---")
    lines = html_gold.split('\n')
    for line in lines:
        if "Nhẫn" in line or "9999" in line:
            print(f"Found Line: {line.strip()[:200]}")
