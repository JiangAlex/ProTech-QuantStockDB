#!/usr/bin/env python3
"""
類股日K線 aggregation
每日日線 job 完成後執行。

對每個 industry 計算該日成交量加權均價 (VWAP)，
寫入 sector_kline 表 (現有 schema)。

現有 schema: sector_code (對 sectors.code), trade_date, open_price, high_price,
             low_price, close_price, volume, change_pct, amount, trades
"""

import psycopg2
import os
from datetime import datetime, date, timedelta

DB_CONFIG = {
    'host': os.getenv('PGHOST', 'blog.softsnail.com'),
    'port': int(os.getenv('PGPORT', 2432)),
    'user': os.getenv('PGUSER', 'reef'),
    'password': os.getenv('PGPASSWORD', 'accton123'),
    'database': os.getenv('PGDATABASE', 'twsestock')
}


def get_industry_to_sector_map():
    """stock_basic.industry name → sectors.code mapping"""
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()
    cur.execute("""
        SELECT DISTINCT sb.industry, s.code
        FROM stock_basic sb
        JOIN sectors s ON sb.industry = s.name
        WHERE sb.industry IS NOT NULL AND sb.industry != ''
    """)
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return {ind: code for ind, code in rows}


def get_all_industry_codes():
    """所有 stock_basic.industry 名稱 → sectors.code（或自己建立 mapping）"""
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()
    cur.execute("""
        SELECT DISTINCT industry
        FROM stock_basic
        WHERE industry IS NOT NULL AND industry != ''
        ORDER BY industry
    """)
    industries = [r[0] for r in cur.fetchall()]
    cur.close()
    conn.close()
    return industries


def build_industry_sector_code_map():
    """stock_basic.industry name → sectors.code (直接 JOIN 乾淨的 sectors 表)"""
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()
    cur.execute("""
        SELECT sb.industry, s.code
        FROM (SELECT DISTINCT industry FROM stock_basic WHERE industry IS NOT NULL AND industry != '') sb
        LEFT JOIN sectors s ON sb.industry = s.name
    """)
    rows = cur.fetchall()
    cur.close()
    conn.close()
    mapping = {}
    for ind_name, code in rows:
        if code:
            mapping[ind_name] = code
    unmapped = [ind for ind, code in rows if not code]
    if unmapped:
        print(f"[WARN] unmapped industries: {unmapped}")
    return mapping


def aggregate_sector_kline(trade_date=None) -> int:
    """
    對指定交易日，按 industry 聚合 VWAP，寫入 sector_kline。
    """
    if trade_date is None:
        trade_date = (date.today() - timedelta(days=1)).isoformat()
    elif isinstance(trade_date, date):
        trade_date = trade_date.isoformat()

    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()

    # 確認有日線資料
    cur.execute("SELECT COUNT(*) FROM daily_kline WHERE trade_date = %s", (trade_date,))
    if cur.fetchone()[0] == 0:
        print(f"[{trade_date}] daily_kline 無資料，跳過")
        cur.close()
        conn.close()
        return 0

    # 取得 industry → sector_code mapping
    ind_map = build_industry_sector_code_map()

    # VWAP aggregation by industry
    cur.execute("""
        SELECT
            sb.industry,
            SUM(dk.open  * dk.volume) / NULLIF(SUM(dk.volume), 0) AS vwap_open,
            SUM(dk.high  * dk.volume) / NULLIF(SUM(dk.volume), 0) AS vwap_high,
            SUM(dk.low   * dk.volume) / NULLIF(SUM(dk.volume), 0) AS vwap_low,
            SUM(dk.close * dk.volume) / NULLIF(SUM(dk.volume), 0) AS vwap_close,
            SUM(dk.volume)                                          AS total_volume,
            COUNT(DISTINCT dk.stock_code)                           AS stock_count
        FROM daily_kline dk
        JOIN stock_basic sb ON dk.stock_code = sb.stock_code
        WHERE dk.trade_date = %s
          AND sb.industry IS NOT NULL
          AND sb.industry != ''
          AND dk.volume > 0
        GROUP BY sb.industry
    """, (trade_date,))

    rows = cur.fetchall()

    # 取得前一交易日的收盤價（算 change_pct）
    prev_date = (date.fromisoformat(trade_date) - timedelta(days=1)).isoformat()
    cur.execute("""
        SELECT sector_code, close_price
        FROM sector_kline
        WHERE trade_date = %s
    """, (prev_date,))
    prev_close = {row[0]: float(row[1]) for row in cur.fetchall()}

    saved = 0
    for row in rows:
        industry_name, vwap_open, vwap_high, vwap_low, vwap_close, total_volume, stock_count = row

        sector_code = ind_map.get(industry_name)
        if sector_code is None:
            print(f"  [WARN] 找不到 sector_code: '{industry_name}'")
            continue

        # change_pct vs previous close
        prev = prev_close.get(sector_code)
        change_pct = None
        if prev and prev != 0:
            change_pct = (vwap_close - prev) / prev * 100

        cur.execute("""
            INSERT INTO sector_kline
              (sector_code, trade_date, open_price, high_price, low_price,
               close_price, volume, change_pct, amount, trades, created_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW())
            ON CONFLICT (sector_code, trade_date) DO UPDATE SET
              open_price  = EXCLUDED.open_price,
              high_price = EXCLUDED.high_price,
              low_price  = EXCLUDED.low_price,
              close_price= EXCLUDED.close_price,
              volume     = EXCLUDED.volume,
              change_pct = EXCLUDED.change_pct
        """, (sector_code, trade_date,
              vwap_open, vwap_high, vwap_low, vwap_close,
              total_volume, change_pct,
              total_volume,  # amount = volume (近似)
              stock_count))
        saved += 1

    conn.commit()
    cur.close()
    conn.close()
    return saved


def main():
    import argparse
    parser = argparse.ArgumentParser(description='類股日K線 Aggregation')
    parser.add_argument('--date', '-d', default=None, help='YYYY-MM-DD，預設昨天')
    parser.add_argument('--dry-run', action='store_true')
    args = parser.parse_args()

    if args.date:
        trade_date = args.date
    else:
        trade_date = (date.today() - timedelta(days=1)).isoformat()

    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 類股K線 aggregation for {trade_date}")

    if args.dry_run:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        ind_map = build_industry_sector_code_map()
        cur.execute("""
            SELECT sb.industry,
                   SUM(dk.close * dk.volume) / NULLIF(SUM(dk.volume), 0) AS vwap,
                   SUM(dk.volume) AS vol,
                   COUNT(DISTINCT dk.stock_code) AS cnt
            FROM daily_kline dk
            JOIN stock_basic sb ON dk.stock_code = sb.stock_code
            WHERE dk.trade_date = %s
              AND sb.industry IS NOT NULL
              AND dk.volume > 0
            GROUP BY sb.industry
            ORDER BY vol DESC
        """, (trade_date,))
        print(f"\n{'':20s} {'VWAP':>10} {'Volume':>18} {'Stocks':>6} {'Sector':>6}")
        for row in cur.fetchall():
            code = ind_map.get(row[0], '???')
            print(f"  {row[0]:20s} {row[1]:>10.4f} {row[2]:>18,} {row[3]:>6} {code:>6}")
        cur.close()
        conn.close()
    else:
        saved = aggregate_sector_kline(trade_date)
        print(f"寫入完成: {saved} 產業")


if __name__ == '__main__':
    main()
