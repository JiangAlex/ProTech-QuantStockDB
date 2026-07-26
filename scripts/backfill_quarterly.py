#!/usr/bin/env python3
"""
FinMind 季報回填腳本
一次性將 2023~2025 年季報寫入 quarterly_profit 表
"""
import os, sys, time, requests
from pathlib import Path
from collections import defaultdict

from dotenv import load_dotenv
load_dotenv(Path.home() / '.hermes' / '.env')

import psycopg2

DB_CONFIG = {
    'host': os.getenv('PGHOST', 'blog.softsnail.com'),
    'port': int(os.getenv('PGPORT', 2432)),
    'user': os.getenv('PGUSER', 'reef'),
    'password': os.getenv('DB_MEMORY_PASSWORD', ''),
    'database': os.getenv('PGDATABASE', 'twsestock')
}

API_URL = 'https://api.finmindtrade.com/api/v4/data'
START_DATE = '2023-01-01'
END_DATE = '2025-12-31'
BATCH_SIZE = 50  # 每批 stock_id 數（但API只支援一檔，故實際每批1檔）


def fetch_financial(stock_id: str) -> list:
    """從 FinMind API 抓取單檔季報，回傳 list of dicts"""
    params = {
        'dataset': 'TaiwanStockFinancialStatements',
        'data_id': stock_id,
        'start_date': START_DATE,
        'end_date': END_DATE,
    }
    try:
        r = requests.get(API_URL, params=params, timeout=20)
        d = r.json()
        if d.get('status') != 200:
            return []
        return d.get('data', [])
    except Exception as e:
        print(f'  [{stock_id}] API error: {e}', file=sys.stderr)
        return []


def build_quarterly_rows(data: list, stock_id: str) -> dict:
    """
    將 FinMind raw data 轉成 quarterly_profit 格式
    key: (stock_id, year, quarter)
    """
    # pivot by date
    by_date = defaultdict(dict)
    for r in data:
        date = r['date']  # YYYY-MM-DD
        type_ = r['type']
        value = r['value']
        by_date[date][type_] = value

    rows = {}
    for date, fields in by_date.items():
        # date: '2023-03-31' → year=2023, quarter=Q1
        y = int(date[:4])
        m = int(date[5:7])
        q = f'Q{(m - 1) // 3 + 1}'

        revenue = fields.get('Revenue')
        gross = fields.get('GrossProfit')
        op_inc = fields.get('OperatingIncome')
        pretax = fields.get('PreTaxIncome')
        aftertax = fields.get('IncomeAfterTaxes')
        eps = fields.get('EPS')

        # 計算毛利率
        if revenue and gross and revenue != 0:
            gross_margin = round(gross / revenue * 100, 2)
        else:
            gross_margin = None

        # 營益率
        if revenue and op_inc and revenue != 0:
            operating_margin = round(op_inc / revenue * 100, 2)
        else:
            operating_margin = None

        # 稅前純益率
        if revenue and pretax and revenue != 0:
            pretax_margin = round(pretax / revenue * 100, 2)
        else:
            pretax_margin = None

        # 稅後純益率
        if revenue and aftertax and revenue != 0:
            aftertax_margin = round(aftertax / revenue * 100, 2)
        else:
            aftertax_margin = None

        key = (stock_id, y, q)
        rows[key] = {
            'stock_code': stock_id,
            'year': y,
            'quarter': q,
            'revenue': revenue,          # 百萬元
            'gross_margin': gross_margin,
            'operating_margin': operating_margin,
            'pretax_margin': pretax_margin,
            'aftertax_margin': aftertax_margin,
            'eps': eps,
        }
    return rows


def upsert_quarterly(conn, rows: dict):
    """UPSERT 到 quarterly_profit"""
    if not rows:
        return 0
    cur = conn.cursor()
    count = 0
    for key, r in rows.items():
        cur.execute("""
            INSERT INTO quarterly_profit
              (stock_code, year, quarter, revenue,
               gross_margin, operating_margin, pretax_margin, aftertax_margin,
               created_at)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,NOW())
            ON CONFLICT (stock_code, year, quarter) DO UPDATE SET
              revenue           = EXCLUDED.revenue,
              gross_margin      = EXCLUDED.gross_margin,
              operating_margin  = EXCLUDED.operating_margin,
              pretax_margin     = EXCLUDED.pretax_margin,
              aftertax_margin   = EXCLUDED.aftertax_margin
        """, (r['stock_code'], r['year'], r['quarter'],
              r['revenue'], r['gross_margin'], r['operating_margin'],
              r['pretax_margin'], r['aftertax_margin']))
        count += 1
    conn.commit()
    cur.close()
    return count


def get_all_stock_codes(conn) -> list:
    cur = conn.cursor()
    cur.execute("SELECT stock_code FROM stock_basic ORDER BY stock_code")
    codes = [row[0] for row in cur.fetchall()]
    cur.close()
    return codes


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--dry-run', action='store_true')
    parser.add_argument('--limit', type=int, default=0, help='限制處理的股票數量（除錯用）')
    args = parser.parse_args()

    print(f'[{time.strftime("%Y-%m-%d %H:%M:%S")}] 連接 DB...')
    conn = psycopg2.connect(**DB_CONFIG)

    stock_codes = get_all_stock_codes(conn)
    if args.limit:
        stock_codes = stock_codes[:args.limit]
    total = len(stock_codes)
    print(f'共 {total} 檔股票待處理 ({START_DATE} ~ {END_DATE})')
    if args.dry_run:
        print('DRY RUN - 不寫入資料庫')

    total_rows = 0
    errors = 0

    for i, code in enumerate(stock_codes):
        if i % 100 == 0:
            print(f'進度: {i}/{total} ({i*100//total}%)')

        data = fetch_financial(code)
        if not data:
            errors += 1
            time.sleep(0.1)
            continue

        rows = build_quarterly_rows(data, code)
        if rows and not args.dry_run:
            n = upsert_quarterly(conn, rows)
            total_rows += n

        # 避免 API 限速， slightly throttle
        time.sleep(0.05)

    print(f'完成。寫入 {total_rows} 筆記錄，{errors} 檔失敗')
    if errors > 0:
        print(f'失敗的股票可能是已下市或無季報資料')

    conn.close()
    print(f'[{time.strftime("%Y-%m-%d %H:%M:%S")}] 結束')


if __name__ == '__main__':
    main()
