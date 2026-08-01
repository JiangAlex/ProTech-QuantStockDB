#!/usr/bin/env python3
"""
Backfill us_index_kline data using Yahoo Finance (yfinance).

Symbols:
  ^TWII  -> TWII (台灣加權指數)
  ^DJI   -> DJI  (道瓊工業指數)
  ^IXIC  -> IXIC (Nasdaq)
  ^SOX   -> SOX  (費城半導體指數)
"""

import yfinance as yf
import psycopg2
from datetime import date, timedelta

DB_CONFIG = {
    'host': 'blog.softsnail.com',
    'port': 2432,
    'user': 'reef',
    'password': 'accton123',
    'database': 'twsestock'
}

# Yahoo symbol -> DB symbol
SYMBOLS = {
    '^TWII': 'TWII',
    '^DJI': 'DJI',
    '^IXIC': 'IXIC',
    '^SOX': 'SOX',
}


def get_latest_date(conn, symbol):
    """Get the latest trade_date for a symbol in us_index_kline."""
    with conn.cursor() as cur:
        cur.execute(
            "SELECT MAX(trade_date) FROM us_index_kline WHERE symbol = %s",
            (symbol,)
        )
        row = cur.fetchone()
        return row[0] if row[0] else None


def backfill_symbol(conn, yahoo_symbol, db_symbol, end_date):
    """Fetch and insert missing data for one symbol."""
    latest = get_latest_date(conn, db_symbol)
    if latest is None:
        print(f"  {db_symbol}: No existing data, skipping (need manual start date)")
        return 0

    start_date = latest + timedelta(days=1)
    if start_date > end_date:
        print(f"  {db_symbol}: Already up to date (latest={latest})")
        return 0

    print(f"  {db_symbol}: Fetching {start_date} ~ {end_date} ...")

    # yfinance end is exclusive, so add 1 day
    ticker = yf.Ticker(yahoo_symbol)
    df = ticker.history(start=start_date.isoformat(), end=(end_date + timedelta(days=1)).isoformat())

    if df.empty:
        print(f"  {db_symbol}: No data returned from Yahoo Finance")
        return 0

    inserted = 0
    with conn.cursor() as cur:
        for idx, row in df.iterrows():
            trade_date = idx.date()
            if trade_date < start_date or trade_date > end_date:
                continue
            cur.execute("""
                INSERT INTO us_index_kline (symbol, trade_date, open, high, low, close, volume)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (symbol, trade_date) DO NOTHING
            """, (
                db_symbol,
                trade_date,
                round(row['Open'], 2),
                round(row['High'], 2),
                round(row['Low'], 2),
                round(row['Close'], 2),
                int(row['Volume']) if row['Volume'] else 0
            ))
            if cur.rowcount > 0:
                inserted += 1

    conn.commit()
    print(f"  {db_symbol}: Inserted {inserted} rows")
    return inserted


def main():
    import argparse
    parser = argparse.ArgumentParser(description='us_index_kline 指數抓取 (TWII/DJI/IXIC/SOX)')
    parser.add_argument('--date', '-d', default=None, help='指定結束日期 (YYYY-MM-DD)，預設=今天')
    parser.add_argument('--symbol', '-s', default=None, help='只抓特定 symbol (TWII/DJI/IXIC/SOX)')
    args = parser.parse_args()

    if args.date:
        end_date = date.fromisoformat(args.date)
    else:
        end_date = date.today()

    symbols = SYMBOLS
    if args.symbol:
        # Find matching yahoo symbol
        symbols = {k: v for k, v in SYMBOLS.items() if v == args.symbol.upper()}
        if not symbols:
            print(f"Unknown symbol: {args.symbol}")
            return

    print(f"Backfilling us_index_kline up to {end_date}")
    print("=" * 50)

    conn = psycopg2.connect(**DB_CONFIG)
    total = 0
    try:
        for yahoo_sym, db_sym in symbols.items():
            count = backfill_symbol(conn, yahoo_sym, db_sym, end_date)
            total += count
        print("=" * 50)
        print(f"Done. Total inserted: {total} rows")
    finally:
        conn.close()


if __name__ == '__main__':
    main()
