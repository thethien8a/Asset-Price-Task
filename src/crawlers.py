"""
Asset Price Crawlers for Vietnamese Financial Markets

This module provides crawlers for:
- Stocks (9): HPG, FPT, MBB, SSI, POW, VCG, DGC, VND, VTP
- ETFs (3): FUEVFVND, E1VFVN30, FUESSVFL  
- Open-end Funds (17): Various VinaCapital, VCBF, SSI, Dragon Capital funds
- Gold (2): SJC Gold Bar, Gold Ring 9999

IMPORTANT: Due to IP blocking from Vietnamese financial websites, not all
sources work from all network environments. This implementation uses:
- VNDirect API: Works for stocks, ETFs, and some funds (VESAF, VEOF)
- giavang.org: Attempted for gold prices (may return stale data)

For full fund coverage, use Selenium with --selenium flag:
    python -m src.main --selenium
"""
from tkinter import Button
import bs4
import logging
import re
from datetime import datetime
import time
from utils import make_request

# Base class for all API Crawler
class BaseCrawler:
    """Base crawler class."""
    def crawl(self, assets):
        raise NotImplementedError


class StockCrawler(BaseCrawler):
    """
    Crawl stock and ETF prices using VNDirect API.
    This is the most reliable source - works from most IP addresses.
    """
    
    def crawl(self, assets):
        """
        Crawl stock/ETF prices from VNDirect dchart API.
        
        Args:
            assets: List of asset dicts with 'asset_code' key
            
        Returns:
            List of price result dicts
        """
        results = []
        end_time = int(time.time())
        start_time = end_time - 7 * 24 * 3600  
        
        for asset in assets:
            symbol = asset['asset_code']
            url = f"https://dchart-api.vndirect.com.vn/dchart/history?resolution=D&symbol={symbol}&from={start_time}&to={end_time}"
            
            logging.info(f"Crawling stock/ETF: {symbol}")
            response = make_request(url)
            
            if response and response.status_code == 200:
                try:
                    data = response.json()
                    if data and isinstance(data, dict) and len(data.get('t', [])) > 0:
                        last_idx = -1
                        price = float(data['c'][last_idx])
                        timestamp = data['t'][last_idx]
                        data_date = datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d')
                        
                        # Normalize price to VND (VNDirect returns price in thousands)
                        final_price = price * 1000
                        
                        results.append({
                            'asset_code': symbol,
                            'price': final_price,
                            'date': data_date,
                            'source': 'VNDirect'
                        })
                        logging.info(f"  {symbol}: {final_price:,.0f} VND")
                    else:
                        logging.warning(f"No data found for {symbol}")
                except Exception as e:
                    logging.error(f"Error parsing data for {symbol}: {e}")
            else:
                status = response.status_code if response else 'No response'
                logging.error(f"Failed to fetch {symbol}: {status}")
            
            time.sleep(0.5)   
        
        return results


class FmarketCrawler(BaseCrawler):
    """
    Crawl fund NAV prices from Fmarket API.
    
    This API provides NAV data for most Vietnamese open-end funds including:
    - VinaCapital: VESAF, VEOF, VMEEF, VDEF, VIBF, VFF, VLGF
    - VCBF: VCBFMGF, VCBFBCF, VCBFAIF, VCBFTBF, VCBFFIF
    - SSI: SSISCA, SSIBF
    - Dragon Capital: DCDS, DCDE, DCBF
    
    This is the RECOMMENDED crawler for fund data - works without Selenium.
    """
    
    API_URL = 'https://api.fmarket.vn/res/products/filter'
    
    def crawl(self, assets):
        """
        Crawl fund NAV prices from Fmarket API.
        
        Args:
            assets: List of fund asset dicts
            
        Returns:
            List of price result dicts
        """
        results = []
        today_str = datetime.now().strftime('%Y-%m-%d')
        
        # Fetch all trading funds from Fmarket
        logging.info("Fetching fund NAVs from Fmarket API...")
        fmarket_data = self._fetch_fmarket_funds()
        
        if not fmarket_data:
            logging.warning("Failed to fetch data from Fmarket API")
            return results
        
        list_assets = set([a['asset_code'] for a in assets])

        for fund in fmarket_data:
            code = fund.get('code', '')
            short_name = fund.get('shortName', '')
            nav = fund.get('nav', 0)
            if code in list_assets:
                results.append({
                    'asset_code': code,
                    'price': nav,
                    'date': today_str,
                    'source': 'Fmarket'
                })
            elif short_name in list_assets:
                results.append({
                    'asset_code': short_name,
                    'price': nav,
                    'date': today_str,
                    'source': 'Fmarket'
                })
        
        if len(list_assets) != len(results):
            logging.warning(f"Assets: {[a['asset_code'] for a in assets if a['asset_code'] not in [r['asset_code'] for r in results]]} not crawled by FmarketCrawler")          
        
        return results
    
    def _fetch_fmarket_funds(self):
        """Fetch all trading funds from Fmarket API."""
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'application/json',
            'Content-Type': 'application/json',
            'Origin': 'https://fmarket.vn',
            'Referer': 'https://fmarket.vn/'
        }
        
        all_funds = []
        
        # Fetch both NEW_FUND and TRADING_FUND types
        for fund_type in ['TRADING_FUND', 'NEW_FUND']:
            payload = {
                'isIpo': False,
                'page': 1,
                'pageSize': 200,
                'types': [fund_type]
            }
            
            try:
                response = make_request(
                    self.API_URL,
                    method='POST',
                    headers=headers,
                    payload=payload
                )
                
                if response and response.status_code == 200:
                    data = response.json()
                    rows = data.get('data', {}).get('rows', [])
                    all_funds.extend(rows)
                    logging.info(f"Fetched {len(rows)} {fund_type} funds")
                else:
                    status = response.status_code if response else 'No response'
                    logging.warning(f"Failed to fetch {fund_type}: {status}")
                    
            except Exception as e:
                logging.error(f"Error fetching {fund_type}: {e}")
        
        return all_funds


class GoldCrawler(BaseCrawler):
    """
    Crawl gold prices from Vietnamese sources.
    
    IMPORTANT: Most gold price websites (SJC, BTMC, PNJ) block automated requests.
    giavang.org sometimes works but may return stale/incorrect data.
    
    For reliable gold prices, use --selenium flag.
    """
    
    def crawl(self, assets):
        """
        Attempt to crawl gold prices.
        
        Returns prices only if reliable data is obtained.
        """
        results = []
        today_str = datetime.now().strftime('%Y-%m-%d')
        
        # Try giavang.org
        logging.info("Attempting to fetch gold prices from giavang.org...")
        gold_prices = self._crawl_giavang()
        
        for asset in assets:
            code = asset['asset_code']
            try:
                if code == 'GOLD_SJC' and gold_prices.get('sjc'):
                    price = gold_prices['sjc']
                    results.append({
                        'asset_code': code,
                        'price': price,
                        'date': today_str,
                        'source': 'giavang.org'
                    })
                    logging.info(f"GOLD_SJC: {price:,.0f} VND")
                
                elif code == 'GOLD_RING' and gold_prices.get('ring'):
                    price = gold_prices['ring']
                    results.append({
                        'asset_code': code,
                        'price': price,
                        'date': today_str,
                        'source': 'giavang.org'
                    })
                    logging.info(f"GOLD_RING: {price:,.0f} VND")
            except Exception as e:
                logging.error(f"Error crawling giavang.org: {e}")
                return None
            
        return results
    
    def _crawl_giavang(self):
        """
        Crawl gold prices from giavang.org.
        
        Returns dict with 'sjc' and 'ring' prices if found.
        """
        result: dict = {'sjc': None, 'ring': None}
        url = "https://giavang.org/"
        
        response = make_request(url)
        if response and response.status_code == 200:
            try:
                soup = bs4.BeautifulSoup(response.text, 'html.parser')
                # Find the gold-price-box containing both SJC and Ring prices
                gold_price_box = soup.find('div', class_='gold-price-box')
                if gold_price_box:
                    # Find all buy boxes (box-cgre) - first is SJC, second is Ring
                    buy_boxes = gold_price_box.find_all('div', class_='box-cgre')
                    if len(buy_boxes) >= 1:
                        result['sjc'] = self._parse_price_from_box(buy_boxes[0])
                    if len(buy_boxes) >= 2:
                        result['ring'] = self._parse_price_from_box(buy_boxes[1])
                return result      
            except Exception as e:
                raise e

    def _parse_price_from_box(self, buy_box):
        """Parse price from a box-cgre element."""
        if buy_box:
            price_span = buy_box.find('span', class_='gold-price')
            if price_span:
                # Lấy ra giá
                price_text = price_span.get_text()
                price_match = re.search(r'([\d.]+)', price_text)
                if price_match:
                    price_str = price_match.group(1).replace('.', '')
                    price = int(price_str) * 1000
                    return price
        return None