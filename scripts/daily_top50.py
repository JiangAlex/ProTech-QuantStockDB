#!/usr/bin/env python3
"""
Daily Top50 - 每日漲跌幅排行榜
漲幅 Top50 (gainer) + 跌幅 Top50 (loser)

執行方式:
    python daily_top50.py [YYYY-MM-DD]
    若無日期引數，預設為前一交易日
"""

import psycopg2
import os
import sys
from datetime import date, timedelta
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.notify import notify_error, notify_ok

DB_CONFIG = {
    'host': os.getenv('PGHOST', 'blog.softsnail.com'),
    'port': int(os.getenv('PGPORT', 2432)),
    'user': os.getenv('PGUSER', 'reef'),
    'password': os.getenv('PGPASSWORD', 'accton123'),
    'database': os.getenv('PGDATABASE', 'twsestock')
}

TOP_N = 50


def get_prev_trading_day(conn, ref_date: date) -> date:
    """取得 ref_date 的前一交易日（週末/假日往前找）"""
    cur = conn.cursor()
    cur.execute("""
        SELECT MAX(trade_date) FROM daily_kline
        WHERE trade_date < %s
    """, (ref_date,))
    row = cur.fetchone()
    cur.close()
    if row and row[0]:
        return row[0]
    return ref_date - timedelta(days=1)


def get_top50(conn, trade_date: date, category: str) -> list:
    """
    取得指定日期、指定類别的 Top50。
    category: 'gainer' (漲幅最高) 或 'loser' (跌幅最大)
    change_percent 以前一交易日收盤價為基準計算
    """
    order = 'DESC' if category == 'gainer' else 'ASC'

    # 使用 LAG 視窗函數取得前一交易日收盤價
    # 關鍵：CTE 先算出 LAG，再 filter，避免 LAG 無法跨列比較
    cur = conn.cursor()
    cur.execute(f"""
        WITH windowed AS (
            SELECT
                k.stock_code,
                COALESCE(b.stock_name, k.stock_code) AS name,
                k.trade_date,
                k.close AS close_price,
                k.volume,
                LAG(k.close) OVER (
                    PARTITION BY k.stock_code ORDER BY k.trade_date
                ) AS prev_close
            FROM daily_kline k
            LEFT JOIN stock_basic b ON k.stock_code = b.stock_code
            WHERE k.trade_date <= %s
              AND k.close IS NOT NULL
              AND k.close > 0
        ),
        calculated AS (
            SELECT
                stock_code,
                name,
                trade_date,
                close_price,
                volume,
                close_price - prev_close AS change_amount,
                ROUND(
                    (close_price - prev_close) / NULLIF(prev_close, 0) * 100, 2
                ) AS change_percent
            FROM windowed
            WHERE trade_date = %s
              AND prev_close IS NOT NULL
        )
        SELECT stock_code, name, change_amount, change_percent, close_price, volume
        FROM calculated
        WHERE change_percent IS NOT NULL
          AND change_percent != 0
        ORDER BY change_percent {order}, stock_code ASC
        LIMIT %s
    """, (trade_date, trade_date, TOP_N))

    rows = cur.fetchall()
    cur.close()
    return rows


def upsert_top50(conn, trade_date: date, category: str, rows: list):
    """Upsert top50 資料"""
    cur = conn.cursor()

    # 刪除該日該類别的舊資料
    cur.execute("""
        DELETE FROM daily_top50
        WHERE trade_date = %s AND category = %s
    """, (trade_date, category))

    # 插入新資料
    for rank, (stock_code, name, change_amount, change_percent, close_price, volume) in enumerate(rows, 1):
        cur.execute("""
            INSERT INTO daily_top50
            (trade_date, rank, category, stock_code, name, change_percent, change_amount, close_price, volume)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (trade_date, rank, category, stock_code, name, change_percent, change_amount, close_price, volume))

    cur.close()
    conn.commit()


def run(trade_date: date):
    """主程式"""
    conn = psycopg2.connect(**DB_CONFIG)

    # 確認日期有資料
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM daily_kline WHERE trade_date = %s", (trade_date,))
    count = cur.fetchone()[0]
    cur.close()

    if count == 0:
        # 自動往前找有資料的交易日
        real_date = get_prev_trading_day(conn, trade_date)
        print(f'指定日期 {trade_date} 無資料，自動改用 {real_date}')
        trade_date = real_date

    print(f'=== Daily Top50 for {trade_date} ===')

    for category in ('gainer', 'loser'):
        rows = get_top50(conn, trade_date, category)
        upsert_top50(conn, trade_date, category, rows)
        print(f'  [{category:6s}] {len(rows)} records upserted')

    conn.close()
    return trade_date


if __name__ == '__main__':
    if len(sys.argv) >= 2:
        trade_date = date.fromisoformat(sys.argv[1])
    else:
        # 預設前一交易日
        conn = psycopg2.connect(**DB_CONFIG)
        trade_date = get_prev_trading_day(conn, date.today())
        conn.close()
        print(f'使用前一交易日: {trade_date}')

    try:
        result_date = run(trade_date)
        notify_ok('daily_top50', f'{result_date} 完成')
    except Exception as e:
        notify_error('daily_top50', e)
        raise
