-- Indexes for Stock Database
-- 資料庫索引定義

-- stock_basic indexes
CREATE INDEX idx_stock_basic_market ON stock_basic(market);
CREATE INDEX idx_stock_basic_industry ON stock_basic(industry);

-- daily_kline indexes
CREATE INDEX idx_daily_kline_stock_date ON daily_kline(stock_code, trade_date);
CREATE INDEX idx_daily_kline_date ON daily_kline(trade_date);

-- sector_kline indexes
CREATE INDEX idx_sector_kline_date ON sector_kline(sector_code, trade_date);

-- sectors indexes
CREATE INDEX idx_sectors_parent ON sectors(parent_code);
CREATE INDEX idx_sectors_level ON sectors(level);

-- institutional_investors indexes
CREATE INDEX idx_inst_investors_stock_date ON institutional_investors(stock_code, trade_date);
CREATE INDEX idx_inst_investors_date ON institutional_investors(trade_date);

-- monthly_revenue indexes
CREATE INDEX idx_monthly_revenue_stock_month ON monthly_revenue(stock_code, year_month);

-- monthly_revenue_tpex indexes
CREATE INDEX idx_monthly_revenue_tpex_stock_month ON monthly_revenue_tpex(stock_code, year_month);

-- quarterly_profit indexes
CREATE INDEX idx_quarterly_profit_stock_quarter ON quarterly_profit(stock_code, quarter);

-- fetch_history indexes
CREATE INDEX idx_fetch_history_table_date ON fetch_history(table_name, created_at);
CREATE INDEX idx_fetch_history_status ON fetch_history(status);
