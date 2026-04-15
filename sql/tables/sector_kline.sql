-- Sector K-Line Table
-- 產業 K 線資料
CREATE TABLE IF NOT EXISTS sector_kline (
    id SERIAL PRIMARY KEY,
    sector_code VARCHAR(20) NOT NULL,
    trade_date DATE NOT NULL,
    open_price NUMERIC(10, 2),
    high_price NUMERIC(10, 2),
    low_price NUMERIC(10, 2),
    close_price NUMERIC(10, 2),
    volume BIGINT,
    amount NUMERIC(20, 2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(sector_code, trade_date)
);
