#!/usr/bin/env python3
"""
TWSE 季財報抓取程式
資料來源: https://mopsfin.twse.com.tw/opendata/t187ap14_L.csv (EPS/營益/淨利)
              https://mopsfin.twse.com.tw/opendata/t187ap17_L.csv (毛利率/利益率/純益率)

每季發布: Q1在5月, Q2在8月, Q3在11月, Q4在隔年3月
"""

import requests
import psycopg2
import csv
import io
import os
from datetime import datetime

DB_CONFIG = {
    'host': os.getenv('PGHOST', 'blog.softsnail.com'),
    'port': int(os.getenv('PGPORT', 2432)),
    'user': os.getenv('PGUSER', 'reef'),
    'password': os.getenv('PGPASSWORD', 'accton123'),
    'database': os.getenv('PGDATABASE', 'twsestock')
}

URL_MARGINS = 'https://mopsfin.twse.com.tw/opendata/t187ap17_L.csv'
URL_EPS     = 'https://mopsfin.twse.com.tw/opendata/t187ap14_L.csv'
USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'


def fetch_csv(url: str) -> list:
    """下載並解析 CSV，回傳 list of dicts"""
    r = requests.get(url, headers={'User-Agent': USER_AGENT}, timeout=30)
    r.raise_for_status()
    content = r.content
    if content[:3] == b'\xef\xbb\xbf':
        content = content[3:]
    text = content.decode('utf-8')
    reader = csv.DictReader(io.StringIO(text))
    return list(reader)


def roc_to_western(roc_year: str) -> int:
    """ROC 年分 (114) → 西元 (2025)
    民國114年 = 西元2025年 (114 + 1911 = 2025)
    """
    return int(roc_year) + 1911


def parse_revenue_date(date_str: str) -> str:
    """出表日期 1150415 → YYYY-MM-DD"""
    date_str = date_str.strip().strip('"')
    if len(date_str) != 7:
        return None
    roc_y = int(date_str[:3])
    western = roc_y + 1911
    return f"{western}-{date_str[3:5]}-{date_str[5:7]}"


def fetch_quarterly() -> tuple:
    """
    合併 t187ap14 (EPS/絕對值) + t187ap17 (比率)
    回傳: (margins_data, eps_data)
    """
    margins_raw = fetch_csv(URL_MARGINS)
    eps_raw     = fetch_csv(URL_EPS)

    # margins: index by (stock_code, year, quarter)
    margins_map = {}
    for row in margins_raw:
        yr = roc_to_western(row['年度'])
        q  = row['季別'].strip().strip('"')
        code = row['公司代號'].strip().strip('"')
        if not code.isdigit() or len(code) != 4:
            continue
        key = (code, yr, q)
        try:
            margins_map[key] = {
                'stock_code':       code,
                'stock_name':       row['公司名稱'].strip().strip('"'),
                'revenue':          float(row['營業收入(百萬元)'].strip().strip('"').replace(',', '')) if row['營業收入(百萬元)'].strip().strip('"') not in ('-', '') else None,
                'gross_margin':     float(row['毛利率(%)(營業毛利)/(營業收入)'].strip().strip('"')) if row['毛利率(%)(營業毛利)/(營業收入)'].strip().strip('"') not in ('-', '') else None,
                'operating_margin': float(row['營業利益率(%)(營業利益)/(營業收入)'].strip().strip('"')) if row['營業利益率(%)(營業利益)/(營業收入)'].strip().strip('"') not in ('-', '') else None,
                'pretax_margin':    float(row['稅前純益率(%)(稅前純益)/(營業收入)'].strip().strip('"')) if row['稅前純益率(%)(稅前純益)/(營業收入)'].strip().strip('"') not in ('-', '') else None,
                'aftertax_margin': float(row['稅後純益率(%)(稅後純益)/(營業收入)'].strip().strip('"')) if row['稅後純益率(%)(稅後純益)/(營業收入)'].strip().strip('"') not in ('-', '') else None,
                'fetch_date':       parse_revenue_date(row['出表日期']),
            }
        except (ValueError, KeyError):
            continue

    # eps: 簡單 list（也可擴充至 map）
    eps_map = {}
    for row in eps_raw:
        yr = roc_to_western(row['年度'])
        q  = row['季別'].strip().strip('"')
        code = row['公司代號'].strip().strip('"')
        if not code.isdigit() or len(code) != 4:
            continue
        key = (code, yr, q)
        try:
            rev_str = row['營業收入'].strip().strip('"').replace(',', '')
            revenue_abs = float(rev_str) if rev_str and rev_str != '-' else None
            eps_str = row['基本每股盈餘(元)'].strip().strip('"')
            eps = float(eps_str) if eps_str and eps_str != '-' else None
            eps_map[key] = {
                'eps':      eps,
                'revenue_abs': revenue_abs,  # 營業收入絕對值(元)，備查
            }
        except (ValueError, KeyError):
            continue

    return margins_map, eps_map


def save_quarterly(margins_map: dict, eps_map: dict) -> int:
    """UPSERT quarterly_profit"""
    if not margins_map:
        return 0

    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()

    count = 0
    for key, m in margins_map.items():
        code, yr, q = key
        e = eps_map.get(key, {})

        cur.execute("""
            INSERT INTO quarterly_profit
              (stock_code, stock_name, year, quarter,
               revenue, gross_margin, operating_margin, pretax_margin, aftertax_margin,
               created_at)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,NOW())
            ON CONFLICT (stock_code, year, quarter) DO UPDATE SET
              stock_name        = EXCLUDED.stock_name,
              revenue           = EXCLUDED.revenue,
              gross_margin      = EXCLUDED.gross_margin,
              operating_margin  = EXCLUDED.operating_margin,
              pretax_margin     = EXCLUDED.pretax_margin,
              aftertax_margin   = EXCLUDED.aftertax_margin
        """, (code, m['stock_name'], yr, q,
              m['revenue'], m['gross_margin'], m['operating_margin'],
              m['pretax_margin'], m['aftertax_margin']))
        count += 1

    conn.commit()
    cur.close()
    conn.close()
    return count


def main():
    import argparse
    parser = argparse.ArgumentParser(description='TWSE 季財報抓取')
    parser.add_argument('--dry-run', action='store_true', help='只抓不寫入')
    args = parser.parse_args()

    print(f"[{datetime.now():%Y-%m-%d %H:%M:%S}] TWSE 季財報抓取開始")

    margins_map, eps_map = fetch_quarterly()
    print(f"解析: {len(margins_map)} 筆 (margin), {len(eps_map)} 筆 (EPS)")

    # Show available quarters
    quarters = sorted(set((v['stock_name'] is not None, k[1], k[2])
                           for k, v in margins_map.items()))
    year_quarters = sorted(set((k[1], k[2]) for k in margins_map.keys()))
    print(f"資料年月: {year_quarters}")

    if args.dry_run:
        print("\n=== 前5筆預覽 ===")
        for i, (k, m) in enumerate(list(margins_map.items())[:5]):
            code, yr, q = k
            e = eps_map.get(k, {})
            print(f"  {code} {m['stock_name']:10s} | {yr}-Q{q} | "
                  f"營收={m['revenue']:>12,.2f}M | "
                  f"毛利率={m['gross_margin']:>6}% | "
                  f"營益率={m['operating_margin']:>7}% | "
                  f"EPS={e.get('eps', 'N/A')}")
    else:
        saved = save_quarterly(margins_map, eps_map)
        print(f"寫入完成: {saved} 筆")

    print(f"[{datetime.now():%Y-%m-%d %H:%M:%S}] 結束")


if __name__ == '__main__':
    main()
