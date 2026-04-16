-- Migration 001: Sectors cleanup + Industry table + SectorKline backfill
-- Date: 2026-04-16
-- Description: Clean dirty sectors, create industry table, update stock_basic.industry, backfill sector_kline

BEGIN;

--------------------------------------------------------------------------------
-- 1. Clean sectors table: remove garbage entries
--------------------------------------------------------------------------------

-- 9103 存託憑證 → ETF
UPDATE stock_basic SET industry = 'ETF' WHERE industry = '存託憑證';

-- Delete dirty sectors from sector_kline
DELETE FROM sector_kline WHERE sector_code = '10';  -- 玻璃 (no real stocks)
DELETE FROM sector_kline WHERE sector_code = '17';  -- Index (invalid)
DELETE FROM sector_kline WHERE sector_code = '98';  -- 存託憑證

-- Delete dirty sectors
DELETE FROM sectors WHERE code = '10';
DELETE FROM sectors WHERE code = '17';
DELETE FROM sectors WHERE code = '98';

--------------------------------------------------------------------------------
-- 2. Create industry table (clean industry name → code mapping)
--------------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS industry (
    code    VARCHAR(4) PRIMARY KEY,
    name    VARCHAR(100) NOT NULL,
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Sync from sectors table (sectors is now clean)
DELETE FROM industry;
INSERT INTO industry (code, name, updated_at)
SELECT code, name, NOW()
FROM sectors
ON CONFLICT (code) DO UPDATE SET name = EXCLUDED.name, updated_at = NOW();

--------------------------------------------------------------------------------
-- 3. Fill stock_basic.industry blanks from monthly revenue CSV
--    (run after monthly_revenue table is populated)
--------------------------------------------------------------------------------

-- 4. Backfill sector_kline from daily_kline (all history)
--------------------------------------------------------------------------------

TRUNCATE sector_kline;

INSERT INTO sector_kline (
    sector_code, trade_date,
    open_price, high_price, low_price, close_price,
    volume, change_pct, amount, trades,
    created_at
)
SELECT
    s.code::varchar,
    dk.trade_date,
    -- VWAP: volume-weighted average price
    SUM(dk.open  * dk.volume) / NULLIF(SUM(dk.volume), 0) AS open_price,
    SUM(dk.high  * dk.volume) / NULLIF(SUM(dk.volume), 0) AS high_price,
    SUM(dk.low   * dk.volume) / NULLIF(SUM(dk.volume), 0) AS low_price,
    SUM(dk.close * dk.volume) / NULLIF(SUM(dk.volume), 0) AS close_price,
    SUM(dk.volume)                                          AS volume,
    NULL                                                    AS change_pct,
    SUM(dk.volume)                                          AS amount,
    COUNT(DISTINCT dk.stock_code)                           AS trades,
    NOW()                                                   AS created_at
FROM daily_kline dk
JOIN stock_basic sb ON dk.stock_code = sb.stock_code
JOIN sectors s ON sb.industry = s.name
WHERE dk.volume > 0
  AND dk.close IS NOT NULL
  AND dk.close > 0
  AND sb.industry IS NOT NULL
  AND sb.industry != ''
  AND sb.industry NOT IN ('存託憑證')
GROUP BY s.code, dk.trade_date
ON CONFLICT (sector_code, trade_date) DO NOTHING;

--------------------------------------------------------------------------------
-- 5. Update change_pct for sector_kline (requires sorted iteration)
--------------------------------------------------------------------------------

-- First, sort by trade_date and compute prev close for each sector
-- This is done in Python: scripts/sector_kline_backfill_changepct.py
-- Run separately after this migration

COMMIT;
