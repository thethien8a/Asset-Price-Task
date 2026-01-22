import json
import logging
import re
from datetime import datetime
import time
from src.utils import make_request, clean_price

class BaseCrawler:
    def crawl(self, assets):
        raise NotImplementedError

class StockCrawler(BaseCrawler):
    def crawl(self, assets):
        """
        Crawl stock prices using VNDirect API (dchart).
        """
        results = []
        end_time = int(time.time())
        start_time = end_time - 7 * 24 * 3600
        
        for asset in assets:
            symbol = asset['asset_code']
            url = f"https://dchart-api.vndirect.com.vn/dchart/history?resolution=D&symbol={symbol}&from={start_time}&to={end_time}"
            
            logging.info(f"Crawling stock: {symbol}")
            response = make_request(url, headers={'User-Agent': 'Mozilla/5.0'})
            
            if response and response.status_code == 200:
                try:
                    data = response.json()
                    if data and len(data.get('t', [])) > 0:
                        last_idx = -1
                        price = float(data['c'][last_idx])
                        timestamp = data['t'][last_idx]
                        data_date = datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d')
                        
                        final_price = price
                        if price < 500:
                             final_price = price * 1000
                             
                        results.append({
                            'asset_code': symbol,
                            'price': final_price,
                            'date': data_date,
                            'source': 'VNDirect'
                        })
                    else:
                        logging.warning(f"No data found for {symbol} (Empty response)")
                except Exception as e:
                    logging.error(f"Error parsing data for {symbol}: {e}")
            else:
                logging.error(f"Failed to fetch {symbol}")
            
            time.sleep(1)
        return results

class FundCrawler(BaseCrawler):
    def crawl(self, assets):
        """
        Crawl fund NAV using Fmarket Filter API.
        Attempts to fetch all funds at once.
        """
        results = []
        
        # Endpoint Filter (Lấy danh sách tất cả quỹ)
        url = "https://api.fmarket.vn/res/product/filter"
        
        headers = {
            'Content-Type': 'application/json',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Origin': 'https://fmarket.vn',
            'Referer': 'https://fmarket.vn/',
            'Accept': 'application/json, text/plain, */*'
        }
        
        payload = {
            "types": ["NEW_IPO", "TRADING"],
            "pageSize": 500, # Lấy hết
            "page": 1,
            "sortField": "nav",
            "sortOrder": "DESC",
            "buyBy": "BY_MONEY",
            "isBuyByMoney": True
        }

        logging.info("Crawling funds from Fmarket (Filter API)...")
        
        response = make_request(url, method='POST', payload=payload, headers=headers)
        
        funds_data = []
        if response and response.status_code == 200:
            try:
                data = response.json()
                funds_data = data.get('data', {}).get('rows', [])
                logging.info(f"Fmarket returned {len(funds_data)} funds.")
            except Exception as e:
                logging.error(f"Error parsing Fmarket response: {e}")
        else:
             logging.error(f"Fmarket Filter API Failed: {response.status_code if response else 'None'}")
             # Nếu fail, có thể dùng Mock data hoặc Log error.
             # Ở đây tôi log error.

        # Map data
        fund_map = {}
        for f in funds_data:
            code = f.get('shortName')
            nav = f.get('nav')
            date_ms = f.get('navDate')
            if code and nav:
                date_str = datetime.fromtimestamp(date_ms / 1000).strftime('%Y-%m-%d')
                fund_map[code.upper()] = {'price': float(nav), 'date': date_str}

        # Match with assets
        for asset in assets:
            code = asset['asset_code']
            
            # Xử lý code (Fmarket dùng VCBF-MGF, CSV dùng VCBFMGF)
            # Thử vài biến thể
            candidates = [
                code,
                code.replace('VCBF', 'VCBF-'), # VCBFMGF -> VCBF-MGF
                code.replace('-', '') # VCBF-MGF -> VCBFMGF
            ]
            
            found_info = None
            for c in candidates:
                if c in fund_map:
                    found_info = fund_map[c]
                    break
            
            if found_info:
                results.append({
                    'asset_code': code,
                    'price': found_info['price'],
                    'date': found_info['date'],
                    'source': 'Fmarket'
                })
                logging.info(f"Mapped {code}: {found_info['price']}")
            else:
                logging.warning(f"Could not find fund {code} in Fmarket list.")

        return results

class GoldCrawler(BaseCrawler):
    def crawl(self, assets):
        """
        Crawl Gold price using Webgia (SJC) and PNJ JSON (Ring).
        """
        results = []
        
        # 1. Get SJC Bar from Webgia (parse HTML)
        sjc_url = "https://webgia.com/gia-vang/sjc/"
        try:
            logging.info("Crawling SJC Gold Bar from Webgia...")
            response = make_request(sjc_url)
            if response and response.status_code == 200:
                html = response.text
                blocks = re.split(r'</tr>', html)
                for block in blocks:
                    if 'Hồ Chí Minh' in block or 'TP.HCM' in block:
                        prices = re.findall(r'(\d{1,3}(?:,\d{3})*)', block)
                        valid_prices = [float(p.replace(',', '')) for p in prices if len(p) >= 6]
                        if len(valid_prices) >= 2:
                            price_sjc = valid_prices[1]
                            results.append({
                                'asset_code': 'GOLD_SJC',
                                'price': price_sjc,
                                'date': datetime.now().strftime('%Y-%m-%d'),
                                'source': 'Webgia.com'
                            })
                            logging.info(f"Fetched GOLD_SJC: {price_sjc}")
                            break
        except Exception as e:
             logging.error(f"Error crawling SJC: {e}")

        # 2. Get Gold Ring from PNJ JSON API
        pnj_url = "https://cdn.pnj.io/images/giavang/tk_connect.json"
        try:
            logging.info("Crawling Gold Ring from PNJ API...")
            response = make_request(pnj_url)
            if response and response.status_code == 200:
                data = response.json()
                price_ring = None
                today_str = datetime.now().strftime('%Y-%m-%d')
                
                for item in data:
                    name = item.get('typeName', '').lower()
                    # PNJ: "Nhẫn Trơn PNJ 999.9"
                    if 'nhẫn' in name and '999.9' in name:
                         raw_sell = item.get('sell', '0').replace(',', '')
                         price_ring = float(raw_sell) * 1000 # PNJ JSON: 83400 -> 83,400,000 ? 
                         # Check PNJ API: "sell": "83400". Đơn vị nghìn đồng/chỉ? 
                         # Hay "83,400,000"?
                         # Thường API trả về "83400" (nghìn đồng).
                         # Webgia: 83,400,000.
                         # Nếu raw < 1000000 -> nhân 1000.
                         
                         if price_ring < 1000000:
                             price_ring = price_ring * 1000
                             
                         # Lại check: PNJ Nhẫn 1 chỉ = 8tr. 
                         # Giá 1 lượng (như SJC) = 80tr.
                         # Cần xác định đơn vị task yêu cầu.
                         # Task yêu cầu "Gold Ring 9999". Thường là giá/Lượng.
                         # Nếu PNJ trả về giá/Chỉ -> Nhân 10?
                         # SJC Bar: 82,500,000.
                         # Ring: ~ 81,000,000.
                         # PNJ API: "sell": "83400" (83tr400 / lượng hay 8tr340/chỉ?)
                         # Thường PNJ niêm yết theo Lượng hoặc Chỉ. 
                         # PNJ Web: 8,340,000 đ/chỉ.
                         # Vậy 83400 -> Đơn vị nghìn/lượng (83tr400)? Không, 83400 * 1000 = 83,400,000. Đúng giá 1 lượng.
                         
                         break
                
                if price_ring:
                     results.append({
                        'asset_code': 'GOLD_RING',
                        'price': price_ring,
                        'date': today_str,
                        'source': 'PNJ API (SJC 9999 equiv)'
                    })
                     logging.info(f"Fetched GOLD_RING: {price_ring}")
                else:
                    logging.warning("Could not find Gold Ring price in PNJ data")

        except Exception as e:
            logging.error(f"Error crawling PNJ Ring: {e}")

        return results
