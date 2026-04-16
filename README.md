# ProTech-QuantStockDB

股票數據系統 - 台灣上市/櫃股票歷史資料庫

## 資料庫架構

共 9 個資料表，以 `stock_code` 關聯至 `stock_basic` 形成星狀結構：

| 資料表 | 說明 | 主鍵 |
|--------|------|------|
| **stock_basic** | 上市/櫃股票基本資料（代碼、名稱、市場別、產業分類） | stock_code |
| **daily_kline** | 個股日K線（開高低收成交量） | (stock_code, trade_date) |
| **sectors** | 產業分類（代碼、名稱），用於 sector_kline FK | code |
| **sector_kline** | 產業指數日K線（VWAP 成交量加權均價） | (sector_code, trade_date) |
| **institutional_investors** | 三大法人買賣超（外資、投信、自營商） | (stock_code, trade_date) |
| **monthly_revenue** | 上市(TWSE)月營收，含年增率 | (stock_code, year_month) |
| **monthly_revenue_tpex** | 上櫃(TPEx)月營收 | (stock_code, year_month) |
| **quarterly_profit** | 季報獲利（營收、毛利率、EPS） | (stock_code, year, quarter) |
| **industry** | 產業代碼對照表（code → 名稱），乾淨版 | code |
| **fetch_history** | 資料擷取歷史記錄 | (stock_code, start_date) |

## ER 關聯圖

```
STOCK_BASIC ─┬─ daily_kline       (每日K線)
             ├─ institutional_investors (法人買賣)
             ├─ monthly_revenue         (月營收-TWSE)
             ├─ monthly_revenue_tpex    (月營收-TPEx)
             ├─ quarterly_profit        (季報獲利)
             └─ fetch_history           (擷取記錄)

SECTORS ─ sector_kline (產業指數)
```

## 市場別說明

- **TWSE**: Taiwan Stock Exchange（上市的股票，如 2330）
- **TPEx**: Taipei Exchange（上櫃的股票，如 3152）

## 專案結構

```
ProTech-QuantStockDB/
├── docs/
│   ├── er_diagram.md    # ER 關聯圖
│   └── flowchart.md     # 流程圖
├── migrations/          # 資料庫遷移腳本（SQL）
├── scripts/             # 資料抓取腳本
│   ├── tse_tpex_fetcher.py       # 每日日線 + 三大法人 + 類股K線
│   ├── monthly_revenue_fetcher.py # TWSE 月營收 (t187ap05_L.csv)
│   ├── quarterly_profit_fetcher.py # TWSE 季報 (t187ap14_L + t187ap17_L)
│   └── sector_kline_fetcher.py    # 類股日K線 aggregation
├── sql/                 # SQL schema 定義
└── package.json         # Node.js 相依
```

## 資料來源

### TWSE（台灣證券交易所）

| 資料 | API URL | 格式 | 更新頻率 |
|------|---------|------|----------|
| 日K線 | `https://www.twse.com.tw/rwd/zh/aftertrading/MI_INDEX?type=ALL&response=json&date=YYYYMMDD` | JSON | 每日 |
| 三大法人 | `https://www.twse.com.tw/rwd/zh/fund/T86?date=YYYYMMDD&selectType=ALLBUT0999&response=json` | JSON | 每日 |
| 月營收 | `https://mopsfin.twse.com.tw/opendata/t187ap05_L.csv` | CSV UTF-8 | 每月 10 號 |
| 季報(EPS/純益) | `https://mopsfin.twse.com.tw/opendata/t187ap14_L.csv` | CSV UTF-8 | 每年 3/5/8/11 月 10 號 |
| 季報(毛利率) | `https://mopsfin.twse.com.tw/opendata/t187ap17_L.csv` | CSV UTF-8 | 每年 3/5/8/11 月 10 號 |

### TPEx（證券櫃檯買賣中心）

| 資料 | 狀態 |
|------|------|
| 日K線 | HTML 404，待研究 |
| 月營收 | `monthly_revenue_tpex` 已有 2026-03 資料（1074 檔），待自動化 |

### 產業分類

- `stock_basic.industry` — 來源於月營收 CSV 的 `產業別` 欄位，1900 檔股票，36 個產業
- `sectors` — 產業代碼對照表，33 個有效產業（排除 ETF、存託憑證）
- `sector_kline` — 類股日K線，VWAP 成交量加權均價演算法，806 交易日全回填

## 連線資訊

連線資訊儲存於環境變數或 `.env` 檔案中，請參閱內部文件。
