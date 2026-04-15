# ProTech-QuantStockDB-20260413 工作計畫

## 專案資訊

| 項目 | 內容 |
|------|------|
| 專案代號 | ProTech-QuantStockDB-20260413 |
| 資料庫 | PostgreSQL (blog.softsnail.com:2432) |
| 用途 | 股票分析系統資料庫 |
| 資料期間 | 2023-04-14 ~ 2026-04-14 (三年歷史資料) |

---

## 一、資料表清單

| 資料表 | 功能說明 |
|--------|----------|
| stock_basic | 股票基本資料 |
| daily_kline | 日K線行情 |
| sector_kline | 產業K線行情 |
| sectors | 產業分類 |
| institutional_investors | 法人買賣資料 |
| monthly_revenue | 月營收 (上市) |
| monthly_revenue_tpex | 月營收 (上櫃) |
| quarterly_profit | 季獲利資料 |
| fetch_history | 資料擷取歷史 |

---

## 二、工作分配

### [1] 日線抓取 (Daily) - 每交易日

```
頻率: 每交易日
資料表: daily_kline, institutional_investors
總次數: ~720 次
期間: 2023-04-14 ~ 2026-04-14
```

**工作內容:**
1. 取得股票清單 (stock_basic)
2. 依序抓取每檔股票日線
3. 解析並寫入 daily_kline
4. 記錄至 fetch_history

---

### [2] 月營收 (Monthly) - 每月

```
頻率: 每月15日
資料表: monthly_revenue, monthly_revenue_tpex
總次數: 24 次
期間: 2023-05 ~ 2026-01
```

**工作內容:**
1. 每月固定日期抓取
2. 解析營收數據
3. 寫入 monthly_revenue
4. 記錄至 fetch_history

---

### [3] 季獲利 (Quarterly) - 每季

```
頻率: 每季末
資料表: quarterly_profit
總次數: 12 次
期間: 2023-Q2 ~ 2026-Q1
```

**季度排程:**
| 季度 | 執行日期 |
|------|----------|
| 2023-Q2 | 2023-06-30 |
| 2023-Q3 | 2023-09-30 |
| 2023-Q4 | 2023-12-31 |
| 2024-Q1 | 2024-03-31 |
| 2024-Q2 | 2024-06-30 |
| 2024-Q3 | 2024-09-30 |
| 2024-Q4 | 2024-12-31 |
| 2025-Q1 | 2025-03-31 |
| 2025-Q2 | 2025-06-30 |
| 2025-Q3 | 2025-09-30 |
| 2025-Q4 | 2025-12-31 |
| 2026-Q1 | 2026-03-31 |

---

### [4] 一次性工作 (初始執行)

| 工作 | 資料表 | 說明 |
|------|--------|------|
| 產業分類 | sectors | 僅需執行一次 |
| 股票基本資料 | stock_basic | 初始載入 |

---

## 三、總工作次數

| 類型 | 次數 |
|------|------|
| 日線 (Daily) | 783 次 |
| 月營收 (Monthly) | 24 次 |
| 季獲利 (Quarterly) | 12 次 |
| 一次性 (One-time) | 2 次 |
| **總計** | **821 次** |

---

## 四、資料來源

- **TWSE** - 台灣證券交易所
- **TPEx** - 證券櫃檯買賣中心 (上櫃)

---

## 五、腳本檔案

| 檔案 | 功能 |
|------|------|
| scripts/data_fetcher.py | 數據抓取主程式 |
| scripts/job_scheduler.py | 工作排程分配器 |
| sql/schema.sql | 資料庫結構定義 |
| Skill: twse-tpex-stock-fetcher | TWSE+TPEx 股票抓取系統 |

---

## 六、整合 Skill - TWSE+TPEx 股票資料抓取

### 目標
- 上市 (TSE) + 上櫃 (TPEx)
- 4 位數代碼 (如 0050, 2330)
- 時間範圍：2023-01-01 ~ 2026-03-31 (3年3個月)

### 資料來源

**TWSE API:**
- 每日收盤行情: `https://www.twse.com.tw/rwd/zh/afterTrading/MI_INDEX?date=YYYYMMDD&response=json&type=ALL`
- 三大法人買賣超: `https://www.twse.com.tw/rwd/zh/fund/T86`

**TPEx API:**
- 每日收盤行情: `https://www.tpex.org.tw/www/zh-tw/afterTrading/otc?d=YYYYMMDD&o=json`
- 三大法人買賣超: `https://www.tpex.org.tw/www/zh-tw/insti/dailyTrade`

### 排程分散策略
- 使用 ClawTeam 排程分散請求
- 每次請求間隔 2-3 秒
- Rate Limit: 10 秒/請求
- 失敗重試: 3 次，指數退避

### 重要注意事項
1. 民國年轉換 (ROC → 西元: +1911)
2. 記錄除權息日期至 stock_dividend
3. 記錄每次請求至 fetch_history

---

## 七、待辦事項

- [x] 安裝 twstock (`pip install twstock`)
- [x] 安裝 psycopg2-binary
- [x] 測試資料庫連線 (PostgreSQL blog.softsnail.com:2432)
- [x] TWSE API 驗證
- [x] TPEx API 驗證
- [x] 建立 stock_basic 初始資料 (1,964 檔股票)
- [x] 驗證歷史資料抓取 (808,058 筆日K線)

---

## 八、排程設定

### Cron Jobs (Hermes)

| 排程名稱 | 時間 | 說明 |
|---------|------|------|
| 日線+法人買賣抓取 | 每日 18:00（週一至週五） | 執行 data_fetcher.py |
| 狀態檢查 | 每日 19:00 | 檢查進度並回報 Telegram |
| 月營收抓取 | 每月 15日 08:00 | monthly_revenue |
| 季獲利抓取 | 3,6,9,12月 30日 09:00 | quarterly_profit |

### 資料庫狀況

| 資料表 | 筆數 | 日期範圍 |
|--------|------|----------|
| stock_basic | 1,964 | - |
| daily_kline | 808,058 | 2023-01-03 ~ 2026-04-14 |
| monthly_revenue | 1,070 | - |
| quarterly_profit | 973 | - |
| institutional_investors | 6,507 | - |
| sectors | 40 | - |
| fetch_history | 3,465 | - |

---

*建立日期: 2026-04-14*
*更新日期: 2026-04-14*