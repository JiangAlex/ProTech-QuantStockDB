#!/usr/bin/env python3
"""
Test Data Generation Script
Generates sample stock data for testing and development.
"""

import os
import sys
import argparse
import random
import string
from datetime import datetime, timedelta
from pathlib import Path

try:
    import psycopg2
    from psycopg2 import sql
except ImportError:
    print("Error: psycopg2 not installed. Run: pip install psycopg2-binary")
    sys.exit(1)

# Database connection configuration
DB_CONFIG = {
    'host': 'blog.softsnail.com',
    'port': 2432,
    'user': 'reef',
    'password': 'accton123',
    'dbname': 'twsestock'
}

# Sample data
STOCK_SYMBOLS = [
    '2330', '2454', '2317', '2308', '2382',  # Taiwan stocks
    'AAPL', 'GOOGL', 'MSFT', 'AMZN', 'NVDA',  # US stocks
    'TSMC', '0050', '0051', '00646', '00878'  # ETFs
]

STOCK_NAMES = {
    '2330': '台積電', '2454': '聯發科', '2317': '鴻海', '2308': '台達電', '2382': '廣達',
    'AAPL': 'Apple Inc.', 'GOOGL': 'Alphabet Inc.', 'MSFT': 'Microsoft Corp.',
    'AMZN': 'Amazon.com', 'NVDA': 'NVIDIA Corp.', 'TSMC': 'Taiwan Semiconductor',
    '0050': '元大台灣50', '0051': '元大中型100', '00646': '元大高股息', '00878': '國泰永續高股息'
}


class DataSeeder:
    def __init__(self):
        self.conn = None
        self.cursor = None
    
    def connect(self):
        """Connect to database."""
        try:
            self.conn = psycopg2.connect(**DB_CONFIG)
            self.cursor = self.conn.cursor()
            print(f"Connected to database: {DB_CONFIG['dbname']}@{DB_CONFIG['host']}")
        except Exception as e:
            print(f"Database connection failed: {e}")
            sys.exit(1)
    
    def close(self):
        """Close database connection."""
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()
        print("Database connection closed.")
    
    def seed_stocks(self, count: int = 10):
        """Generate sample stock master data."""
        print(f"Seeding {count} stock records...")
        
        # Insert sample stocks
        for i, symbol in enumerate(STOCK_SYMBOLS[:count]):
            name = STOCK_NAMES.get(symbol, f'Stock_{symbol}')
            # Try to insert - ignore if already exists
            try:
                self.cursor.execute("""
                    INSERT INTO stocks (symbol, name, created_at)
                    VALUES (%s, %s, %s)
                    ON CONFLICT (symbol) DO NOTHING
                """, (symbol, name, datetime.now()))
            except Exception as e:
                # Table might not exist, skip
                print(f"  Note: Could not insert {symbol} - table may not exist")
        
        self.conn.commit()
        print(f"  Inserted {count} stock records (or skipped duplicates)")
    
    def seed_price_data(self, days: int = 30):
        """Generate sample price data for stocks."""
        print(f"Seeding {days} days of price data...")
        
        end_date = datetime.now()
        
        for symbol in STOCK_SYMBOLS:
            for i in range(days):
                date = end_date - timedelta(days=i)
                
                # Generate realistic price data
                base_price = random.uniform(50, 1000)
                open_price = base_price * random.uniform(0.98, 1.02)
                high_price = base_price * random.uniform(1.00, 1.05)
                low_price = base_price * random.uniform(0.95, 1.00)
                close_price = base_price * random.uniform(0.97, 1.03)
                volume = random.randint(1000000, 10000000)
                
                try:
                    self.cursor.execute("""
                        INSERT INTO stock_prices 
                        (symbol, date, open, high, low, close, volume, created_at)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (symbol, date) DO NOTHING
                    """, (symbol, date.date(), open_price, high_price, low_price, 
                          close_price, volume, datetime.now()))
                except Exception as e:
                    # Table might not exist
                    pass
        
        self.conn.commit()
        print(f"  Generated price data for {len(STOCK_SYMBOLS)} stocks")
    
    def seed_transactions(self, count: int = 100):
        """Generate sample transactions."""
        print(f"Seeding {count} transactions...")
        
        for i in range(count):
            symbol = random.choice(STOCK_SYMBOLS)
            date = datetime.now() - timedelta(days=random.randint(0, 30))
            price = random.uniform(50, 1000)
            quantity = random.randint(100, 10000)
            transaction_type = random.choice(['buy', 'sell'])
            
            try:
                self.cursor.execute("""
                    INSERT INTO transactions 
                    (symbol, date, price, quantity, type, created_at)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    ON CONFLICT DO NOTHING
                """, (symbol, date, price, quantity, transaction_type, datetime.now()))
            except Exception as e:
                pass
        
        self.conn.commit()
        print(f"  Generated {count} transactions")
    
    def create_tables(self):
        """Create sample tables if they don't exist."""
        print("Creating sample tables...")
        
        # Create stocks table
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS stocks (
                id SERIAL PRIMARY KEY,
                symbol VARCHAR(20) UNIQUE NOT NULL,
                name VARCHAR(255),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create stock_prices table
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS stock_prices (
                id SERIAL PRIMARY KEY,
                symbol VARCHAR(20) NOT NULL,
                date DATE NOT NULL,
                open DECIMAL(10, 2),
                high DECIMAL(10, 2),
                low DECIMAL(10, 2),
                close DECIMAL(10, 2),
                volume BIGINT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(symbol, date)
            )
        """)
        
        # Create transactions table
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS transactions (
                id SERIAL PRIMARY KEY,
                symbol VARCHAR(20) NOT NULL,
                date TIMESTAMP NOT NULL,
                price DECIMAL(10, 2) NOT NULL,
                quantity INTEGER NOT NULL,
                type VARCHAR(10) NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        self.conn.commit()
        print("  Tables created successfully")
    
    def clear_data(self):
        """Clear all seeded data."""
        print("Clearing all seeded data...")
        
        self.cursor.execute("DELETE FROM transactions")
        self.cursor.execute("DELETE FROM stock_prices")
        self.cursor.execute("DELETE FROM stocks")
        self.conn.commit()
        
        print("  Data cleared")


def main():
    parser = argparse.ArgumentParser(description='Test Data Seeder')
    parser.add_argument('command', choices=['seed', 'create', 'clear'],
                       help='Command to execute')
    parser.add_argument('-n', '--count', type=int, default=10,
                       help='Number of records to generate')
    parser.add_argument('-d', '--days', type=int, default=30,
                       help='Number of days for price data')
    
    args = parser.parse_args()
    
    seeder = DataSeeder()
    seeder.connect()
    
    try:
        if args.command == 'seed':
            seeder.seed_stocks(args.count)
            seeder.seed_price_data(args.days)
            seeder.seed_transactions(args.count)
            print("Seeding complete!")
        elif args.command == 'create':
            seeder.create_tables()
            print("Tables created!")
        elif args.command == 'clear':
            seeder.clear_data()
            print("Data cleared!")
    finally:
        seeder.close()


if __name__ == '__main__':
    main()