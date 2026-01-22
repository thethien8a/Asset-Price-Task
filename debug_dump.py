import requests
import warnings
warnings.filterwarnings("ignore") # Tắt warning SSL

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}

def save_html(url, filename):
    try:
        resp = requests.get(url, headers=headers, verify=False, timeout=10)
        if resp.status_code == 200:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(resp.text)
            print(f"Saved {filename}")
        else:
            print(f"Failed {url}: {resp.status_code}")
    except Exception as e:
        print(f"Error {url}: {e}")

# Save Webgia HTML to analyze Gold Ring
save_html("https://webgia.com/gia-vang/sjc/", "webgia.html")

# Save Dragon Capital HTML
save_html("https://dragoncapital.com.vn/en/funds/dcds/", "dragon.html")

# Test Investing.com for VESAF
save_html("https://vn.investing.com/funds/vina-capital-equity-special-fund", "investing.html")
