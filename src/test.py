from crawlers import GoldCrawler
from utils import load_assets
from pathlib import Path
ASSETS_FILE = Path("data/assets.csv")
assets = load_assets(ASSETS_FILE)
fund_assets = [a for a in assets if a['asset_type'] == 'gold']
crawler = GoldCrawler()
crawler._crawl_giavang()