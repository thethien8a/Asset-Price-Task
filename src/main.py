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
from crawlers import StockCrawler, FmarketCrawler, GoldCrawler
from config import DATA_FILE, ASSETS_FILE
from utils import load_assets, save_data
import pandas as pd
from datetime import datetime
def main():
    """Main execution function."""
    assets = load_assets(ASSETS_FILE)
    
    # Group assets by type
    stock_assets = [a for a in assets if a['asset_type'] == 'stock']
    etf_assets = [a for a in assets if a['asset_type'] == 'etf']
    fund_assets = [a for a in assets if a['asset_type'] == 'fund']
    gold_assets = [a for a in assets if a['asset_type'] == 'gold']
    
    print(f"\nAssets to collect:")
    print(f"Stocks: {len(stock_assets)}")
    print(f"ETFs: {len(etf_assets)}")
    print(f"Funds: {len(fund_assets)}")
    print(f"Gold: {len(gold_assets)}")
    print(f"Total: {len(assets)}")
    
    all_results = []
    
    # 1. Stocks
    if stock_assets:
        print(f"\n[1/4] Fetching {len(stock_assets)} stocks...")
        crawler = StockCrawler()
        results = crawler.crawl(stock_assets)
        all_results.extend(results)

    # 2. ETFs
    if etf_assets:
        print(f"\n[2/4] Fetching {len(etf_assets)} ETFs...")
        crawler = StockCrawler() 
        results = crawler.crawl(etf_assets)
        all_results.extend(results)
        
    # 3. Funds
    if fund_assets:
        print(f"\n[3/4] Fetching {len(fund_assets)} funds...")
        print("  Using Fmarket API...")
        fmarket_crawler = FmarketCrawler()
        fmarket_results = fmarket_crawler.crawl(fund_assets)
        all_results.extend(fmarket_results)
 
    # 4. Gold
    if gold_assets:
        print(f"\n[4/4] Fetching {len(gold_assets)} gold prices...")
        crawler = GoldCrawler()
        results = crawler.crawl(gold_assets)
        all_results.extend(results)

    # Enrich data
    crawl_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    df_1 = pd.DataFrame(all_results)
    df_2 = pd.DataFrame(assets)
    df_2.drop(columns=['asset_id'], inplace=True)
    result_df = pd.merge(df_1, df_2, on='asset_code', how='left')
    result_df['crawl_time'] = crawl_time
    result_df["currency"] = "VND"
    
    

if __name__ == "__main__":
    main()
