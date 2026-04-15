-- Stock Basic Table
-- 股票基本資料
CREATE TABLE IF NOT EXISTS stock_basic (
    stock_code VARCHAR(20) PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    market VARCHAR(20),
    industry VARCHAR(100),
    listed_date DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
