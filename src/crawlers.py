import json
import logging
import re
from datetime import datetime
import time
# from bs4 import BeautifulSoup # Bỏ import để tránh lỗi môi trường
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
        Crawl fund NAV from TinNhanhChungKhoan using Regex.
        """
        results = []
        url = "https://www.tinnhanhchungkhoan.vn/du-lieu/chung-chi-quy.html"
        
        logging.info("Crawling funds from TinNhanhChungKhoan...")
        response = make_request(url)
        
        fund_map = {}
        if response and response.status_code == 200:
            html = response.text
            # Tìm các dòng table
            # Pattern: <tr>...<td>Mã Quỹ</td>...<td>Giá</td>...</tr>
            # Dùng regex tìm từng row: <tr.*?</tr>
            
            rows = re.findall(r'<tr.*?>(.*?)</tr>', html, re.DOTALL | re.IGNORECASE)
            for row in rows:
                cols = re.findall(r'<td.*?>(.*?)</td>', row, re.DOTALL | re.IGNORECASE)
                if not cols: continue
                
                # Clean html tags in cols
                clean_cols = [re.sub(r'<.*?>', '', c).strip() for c in cols]
                
                if len(clean_cols) >= 2:
                    name_cell = clean_cols[0].upper() # Giả sử cột 1 là Mã
                    
                    # Tìm giá (số) trong các cột còn lại
                    price = None
                    for val in clean_cols[1:]:
                         try:
                             # 18,200 hoặc 18.200
                             clean_val = val.replace(',', '').replace('.', '') # Xóa hết để check digit? Không
                             # VN: 18,200.00 -> 18200
                             # Regex check format số: \d{1,3}(,\d{3})*
                             
                             # Đơn giản: Lấy số float từ string
                             # Xóa ký tự không phải số và dấu chấm/phẩy
                             # Nếu format là 18,230 -> replace ',' -> 18230
                             
                             if re.match(r'^\d{1,3}(,\d{3})*(\.\d+)?$', val) or re.match(r'^\d+(\.\d+)?$', val):
                                 p = float(val.replace(',', ''))
                                 if p > 1000:
                                     price = p
                                     break
                         except:
                             continue
                    
                    if price:
                        fund_map[name_cell] = price

        # Match data
        for asset in assets:
            code = asset['asset_code']
            price = None
            date_str = datetime.now().strftime('%Y-%m-%d')
            
            # Fuzzy Logic
            for k, v in fund_map.items():
                if code in k: # Code "VESAF" in "VinaCapital VESAF"
                    price = v
                    break
            
            if price:
                results.append({
                    'asset_code': code,
                    'price': price,
                    'date': date_str,
                    'source': 'TinNhanhChungKhoan'
                })
                logging.info(f"Found Fund {code}: {price}")
            else:
                logging.warning(f"Fund {code} not found (Source blocked/missing)")
                
        return results

class GoldCrawler(BaseCrawler):
    def crawl(self, assets):
        """
        Crawl Gold using Regex on Webgia.
        """
        results = []
        url = "https://webgia.com/gia-vang/sjc/"
        
        logging.info("Crawling Gold from Webgia (Regex)...")
        response = make_request(url)
        
        if response and response.status_code == 200:
            html = response.text
            today_str = datetime.now().strftime('%Y-%m-%d')
            
            # 1. SJC
            # Tìm block chứa Hồ Chí Minh
            # Regex: <tr.*?>.*?Hồ Chí Minh.*?</tr> (DOTALL)
            # Lưu ý Webgia dùng rowspan
            
            # Cách đơn giản: split theo </tr>
            blocks = re.split(r'</tr>', html)
            
            price_sjc = None
            price_ring = None
            
            for block in blocks:
                if 'Hồ Chí Minh' in block or 'SJC 1L' in block:
                    # Tìm số: >16.730.000<
                    prices = re.findall(r'>\s*(\d{1,3}(?:\.\d{3})*)', block) # Webgia dùng chấm phân cách ngàn? 
                    # Check debug output: 16.730.000 -> Dùng dấu chấm.
                    
                    valid_prices = [float(p.replace('.', '')) for p in prices if len(p) >= 5]
                    if len(valid_prices) >= 1:
                        price_sjc = valid_prices[-1] # Lấy giá cuối (Bán)
                
                if 'Nhẫn' in block and '99' in block:
                     prices = re.findall(r'>\s*(\d{1,3}(?:\.\d{3})*)', block)
                     valid_prices = [float(p.replace('.', '')) for p in prices if len(p) >= 5]
                     if len(valid_prices) >= 1:
                         price_ring = valid_prices[-1]

            for asset in assets:
                code = asset['asset_code']
                p = None
                if code == 'GOLD_SJC': p = price_sjc
                elif code == 'GOLD_RING': p = price_ring
                
                if p:
                    results.append({
                        'asset_code': code,
                        'price': p,
                        'date': today_str,
                        'source': 'Webgia.com'
                    })
                    logging.info(f"Fetched Gold {code}: {p}")
                else:
                    logging.warning(f"Gold {code} not found")
        
        return results
