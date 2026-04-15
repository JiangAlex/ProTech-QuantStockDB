-- Stock Database Schema for twsestock
-- PostgreSQL Database
-- Generated: 2026-04-13

-- ============================================================
-- Table: stock_basic - 股票基本資料
-- ============================================================
CREATE TABLE IF NOT EXISTS stock_basic (
    stock_code VARCHAR(20) PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    market VARCHAR(20),
    industry VARCHAR(100),
    listed_date DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_stock_basic_market ON stock_basic(market);
CREATE INDEX idx_stock_basic_industry ON stock_basic(industry);

-- ============================================================
-- Table: daily_kline - 日 K 線資料
-- ============================================================
CREATE TABLE IF NOT EXISTS daily_kline (
    id SERIAL PRIMARY KEY,
    stock_code VARCHAR(20) NOT NULL,
    trade_date DATE NOT NULL,
    open_price NUMERIC(10, 2),
    high_price NUMERIC(10, 2),
    low_price NUMERIC(10, 2),
    close_price NUMERIC(10, 2),
    volume BIGINT,
    amount NUMERIC(20, 2),
    change NUMERIC(10, 2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(stock_code, trade_date)
);

CREATE INDEX idx_daily_kline_stock_date ON daily_kline(stock_code, trade_date);
CREATE INDEX idx_daily_kline_date ON daily_kline(trade_date);

-- ============================================================
-- Table: sector_kline - 產業 K 線資料
-- ============================================================
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

CREATE INDEX idx_sector_kline_date ON sector_kline(sector_code, trade_date);

-- ============================================================
-- Table: sectors - 產業分類
-- ============================================================
CREATE TABLE IF NOT EXISTS sectors (
    sector_code VARCHAR(20) PRIMARY KEY,
    sector_name VARCHAR(100) NOT NULL,
    parent_code VARCHAR(20),
    level INTEGER DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_sectors_parent ON sectors(parent_code);
CREATE INDEX idx_sectors_level ON sectors(level);

-- ============================================================
-- Table: institutional_investors - 法人買賣資料
-- ============================================================
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

CREATE INDEX idx_inst_investors_stock_date ON institutional_investors(stock_code, trade_date);
CREATE INDEX idx_inst_investors_date ON institutional_investors(trade_date);

-- ============================================================
-- Table: monthly_revenue - 月營收 (上市)
-- ============================================================
CREATE TABLE IF NOT EXISTS monthly_revenue (
    id SERIAL PRIMARY KEY,
    stock_code VARCHAR(20) NOT NULL,
    year_month VARCHAR(7) NOT NULL,
    revenue NUMERIC(20, 2),
    month_over_month NUMERIC(10, 2),
    year_over_year NUMERIC(10, 2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(stock_code, year_month)
);

CREATE INDEX idx_monthly_revenue_stock_month ON monthly_revenue(stock_code, year_month);

-- ============================================================
-- Table: monthly_revenue_tpex - 月營收 (上櫃)
-- ============================================================
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

CREATE INDEX idx_monthly_revenue_tpex_stock_month ON monthly_revenue_tpex(stock_code, year_month);

-- ============================================================
-- Table: quarterly_profit - 季獲利資料
-- ============================================================
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

CREATE INDEX idx_quarterly_profit_stock_quarter ON quarterly_profit(stock_code, quarter);

-- ============================================================
-- Table: fetch_history - 資料擷取歷史
-- ============================================================
CREATE TABLE IF NOT EXISTS fetch_history (
    id SERIAL PRIMARY KEY,
    table_name VARCHAR(50) NOT NULL,
    stock_code VARCHAR(20),
    start_date DATE,
    end_date DATE,
    record_count INTEGER,
    status VARCHAR(20),
    error_message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_fetch_history_table_date ON fetch_history(table_name, created_at);
CREATE INDEX idx_fetch_history_status ON fetch_history(status);
