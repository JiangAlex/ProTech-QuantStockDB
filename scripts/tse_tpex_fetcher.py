#!/usr/bin/env python3
"""
TSE/TPEx 股價抓取程式 (v3)
使用 MI_INDEX API (Table 8) 一次抓取全部股票

API Sources:
- TSE: https://www.twse.com.tw/exchangeReport/MI_INDEX (type=ALL, Table 8)
- TPEx: https://www.tpex.org.tw/web/stock/aftertrading/DAILY_QUOTE
"""

import requests
import psycopg2
import time
from datetime import datetime, timedelta
from typing import List, Tuple, Optional
from pathlib import Path
import os

# DB 連線設定
DB_CONFIG = {
    'host': os.getenv('PGHOST', 'blog.softsnail.com'),
    'port': int(os.getenv('PGPORT', 2432)),
    'user': os.getenv('PGUSER', 'reef'),
    'password': os.getenv('PGPASSWORD', 'accton123'),
    'database': os.getenv('PGDATABASE', 'twsestock')
}

SCRIPT_DIR = Path(__file__).parent.resolve()

# API URLs
TWSE_MI_INDEX_URL = 'https://www.twse.com.tw/exchangeReport/MI_INDEX'
TPEX_DAILY_QUOTE_URL = 'https://www.tpex.org.tw/web/stock/aftertrading/DAILY_QUOTE'
TWSE_T86_URL = 'https://www.twse.com.tw/rwd/zh/fund/T86'

USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'


def to_roc_date(date_obj: datetime) -> str:
    """西元日期轉民國日期"""
    roc_year = date_obj.year - 1911
    return f"{roc_year}/{date_obj.month:02d}/{date_obj.day:02d}"


def fetch_tse_all_stocks(date_obj: datetime = None) -> Optional[List[Tuple]]:
    """使用 MI_INDEX 一次抓取所有 TSE 股票"""
    if date_obj is None:
        date_obj = datetime.now()
    
    date_str = date_obj.strftime('%Y%m%d')
    
    try:
        params = {
            'date': date_str,
            'response': 'json',
            'type': 'ALL',
            'lang': 'zh-tw'
        }
        headers = {'User-Agent': USER_AGENT}
        r = requests.get(TWSE_MI_INDEX_URL, params=params, headers=headers, timeout=30)
        
        if r.status_code != 200:
            print(f"Error: TSE API status {r.status_code}")
            return None
        
        data = r.json()
        
        if data.get('stat') != 'OK':
            print(f"Error: stat = {data.get('stat')}")
            return None
        
        # Table 8: 每日收盤行情(全部)
        if 'tables' not in data or len(data['tables']) < 9:
            print("Error: No tables data")
            return None
        
        stock_table = data['tables'][8]
        if not stock_table.get('data'):
            print("Error: No stock data in table 8")
            return None
        
        records = []
        trade_date = date_obj.date()
        
        for row in stock_table['data']:
            if len(row) < 9:
                continue
            
            try:
                stock_no = row[0].strip()
                stock_name = row[1].strip() if len(row) > 1 else ''
                
                # Only 4-digit stocks (regular TSE/TPEx stocks)
                if not stock_no.isdigit() or len(stock_no) != 4:
                    continue
                
                close_price = float(row[8].replace(',', '')) if row[8] != '-' and row[8] else None
                open_price = float(row[5].replace(',', '')) if row[5] != '-' and row[5] else None
                high_price = float(row[6].replace(',', '')) if row[6] != '-' and row[6] else None
                low_price = float(row[7].replace(',', '')) if row[7] != '-' and row[7] else None
                volume = int(row[2].replace(',', '')) if row[2] != '-' and row[2] else 0
                
                if close_price and volume > 0:
                    records.append((stock_no, trade_date, open_price, high_price, low_price, close_price, volume))
                    
            except (IndexError, ValueError) as e:
                continue
        
        print(f"TSE fetched: {len(records)} records")
        return records
        
    except Exception as e:
        print(f"Error fetching TSE: {e}")
        return None


def fetch_tpex_all_stocks(date_obj: datetime = None) -> Optional[List[Tuple]]:
    """抓取 TPEx 所有上櫃股票 (使用 daily quote)"""
    if date_obj is None:
        date_obj = datetime.now()
    
    # TPEx uses ROC date format: 115/04/01
    roc_date = to_roc_date(date_obj)
    
    try:
        # Get all stocks at once
        params = {
            'd': roc_date,
            'o': 'json'
        }
        headers = {'User-Agent': USER_AGENT}
        r = requests.get(TPEX_DAILY_QUOTE_URL, params=params, headers=headers, timeout=30)
        
        if r.status_code != 200:
            print(f"Error: TPEx API status {r.status_code}")
            return None
        
        # Check if JSON
        if 'application/json' not in r.headers.get('Content-Type', ''):
            print(f"Error: TPEx not JSON: {r.text[:100]}")
            return None
        
        data = r.json()
        
        if 'aaData' not in data:
            print("Error: No aaData in TPEx response")
            return None
        
        records = []
        trade_date = date_obj.date()
        
        for row in data['aaData']:
            if len(row) < 8:
                continue
            
            try:
                stock_no = row[0].strip()
                
                # Only 4-digit stocks
                if not stock_no.isdigit() or len(stock_no) != 4:
                    continue
                
                close_price = float(row[2].replace(',', '')) if row[2] != '-' and row[2] else None
                open_price = float(row[4].replace(',', '')) if row[4] != '-' and row[4] else None
                high_price = float(row[5].replace(',', '')) if row[5] != '-' and row[5] else None
                low_price = float(row[6].replace(',', '')) if row[6] != '-' and row[6] else None
                volume = int(row[7].replace(',', '')) if len(row) > 7 and row[7] != '-' and row[7] else 0
                
                if close_price and volume > 0:
                    records.append((stock_no, trade_date, open_price, high_price, low_price, close_price, volume))
                    
            except (IndexError, ValueError) as e:
                continue
        
        print(f"TPEx fetched: {len(records)} records")
        return records
        
    except Exception as e:
        print(f"Error fetching TPEx: {e}")
        return None


def fetch_tse_institutional(date_obj: datetime = None) -> Optional[List[Tuple]]:
    """使用 T86 API 抓取三大法人買賣資料"""
    if date_obj is None:
        date_obj = datetime.now()

    date_str = date_obj.strftime('%Y%m%d')

    try:
        params = {
            'date': date_str,
            'selectType': 'ALLBUT0999',
            'response': 'json'
        }
        headers = {'User-Agent': USER_AGENT}
        r = requests.get(TWSE_T86_URL, params=params, headers=headers, timeout=30)

        if r.status_code != 200:
            print(f"Error: T86 API status {r.status_code}")
            return None

        data = r.json()
        if data.get('stat') != 'OK' or 'data' not in data:
            print(f"Error: T86 stat = {data.get('stat')}")
            return None

        records = []
        trade_date = date_obj.date()

        for row in data['data']:
            if len(row) < 19:
                continue
            try:
                stock_no = row[0].strip()
                if not stock_no.isdigit() or len(stock_no) != 4:
                    continue

                foreign = int(row[4].replace(',', '')) if row[4] != '-' and row[4] else 0
                trust = int(row[10].replace(',', '')) if row[10] != '-' and row[10] else 0
                dealer = int(row[16].replace(',', '')) if row[16] != '-' and row[16] else 0
                total = int(row[18].replace(',', '')) if row[18] != '-' and row[18] else 0

                records.append((stock_no, trade_date, foreign, trust, dealer, total))

            except (IndexError, ValueError):
                continue

        print(f"TSE 法人 fetched: {len(records)} records")
        return records

    except Exception as e:
        print(f"Error fetching T86: {e}")
        return None


def save_institutional(data: List[Tuple]) -> int:
    """寫入 institutional_investors 表"""
    if not data:
        return 0

    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()

    count = 0
    for record in data:
        stock_no, trade_date, foreign, trust, dealer, total = record
        cur.execute("""
            INSERT INTO institutional_investors
            (stock_code, trade_date, foreign_buy, trust_buy, dealer_buy, total, created_at)
            VALUES (%s, %s, %s, %s, %s, %s, NOW())
            ON CONFLICT (stock_code, trade_date) DO UPDATE SET
            foreign_buy = EXCLUDED.foreign_buy,
            trust_buy = EXCLUDED.trust_buy,
            dealer_buy = EXCLUDED.dealer_buy,
            total = EXCLUDED.total
        """, (stock_no, trade_date, foreign, trust, dealer, total))
        count += 1

    conn.commit()
    cur.close()
    conn.close()
    print(f"Saved to DB institutional: {count} records")
    return count


def log_fetch_history(date_obj: datetime, stock_code: str, record_count: int, status: str) -> None:
    """寫入 fetch_history"""
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()
    try:
        cur.execute("""
            INSERT INTO fetch_history (stock_code, start_date, end_date, status, records_fetched, created_at)
            VALUES (%s, %s, %s, %s, %s, NOW())
            ON CONFLICT DO NOTHING
        """, (stock_code, date_obj.date(), date_obj.date(), status, record_count))
        conn.commit()
    except Exception as e:
        print(f"Warning: fetch_history log failed: {e}")
        conn.rollback()
    finally:
        cur.close()
        conn.close()


def save_daily_prices(price_data: List[Tuple], market_type: str = 'TSE') -> int:
    """批次寫入 daily_kline 表"""
    if not price_data:
        return 0
    
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()
    
    insert_count = 0
    for record in price_data:
        stock_no, trade_date, open_price, high_price, low_price, close_price, volume = record
        sector_code = stock_no[:2] if len(stock_no) >= 2 else '00'
        
        # Use UPSERT
        cur.execute("""
            INSERT INTO daily_kline 
            (stock_code, trade_date, open, high, low, close, volume, sector_code, created_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, NOW())
            ON CONFLICT (stock_code, trade_date) DO UPDATE SET
            open = EXCLUDED.open, high = EXCLUDED.high, low = EXCLUDED.low, 
            close = EXCLUDED.close, volume = EXCLUDED.volume
        """, (stock_no, trade_date, open_price, high_price, low_price, close_price, volume, sector_code))
        insert_count += 1
    
    conn.commit()
    cur.close()
    conn.close()
    print(f"Saved to DB: {insert_count} records ({market_type})")
    return insert_count


def update_stock_list(stocks: List[Tuple], market_type: str = 'TSE') -> int:
    """更新 stock_basic 表"""
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()
    
    insert_count = 0
    for stock_no, stock_name in stocks:
        # Check if exists
        cur.execute("SELECT 1 FROM stock_basic WHERE stock_code = %s", (stock_no,))
        if not cur.fetchone():
            cur.execute("""
                INSERT INTO stock_basic (stock_code, stock_name, market, list_date, created_at)
                VALUES (%s, %s, %s, %s, NOW())
            """, (stock_no, stock_name, market_type, datetime.now().date()))
            insert_count += 1
    
    conn.commit()
    cur.close()
    conn.close()
    return insert_count


def fetch_single_date(date_obj: datetime = None):
    """抓取單日資料"""
    if date_obj is None:
        date_obj = datetime.now()
    
    date_str = date_obj.strftime('%Y%m%d')
    print(f"\n=== {date_str} ===")
    
    # TSE
    tse_records = fetch_tse_all_stocks(date_obj)
    tse_count = save_daily_prices(tse_records, 'TSE') if tse_records else 0
    log_fetch_history(date_obj, 'TSE_ALL', tse_count, 'ok' if tse_count > 0 else 'fail')

    time.sleep(1)  # Rate limit

    # TPEx
    tpex_records = fetch_tpex_all_stocks(date_obj)
    tpex_count = save_daily_prices(tpex_records, 'TPEx') if tpex_records else 0
    log_fetch_history(date_obj, 'TPEX_ALL', tpex_count, 'ok' if tpex_count > 0 else 'fail')

    # 三大法人 (TSE only)
    time.sleep(1)
    inst_records = fetch_tse_institutional(date_obj)
    inst_count = save_institutional(inst_records) if inst_records else 0
    log_fetch_history(date_obj, 'INST_ALL', inst_count, 'ok' if inst_count > 0 else 'fail')

    # 類股K線 aggregation
    time.sleep(1)
    import subprocess, sys
    date_iso = date_obj.strftime('%Y-%m-%d')
    try:
        result = subprocess.run(
            [sys.executable, SCRIPT_DIR / 'sector_kline_fetcher.py', '--date', date_iso],
            capture_output=True, text=True, timeout=60
        )
        if result.returncode == 0:
            for line in result.stdout.strip().split('\n'):
                if line.strip():
                    print(f"  [sector] {line}")
        else:
            print(f"  [sector] WARN: {result.stderr[:200]}")
    except Exception as e:
        print(f"  [sector] skip: {e}")


def main():
    import argparse
    parser = argparse.ArgumentParser(description='TSE/TPEx 股價抓取 v3')
    parser.add_argument('--start', '-s', default=None, help='開始日期 (YYYYMMDD)')
    parser.add_argument('--end', '-e', default=None, help='結束日期 (YYYYMMDD)')
    parser.add_argument('--date', '-d', default=None, help='單一日期 (YYYYMMDD)')
    args = parser.parse_args()
    
    if args.date:
        # Single date
        date_obj = datetime.strptime(args.date, '%Y%m%d')
        fetch_single_date(date_obj)
    else:
        # Date range
        if args.start:
            start_date = datetime.strptime(args.start, '%Y%m%d')
        else:
            start_date = datetime.now()
        
        if args.end:
            end_date = datetime.strptime(args.end, '%Y%m%d')
        else:
            end_date = start_date
        
        # Generate trading days
        current = start_date
        while current <= end_date:
            if current.weekday() < 5:  # Mon-Fri
                fetch_single_date(current)
                time.sleep(1)  # Between days
            current += timedelta(days=1)


if __name__ == '__main__':
    main()