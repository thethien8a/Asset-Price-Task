# Asset Source Mapping

Tài liệu này định nghĩa nguồn dữ liệu (Source) và URL để thu thập giá cho từng loại tài sản.

## Chiến lược chọn nguồn (Source Strategy)

Để đảm bảo tính ổn định và dễ bảo trì, chúng ta sẽ nhóm các tài sản vào 3 nguồn chính:

1.  **Nhóm Cổ phiếu & ETF (Stocks & ETFs):**
    *   **Nguồn:** FireAnt (API/Web) hoặc CafeF.
    *   **Lý do:** Dữ liệu cập nhật nhanh, đầy đủ các mã trên HOSE/HNX.
    *   **Dữ liệu lấy:** Giá đóng cửa (Close Price) hoặc Giá khớp lệnh gần nhất (Current Price) nếu trong phiên.

2.  **Nhóm Chứng chỉ quỹ mở (Open-ended Funds):**
    *   **Nguồn:** Fmarket (fmarket.vn)
    *   **Lý do:** Fmarket là nền tảng phân phối chứng chỉ quỹ tập trung, có đầy đủ các quỹ của VinaCapital, Dragon Capital, SSI, VCBF. Cào từ 1 nguồn thống nhất dễ hơn cào từ 4 website công ty quản lý quỹ khác nhau.
    *   **Dữ liệu lấy:** NAV/CCQ (Net Asset Value per Unit) mới nhất.

3.  **Nhóm Vàng (Gold):**
    *   **Nguồn:** SJC (sjc.com.vn) hoặc Webgia.com (nếu trang SJC chặn cào).
    *   **Lý do:** SJC là thương hiệu vàng quốc gia.
    *   **Dữ liệu lấy:** Giá Bán ra (Sell Price) cho SJC Gold Bar và Gold Ring 9999.

## Chi tiết Mapping

| Asset Code | Loại | Nguồn (Source) | URL Chi tiết (Example) | Loại giá |
| :--- | :--- | :--- | :--- | :--- |
| **Nhóm Quỹ (Funds)** | | | | |
| VESAF | Fund | Fmarket | `https://fmarket.vn/san-pham/VESAF` | NAV/Unit |
| VEOF | Fund | Fmarket | `https://fmarket.vn/san-pham/VEOF` | NAV/Unit |
| VMEEF | Fund | Fmarket | `https://fmarket.vn/san-pham/VMEEF` | NAV/Unit |
| VDEF | Fund | Fmarket | `https://fmarket.vn/san-pham/VDEF` | NAV/Unit |
| VIBF | Fund | Fmarket | `https://fmarket.vn/san-pham/VIBF` | NAV/Unit |
| VFF | Fund | Fmarket | `https://fmarket.vn/san-pham/VFF` | NAV/Unit |
| VCBFMGF | Fund | Fmarket | `https://fmarket.vn/san-pham/VCBFMGF` | NAV/Unit |
| VCBFBCF | Fund | Fmarket | `https://fmarket.vn/san-pham/VCBFBCF` | NAV/Unit |
| VCBFAIF | Fund | Fmarket | `https://fmarket.vn/san-pham/VCBFAIF` | NAV/Unit |
| VCBFTBF | Fund | Fmarket | `https://fmarket.vn/san-pham/VCBFTBF` | NAV/Unit |
| VCBFFIF | Fund | Fmarket | `https://fmarket.vn/san-pham/VCBFFIF` | NAV/Unit |
| SSISCA | Fund | Fmarket | `https://fmarket.vn/san-pham/SSISCA` | NAV/Unit |
| VLGF | Fund | Fmarket | `https://fmarket.vn/san-pham/VLGF` | NAV/Unit |
| SSIBF | Fund | Fmarket | `https://fmarket.vn/san-pham/SSIBF` | NAV/Unit |
| DCDS | Fund | Fmarket | `https://fmarket.vn/san-pham/DCDS` | NAV/Unit |
| DCDE | Fund | Fmarket | `https://fmarket.vn/san-pham/DCDE` | NAV/Unit |
| DCBF | Fund | Fmarket | `https://fmarket.vn/san-pham/DCBF` | NAV/Unit |
| **Nhóm ETF & Stock** | | | | |
| FUEVFVND | ETF | FireAnt / CafeF | `https://fireant.vn/dashboard/content/symbols/FUEVFVND` | Close |
| E1VFVN30 | ETF | FireAnt / CafeF | `https://fireant.vn/dashboard/content/symbols/E1VFVN30` | Close |
| FUESSVFL | ETF | FireAnt / CafeF | `https://fireant.vn/dashboard/content/symbols/FUESSVFL` | Close |
| HPG | Stock| FireAnt / CafeF | `https://fireant.vn/dashboard/content/symbols/HPG` | Close |
| FPT | Stock| FireAnt / CafeF | `https://fireant.vn/dashboard/content/symbols/FPT` | Close |
| MBB | Stock| FireAnt / CafeF | `https://fireant.vn/dashboard/content/symbols/MBB` | Close |
| SSI | Stock| FireAnt / CafeF | `https://fireant.vn/dashboard/content/symbols/SSI` | Close |
| POW | Stock| FireAnt / CafeF | `https://fireant.vn/dashboard/content/symbols/POW` | Close |
| VCG | Stock| FireAnt / CafeF | `https://fireant.vn/dashboard/content/symbols/VCG` | Close |
| DGC | Stock| FireAnt / CafeF | `https://fireant.vn/dashboard/content/symbols/DGC` | Close |
| VND | Stock| FireAnt / CafeF | `https://fireant.vn/dashboard/content/symbols/VND` | Close |
| VTP | Stock| FireAnt / CafeF | `https://fireant.vn/dashboard/content/symbols/VTP` | Close |
| **Nhóm Vàng (Gold)** | | | | |
| GOLD_SJC | Gold | SJC / Webgia | `https://sjc.com.vn/gia-vang` | Sell |
| GOLD_RING | Gold | SJC / Webgia | `https://sjc.com.vn/gia-vang` | Sell |

## Ghi chú kỹ thuật
- **Fmarket:** Sử dụng API ẩn `https://api.fmarket.vn/res/product/get-product-detail` để lấy JSON chính xác thay vì parse HTML.
- **Stock:** Sử dụng thư viện `vnstock` (nếu dùng Python) hoặc gọi API public của các bảng giá.
- **Gold:** Parse HTML từ trang SJC.
