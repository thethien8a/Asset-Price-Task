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

For full fund coverage, consider using Selenium with a real browser.
"""

import json
import logging
import re
from datetime import datetime
import time
from src.utils import make_request

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
        start_time = end_time - 7 * 24 * 3600  # Last 7 days
        
        for asset in assets:
            symbol = asset['asset_code']
            url = f"https://dchart-api.vndirect.com.vn/dchart/history?resolution=D&symbol={symbol}&from={start_time}&to={end_time}"
            
            logging.info(f"Crawling stock/ETF: {symbol}")
            response = make_request(url, headers={'User-Agent': 'Mozilla/5.0'})
            
            if response and response.status_code == 200:
                try:
                    data = response.json()
                    if data and isinstance(data, dict) and len(data.get('t', [])) > 0:
                        last_idx = -1
                        price = float(data['c'][last_idx])
                        timestamp = data['t'][last_idx]
                        data_date = datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d')
                        
                        # Normalize price to VND (VNDirect returns price in thousands)
                        final_price = price
                        if price < 500:
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
            
            time.sleep(0.5)  # Rate limiting
        
        return results


class FundCrawler(BaseCrawler):
    """
    Crawl open-end fund NAV prices.
    
    Strategy:
    1. Try VNDirect API first (works for VESAF, VEOF, and ETFs)
    2. For other funds, return empty (APIs are blocked)
    
    NOTE: Most fund manager websites (VinaCapital, VCBF, SSIAM, Dragon Capital)
    block requests from cloud/server IPs. For full coverage, use Selenium.
    """
    
    # Funds that are available on VNDirect (exchange-listed)
    VNDIRECT_FUNDS = ['VESAF', 'VEOF']
    
    def crawl(self, assets):
        """
        Crawl fund NAV prices.
        
        Args:
            assets: List of fund asset dicts
            
        Returns:
            List of price result dicts (only for available funds)
        """
        results = []
        
        # Separate funds into VNDirect-available and others
        vnd_assets = [a for a in assets if a['asset_code'] in self.VNDIRECT_FUNDS]
        other_assets = [a for a in assets if a['asset_code'] not in self.VNDIRECT_FUNDS]
        
        # 1. Get VNDirect funds using same API as stocks
        if vnd_assets:
            logging.info(f"Fetching {len(vnd_assets)} funds from VNDirect...")
            vnd_results = self._crawl_vndirect(vnd_assets)
            results.extend(vnd_results)
        
        # 2. Log warning for unavailable funds
        if other_assets:
            unavailable = [a['asset_code'] for a in other_assets]
            logging.warning(f"Cannot fetch {len(other_assets)} funds - APIs blocked: {unavailable}")
            logging.warning("Consider using Selenium-based crawler for these funds")
        
        return results
    
    def _crawl_vndirect(self, assets):
        """Fetch fund prices from VNDirect API."""
        results = []
        end_time = int(time.time())
        start_time = end_time - 30 * 24 * 3600  # Last 30 days for funds
        
        for asset in assets:
            symbol = asset['asset_code']
            url = f"https://dchart-api.vndirect.com.vn/dchart/history?resolution=D&symbol={symbol}&from={start_time}&to={end_time}"
            
            logging.info(f"Crawling fund: {symbol}")
            response = make_request(url, headers={'User-Agent': 'Mozilla/5.0'})
            
            if response and response.status_code == 200:
                try:
                    data = response.json()
                    if data and isinstance(data, dict) and len(data.get('t', [])) > 0:
                        price = float(data['c'][-1])
                        timestamp = data['t'][-1]
                        data_date = datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d')
                        
                        # Normalize to VND
                        if price < 1000:
                            price = price * 1000
                        
                        results.append({
                            'asset_code': symbol,
                            'price': round(price, 2),
                            'date': data_date,
                            'source': 'VNDirect'
                        })
                        logging.info(f"  {symbol}: {price:,.0f} VND")
                except Exception as e:
                    logging.error(f"Error parsing fund {symbol}: {e}")
            
            time.sleep(0.5)
        
        return results


class GoldCrawler(BaseCrawler):
    """
    Crawl gold prices from Vietnamese sources.
    
    IMPORTANT: Most gold price websites (SJC, BTMC, PNJ) block automated requests.
    giavang.org sometimes works but may return stale/incorrect data.
    
    For reliable gold prices, consider:
    1. Using Selenium with real browser
    2. Official SJC/BTMC mobile app APIs (if available)
    3. Manual data entry from official sources
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
            
            if code == 'GOLD_SJC' and gold_prices.get('sjc'):
                price = gold_prices['sjc']
                # Validate price is in reasonable range (75-95 million VND as of 2024-2026)
                if 75_000_000 < price < 95_000_000:
                    results.append({
                        'asset_code': code,
                        'price': price,
                        'date': today_str,
                        'source': 'giavang.org'
                    })
                    logging.info(f"  GOLD_SJC: {price:,.0f} VND")
                else:
                    logging.warning(f"GOLD_SJC price {price:,.0f} out of expected range, skipping")
            
            elif code == 'GOLD_RING' and gold_prices.get('ring'):
                price = gold_prices['ring']
                # Ring gold usually cheaper than SJC
                if 70_000_000 < price < 90_000_000:
                    results.append({
                        'asset_code': code,
                        'price': price,
                        'date': today_str,
                        'source': 'giavang.org'
                    })
                    logging.info(f"  GOLD_RING: {price:,.0f} VND")
                else:
                    logging.warning(f"GOLD_RING price {price:,.0f} out of expected range, skipping")
        
        if not results:
            logging.warning("Could not obtain valid gold prices from any source")
            logging.warning("Gold price sources are blocking automated requests")
        
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
                response.encoding = 'utf-8'
                html = response.text
                
                # Look for SJC price - format: XX.XXX.XXX or XX,XXX,XXX
                # SJC prices should be in 80-90 million range
                sjc_pattern = re.findall(r'SJC[^<>]{0,100}?(8[0-9][,\.]\d{3}[,\.]\d{3})', html, re.IGNORECASE | re.DOTALL)
                if sjc_pattern:
                    for price_str in sjc_pattern:
                        try:
                            price = float(price_str.replace('.', '').replace(',', ''))
                            if 75_000_000 < price < 95_000_000:
                                result['sjc'] = price
                                break
                        except:
                            continue
                
                # Look for ring/nhan gold
                ring_pattern = re.findall(r'[Nn]h[aẫ]n[^<>]{0,100}?(8[0-9][,\.]\d{3}[,\.]\d{3})', html, re.DOTALL)
                if ring_pattern:
                    for price_str in ring_pattern:
                        try:
                            price = float(price_str.replace('.', '').replace(',', ''))
                            if 70_000_000 < price < 95_000_000:
                                result['ring'] = price
                                break
                        except:
                            continue
                
            except Exception as e:
                logging.error(f"Error parsing giavang.org: {e}")
        else:
            logging.warning("Failed to fetch giavang.org")
        
        return result


# Optional: Selenium-based crawler for blocked sites
class SeleniumFundCrawler:
    """
    Selenium-based crawler for fund NAV data from websites that block regular requests.
    
    Requirements:
    - pip install selenium
    - Chrome/Firefox browser installed
    - ChromeDriver/GeckoDriver in PATH
    
    Usage:
        crawler = SeleniumFundCrawler()
        results = crawler.crawl_all()
    """
    
    def __init__(self, headless=True):
        """Initialize Selenium crawler (lazy loading)."""
        self.headless = headless
        self.driver = None
    
    def _init_driver(self):
        """Initialize Chrome WebDriver."""
        if self.driver is not None:
            return
        
        try:
            from selenium import webdriver
            from selenium.webdriver.chrome.options import Options
            
            options = Options()
            if self.headless:
                options.add_argument('--headless')
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument('--disable-gpu')
            options.add_argument('--window-size=1920,1080')
            options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
            
            self.driver = webdriver.Chrome(options=options)
            logging.info("Selenium WebDriver initialized")
        except ImportError:
            logging.error("Selenium not installed. Run: pip install selenium")
            raise
        except Exception as e:
            logging.error(f"Failed to initialize Selenium: {e}")
            raise
    
    def close(self):
        """Close the WebDriver."""
        if self.driver:
            self.driver.quit()
            self.driver = None
    
    def crawl_vcbf(self):
        """Crawl VCBF fund NAV from their website."""
        self._init_driver()
        results = {}
        
        if self.driver is None:
            logging.error("WebDriver not initialized")
            return results
        
        fund_pages = {
            'VCBFMGF': 'https://www.vcbf.com/quy-mo/cac-quy-mo/quy-dau-tu-co-phieu-tang-truong-vcbf-vcbf-mgf/',
            'VCBFBCF': 'https://www.vcbf.com/quy-mo/cac-quy-mo/quy-dau-tu-co-phieu-hang-dau-vcbf-vcbf-bcf/',
            'VCBFFIF': 'https://www.vcbf.com/quy-mo/cac-quy-mo/quy-dau-tu-trai-phieu-vcbf-vcbf-fif/',
        }
        
        for code, url in fund_pages.items():
            try:
                self.driver.get(url)
                time.sleep(3)  # Wait for page load
                
                html = self.driver.page_source
                nav_matches = re.findall(r'NAV[^<>]*?(\d{2}[,\.]\d{3}(?:\.\d+)?)', html, re.IGNORECASE)
                
                if nav_matches:
                    for m in nav_matches:
                        price = float(m.replace(',', '').replace('.', ''))
                        if 10000 < price < 100000:
                            results[code] = price
                            logging.info(f"Selenium: {code} = {price:,.0f} VND")
                            break
            except Exception as e:
                logging.error(f"Selenium error for {code}: {e}")
        
        return results
    
    def crawl_gold_sjc(self):
        """Crawl gold prices from SJC website using Selenium."""
        self._init_driver()
        
        if self.driver is None:
            logging.error("WebDriver not initialized")
            return None
        
        try:
            self.driver.get('https://sjc.com.vn/')
            time.sleep(5)  # Wait for dynamic content
            
            html = self.driver.page_source
            
            # Look for SJC gold prices
            prices = re.findall(r'(8[0-9][,\.]\d{3}[,\.]\d{3})', html)
            
            if prices:
                for p in prices:
                    price = float(p.replace('.', '').replace(',', ''))
                    if 75_000_000 < price < 95_000_000:
                        logging.info(f"Selenium: GOLD_SJC = {price:,.0f} VND")
                        return price
        except Exception as e:
            logging.error(f"Selenium error for SJC gold: {e}")
        
        return None
