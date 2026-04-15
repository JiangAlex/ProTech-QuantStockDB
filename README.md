# ProTech-QuantStockDB

股票數據系統 - 台灣上市/櫃股票歷史資料庫

## 資料庫架構

共 9 個資料表，以 `stock_code` 關聯至 `stock_basic` 形成星狀結構：

| 資料表 | 說明 | 主鍵 |
|--------|------|------|
| **stock_basic** | 上市/櫃股票基本資料（代碼、名稱、市場別） | stock_code |
| **daily_kline** | 個股日K線（開高低收成交量） | (stock_code, trade_date) |
| **sectors** | 產業分類（代碼、名稱） | code |
| **sector_kline** | 產業指數日K線 | (sector_code, trade_date) |
| **institutional_investors** | 三大法人買賣超（外資、投信、自營商） | (stock_code, trade_date) |
| **monthly_revenue** | 上市(TWSE)月營收，含年增率 | (stock_code, year_month) |
| **monthly_revenue_tpex** | 上櫃(TPEx)月營收 | (stock_code, year_month) |
| **quarterly_profit** | 季報獲利（營收、毛利率） | (stock_code, year, quarter) |
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
├── scripts/             # 資料抓取腳本
├── sql/                 # SQL schema 定義
└── package.json         # Node.js 相依
```

## 資料來源

- TWSE（台灣證券交易所）: 日K線、月營收、季報
- TPEx（證券櫃檯買賣中心）: 上櫃股票資料
- 產業分類: TWSE 產業分類標準

## 連線資訊

連線資訊儲存於環境變數或 `.env` 檔案中，請參閱內部文件。
