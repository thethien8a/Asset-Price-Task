# Daily Asset Price Collection Tool

Automated daily price collection for Vietnamese financial assets (Stocks, ETFs, Open-end Funds, Gold).

## Overview

This tool collects closing prices (for stocks/ETFs), NAV (for funds), and gold prices from public Vietnamese financial data sources.

### Current Status (as of Jan 2026)

| Asset Type | Count | API Mode | Selenium Mode | Source |
|------------|-------|----------|---------------|--------|
| Stocks | 9 | 9/9 (100%) | 9/9 (100%) | VNDirect API |
| ETFs | 3 | 3/3 (100%) | 3/3 (100%) | VNDirect API |
| Funds | 17 | 17/17 (100%) | 17/17 (100%) | Fmarket API |
| Gold | 2 | 0/2 (0%) | 2/2 (100%) | DOJI |
| **Total** | **31** | **29/31 (94%)** | **31/31 (100%)** | - |

## Features

- **Multi-Source Data Collection**: VNDirect API, Fmarket API, DOJI gold prices
- **Smart Storage**: CSV append-only with deduplication by date
- **Honest Reporting**: Clearly shows what data was collected vs. what failed
- **Selenium Support**: Optional browser automation for gold prices
- **Retry & Logging**: Built-in error handling and detailed logs

## Quick Start

```bash
# Clone and install
git clone https://github.com/thethien8a/Asset-Price-Task
cd Asset-Price-Task
pip install -r requirements.txt

# Run (API only - 29/31 assets)
python -m src.main

# Run with Selenium (31/31 assets including gold)
python -m src.main --selenium
```

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
│   ├── crawlers.py            # All crawlers (Stock, Fund, Gold, Selenium)
│   ├── main.py                # Main orchestrator
│   └── utils.py               # Request helpers, retry, logging
├── requirements.txt
└── README.md
```

## Usage

### Basic Usage (API Only)
```bash
python -m src.main
```
Collects 29/31 assets (stocks, ETFs, funds). Gold requires Selenium.

### Full Collection (with Selenium)
```bash
python -m src.main --selenium
```
Collects all 31/31 assets including gold prices.

### Sample Output
```
============================================================
COLLECTION SUMMARY
============================================================

Total assets in config: 31
Successfully collected: 31
Failed to collect: 0
New records saved: 31

[OK] Collected (31):
     DCBF: 29,072 VND (Fmarket)
     DGC: 73,800 VND (VNDirect)
     FPT: 103,500 VND (VNDirect)
     GOLD_RING: 167,500,000 VND (Gold Crawler)
     GOLD_SJC: 169,300,000 VND (Gold Crawler)
     HPG: 26,850 VND (VNDirect)
     ...
============================================================
```

## Data Sources

| Source | Assets | Method | Reliability |
|--------|--------|--------|-------------|
| **VNDirect API** | 9 stocks, 3 ETFs | HTTP API | Excellent |
| **Fmarket API** | 17 funds | HTTP API | Excellent |
| **DOJI (giavang.doji.vn)** | 2 gold prices | HTTP (static HTML) | Good |

### Data Output

Data is saved to `data/daily_prices.csv`:

| date | asset_code | price | asset_name | asset_type | currency | source |
|------|------------|-------|------------|------------|----------|--------|
| 2026-01-23 | HPG | 26850.0 | Hoa Phat Group | stock | VND | VNDirect |
| 2026-01-23 | VESAF | 36451.97 | VinaCapital Equity Special | fund | VND | Fmarket |
| 2026-01-23 | GOLD_SJC | 169300000.0 | SJC Gold Bar | gold | VND | Gold Crawler |

## Assets Tracked (31 Total)

### Stocks (9)
| Code | Name |
|------|------|
| HPG | Hoa Phat Group |
| FPT | FPT Corp |
| MBB | MB Bank |
| SSI | SSI Securities |
| POW | PV Power |
| VCG | Vinaconex |
| DGC | Duc Giang Chemicals |
| VND | VNDirect Securities |
| VTP | Viettel Post |

### ETFs (3)
| Code | Name |
|------|------|
| FUEVFVND | DCVFM VNDiamond ETF |
| E1VFVN30 | DCVFM VN30 ETF |
| FUESSVFL | SSI VNFin Lead ETF |

### Open-end Funds (17)
| Manager | Funds |
|---------|-------|
| VinaCapital | VESAF, VEOF, VMEEF, VDEF, VIBF, VFF, VLGF |
| VCBF | VCBFMGF, VCBFBCF, VCBFAIF, VCBFTBF, VCBFFIF |
| SSI | SSISCA, SSIBF |
| Dragon Capital | DCDS, DCDE, DCBF |

### Gold (2)
| Code | Name | Unit |
|------|------|------|
| GOLD_SJC | SJC Gold Bar | VND/luong |
| GOLD_RING | Gold Ring 9999 | VND/luong |

## Technical Details

### Crawlers

1. **StockCrawler**: VNDirect dchart API for stocks and ETFs
2. **FmarketCrawler**: Fmarket API for all 17 open-end funds
3. **SeleniumGoldCrawler**: DOJI gold prices with SJC/BTMC fallback

### Gold Price Extraction

Gold prices from DOJI are shown in `nghìn/chỉ` (thousand VND per chi):
- 1 lượng = 10 chỉ
- Price per lượng = displayed_price × 10 × 1000

Example: `16,930` nghìn/chỉ = 169,300,000 VND/lượng

### Fallback Chain for Gold

```
DOJI (HTTP) → SJC (Selenium) → BTMC (Selenium)
```

DOJI is preferred as it provides static HTML (no JavaScript rendering needed).

## Automation

See `docs/automation_setup.md` for:
- Windows Task Scheduler setup
- Linux cron setup
- GitHub Actions workflow

## Requirements

- Python 3.8+
- Chrome browser (for Selenium mode)
- Dependencies: `requests`, `selenium`, `webdriver-manager`

## Contributing

Contributions welcome! If you find a better data source or improve the crawlers, please submit a PR.

---
*Built with Python. Data sources: VNDirect, Fmarket, DOJI.*
