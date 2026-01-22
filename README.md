# Daily Asset Price Collection Tool

Automated daily price collection for Vietnamese financial assets (Stocks, ETFs, Open-end Funds, Gold).

## Overview

This tool collects closing prices (for stocks/ETFs), NAV (for funds), and gold prices from public Vietnamese financial data sources.

### Current Status (as of Jan 2026)

| Asset Type | Count | Working | Source | Status |
|------------|-------|---------|--------|--------|
| Stocks | 9 | 9/9 | VNDirect API | 100% |
| ETFs | 3 | 3/3 | VNDirect API | 100% |
| Funds | 17 | 2/17 | VNDirect API | 12% |
| Gold | 2 | 0/2 | Blocked | 0% |
| **Total** | **31** | **14/31** | - | **45%** |

**Note:** Many Vietnamese financial websites block automated requests from cloud/server IPs. The tool is designed to collect what's available and clearly report what failed.

## Features

- **VNDirect API Integration**: Reliable source for stocks, ETFs, and some funds
- **Smart Storage**: CSV append-only with deduplication by date
- **Honest Reporting**: Clearly shows what data was collected vs. what failed
- **Selenium Support**: Optional browser automation for blocked sites
- **Retry & Logging**: Built-in error handling and detailed logs

## Project Structure

```
Asset-Price-Task/
├── data/
│   ├── assets.csv             # 31 asset definitions (input)
│   └── daily_prices.csv       # Collected prices (output)
├── docs/
│   ├── asset_source_mapping.md
│   ├── data_schema_design.md
│   └── automation_setup.md
├── src/
│   ├── crawlers.py            # StockCrawler, FundCrawler, GoldCrawler
│   ├── main.py                # Main orchestrator
│   └── utils.py               # Request helpers, retry, logging
├── requirements.txt
└── README.md
```

## Installation & Usage

### Requirements
- Python 3.8+
- Git

### Installation
```bash
git clone https://github.com/thethien8a/Asset-Price-Task
cd Asset-Price-Task
pip install -r requirements.txt
```

### Run Manually
```bash
python -m src.main
```

### Sample Output
```
============================================================
COLLECTION SUMMARY
============================================================

Total assets in config: 31
Successfully collected: 14
Failed to collect: 17
New records saved: 14

[OK] Collected (14):
     HPG: 26,850 VND (VNDirect)
     FPT: 103,500 VND (VNDirect)
     ...
     VESAF: 36,452 VND (VNDirect)
     VEOF: 37,702 VND (VNDirect)

[XX] Failed (17):
     GOLD_SJC (gold)
     VCBFMGF (fund)
     ...
```

## Data Output

Data is saved to `data/daily_prices.csv` in this format:

| date | asset_code | price | asset_name | asset_type | source |
|------|------------|-------|------------|------------|--------|
| 2026-01-22 | HPG | 26850.0 | Hoa Phat Group | stock | VNDirect |
| 2026-01-22 | VESAF | 36451.97 | VinaCapital Equity Special | fund | VNDirect |

## What Works

### VNDirect API (100% Working)
- All 9 stocks: HPG, FPT, MBB, SSI, POW, VCG, DGC, VND, VTP
- All 3 ETFs: FUEVFVND, E1VFVN30, FUESSVFL
- 2 funds: VESAF, VEOF (listed on exchange)

### Not Available via API
Due to IP blocking/anti-bot protection:
- 15 funds: VMEEF, VDEF, VIBF, VFF, VLGF, VCBFMGF, VCBFBCF, VCBFAIF, VCBFTBF, VCBFFIF, SSISCA, SSIBF, DCDS, DCDE, DCBF
- 2 gold prices: GOLD_SJC, GOLD_RING

## Solutions for Blocked Data

1. **Use Selenium** (included in `crawlers.py`):
   ```python
   from src.crawlers import SeleniumFundCrawler
   crawler = SeleniumFundCrawler()
   results = crawler.crawl_vcbf()  # Crawl VCBF funds
   crawler.close()
   ```

2. **Run from different network**: Home IP addresses may have better access

3. **Use residential proxy**: Services like Bright Data, Oxylabs

4. **Manual data entry**: Get prices from official fund manager websites

## Assets Tracked

### Stocks (9)
HPG, FPT, MBB, SSI, POW, VCG, DGC, VND, VTP

### ETFs (3)
FUEVFVND, E1VFVN30, FUESSVFL

### Open-end Funds (17)
- VinaCapital: VESAF, VEOF, VMEEF, VDEF, VIBF, VFF, VLGF
- VCBF: VCBFMGF, VCBFBCF, VCBFAIF, VCBFTBF, VCBFFIF
- SSI: SSISCA, SSIBF
- Dragon Capital: DCDS, DCDE, DCBF

### Gold (2)
GOLD_SJC (SJC Gold Bar), GOLD_RING (Gold Ring 9999)

## Contributing

If you find a working data source for the blocked assets, please update `src/crawlers.py` and submit a PR.

---
*Built with Python. Data sources: VNDirect API.*
