# Asset Price Tracker 📈

Hệ thống tự động thu thập giá tài sản (Cổ phiếu, ETF, Chứng chỉ quỹ, Vàng) và lưu trữ đa nền tảng.

## Tính năng
- **Crawl đa nguồn**: 
  - Cổ phiếu & ETF: SSI iBoard.
  - Chứng chỉ quỹ: Fmarket API.
  - Giá vàng (SJC & Nhẫn): Giavang.org.
- **Lưu trữ linh hoạt**: Tự động lưu vào CSV local và đẩy dữ liệu lên Google Sheets.
- **Deduplication**: Cơ chế kiểm tra trùng lặp dựa trên `date` và `asset_code`.
- **Robustness**: Xử lý lỗi request, khoảng trắng dữ liệu và định dạng giá tự động.

## Cài đặt & Sử dụng
1. Cài đặt thư viện:
   ```bash
   pip install -r requirements.txt
   ```
2. Chạy tool:
   ```bash
   python src/main.py
   ```