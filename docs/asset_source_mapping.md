# Asset Source Mapping

Tài liệu này định nghĩa nguồn dữ liệu (Source) và URL để thu thập giá cho từng loại tài sản.

## Tổng quan nguồn dữ liệu (Jan 2026)

| Nhóm | Số lượng | Nguồn thực tế | Trạng thái |
|------|----------|---------------|------------|
| Stocks | 9 | VNDirect API | 100% |
| ETFs | 3 | VNDirect API | 100% |
| Funds | 17 | Fmarket API | 100% |
| Gold | 2 | DOJI | 100% |
| **Tổng** | **31** | - | **100%** |

## Chiến lược chọn nguồn (Source Strategy)

### 1. Nhóm Cổ phiếu & ETF (Stocks & ETFs)

**Nguồn:** VNDirect dchart API  
**URL:** `https://dchart-api.vndirect.com.vn/dchart/history?resolution=D&symbol={SYMBOL}&from={START}&to={END}`  
**Dữ liệu lấy:** Giá đóng cửa (Close Price) từ mảng `c` trong response JSON  
**Trạng thái:** Hoạt động tốt, không bị chặn IP

### 2. Nhóm Chứng chỉ quỹ mở (Open-ended Funds)

**Nguồn:** Fmarket API  
**URL:** `https://api.fmarket.vn/res/products/filter`  
**Method:** POST với payload `{"types": ["TRADING_FUND"], "pageSize": 200}`  
**Dữ liệu lấy:** NAV/CCQ từ field `nav` trong response JSON  
**Trạng thái:** Hoạt động tốt, cung cấp đầy đủ 17 quỹ

### 3. Nhóm Vàng (Gold)

**Nguồn chính:** DOJI (giavang.doji.vn)  
**URL:** `http://giavang.doji.vn/`  
**Dữ liệu lấy:** Giá bán (Sell Price) cho SJC Gold Bar và Gold Ring 9999  
**Đơn vị:** nghìn/chỉ → chuyển đổi sang VND/lượng  
**Trạng thái:** Hoạt động tốt, HTML tĩnh (không cần Selenium)

**Nguồn dự phòng:**
- SJC (sjc.com.vn) - cần Selenium
- BTMC (btmc.vn) - cần Selenium

## Chi tiết Mapping

### Nhóm Quỹ (Funds) - Fmarket API

| Asset Code | Tên quỹ | Công ty quản lý | Fmarket Code |
|------------|---------|-----------------|--------------|
| VESAF | VinaCapital Equity Special Access | VinaCapital | VESAF |
| VEOF | VinaCapital Equity Opportunity | VinaCapital | VEOF |
| VMEEF | VinaCapital Modern Economy Equity | VinaCapital | VMEEF |
| VDEF | VinaCapital Defensive Equity | VinaCapital | VDEF |
| VIBF | VinaCapital Insight Balanced | VinaCapital | VIBF |
| VFF | VinaCapital Fixed Income | VinaCapital | VFF |
| VLGF | VinaCapital Liquidity Bond | VinaCapital | VLGF |
| VCBFMGF | VCBF Midcap Growth | VCBF | VCBF-MGF |
| VCBFBCF | VCBF Blue Chip | VCBF | VCBF-BCF |
| VCBFAIF | VCBF Aggressive Investing | VCBF | VCBF-AIF |
| VCBFTBF | VCBF Tactical Balanced | VCBF | VCBF-TBF |
| VCBFFIF | VCBF Fixed Income | VCBF | VCBF-FIF |
| SSISCA | SSI Sustainable Competitive Advantage | SSIAM | SSISCA |
| SSIBF | SSI Bond Fund | SSIAM | SSIBF |
| DCDS | Dragon Capital Dynamic Select | DCVFM | DCDS |
| DCDE | Dragon Capital Dividend Equity | DCVFM | DCDE |
| DCBF | Dragon Capital Bond Fund | DCVFM | DCBF |

### Nhóm ETF & Stock - VNDirect API

| Asset Code | Loại | Sàn | Tên |
|------------|------|-----|-----|
| FUEVFVND | ETF | HOSE | DCVFM VNDiamond ETF |
| E1VFVN30 | ETF | HOSE | DCVFM VN30 ETF |
| FUESSVFL | ETF | HOSE | SSI VNFin Lead ETF |
| HPG | Stock | HOSE | Hoa Phat Group |
| FPT | Stock | HOSE | FPT Corp |
| MBB | Stock | HOSE | MB Bank |
| SSI | Stock | HOSE | SSI Securities |
| POW | Stock | HOSE | PV Power |
| VCG | Stock | HOSE | Vinaconex |
| DGC | Stock | HOSE | Duc Giang Chemicals |
| VND | Stock | HOSE | VNDirect Securities |
| VTP | Stock | HOSE | Viettel Post |

### Nhóm Vàng (Gold) - DOJI

| Asset Code | Tên | Nguồn | Sản phẩm DOJI |
|------------|-----|-------|---------------|
| GOLD_SJC | SJC Gold Bar | DOJI | AVPL/SJC - BÁN LẺ |
| GOLD_RING | Gold Ring 9999 | DOJI | NHẪN TRÒN 9999 (HƯNG THỊNH VƯỢNG) |

## Ghi chú kỹ thuật

### VNDirect API
```python
url = f"https://dchart-api.vndirect.com.vn/dchart/history?resolution=D&symbol={symbol}&from={start}&to={end}"
response = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'})
data = response.json()
price = data['c'][-1]  # Last close price
```

### Fmarket API
```python
url = "https://api.fmarket.vn/res/products/filter"
payload = {"types": ["TRADING_FUND"], "pageSize": 200, "isIpo": False, "page": 1}
response = requests.post(url, json=payload, headers={
    'Content-Type': 'application/json',
    'Origin': 'https://fmarket.vn'
})
funds = response.json()['data']['rows']
nav = funds[0]['nav']  # NAV per unit
```

### DOJI Gold Price
```python
url = "http://giavang.doji.vn/"
response = requests.get(url)
html = response.text

# Extract ring gold price (nghìn/chỉ)
# Pattern: NHẪN TRÒN 9999...16,450...16,750
# Sell price = 16,750 nghìn/chỉ
# Convert to VND/lượng: 16,750 × 10 × 1000 = 167,500,000 VND
```

### Công thức chuyển đổi giá vàng DOJI

```
Giá trên DOJI: X nghìn/chỉ
Giá VND/lượng = X × 10 × 1000

Ví dụ:
- DOJI hiển thị: 16,750 nghìn/chỉ
- 1 lượng = 10 chỉ
- Giá = 16,750 × 10 × 1,000 = 167,500,000 VND/lượng
```

## Fallback Chain

### Gold Prices
```
DOJI (HTTP, static HTML) 
  ↓ nếu thất bại
SJC (Selenium) 
  ↓ nếu thất bại
BTMC (Selenium)
```

DOJI được ưu tiên vì:
1. HTML tĩnh, không cần JavaScript rendering
2. Có giá vàng nhẫn 9999 (GOLD_RING) rõ ràng
3. Không cần Selenium, chỉ cần HTTP request

## Lịch sử thay đổi

| Ngày | Thay đổi |
|------|----------|
| Jan 2026 | Thêm DOJI làm nguồn chính cho gold, đạt 31/31 assets |
| Jan 2026 | Thêm Fmarket API cho tất cả 17 funds |
| Jan 2026 | Xác nhận VNDirect API hoạt động cho stocks/ETFs |
