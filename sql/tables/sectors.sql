-- Sectors Table
-- 產業分類
CREATE TABLE IF NOT EXISTS sectors (
    sector_code VARCHAR(20) PRIMARY KEY,
    sector_name VARCHAR(100) NOT NULL,
    parent_code VARCHAR(20),
    level INTEGER DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
