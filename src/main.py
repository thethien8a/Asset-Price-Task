from crawlers import StockCrawler, FmarketCrawler, GoldCrawler
from config import DATA_FILE, ASSETS_FILE
from utils import load_assets, save_data, save_to_gsheet
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

    # Enrich and save data
    if not all_results:
        print("\n[!] No data collected. Skipping save.")
        return

    crawl_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    # Create DataFrames with meaningful names
    results_df = pd.DataFrame(all_results)
    assets_df = pd.DataFrame(assets).drop(columns=['asset_id'], errors='ignore')
    
    # Merge and enrich using method chaining
    result_df = (
        results_df
        .merge(assets_df, on='asset_code', how='left')
        .assign(
            crawl_time=crawl_time,
            currency="VND"
        )
    )
    
    final_data = result_df.to_dict(orient='records')
    # Save to Google Sheets
    print("\n[Connecting] Đang đẩy dữ liệu lên Google Sheets...")
    # Thay "Asset-Price-Tracker" bằng tên file Google Sheet của ông nếu khác
    gsheet_count = save_to_gsheet(final_data, sheet_name="assets-crawl")
    
    print(f"\n[Success] Processed {len(all_results)} assets.")
    print(f"          Saved {gsheet_count} new records to Google Sheets.")


if __name__ == "__main__":
    main()
