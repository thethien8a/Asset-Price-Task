# Data Schema Design

Tài liệu này mô tả thiết kế schema cho việc lưu trữ dữ liệu giá tài sản hàng ngày.

## 1. Nguyên tắc lưu trữ (Storage Principles)

*   **Format:** CSV (cho local storage) hoặc Google Sheets (cho cloud shared).
*   **Strategy:** Append-only (Chỉ thêm dòng mới).
    *   **Lý do:** Đảm bảo toàn vẹn lịch sử dữ liệu. Tránh việc ghi đè nhầm lẫn làm mất dữ liệu cũ. Dễ dàng audit (kiểm tra lại) thời điểm dữ liệu được cập nhật.
*   **Duplicate Handling:**
    *   Trước khi ghi dữ liệu mới, hệ thống sẽ kiểm tra cặp khóa `(date, asset_code)`.
    *   Nếu dữ liệu cho ngày hôm đó và mã tài sản đó đã tồn tại -> **Bỏ qua** hoặc **Cập nhật** (tùy cấu hình, mặc định là Skip để giữ dữ liệu thu thập sớm nhất hoặc Update nếu muốn dữ liệu mới nhất trong ngày).
    *   *Đề xuất:* Nếu chạy lại trong cùng một ngày, nên update giá trị cũ để sửa lỗi nếu có, hoặc ghi log cảnh báo.

## 2. Cấu trúc bảng (Schema Structure)

| Column Name | Data Type | Description | Example |
| :--- | :--- | :--- | :--- |
| **date** | Date (YYYY-MM-DD)| Ngày của dữ liệu giá. | `2023-10-27` |
| **asset_code** | String | Mã định danh tài sản. | `HPG`, `VESAF` |
| **price** | Float | Giá đóng cửa, NAV, hoặc giá bán ra. | `23500.0`, `18230.5` |
| **asset_name** | String | Tên đầy đủ (optional, dùng để tham chiếu). | `Hoa Phat Group` |
| **asset_type** | String | Phân loại tài sản. | `stock`, `fund`, `gold` |
| **currency** | String | Đơn vị tiền tệ. | `VND` |
| **source** | String | Nguồn dữ liệu. | `FireAnt`, `Fmarket` |
| **crawl_time** | DateTime | Thời điểm thực thi code. | `2023-10-27 15:30:05` |

## 3. Xử lý trường hợp đặc biệt

*   **Ngày nghỉ/Ngày lễ:** Không có dữ liệu giao dịch. Script sẽ không tìm thấy dữ liệu mới hoặc API trả về dữ liệu của ngày giao dịch gần nhất.
    *   *Giải pháp:* Luôn kiểm tra `date` trả về từ nguồn dữ liệu. Nếu `date` từ nguồn < `current_date` (tức là dữ liệu cũ), ta vẫn có thể lưu nhưng cần cẩn trọng khi visualize. Tốt nhất là chỉ lưu nếu `data_date` == `current_date` (hoặc cấu hình cho phép fill-gap).
*   **Lỗi dữ liệu (Price = 0 hoặc null):**
    *   Log error và không lưu vào database để tránh làm nhiễu biểu đồ.

## 4. Định dạng Output

### CSV File (`daily_prices.csv`)
```csv
date,asset_code,price,asset_name,asset_type,currency,source,crawl_time
2023-10-27,HPG,23500,Hoa Phat Group,stock,VND,FireAnt,2023-10-27T15:00:00
2023-10-27,VESAF,18200,VinaCapital Equity Special,fund,VND,Fmarket,2023-10-27T15:00:00
...
```
