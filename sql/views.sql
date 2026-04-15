-- Views for Stock Database
-- 常用視圖定義

-- 視圖: 個股日線合併基本資料
CREATE OR REPLACE VIEW v_stock_daily_with_basic AS
SELECT 
    dk.stock_code,
    sb.stock_name,
    sb.market,
    sb.industry,
    dk.trade_date,
    dk.open,
    dk.high,
    dk.low,
    dk.close,
    dk.volume,
    dk.sector_code
FROM daily_kline dk
LEFT JOIN stock_basic sb ON dk.stock_code = sb.stock_code;

-- 視圖: 法人買賣彙總
CREATE OR REPLACE VIEW v_institutional_summary AS
SELECT 
    stock_code,
    trade_date,
    foreign_buy,
    trust_buy,
    dealer_buy,
    total
FROM institutional_investors
WHERE trade_date >= CURRENT_DATE - INTERVAL '30 days';

-- 視圖: 月營收合併 (上市+上櫃)
CREATE OR REPLACE VIEW v_monthly_revenue_combined AS
SELECT 
    stock_code,
    year_month,
    revenue,
    revenue_last_month,
    revenue_yoy,
    revenue_mom,
    revenue_ytd,
    revenue_ytd_yoy,
    'TWSE' AS source
FROM monthly_revenue
UNION ALL
SELECT 
    stock_code,
    year_month,
    revenue,
    NULL AS revenue_last_month,
    NULL AS revenue_yoy,
    NULL AS revenue_mom,
    NULL AS revenue_ytd,
    NULL AS revenue_ytd_yoy,
    'TPEX' AS source
FROM monthly_revenue_tpex;

-- 視圖: 季獲利與股價關聯
CREATE OR REPLACE VIEW v_quarterly_profit_with_price AS
SELECT 
    qp.stock_code,
    qp.stock_name,
    qp.year,
    qp.quarter,
    qp.revenue AS quarter_revenue,
    qp.aftertax_margin,
    qp.gross_margin,
    dk.close AS latest_price,
    dk.trade_date AS price_date
FROM quarterly_profit qp
LEFT JOIN LATERAL (
    SELECT close, trade_date 
    FROM daily_kline 
    WHERE stock_code = qp.stock_code 
    ORDER BY trade_date DESC 
    LIMIT 1
) dk ON true;

-- 視圖: 資料擷取狀態
CREATE OR REPLACE VIEW v_fetch_status AS
SELECT 
    stock_code,
    start_date,
    end_date,
    status,
    records_fetched,
    created_at,
    updated_at
FROM fetch_history;

-- 視圖: 產業指數日線
CREATE OR REPLACE VIEW v_sector_daily AS
SELECT 
    sk.sector_code,
    s.name AS sector_name,
    sk.trade_date,
    sk.open_price,
    sk.high_price,
    sk.low_price,
    sk.close_price,
    sk.volume,
    sk.amount,
    sk.change_pct
FROM sector_kline sk
LEFT JOIN sectors s ON sk.sector_code = s.code;