-- Fetch History Table
-- 資料擷取歷史
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
