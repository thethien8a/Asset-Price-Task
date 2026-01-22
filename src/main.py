"""
Main orchestrator for daily asset price collection.

This script collects prices for Vietnamese financial assets:
- Stocks (9): HPG, FPT, MBB, SSI, POW, VCG, DGC, VND, VTP
- ETFs (3): FUEVFVND, E1VFVN30, FUESSVFL
- Open-end Funds (17): Various funds from VinaCapital, VCBF, SSI, Dragon Capital
- Gold (2): SJC Gold Bar, Gold Ring 9999

Usage:
    python -m src.main

Output:
    - data/daily_prices.csv (append-only, deduplicated by date+asset)
    - crawler.log (execution logs)
"""

import csv
import os
import logging
from datetime import datetime
from src.crawlers import StockCrawler, FundCrawler, GoldCrawler

# Setup constants
DATA_FILE = 'data/daily_prices.csv'
ASSETS_FILE = 'data/assets.csv'


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


def main():
    """Main execution function."""
    print("=" * 60)
    print("Daily Asset Price Collection Tool")
    print("=" * 60)
    
    assets = load_assets(ASSETS_FILE)
    
    # Group assets by type
    stock_assets = [a for a in assets if a['asset_type'] == 'stock']
    etf_assets = [a for a in assets if a['asset_type'] == 'etf']
    fund_assets = [a for a in assets if a['asset_type'] == 'fund']
    gold_assets = [a for a in assets if a['asset_type'] == 'gold']
    
    print(f"\nAssets to collect:")
    print(f"  Stocks: {len(stock_assets)}")
    print(f"  ETFs: {len(etf_assets)}")
    print(f"  Funds: {len(fund_assets)}")
    print(f"  Gold: {len(gold_assets)}")
    print(f"  Total: {len(assets)}")
    
    all_results = []
    crawl_time = datetime.now().isoformat()
    
    # Track what we collected vs what we couldn't
    collected = []
    failed = []
    
    # 1. Stocks
    if stock_assets:
        print(f"\n[1/4] Fetching {len(stock_assets)} stocks...")
        crawler = StockCrawler()
        results = crawler.crawl(stock_assets)
        all_results.extend(results)
        collected.extend([r['asset_code'] for r in results])
        failed.extend([a['asset_code'] for a in stock_assets if a['asset_code'] not in [r['asset_code'] for r in results]])
    
    # 2. ETFs
    if etf_assets:
        print(f"\n[2/4] Fetching {len(etf_assets)} ETFs...")
        crawler = StockCrawler()  # ETFs use same API as stocks
        results = crawler.crawl(etf_assets)
        all_results.extend(results)
        collected.extend([r['asset_code'] for r in results])
        failed.extend([a['asset_code'] for a in etf_assets if a['asset_code'] not in [r['asset_code'] for r in results]])
        
    # 3. Funds
    if fund_assets:
        print(f"\n[3/4] Fetching {len(fund_assets)} funds...")
        crawler = FundCrawler()
        results = crawler.crawl(fund_assets)
        all_results.extend(results)
        collected.extend([r['asset_code'] for r in results])
        failed.extend([a['asset_code'] for a in fund_assets if a['asset_code'] not in [r['asset_code'] for r in results]])
        
    # 4. Gold
    if gold_assets:
        print(f"\n[4/4] Fetching {len(gold_assets)} gold prices...")
        crawler = GoldCrawler()
        results = crawler.crawl(gold_assets)
        all_results.extend(results)
        collected.extend([r['asset_code'] for r in results])
        failed.extend([a['asset_code'] for a in gold_assets if a['asset_code'] not in [r['asset_code'] for r in results]])
    
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
    saved_count = 0
    if final_data:
        saved_count = save_data(final_data)
    
    # Print summary
    print("\n" + "=" * 60)
    print("COLLECTION SUMMARY")
    print("=" * 60)
    print(f"\nTotal assets in config: {len(assets)}")
    print(f"Successfully collected: {len(collected)}")
    print(f"Failed to collect: {len(failed)}")
    print(f"New records saved: {saved_count}")
    
    if collected:
        print(f"\n[OK] Collected ({len(collected)}):")
        for code in sorted(collected):
            # Find price
            price = next((r['price'] for r in all_results if r['asset_code'] == code), 0)
            source = next((r['source'] for r in all_results if r['asset_code'] == code), 'Unknown')
            print(f"     {code}: {price:,.0f} VND ({source})")
    
    if failed:
        print(f"\n[XX] Failed ({len(failed)}):")
        for code in sorted(failed):
            asset_type = asset_info_map.get(code, {}).get('asset_type', 'unknown')
            print(f"     {code} ({asset_type})")
        
        print("\n[!] Some assets could not be collected because:")
        print("    - Fund manager websites (VinaCapital, VCBF, SSIAM, Dragon Capital)")
        print("      block automated requests from this IP")
        print("    - Gold price websites (SJC, BTMC) have anti-bot protection")
        print("\n[!] Solutions:")
        print("    1. Use Selenium with a real browser (see SeleniumFundCrawler)")
        print("    2. Use a residential proxy service")
        print("    3. Run the script from a different network")
        print("    4. Enter data manually from official sources")
    
    print("\n" + "=" * 60)
    
    return len(collected), len(failed)


if __name__ == "__main__":
    main()
