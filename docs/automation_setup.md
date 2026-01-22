# Automation Setup Guide

Tài liệu này hướng dẫn cách thiết lập tự động hóa (Automation) để chạy script thu thập giá tài sản hàng ngày.

## Option 1: GitHub Actions (Khuyến nghị)

Đây là cách tốt nhất vì hoàn toàn miễn phí, tự động 100%, không cần mở máy tính.

### 1. Cấu hình Workflow
Tạo file `.github/workflows/daily_crawl.yml` trong repository này với nội dung sau:

```yaml
name: Daily Asset Price Crawl

on:
  schedule:
    # Chạy lúc 00:00 UTC hàng ngày (7:00 AM VN)
    - cron: '0 0 * * *'
  workflow_dispatch: # Cho phép chạy thủ công từ tab Actions

jobs:
  build:
    runs-on: ubuntu-latest
    permissions:
      contents: write # Cấp quyền ghi để commit dữ liệu mới

    steps:
    - name: Checkout code
      uses: actions/checkout@v3

    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.9'

    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt

    - name: Run Crawler
      run: |
        python -m src.main

    - name: Commit and Push changes
      run: |
        git config --global user.name 'GitHub Action'
        git config --global user.email 'action@github.com'
        git add data/daily_prices.csv
        git diff --quiet && git diff --staged --quiet || (git commit -m "Update daily prices" && git push)
```

### 2. Yêu cầu
*   File `requirements.txt` phải có sẵn.
*   Repository phải là Private (để bảo mật) hoặc Public tùy bạn.

## Option 2: Google Colab (Manual/Scheduled)

Nếu bạn bắt buộc phải dùng Google Colab:

1.  Upload toàn bộ folder project lên Google Drive.
2.  Tạo một Notebook mới `run_crawler.ipynb`.
3.  Mount Google Drive:
    ```python
    from google.colab import drive
    drive.mount('/content/drive')
    %cd /content/drive/MyDrive/Asset-Price-Task
    ```
4.  Cài đặt thư viện:
    ```python
    !pip install -r requirements.txt
    ```
5.  Chạy script:
    ```python
    !python -m src.main
    ```
6.  **Lập lịch:** Colab phiên bản Free không hỗ trợ schedule tự động tắt/bật. Bạn phải dùng gói Colab Pro+ hoặc dùng thư viện `schedule` của Python và treo tab trình duyệt chạy 24/7 (không khuyến khích).
    *   *Workaround:* Dùng Apps Script để trigger Colab (phức tạp và không ổn định).
    *   *Khuyên dùng Option 1.*

## Kiểm tra dữ liệu
Dữ liệu sẽ được lưu vào file `data/daily_prices.csv`. Bạn có thể mở file này trực tiếp trên GitHub hoặc download về để xem.
