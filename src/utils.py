import requests
import time
import logging
from datetime import datetime
import random

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("crawler.log"),
        logging.StreamHandler()
    ]
)

def get_current_date_str():
    return datetime.now().strftime('%Y-%m-%d')

def make_request(url, method='GET', headers=None, payload=None, retries=3, delay=2):
    """
    Thực hiện request với cơ chế retry và delay.
    """
    default_headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    if headers:
        default_headers.update(headers)

    for attempt in range(retries):
        try:
            if method == 'GET':
                response = requests.get(url, headers=default_headers, timeout=10)
            elif method == 'POST':
                response = requests.post(url, headers=default_headers, json=payload, timeout=10)
            else:
                return None
            
            response.raise_for_status()
            return response
        except requests.exceptions.RequestException as e:
            logging.warning(f"Request failed (Attempt {attempt + 1}/{retries}): {e}")
            if attempt < retries - 1:
                sleep_time = delay * (attempt + 1) + random.uniform(0, 1)
                time.sleep(sleep_time)
            else:
                logging.error(f"Request failed after {retries} attempts: {url}")
                return None

def clean_price(price_str):
    """
    Chuyển đổi chuỗi giá sang float.
    Ví dụ: "23,500" -> 23500.0
    """
    if not price_str:
        return None
    try:
        # Loại bỏ dấu phẩy, ký tự lạ
        clean = str(price_str).replace(',', '').replace('.', '').replace(' VND', '').strip()
        return float(clean)
    except ValueError:
        return None
