-- Monthly Revenue TPEx Table (TPEx - 上櫃)
-- 月營收資料 (上櫃)
CREATE TABLE IF NOT EXISTS monthly_revenue_tpex (
    id SERIAL PRIMARY KEY,
    stock_code VARCHAR(20) NOT NULL,
    year_month VARCHAR(7) NOT NULL,
    revenue NUMERIC(20, 2),
    month_over_month NUMERIC(10, 2),
    year_over_year NUMERIC(10, 2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(stock_code, year_month)
);
