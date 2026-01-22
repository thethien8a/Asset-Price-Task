# Daily Asset Price Collection Tool 📈

Công cụ tự động thu thập giá tài sản tài chính Việt Nam hàng ngày (Cổ phiếu, ETF, Chứng chỉ quỹ, Vàng) phục vụ phân tích thị trường và time-series forecasting.

## 📋 Giới thiệu

Dự án này được xây dựng để crawl dữ liệu giá đóng cửa (Close Price), NAV (cho quỹ) và giá vàng SJC mỗi ngày từ các nguồn public uy tín.

**Các tính năng chính:**
*   🚀 **Đa nguồn:** Hỗ trợ thu thập từ VNDirect (Stocks/ETFs), CafeF/Fmarket (Funds), Webgia (Gold).
*   💾 **Lưu trữ thông minh:** Dữ liệu lưu dạng CSV Append-only, tự động kiểm tra trùng lặp (Deduplication) theo ngày.
*   🔄 **Tự động hóa:** Tích hợp sẵn hướng dẫn chạy tự động trên GitHub Actions hoặc Google Colab.
*   🛡 **An toàn:** Cơ chế Retry, Delay và Logging chi tiết.

## 🗂 Cấu trúc dự án

```
Asset-Price-Task/
├── data/
│   ├── assets.csv             # Danh sách 31 tài sản cần theo dõi (Input)
│   └── daily_prices.csv       # Dữ liệu giá thu thập được (Output)
├── docs/
│   ├── asset_source_mapping.md # Tài liệu nguồn dữ liệu
│   ├── data_schema_design.md   # Thiết kế cấu trúc dữ liệu
│   └── automation_setup.md     # Hướng dẫn setup chạy tự động
├── src/
│   ├── crawlers.py            # Logic cào dữ liệu (Stocks, Funds, Gold)
│   ├── main.py                # Script chính điều phối luồng chạy
│   └── utils.py               # Các hàm tiện ích (Request, Logging)
├── .gitignore                 # File cấu hình Git ignore
├── requirements.txt           # Thư viện Python yêu cầu
└── README.md                  # Tài liệu hướng dẫn (File này)
```

## 🛠 Cài đặt & Sử dụng Local

### 1. Yêu cầu
*   Python 3.8+
*   Git

### 2. Cài đặt
Clone repository và cài đặt thư viện:

```bash
git clone <your-repo-url>
cd Asset-Price-Task
pip install -r requirements.txt
```

### 3. Chạy thủ công
Để thu thập dữ liệu giá cho ngày hiện tại:

```bash
python -m src.main
```

Dữ liệu mới sẽ được thêm vào file `data/daily_prices.csv`. Log quá trình chạy được ghi tại `crawler.log`.

## 🤖 Tự động hóa (Automation)

Bạn có thể thiết lập để tool chạy tự động vào 00:00 UTC hàng ngày miễn phí.

*   👉 **[Xem hướng dẫn Setup GitHub Actions](docs/automation_setup.md)** (Khuyên dùng)
*   👉 **[Xem hướng dẫn chạy trên Google Colab](docs/automation_setup.md)**

## 📊 Dữ liệu & Schema

Dữ liệu đầu ra được chuẩn hóa theo format sau:

| date | asset_code | price | asset_name | asset_type | source |
|------|------------|-------|------------|------------|--------|
| 2023-10-27 | HPG | 26500.0 | Hoa Phat Group | stock | VNDirect |
| 2023-10-27 | GOLD_SJC | 82500000.0 | SJC Gold Bar | gold | Webgia.com |

Chi tiết xem tại: [Data Schema Design](docs/data_schema_design.md).

## 📝 Danh sách tài sản
Project hiện theo dõi 31 mã tài sản bao gồm:
*   **Stocks:** HPG, FPT, MBB, SSI, POW, VCG, DGC, VND, VTP...
*   **ETFs:** FUEVFVND, E1VFVN30, FUESSVFL.
*   **Funds:** VESAF, VEOF, VCBF-MGF, DCDS, DCDE...
*   **Gold:** SJC Gold Bar, Gold Ring 9999.

## 🤝 Đóng góp
Nếu bạn phát hiện lỗi hoặc nguồn dữ liệu bị thay đổi, vui lòng sửa file `src/crawlers.py` hoặc tạo Issue mới.

---
*Project thực hiện bởi Antigravity (Opencode Agent).*
