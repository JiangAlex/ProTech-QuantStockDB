-- Institutional Investors Table
-- 法人買賣資料
CREATE TABLE IF NOT EXISTS institutional_investors (
    id SERIAL PRIMARY KEY,
    stock_code VARCHAR(20) NOT NULL,
    trade_date DATE NOT NULL,
    foreign_buy NUMERIC(20, 2),
    foreign_sell NUMERIC(20, 2),
    foreign_net NUMERIC(20, 2),
    trust_buy NUMERIC(20, 2),
    trust_sell NUMERIC(20, 2),
    trust_net NUMERIC(20, 2),
    dealer_buy NUMERIC(20, 2),
    dealer_sell NUMERIC(20, 2),
    dealer_net NUMERIC(20, 2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(stock_code, trade_date)
);
