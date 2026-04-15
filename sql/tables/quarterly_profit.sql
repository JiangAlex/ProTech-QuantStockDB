-- Quarterly Profit Table
-- 季獲利資料
CREATE TABLE IF NOT EXISTS quarterly_profit (
    id SERIAL PRIMARY KEY,
    stock_code VARCHAR(20) NOT NULL,
    quarter VARCHAR(7) NOT NULL,
    revenue NUMERIC(20, 2),
    gross_profit NUMERIC(20, 2),
    operating_profit NUMERIC(20, 2),
    net_profit NUMERIC(20, 2),
    eps NUMERIC(10, 2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(stock_code, quarter)
);
