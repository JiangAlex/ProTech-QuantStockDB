# ProTech-QuantStockDB-20260413 工作計畫

## 專案資訊

| 項目 | 內容 |
|------|------|
| 專案代號 | ProTech-QuantStockDB-20260413 |
| 資料庫 | PostgreSQL (blog.softsnail.com:2432, db: twsestock) |
| 用途 | 股票分析系統資料庫 |
| 資料期間 | 2023-01-03 ~ ongoing |

---

## 一、資料表清單

| 資料表 | 功能說明 | 主鍵 |
|--------|----------|------|
| stock_basic | 股票基本資料（代碼、名稱、市場別、產業分類） | stock_code |
| daily_kline | 個股日K線（開高低收成交量） | (stock_code, trade_date) |
| daily_top50 | 每日漲跌幅排行榜（漲幅/跌幅各50檔） | (trade_date, category, rank) |
| sector_kline | 產業K線行情（VWAP 成交量加權均價） | (sector_code, trade_date) |
| sectors | 產業分類（代碼、名稱） | sector_code |
| institutional_investors | 法人買賣資料（外資、投信、自營商） | (stock_code, trade_date) |
| monthly_revenue | 月營收 (上市 TWSE) | (stock_code, year_month) |
| monthly_revenue_tpex | 月營收 (上櫃 TPEx) | (stock_code, year_month) |
| quarterly_profit | 季報獲利資料（營收、毛利率、EPS） | (stock_code, quarter) |
| fetch_history | 資料擷取歷史記錄 | id |

---

## 二、排程設定（systemd user timer）

| 排程名稱 | 時間 | 執行腳本 | 說明 |
|---------|------|----------|------|
| quantstock-daily.timer | Mon-Fri 18:00 | tse_tpex_fetcher.py + daily_top50.py | 日線+法人+Top50 |
| quantstock-monthly.timer | 每月15日 08:00 | monthly_revenue_fetcher.py | 月營收 |
| quantstock-quarterly.timer | 3/6/9/12月30日 09:00 | quarterly_profit_fetcher.py | 季報 |

Unit 檔位置: `~/.config/systemd/user/`
通知: `scripts/notify.py`（失敗時發送 Telegram）

---

## 三、資料庫狀況

| 資料表 | 筆數 | 日期範圍 |
|--------|------|----------|
| stock_basic | ~1,964 | - |
| daily_kline | ~895,000 | 2023-01-03 ~ 2026-05-13（825交易日） |
| daily_top50 | 100筆/日 | 2026-05-13 起（漲幅50 + 跌幅50） |
| sector_kline | ~26,598 | 806交易日 × 33產業 |
| sectors | 40 | - |
| institutional_investors | - | - |
| monthly_revenue | - | - |
| monthly_revenue_tpex | - | - |
| quarterly_profit | 3,462 | 2023Q1~2025Q3 (290檔) + 2025Q4 (1,086檔) |

---

## 四、待辦事項

### [完成]

- [x] 安裝 twstock、psycopg2-binary
- [x] 測試資料庫連線 (PostgreSQL blog.softsnail.com:2432)
- [x] TWSE API 驗證
- [x] TPEx API 驗證
- [x] 建立 stock_basic 初始資料 (~1,964 檔股票)
- [x] 驗證歷史資料抓取 (~895,000 筆日K線)
- [x] systemd user timer 排程整合
- [x] Telegram 通知整合 (notify.py)
- [x] daily_top50 漲跌幅排行榜（漲幅/跌幅各50檔）

### [進行中] quarterly_profit 熱門股缺口

**問題:**
- FinMind API Token 已失效（`Token is illegal`）
- MOPS `_L.csv` 僅含最新一季，無歷史 archive
- 2330、2317、2454、2412 等熱門股在 2023Q1~2025Q3 皆無季報
- DB 現況：2023Q1~2025Q3 僅 284~290 檔（老傳產），2025Q4 有 1,086 檔

**現有覆蓋（2025Q4 from MOPS _L）：**

| 股票 | 2025Q4 營收 | 毛利率 | 營益率 |
|------|------------|--------|--------|
| 2330 台積電 | 3,809,054M | 59.89% | 50.83% |
| 2317 鴻海 | 8,103,105M | 6.15% | 3.20% |
| 2454 聯發科 | 595,966M | 47.50% | 17.36% |
| 2412 中華電 | 236,114M | 36.83% | 20.56% |

**可行方案（待研究）:**
1. TWSE 公開資訊觀測站完整歷史下載（需公司認證）
2. `twse` / `mops.twse.com.tw` JSON API 歷史介面
3. 付費資料源：FinFlux、CMoney、TEJ
4. FinMind Token 更新（若可重新申請）

### [待研究] TPEx 日K線自動化

- 月營收已有初步資料（2026-03，1074檔）
- 日K線仍為 HTML 404，待研究資料來源

---

## 五、資料來源

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

---

## 六、指令腳本

| 檔案 | 功能 |
|------|------|
| scripts/tse_tpex_fetcher.py | 每日日線 + 三大法人 + 類股K線 |
| scripts/daily_top50.py | 每日漲跌幅排行榜（漲幅/跌幅各50檔） |
| scripts/monthly_revenue_fetcher.py | TWSE 月營收 |
| scripts/quarterly_profit_fetcher.py | TWSE 季報 |
| scripts/sector_kline_fetcher.py | 類股日K線 aggregation |
| scripts/notify.py | Telegram 通知模組 |
| scripts/migrate.py | 資料庫遷移管理 |
| scripts/backup.py | 資料庫備份 |
| sql/schema.sql | 資料庫結構定義 |
| migrations/ | SQL 遷移腳本 |

---

*建立日期: 2026-04-14*
*更新日期: 2026-05-12*
