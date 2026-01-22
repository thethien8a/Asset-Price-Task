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
            logging.warning("Use --selenium flag for these funds")
        
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
    
    # Map our fund codes to Fmarket's shortName format
    CODE_MAPPING = {
        'VESAF': 'VESAF',
        'VEOF': 'VEOF', 
        'VMEEF': 'VMEEF',
        'VDEF': 'VDEF',
        'VIBF': 'VIBF',
        'VFF': 'VFF',
        'VLGF': 'VLGF',
        'VCBFMGF': 'VCBF-MGF',
        'VCBFBCF': 'VCBF-BCF',
        'VCBFAIF': 'VCBF-AIF',
        'VCBFTBF': 'VCBF-TBF',
        'VCBFFIF': 'VCBF-FIF',
        'SSISCA': 'SSISCA',
        'SSIBF': 'SSIBF',
        'DCDS': 'DCDS',
        'DCDE': 'DCDE',
        'DCBF': 'DCBF',
    }
    
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
        
        # Create a lookup by normalized code
        nav_lookup = {}
        for fund in fmarket_data:
            short_name = fund.get('shortName', '')
            nav = fund.get('nav', 0)
            if short_name and nav and nav > 0:
                # Normalize: remove hyphens and spaces, uppercase
                normalized = short_name.replace('-', '').replace(' ', '').upper()
                nav_lookup[normalized] = {'nav': nav, 'api_code': short_name}
                nav_lookup[short_name.upper()] = {'nav': nav, 'api_code': short_name}
        
        # Match our assets to Fmarket data
        for asset in assets:
            code = asset['asset_code']
            
            # Try direct match first
            normalized_code = code.replace('-', '').replace(' ', '').upper()
            
            if normalized_code in nav_lookup:
                nav_data = nav_lookup[normalized_code]
                results.append({
                    'asset_code': code,
                    'price': round(nav_data['nav'], 2),
                    'date': today_str,
                    'source': 'Fmarket'
                })
                logging.info(f"  {code}: {nav_data['nav']:,.2f} VND (Fmarket)")
            else:
                # Try mapping
                fmarket_code = self.CODE_MAPPING.get(code, code)
                fmarket_normalized = fmarket_code.replace('-', '').replace(' ', '').upper()
                
                if fmarket_normalized in nav_lookup:
                    nav_data = nav_lookup[fmarket_normalized]
                    results.append({
                        'asset_code': code,
                        'price': round(nav_data['nav'], 2),
                        'date': today_str,
                        'source': 'Fmarket'
                    })
                    logging.info(f"  {code}: {nav_data['nav']:,.2f} VND (Fmarket)")
                else:
                    logging.warning(f"  {code}: Not found in Fmarket data")
        
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
                    logging.info(f"  Fetched {len(rows)} {fund_type} funds")
                else:
                    status = response.status_code if response else 'No response'
                    logging.warning(f"  Failed to fetch {fund_type}: {status}")
                    
            except Exception as e:
                logging.error(f"  Error fetching {fund_type}: {e}")
        
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
            logging.warning("Use --selenium flag for gold prices")
        
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


# ============================================================================
# SELENIUM-BASED CRAWLERS
# Use these when regular API requests are blocked
# ============================================================================

class SeleniumCrawler:
    """
    Base Selenium crawler with automatic WebDriver management.
    
    Requirements:
    - pip install selenium webdriver-manager
    - Chrome browser installed (WebDriver auto-downloaded)
    
    Usage:
        python -m src.main --selenium
    """
    
    def __init__(self, headless=True, timeout=30):
        """Initialize Selenium crawler (lazy loading)."""
        self.headless = headless
        self.timeout = timeout
        self.driver = None
    
    def _init_driver(self):
        """Initialize Chrome WebDriver with automatic driver management."""
        if self.driver is not None:
            return True
        
        try:
            from selenium import webdriver
            from selenium.webdriver.chrome.options import Options
            from selenium.webdriver.chrome.service import Service
            import os
            
            options = Options()
            if self.headless:
                options.add_argument('--headless=new')
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument('--disable-gpu')
            options.add_argument('--window-size=1920,1080')
            options.add_argument('--disable-blink-features=AutomationControlled')
            options.add_argument('--disable-extensions')
            options.add_argument('--disable-infobars')
            options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
            
            # Method 1: Try auto-detect (Chrome 115+ has built-in chromedriver)
            try:
                logging.info("Initializing Chrome WebDriver...")
                self.driver = webdriver.Chrome(options=options)
                self.driver.set_page_load_timeout(self.timeout)
                self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
                logging.info("Selenium WebDriver initialized successfully")
                return True
            except Exception as e:
                logging.warning(f"Auto-detect Chrome failed: {e}, trying webdriver-manager...")
            
            # Method 2: Fallback to webdriver-manager
            try:
                os.environ['WDM_LOG'] = '0'
                os.environ['WDM_LOCAL'] = '1'
                from webdriver_manager.chrome import ChromeDriverManager
                driver_path = ChromeDriverManager().install()
                service = Service(driver_path)
                self.driver = webdriver.Chrome(service=service, options=options)
                self.driver.set_page_load_timeout(self.timeout)
                self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
                logging.info("Selenium WebDriver initialized with webdriver-manager")
                return True
            except Exception as e:
                logging.error(f"webdriver-manager also failed: {e}")
            
            logging.error("Could not initialize Chrome WebDriver")
            return False
            
        except ImportError as e:
            logging.error("Selenium not installed. Run: pip install selenium webdriver-manager")
            return False
        except Exception as e:
            logging.error(f"Failed to initialize Selenium: {e}")
            return False
    
    def close(self):
        """Close the WebDriver."""
        if self.driver:
            try:
                self.driver.quit()
            except:
                pass
            self.driver = None
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


class SeleniumFundCrawler(SeleniumCrawler):
    """
    Selenium-based crawler for fund NAV data from websites that block regular requests.
    
    Supported fund sources:
    - VinaCapital: VMEEF, VDEF, VIBF, VFF, VLGF
    - VCBF: VCBFMGF, VCBFBCF, VCBFAIF, VCBFTBF, VCBFFIF
    - SSI: SSISCA, SSIBF
    - Dragon Capital: DCDS, DCDE, DCBF
    """
    
    # Fund URL mappings
    VINACAPITAL_FUNDS = {
        'VMEEF': 'https://vinacapital.com/investment-solutions/onshore-funds/vmeef/',
        'VDEF': 'https://vinacapital.com/investment-solutions/onshore-funds/vdef/',
        'VIBF': 'https://vinacapital.com/investment-solutions/onshore-funds/vibf/',
        'VFF': 'https://vinacapital.com/investment-solutions/onshore-funds/vff/',
        'VLGF': 'https://vinacapital.com/investment-solutions/onshore-funds/vlgf/',
    }
    
    VCBF_FUNDS = {
        'VCBFMGF': 'https://www.vcbf.com/quy-mo/cac-quy-mo/quy-dau-tu-co-phieu-tang-truong-vcbf-vcbf-mgf/',
        'VCBFBCF': 'https://www.vcbf.com/quy-mo/cac-quy-mo/quy-dau-tu-co-phieu-hang-dau-vcbf-vcbf-bcf/',
        'VCBFAIF': 'https://www.vcbf.com/quy-mo/cac-quy-mo/quy-dau-tu-linh-hoat-vcbf-vcbf-aif/',
        'VCBFTBF': 'https://www.vcbf.com/quy-mo/cac-quy-mo/quy-dau-tu-can-bang-chien-luoc-vcbf-vcbf-tbf/',
        'VCBFFIF': 'https://www.vcbf.com/quy-mo/cac-quy-mo/quy-dau-tu-trai-phieu-vcbf-vcbf-fif/',
    }
    
    SSI_FUNDS = {
        'SSISCA': 'https://www.ssinam.com.vn/en/ssisca',
        'SSIBF': 'https://www.ssinam.com.vn/en/ssibf',
    }
    
    DRAGON_FUNDS = {
        'DCDS': 'https://dcvfm.com.vn/quy-mo/dcds/',
        'DCDE': 'https://dcvfm.com.vn/quy-mo/dcde/',
        'DCBF': 'https://dcvfm.com.vn/quy-mo/dcbf/',
    }
    
    def crawl(self, assets):
        """
        Crawl fund NAV prices using Selenium.
        
        Args:
            assets: List of fund asset dicts
            
        Returns:
            List of price result dicts
        """
        if not self._init_driver():
            logging.error("Cannot initialize Selenium WebDriver")
            return []
        
        results = []
        today_str = datetime.now().strftime('%Y-%m-%d')
        
        asset_codes = [a['asset_code'] for a in assets]
        
        # Crawl VinaCapital funds
        for code in asset_codes:
            if code in self.VINACAPITAL_FUNDS:
                price = self._crawl_vinacapital(code, self.VINACAPITAL_FUNDS[code])
                if price:
                    results.append({
                        'asset_code': code,
                        'price': price,
                        'date': today_str,
                        'source': 'VinaCapital (Selenium)'
                    })
        
        # Crawl VCBF funds
        for code in asset_codes:
            if code in self.VCBF_FUNDS:
                price = self._crawl_vcbf(code, self.VCBF_FUNDS[code])
                if price:
                    results.append({
                        'asset_code': code,
                        'price': price,
                        'date': today_str,
                        'source': 'VCBF (Selenium)'
                    })
        
        # Crawl SSI funds
        for code in asset_codes:
            if code in self.SSI_FUNDS:
                price = self._crawl_ssi(code, self.SSI_FUNDS[code])
                if price:
                    results.append({
                        'asset_code': code,
                        'price': price,
                        'date': today_str,
                        'source': 'SSI (Selenium)'
                    })
        
        # Crawl Dragon Capital funds
        for code in asset_codes:
            if code in self.DRAGON_FUNDS:
                price = self._crawl_dragon(code, self.DRAGON_FUNDS[code])
                if price:
                    results.append({
                        'asset_code': code,
                        'price': price,
                        'date': today_str,
                        'source': 'DragonCapital (Selenium)'
                    })
        
        return results
    
    def _crawl_vinacapital(self, code, url):
        """Crawl NAV from VinaCapital website."""
        try:
            logging.info(f"Selenium: Crawling {code} from VinaCapital...")
            self.driver.get(url)
            time.sleep(4)  # Wait for dynamic content
            
            html = self.driver.page_source
            
            # VinaCapital format: NAV/unit: XX,XXX.XX VND
            # Look for patterns like "23,456" or "23456.78"
            nav_patterns = [
                r'NAV[^<>]*?(\d{2,3}[,\.]\d{3}(?:\.\d+)?)',  # 23,456 or 23,456.78
                r'NAV[/\s]+[Uu]nit[^<>]*?(\d{2,3}[,\.]\d{3})',
                r'Gi[áa]\s+tr[ịi]\s+t[àa]i\s+s[ảa]n[^<>]*?(\d{2,3}[,\.]\d{3})',
            ]
            
            for pattern in nav_patterns:
                matches = re.findall(pattern, html, re.IGNORECASE | re.DOTALL)
                if matches:
                    for m in matches:
                        try:
                            # Clean price string
                            price_str = m.replace(',', '')
                            if '.' in price_str and len(price_str.split('.')[-1]) == 3:
                                # Vietnamese format: 23.456 means 23456
                                price_str = price_str.replace('.', '')
                            price = float(price_str)
                            
                            # Valid NAV range: 10,000 - 100,000 VND per unit
                            if 10000 < price < 100000:
                                logging.info(f"  {code}: {price:,.0f} VND")
                                return price
                        except:
                            continue
            
            logging.warning(f"  {code}: Could not extract NAV from page")
            return None
            
        except Exception as e:
            logging.error(f"  {code}: Selenium error - {e}")
            return None
    
    def _crawl_vcbf(self, code, url):
        """Crawl NAV from VCBF website."""
        try:
            logging.info(f"Selenium: Crawling {code} from VCBF...")
            self.driver.get(url)
            time.sleep(4)
            
            html = self.driver.page_source
            
            # VCBF format varies, look for NAV patterns
            nav_patterns = [
                r'NAV[^<>]*?(\d{2,3}[,\.]\d{3}(?:\.\d+)?)',
                r'(\d{2,3}[,\.]\d{3})\s*VND',
                r'Gi[áa]\s+tr[ịi][^<>]*?(\d{2,3}[,\.]\d{3})',
            ]
            
            for pattern in nav_patterns:
                matches = re.findall(pattern, html, re.IGNORECASE | re.DOTALL)
                if matches:
                    for m in matches:
                        try:
                            price_str = m.replace(',', '')
                            if '.' in price_str and len(price_str.split('.')[-1]) == 3:
                                price_str = price_str.replace('.', '')
                            price = float(price_str)
                            
                            if 10000 < price < 100000:
                                logging.info(f"  {code}: {price:,.0f} VND")
                                return price
                        except:
                            continue
            
            logging.warning(f"  {code}: Could not extract NAV from page")
            return None
            
        except Exception as e:
            logging.error(f"  {code}: Selenium error - {e}")
            return None
    
    def _crawl_ssi(self, code, url):
        """Crawl NAV from SSI Asset Management website."""
        try:
            logging.info(f"Selenium: Crawling {code} from SSI...")
            self.driver.get(url)
            time.sleep(4)
            
            html = self.driver.page_source
            
            # SSI format
            nav_patterns = [
                r'NAV[^<>]*?(\d{2,3}[,\.]\d{3}(?:\.\d+)?)',
                r'Net\s+Asset\s+Value[^<>]*?(\d{2,3}[,\.]\d{3})',
            ]
            
            for pattern in nav_patterns:
                matches = re.findall(pattern, html, re.IGNORECASE | re.DOTALL)
                if matches:
                    for m in matches:
                        try:
                            price_str = m.replace(',', '')
                            if '.' in price_str and len(price_str.split('.')[-1]) == 3:
                                price_str = price_str.replace('.', '')
                            price = float(price_str)
                            
                            if 10000 < price < 100000:
                                logging.info(f"  {code}: {price:,.0f} VND")
                                return price
                        except:
                            continue
            
            logging.warning(f"  {code}: Could not extract NAV from page")
            return None
            
        except Exception as e:
            logging.error(f"  {code}: Selenium error - {e}")
            return None
    
    def _crawl_dragon(self, code, url):
        """Crawl NAV from Dragon Capital website."""
        try:
            logging.info(f"Selenium: Crawling {code} from Dragon Capital...")
            self.driver.get(url)
            time.sleep(4)
            
            html = self.driver.page_source
            
            # Dragon Capital format
            nav_patterns = [
                r'NAV[^<>]*?(\d{2,3}[,\.]\d{3}(?:\.\d+)?)',
                r'Gi[áa]\s+tr[ịi]\s+đ[ơo]n\s+v[ịi][^<>]*?(\d{2,3}[,\.]\d{3})',
            ]
            
            for pattern in nav_patterns:
                matches = re.findall(pattern, html, re.IGNORECASE | re.DOTALL)
                if matches:
                    for m in matches:
                        try:
                            price_str = m.replace(',', '')
                            if '.' in price_str and len(price_str.split('.')[-1]) == 3:
                                price_str = price_str.replace('.', '')
                            price = float(price_str)
                            
                            if 10000 < price < 100000:
                                logging.info(f"  {code}: {price:,.0f} VND")
                                return price
                        except:
                            continue
            
            logging.warning(f"  {code}: Could not extract NAV from page")
            return None
            
        except Exception as e:
            logging.error(f"  {code}: Selenium error - {e}")
            return None


class SeleniumGoldCrawler(SeleniumCrawler):
    """
    Selenium-based crawler for gold prices.
    
    Sources:
    - SJC (sjc.com.vn) - Official SJC gold prices
    - BTMC (btmc.vn) - Bao Tin Minh Chau gold prices (backup)
    """
    
    def crawl(self, assets):
        """
        Crawl gold prices using multiple sources.
        
        Strategy:
        1. Try DOJI first (best for ring gold, uses simple HTTP - no Selenium needed)
        2. Try SJC if DOJI fails (requires Selenium)
        3. Try BTMC as final fallback (requires Selenium)
        
        Args:
            assets: List of gold asset dicts
            
        Returns:
            List of price result dicts
        """
        results = []
        today_str = datetime.now().strftime('%Y-%m-%d')
        
        # Try DOJI first (static HTML, no Selenium needed, best for ring gold)
        sjc_price, ring_price = self._crawl_doji()
        
        # If DOJI didn't get both prices, try Selenium-based sources
        if sjc_price is None or ring_price is None:
            if not self._init_driver():
                logging.warning("Cannot initialize Selenium WebDriver for fallback sources")
            else:
                # Try SJC website
                if sjc_price is None or ring_price is None:
                    sjc_price2, ring_price2 = self._crawl_sjc()
                    if sjc_price is None:
                        sjc_price = sjc_price2
                    if ring_price is None:
                        ring_price = ring_price2
                
                # Try BTMC as final fallback
                if sjc_price is None or ring_price is None:
                    sjc_price3, ring_price3 = self._crawl_btmc()
                    if sjc_price is None:
                        sjc_price = sjc_price3
                    if ring_price is None:
                        ring_price = ring_price3
        
        for asset in assets:
            code = asset['asset_code']
            
            if code == 'GOLD_SJC' and sjc_price:
                results.append({
                    'asset_code': code,
                    'price': sjc_price,
                    'date': today_str,
                    'source': 'Gold Crawler'
                })
            
            elif code == 'GOLD_RING' and ring_price:
                results.append({
                    'asset_code': code,
                    'price': ring_price,
                    'date': today_str,
                    'source': 'Gold Crawler'
                })
        
        return results
    
    def _crawl_sjc(self):
        """Crawl gold prices from SJC website."""
        sjc_price = None
        ring_price = None
        
        try:
            logging.info("Selenium: Crawling gold prices from SJC...")
            self.driver.get('https://sjc.com.vn/')
            time.sleep(5)  # Wait for dynamic content
            
            html = self.driver.page_source
            
            # Look for SJC gold bar prices (format: 8X.XXX.XXX or 8X,XXX,XXX)
            # SJC gold bar is typically shown first/prominently
            sjc_patterns = [
                r'SJC\s*1L[^<>]*?(8[0-9][,\.]\d{3}[,\.]\d{3})',
                r'V[àa]ng\s+mi[ếe]ng[^<>]*?(8[0-9][,\.]\d{3}[,\.]\d{3})',
                r'(8[0-9][,\.]\d{3}[,\.]\d{3})',
            ]
            
            for pattern in sjc_patterns:
                matches = re.findall(pattern, html, re.IGNORECASE | re.DOTALL)
                if matches:
                    for m in matches:
                        try:
                            price = float(m.replace('.', '').replace(',', ''))
                            if 75_000_000 < price < 95_000_000:
                                sjc_price = price
                                logging.info(f"  GOLD_SJC: {price:,.0f} VND")
                                break
                        except:
                            continue
                if sjc_price:
                    break
            
            # Look for ring/nhan gold prices
            ring_patterns = [
                r'[Nn]h[ẫaà]n[^<>]{0,50}?(8[0-9][,\.]\d{3}[,\.]\d{3})',
                r'99\.99[^<>]*?(8[0-9][,\.]\d{3}[,\.]\d{3})',
            ]
            
            for pattern in ring_patterns:
                matches = re.findall(pattern, html, re.DOTALL)
                if matches:
                    for m in matches:
                        try:
                            price = float(m.replace('.', '').replace(',', ''))
                            if 70_000_000 < price < 92_000_000:
                                ring_price = price
                                logging.info(f"  GOLD_RING: {price:,.0f} VND")
                                break
                        except:
                            continue
                if ring_price:
                    break
            
            if not sjc_price:
                logging.warning("  Could not extract SJC gold price")
            if not ring_price:
                logging.warning("  Could not extract ring gold price")
                
        except Exception as e:
            logging.error(f"Selenium error for SJC: {e}")
        
        return sjc_price, ring_price
    
    def _crawl_btmc(self):
        """Crawl gold prices from BTMC (Bao Tin Minh Chau) as fallback."""
        sjc_price = None
        ring_price = None
        
        try:
            logging.info("Selenium: Trying BTMC (fallback)...")
            self.driver.get('https://btmc.vn/')
            time.sleep(5)
            
            html = self.driver.page_source
            
            # BTMC shows various gold prices
            price_patterns = [
                r'SJC[^<>]*?(8[0-9][,\.]\d{3}[,\.]\d{3})',
                r'(8[0-9][,\.]\d{3}[,\.]\d{3})',
            ]
            
            for pattern in price_patterns:
                matches = re.findall(pattern, html, re.IGNORECASE | re.DOTALL)
                if matches:
                    for m in matches:
                        try:
                            price = float(m.replace('.', '').replace(',', ''))
                            if 75_000_000 < price < 95_000_000 and sjc_price is None:
                                sjc_price = price
                                logging.info(f"  GOLD_SJC (BTMC): {price:,.0f} VND")
                                break
                        except:
                            continue
                if sjc_price:
                    break
            
            # Ring gold from BTMC
            ring_patterns = [
                r'[Nn]h[ẫaà]n[^<>]{0,50}?(8[0-9][,\.]\d{3}[,\.]\d{3})',
            ]
            
            for pattern in ring_patterns:
                matches = re.findall(pattern, html, re.DOTALL)
                if matches:
                    for m in matches:
                        try:
                            price = float(m.replace('.', '').replace(',', ''))
                            if 70_000_000 < price < 92_000_000:
                                ring_price = price
                                logging.info(f"  GOLD_RING (BTMC): {price:,.0f} VND")
                                break
                        except:
                            continue
                if ring_price:
                    break
                    
        except Exception as e:
            logging.error(f"Selenium error for BTMC: {e}")
        
        return sjc_price, ring_price
    
    def _crawl_doji(self):
        """
        Crawl gold prices from DOJI (giavang.doji.vn).
        
        DOJI provides static HTML with gold prices - no JavaScript rendering needed.
        This is the BEST source for ring gold (NHẪN TRÒN 9999).
        
        Price format: nghìn/chỉ (thousand VND per chi)
        1 lượng = 10 chỉ, so: price_per_luong = price_per_chi * 10 * 1000
        
        Returns:
            Tuple (sjc_price, ring_price) in VND per lượng
        """
        sjc_price = None
        ring_price = None
        
        try:
            logging.info("Crawling gold prices from DOJI (giavang.doji.vn)...")
            
            # DOJI uses static HTML - no Selenium needed, just HTTP request
            url = "http://giavang.doji.vn/"
            response = make_request(url, headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            })
            
            if not response or response.status_code != 200:
                logging.warning(f"Failed to fetch DOJI: {response.status_code if response else 'No response'}")
                return sjc_price, ring_price
            
            response.encoding = 'utf-8'
            html = response.text
            
            # Pattern to extract prices from DOJI table structure:
            # <span class="title">NHẪN TRÒN 9999...</span>
            # <td class="goldprice-td"><div>16,450</div></td>  (buy)
            # <td class="goldprice-td"><div>16,750</div></td>  (sell)
            
            # Look for ring gold price (NHẪN TRÒN 9999)
            # The sell price is the second goldprice-td value after the product name
            ring_pattern = r'NH[ẪA]N\s+TR[ÒO]N\s+9999[^<]*</span>.*?goldprice-td[^>]*>[^<]*<div[^>]*>([0-9,]+)</div>.*?goldprice-td[^>]*>[^<]*<div[^>]*>([0-9,]+)</div>'
            ring_match = re.search(ring_pattern, html, re.DOTALL | re.IGNORECASE)
            
            if ring_match:
                try:
                    # Second group is sell price (in nghìn/chỉ = thousand VND per chi)
                    sell_price_chi = float(ring_match.group(2).replace(',', ''))
                    # Convert to VND per lượng: price * 10 (chi per luong) * 1000 (nghin to VND)
                    ring_price = sell_price_chi * 10 * 1000
                    logging.info(f"  GOLD_RING (DOJI): {ring_price:,.0f} VND/lượng (from {sell_price_chi:,.0f} nghìn/chỉ)")
                except Exception as e:
                    logging.warning(f"Failed to parse DOJI ring price: {e}")
            
            # Look for SJC gold bar price (AVPL/SJC or SJC - BÁN LẺ)
            sjc_pattern = r'(?:AVPL/)?SJC[^<]*B[ÁA]N\s+L[ẺE][^<]*</span>.*?goldprice-td[^>]*>[^<]*<div[^>]*>([0-9,]+)</div>.*?goldprice-td[^>]*>[^<]*<div[^>]*>([0-9,]+)</div>'
            sjc_match = re.search(sjc_pattern, html, re.DOTALL | re.IGNORECASE)
            
            if sjc_match:
                try:
                    sell_price_chi = float(sjc_match.group(2).replace(',', ''))
                    sjc_price = sell_price_chi * 10 * 1000
                    logging.info(f"  GOLD_SJC (DOJI): {sjc_price:,.0f} VND/lượng (from {sell_price_chi:,.0f} nghìn/chỉ)")
                except Exception as e:
                    logging.warning(f"Failed to parse DOJI SJC price: {e}")
            
            # Validate prices are in reasonable range
            if sjc_price and not (75_000_000 < sjc_price < 200_000_000):
                logging.warning(f"DOJI SJC price {sjc_price:,.0f} out of range, discarding")
                sjc_price = None
            
            if ring_price and not (70_000_000 < ring_price < 200_000_000):
                logging.warning(f"DOJI ring price {ring_price:,.0f} out of range, discarding")
                ring_price = None
                
        except Exception as e:
            logging.error(f"Error crawling DOJI: {e}")
        
        return sjc_price, ring_price
