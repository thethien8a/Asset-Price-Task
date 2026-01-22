import csv
import os
import logging
from datetime import datetime
from src.crawlers import StockCrawler, FundCrawler, GoldCrawler

# Setup constants
DATA_FILE = 'data/daily_prices.csv'
ASSETS_FILE = 'data/assets.csv'

def load_assets(filepath):
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
                existing_keys.add(key) # Update set để tránh dup ngay trong batch hiện tại
                count += 1
        
        logging.info(f"Saved {count} new records to {DATA_FILE}")

def main():
    assets = load_assets(ASSETS_FILE)
    
    # Group assets
    stock_assets = [a for a in assets if a['asset_type'] in ['stock', 'etf']]
    fund_assets = [a for a in assets if a['asset_type'] == 'fund']
    gold_assets = [a for a in assets if a['asset_type'] == 'gold']
    
    all_results = []
    crawl_time = datetime.now().isoformat()
    
    # 1. Stocks & ETFs
    if stock_assets:
        logging.info(f"Processing {len(stock_assets)} stocks/ETFs...")
        crawler = StockCrawler()
        results = crawler.crawl(stock_assets)
        all_results.extend(results)
        
    # 2. Funds
    if fund_assets:
        logging.info(f"Processing {len(fund_assets)} funds...")
        crawler = FundCrawler()
        results = crawler.crawl(fund_assets)
        all_results.extend(results)
        
    # 3. Gold
    if gold_assets:
        logging.info(f"Processing {len(gold_assets)} gold assets...")
        crawler = GoldCrawler()
        results = crawler.crawl(gold_assets)
        all_results.extend(results)
        
    # Enrich data (add name, type, etc.)
    final_data = []
    asset_info_map = {a['asset_code']: a for a in assets}
    
    for res in all_results:
        code = res['asset_code']
        if code in asset_info_map:
            info = asset_info_map[code]
            res['asset_name'] = info['asset_name']
            res['asset_type'] = info['asset_type']
            res['currency'] = 'VND'
            res['crawl_time'] = crawl_time
            final_data.append(res)
            
    # Save
    if final_data:
        save_data(final_data)
    else:
        logging.warning("No data collected!")

if __name__ == "__main__":
    main()
