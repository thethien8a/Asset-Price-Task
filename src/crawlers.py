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
        Crawl fund NAV using CafeF (Fallback strategy).
        URL format: https://s.cafef.vn/quyo-{symbol}/thong-tin-chung.chn
        """
        results = []
        logging.info("Crawling funds from CafeF...")
        
        for asset in assets:
            code = asset['asset_code']
            # Một số mã có thể khác trên CafeF. Ví dụ VCBF-MGF.
            # Thử convert: VCBFMGF -> VCBFMGF (CafeF thường giữ nguyên hoặc thêm dấu -)
            # CafeF URL pattern: https://s.cafef.vn/quyo-vesaf/thong-tin-chung.chn
            
            url = f"https://s.cafef.vn/quyo-{code.lower()}/thong-tin-chung.chn"
            # Nếu code có VCBF, có thể cần thêm dấu gạch? CafeF thường dùng code liền: VCBFMGF
            
            logging.info(f"Fetching fund: {code}")
            response = make_request(url)
            
            if response and response.status_code == 200:
                try:
                    html = response.text
                    # Parse NAV
                    # Pattern: <div class="dl-thongtin">...<ul>...<li>Giá trị tài sản ròng/CCQ: <b>18,230</b>...
                    # Hoặc tìm text "Giá trị tài sản ròng/CCQ"
                    
                    # Regex tìm "Giá trị tài sản ròng/CCQ" sau đó lấy số
                    # CafeF cấu trúc khá lộn xộn.
                    # Thử tìm chuỗi số sau chữ "NAV/CCQ" hoặc "Giá trị tài sản ròng"
                    
                    match = re.search(r'(?:Giá trị tài sản ròng/CCQ|NAV/CCQ).*?<b>(.*?)</b>', html, re.DOTALL | re.IGNORECASE)
                    if match:
                        price_str = match.group(1) # "18,230"
                        price = clean_price(price_str)
                        
                        # Ngày cập nhật? CafeF thường hiện ngày ở đâu đó.
                        # Pattern: "Ngày cập nhật: 27/10/2023"
                        date_match = re.search(r'Ngày cập nhật.*?(\d{2}/\d{2}/\d{4})', html, re.DOTALL | re.IGNORECASE)
                        data_date = datetime.now().strftime('%Y-%m-%d') # Default today
                        if date_match:
                            try:
                                d_str = date_match.group(1)
                                data_date = datetime.strptime(d_str, '%d/%m/%Y').strftime('%Y-%m-%d')
                            except:
                                pass
                        
                        if price:
                            results.append({
                                'asset_code': code,
                                'price': price,
                                'date': data_date,
                                'source': 'CafeF'
                            })
                    else:
                        logging.warning(f"NAV not found for {code} on CafeF")
                        # Thử URL dự phòng cho quỹ VCBF (có thể có dấu gạch ngang)
                        if 'VCBF' in code and '-' not in code:
                             # Try fallback url logic here if needed
                             pass
                except Exception as e:
                     logging.error(f"Error parsing CafeF for {code}: {e}")
            else:
                 logging.warning(f"CafeF returned {response.status_code if response else 'None'} for {code}")
            
            time.sleep(1)
            
        return results

class GoldCrawler(BaseCrawler):
    def crawl(self, assets):
        """
        Crawl Gold price using Webgia.com.
        """
        results = []
        url = "https://webgia.com/gia-vang/sjc/"
        
        logging.info("Crawling gold prices from Webgia...")
        response = make_request(url)
        
        if response and response.status_code == 200:
            try:
                html = response.text
                today = datetime.now().strftime('%Y-%m-%d')
                
                price_sjc = None
                price_ring = None
                
                # Regex SJC
                blocks = re.split(r'</tr>', html)
                for block in blocks:
                    if 'Hồ Chí Minh' in block or 'TP.HCM' in block:
                        prices = re.findall(r'(\d{1,3}(?:,\d{3})*)', block)
                        valid_prices = [float(p.replace(',', '')) for p in prices if len(p) >= 6]
                        if len(valid_prices) >= 2:
                            price_sjc = valid_prices[1]
                
                # Regex Ring (Nhẫn) - Cố gắng bắt tổng quát hơn
                # Tìm bất kỳ dòng nào có chữ "Nhẫn" và giá trị > 50tr
                for block in blocks:
                    if 'Nhẫn' in block:
                        prices = re.findall(r'(\d{1,3}(?:,\d{3})*)', block)
                        valid_prices = [float(p.replace(',', '')) for p in prices if len(p) >= 6]
                        valid_prices = [p for p in valid_prices if p > 50000000] # Lọc giá rác
                        if len(valid_prices) >= 1:
                            price_ring = valid_prices[-1] # Lấy giá bán (thường là số lớn nhất hoặc sau cùng)
                            break
                            
                for asset in assets:
                    code = asset['asset_code']
                    price = None
                    if code == 'GOLD_SJC':
                        price = price_sjc
                    elif code == 'GOLD_RING':
                        price = price_ring
                    
                    if price:
                        results.append({
                            'asset_code': code,
                            'price': price,
                            'date': today,
                            'source': 'Webgia.com'
                        })
                    else:
                        logging.warning(f"Gold price not found for {code}")
                        
            except Exception as e:
                logging.error(f"Error parsing Gold HTML: {e}")
                
        return results
