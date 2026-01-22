"""
Main orchestrator for daily asset price collection.

This script collects prices for Vietnamese financial assets:
- Stocks (9): HPG, FPT, MBB, SSI, POW, VCG, DGC, VND, VTP
- ETFs (3): FUEVFVND, E1VFVN30, FUESSVFL
- Open-end Funds (17): Various funds from VinaCapital, VCBF, SSI, Dragon Capital
- Gold (2): SJC Gold Bar, Gold Ring 9999

Usage:
    python -m src.main              # Basic mode (VNDirect only)
    python -m src.main --selenium   # Full mode with browser automation
    python -m src.main --headful    # Selenium with visible browser (for debugging)

Output:
    - data/daily_prices.csv (append-only, deduplicated by date+asset)
    - crawler.log (execution logs)
"""

import csv
import os
import sys
import argparse
import logging
from datetime import datetime
from src.crawlers import StockCrawler, FundCrawler, FmarketCrawler, GoldCrawler

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


def run_selenium_crawlers(fund_assets, gold_assets, headless=True):
    """
    Run Selenium-based crawlers for blocked fund and gold sources.
    
    Args:
        fund_assets: List of fund assets to crawl
        gold_assets: List of gold assets to crawl
        headless: Run browser in headless mode (default True)
        
    Returns:
        Tuple of (fund_results, gold_results)
    """
    fund_results = []
    gold_results = []
    
    try:
        from src.crawlers import SeleniumFundCrawler, SeleniumGoldCrawler
    except ImportError:
        logging.error("Selenium crawlers not available. Run: pip install selenium webdriver-manager")
        return fund_results, gold_results
    
    # Filter funds that need Selenium (not available on VNDirect)
    vndirect_funds = ['VESAF', 'VEOF']
    selenium_fund_assets = [a for a in fund_assets if a['asset_code'] not in vndirect_funds]
    
    if selenium_fund_assets:
        print(f"\n[Selenium] Crawling {len(selenium_fund_assets)} blocked funds...")
        try:
            with SeleniumFundCrawler(headless=headless) as crawler:
                fund_results = crawler.crawl(selenium_fund_assets)
        except Exception as e:
            logging.error(f"Selenium fund crawler failed: {e}")
    
    if gold_assets:
        print(f"\n[Selenium] Crawling {len(gold_assets)} gold prices...")
        try:
            with SeleniumGoldCrawler(headless=headless) as crawler:
                gold_results = crawler.crawl(gold_assets)
        except Exception as e:
            logging.error(f"Selenium gold crawler failed: {e}")
    
    return fund_results, gold_results


def main():
    """Main execution function."""
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Daily Asset Price Collection Tool')
    parser.add_argument('--selenium', action='store_true', 
                        help='Use Selenium for blocked fund/gold sources')
    parser.add_argument('--headful', action='store_true',
                        help='Run Selenium with visible browser (for debugging)')
    args = parser.parse_args()
    
    use_selenium = args.selenium or args.headful
    headless = not args.headful
    
    print("=" * 60)
    print("Daily Asset Price Collection Tool")
    if use_selenium:
        print(f"Mode: SELENIUM ({'headless' if headless else 'visible browser'})")
    else:
        print("Mode: API ONLY (use --selenium for full coverage)")
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
        
        # Primary: Use Fmarket API (works for ALL funds!)
        print("  Using Fmarket API...")
        fmarket_crawler = FmarketCrawler()
        fmarket_results = fmarket_crawler.crawl(fund_assets)
        all_results.extend(fmarket_results)
        collected.extend([r['asset_code'] for r in fmarket_results])
        
        fmarket_collected = [r['asset_code'] for r in fmarket_results]
        
        # Fallback 1: Try VNDirect for any funds not in Fmarket
        remaining = [a for a in fund_assets if a['asset_code'] not in fmarket_collected]
        if remaining:
            print(f"  Trying VNDirect for {len(remaining)} remaining funds...")
            vnd_crawler = FundCrawler()
            vnd_results = vnd_crawler.crawl(remaining)
            all_results.extend(vnd_results)
            collected.extend([r['asset_code'] for r in vnd_results])
        
        # Fallback 2: Selenium if enabled and funds still missing
        if use_selenium:
            remaining_for_selenium = [a for a in fund_assets if a['asset_code'] not in collected]
            if remaining_for_selenium:
                print(f"  Using Selenium for {len(remaining_for_selenium)} remaining funds...")
                selenium_fund_results, _ = run_selenium_crawlers(remaining_for_selenium, [], headless)
                all_results.extend(selenium_fund_results)
                collected.extend([r['asset_code'] for r in selenium_fund_results])
        
        # Update failed list
        all_collected_funds = [r['asset_code'] for r in all_results if asset_info_get(fund_assets, r['asset_code'])]
        failed.extend([a['asset_code'] for a in fund_assets if a['asset_code'] not in all_collected_funds])
        
    # 4. Gold
    if gold_assets:
        print(f"\n[4/4] Fetching {len(gold_assets)} gold prices...")
        
        # First try regular crawler
        crawler = GoldCrawler()
        results = crawler.crawl(gold_assets)
        all_results.extend(results)
        collected.extend([r['asset_code'] for r in results])
        
        gold_collected = [r['asset_code'] for r in results]
        
        # If Selenium mode and some gold prices missing, try Selenium
        if use_selenium:
            remaining_gold = [a for a in gold_assets if a['asset_code'] not in gold_collected]
            if remaining_gold:
                _, selenium_gold_results = run_selenium_crawlers([], remaining_gold, headless)
                all_results.extend(selenium_gold_results)
                collected.extend([r['asset_code'] for r in selenium_gold_results])
        
        # Update failed list for gold
        all_collected_gold = [r['asset_code'] for r in all_results if r['asset_code'].startswith('GOLD_')]
        failed.extend([a['asset_code'] for a in gold_assets if a['asset_code'] not in all_collected_gold])
    
    # Remove duplicates from failed (in case of re-processing)
    collected = list(dict.fromkeys(collected))
    failed = [f for f in list(dict.fromkeys(failed)) if f not in collected]
    
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
        
        print("\n[!] Some assets could not be collected.")
        print("    Possible reasons:")
        print("    - API returned no data for this asset")
        print("    - Gold price websites have anti-bot protection")
        if not use_selenium:
            print("\n[!] Try running with --selenium flag for gold prices:")
            print("    python -m src.main --selenium")
    
    print("\n" + "=" * 60)
    
    return len(collected), len(failed)


def asset_info_get(assets, code):
    """Helper to check if code exists in asset list."""
    return any(a['asset_code'] == code for a in assets)


if __name__ == "__main__":
    main()
