-- Daily Top50 Table
-- 每日漲跌幅排行榜 Top50
-- 漲幅 (gainer) + 跌幅 (loser) 分開排行
CREATE TABLE IF NOT EXISTS daily_top50 (
    id SERIAL PRIMARY KEY,
    trade_date DATE NOT NULL,
    rank INTEGER NOT NULL CHECK (rank >= 1 AND rank <= 50),
    category VARCHAR(10) NOT NULL CHECK (category IN ('gainer', 'loser')),
    stock_code VARCHAR(20) NOT NULL,
    name VARCHAR(100),
    change_percent NUMERIC(10, 2) NOT NULL,
    change_amount NUMERIC(10, 2),
    close_price NUMERIC(10, 2),
    volume BIGINT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(trade_date, category, rank),
    UNIQUE(trade_date, category, stock_code)
);

CREATE INDEX idx_daily_top50_date ON daily_top50(trade_date);
CREATE INDEX idx_daily_top50_category ON daily_top50(trade_date, category);
CREATE INDEX idx_daily_top50_stock ON daily_top50(stock_code);
