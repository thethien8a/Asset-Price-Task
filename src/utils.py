import requests
import time
import logging
from datetime import datetime
import random
import csv
import os
from config import DATA_FILE


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
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36'
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



def load_assets(filepath):
    """Load asset definitions from CSV file."""
    assets = []
    with open(filepath, mode='r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            assets.append(row)
    return assets


def save_data(new_data):
    """
    Save data to CSV with append-only and deduplication check (date, asset_code).
    """
    file_exists = os.path.isfile(DATA_FILE)
    existing_keys = set()
    
    if file_exists:
        with open(DATA_FILE, mode='r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                existing_keys.add((row['date'], row['asset_code']))
    
    fieldnames = ['date', 'asset_code', 'price', 'asset_name', 'asset_type', 'currency', 'source', 'crawl_time']
    
    with open(DATA_FILE, mode='a', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        
        if not file_exists:
            writer.writeheader()
            
        count = 0
        for item in new_data:
            key = (item['date'], item['asset_code'])
            if key not in existing_keys:
                writer.writerow(item)
                existing_keys.add(key)
                count += 1
        
        logging.info(f"Saved {count} new records to {DATA_FILE}")
    
    return count

