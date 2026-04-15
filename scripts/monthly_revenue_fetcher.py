#!/usr/bin/env python3
"""
TWSE 月營收抓取程式
資料來源: https://mopsfin.twse.com.tw/opendata/t187ap05_L.csv (data.gov.tw 公開資料)
每個月初發布上月營收
"""

import requests
import psycopg2
import csv
import io
import os
from datetime import datetime

# DB 連線設定
DB_CONFIG = {
    'host': os.getenv('PGHOST', 'blog.softsnail.com'),
    'port': int(os.getenv('PGPORT', 2432)),
    'user': os.getenv('PGUSER', 'reef'),
    'password': os.getenv('PGPASSWORD', 'accton123'),
    'database': os.getenv('PGDATABASE', 'twsestock')
}

TWSE_REVENUE_CSV_URL = 'https://mopsfin.twse.com.tw/opendata/t187ap05_L.csv'
USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'


def fetch_twse_revenue() -> list:
    """從 TWSE 公開資料 CSV 抓取月營收"""
    headers = {'User-Agent': USER_AGENT}
    r = requests.get(TWSE_REVENUE_CSV_URL, headers=headers, timeout=30)
    r.raise_for_status()

    # UTF-8 BOM strip
    content = r.content
    if content[:3] == b'\xef\xbb\xbf':
        content = content[3:]

    text = content.decode('utf-8')

    # CSV columns:
    # 0: 出表日期 (1150415)
    # 1: 資料年月 (11503)
    # 2: 公司代號 (1101)
    # 3: 公司名稱 (台泥)
    # 4: 產業別 (水泥工業)
    # 5: 當月營收
    # 6: 上月營收
    # 7: 去年當月營收
    # 8: 上月比較增減(%)
    # 9: 去年同月增減(%)
    # 10: 累計當月營收
    # 11: 累計去年營收
    # 12: 累計增減(%)
    # 13: 備註

    records = []
    reader = csv.reader(io.StringIO(text))
    next(reader, None)  # skip header

    for row in reader:
        if len(row) < 14:
            continue

        try:
            fetch_date_raw = row[0].strip().strip('"')   # 1150415
            year_month = row[1].strip().strip('"')       # 11503
            stock_code = row[2].strip().strip('"')       # 1101
            stock_name = row[3].strip().strip('"')
            industry = row[4].strip().strip('"')

            # revenue (當月營收)
            rev_str = row[5].strip().strip('"').replace(',', '')
            revenue = int(rev_str) if rev_str and rev_str != '-' else None

            # revenue_last_month (上月營收)
            last_str = row[6].strip().strip('"').replace(',', '')
            revenue_last_month = int(last_str) if last_str and last_str != '-' else None

            # revenue_yoy (去年同月增減%)
            yoy_str = row[9].strip().strip('"')
            revenue_yoy = float(yoy_str) if yoy_str and yoy_str != '-' else None

            # revenue_mom (上月比較增減%)
            mom_str = row[8].strip().strip('"')
            revenue_mom = float(mom_str) if mom_str and mom_str != '-' else None

            # revenue_ytd (累計當月營收)
            ytd_str = row[10].strip().strip('"').replace(',', '')
            revenue_ytd = int(ytd_str) if ytd_str and ytd_str != '-' else None

            # revenue_ytd_yoy (累計增減%)
            ytd_yoy_str = row[12].strip().strip('"')
            revenue_ytd_yoy = float(ytd_yoy_str) if ytd_yoy_str and ytd_yoy_str != '-' else None

            # fetch_date (出表日期, 轉成 DATE)
            if fetch_date_raw:
                roc_y = int(fetch_date_raw[:3])
                fetch_date = f"{roc_y + 1911}-{fetch_date_raw[3:5]}-{fetch_date_raw[5:7]}"
            else:
                fetch_date = None

            # Filter: only 4-digit stock codes
            if not stock_code or not stock_code.isdigit() or len(stock_code) != 4:
                continue

            records.append((
                stock_code,
                stock_name,
                industry,
                year_month,
                revenue,
                revenue_last_month,
                revenue_yoy,
                revenue_mom,
                revenue_ytd,
                revenue_ytd_yoy,
                fetch_date,
            ))

        except (IndexError, ValueError) as e:
            continue

    return records


def save_revenue(records: list) -> int:
    """寫入 monthly_revenue 表 (UPSERT)"""
    if not records:
        return 0

    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()

    count = 0
    for rec in records:
        (stock_code, stock_name, industry, year_month,
         revenue, revenue_last_month, revenue_yoy, revenue_mom,
         revenue_ytd, revenue_ytd_yoy, fetch_date) = rec

        cur.execute("""
            INSERT INTO monthly_revenue
              (stock_code, stock_name, industry, year_month,
               revenue, revenue_last_month, revenue_yoy, revenue_mom,
               revenue_ytd, revenue_ytd_yoy, created_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW())
            ON CONFLICT (stock_code, year_month) DO UPDATE SET
              stock_name   = EXCLUDED.stock_name,
              industry     = EXCLUDED.industry,
              revenue      = EXCLUDED.revenue,
              revenue_last_month = EXCLUDED.revenue_last_month,
              revenue_yoy  = EXCLUDED.revenue_yoy,
              revenue_mom  = EXCLUDED.revenue_mom,
              revenue_ytd  = EXCLUDED.revenue_ytd,
              revenue_ytd_yoy = EXCLUDED.revenue_ytd_yoy
        """, (stock_code, stock_name, industry, year_month,
              revenue, revenue_last_month, revenue_yoy, revenue_mom,
              revenue_ytd, revenue_ytd_yoy))
        count += 1

    conn.commit()
    cur.close()
    conn.close()
    return count


def update_stock_industry(records: list):
    """從月營收 records 更新 stock_basic.industry"""
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()
    updated = 0
    for rec in records:
        stock_code, stock_name, industry, year_month = rec[0], rec[1], rec[2], rec[3]
        if industry:
            cur.execute("""
                UPDATE stock_basic SET industry = %s
                WHERE stock_code = %s AND (industry IS NULL OR industry = '' OR industry != %s)
            """, (industry, stock_code, industry))
            updated += 1
    conn.commit()
    cur.close()
    conn.close()
    return updated


def main():
    import argparse
    parser = argparse.ArgumentParser(description='TWSE 月營收抓取')
    parser.add_argument('--dry-run', action='store_true', help='只抓不寫入')
    args = parser.parse_args()

    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] TWSE 月營收抓取開始")
    print(f"資料來源: {TWSE_REVENUE_CSV_URL}")

    records = fetch_twse_revenue()
    print(f"解析筆數: {len(records)}")

    if records:
        year_months = set(r[3] for r in records)
        print(f"資料年月: {sorted(year_months)}")

        if args.dry_run:
            print("\n=== 前5筆預覽 ===")
            for r in records[:5]:
                print(f"  {r[0]} {r[1]} | {r[3]} | 營收={r[4]:,}  YoY={r[6]}%")
        else:
            saved = save_revenue(records)
            print(f"寫入完成: {saved} 筆")
            ind_updated = update_stock_industry(records)
            print(f"stock_basic.industry 更新: {ind_updated} 筆")

    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 結束")


if __name__ == '__main__':
    main()
