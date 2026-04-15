#!/usr/bin/env python3
"""
Common Query Utilities Library
Provides reusable database query functions for stock data analysis.
"""

import os
import sys
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple

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


class StockQuery:
    """Stock database query utilities."""
    
    def __init__(self, config: Dict = None):
        self.config = config or DB_CONFIG
        self.conn = None
        self.cursor = None
    
    def __enter__(self):
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
    
    def connect(self):
        """Connect to database."""
        self.conn = psycopg2.connect(**self.config)
        self.cursor = self.conn.cursor()
    
    def close(self):
        """Close database connection."""
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()
    
    # ==================== Basic Queries ====================
    
    def get_all_stocks(self) -> List[Dict]:
        """Get all stock symbols."""
        self.cursor.execute("SELECT symbol, name FROM stocks ORDER BY symbol")
        return [{'symbol': r[0], 'name': r[1]} for r in self.cursor.fetchall()]
    
    def get_stock_by_symbol(self, symbol: str) -> Optional[Dict]:
        """Get stock info by symbol."""
        self.cursor.execute(
            "SELECT symbol, name, created_at FROM stocks WHERE symbol = %s",
            (symbol,)
        )
        row = self.cursor.fetchone()
        if row:
            return {'symbol': row[0], 'name': row[1], 'created_at': row[2]}
        return None
    
    # ==================== Price Queries ====================
    
    def get_price_by_date(self, symbol: str, date: str) -> Optional[Dict]:
        """Get stock price for a specific date."""
        self.cursor.execute("""
            SELECT symbol, date, open, high, low, close, volume
            FROM stock_prices WHERE symbol = %s AND date = %s
        """, (symbol, date))
        row = self.cursor.fetchone()
        if row:
            return {
                'symbol': row[0], 'date': row[1], 'open': row[2],
                'high': row[3], 'low': row[4], 'close': row[5], 'volume': row[6]
            }
        return None
    
    def get_price_range(self, symbol: str, start_date: str, end_date: str) -> List[Dict]:
        """Get stock prices for a date range."""
        self.cursor.execute("""
            SELECT symbol, date, open, high, low, close, volume
            FROM stock_prices 
            WHERE symbol = %s AND date BETWEEN %s AND %s
            ORDER BY date
        """, (symbol, start_date, end_date))
        return self._rows_to_dicts(self.cursor.fetchall())
    
    def get_latest_price(self, symbol: str) -> Optional[Dict]:
        """Get the most recent price for a stock."""
        self.cursor.execute("""
            SELECT symbol, date, open, high, low, close, volume
            FROM stock_prices 
            WHERE symbol = %s
            ORDER BY date DESC LIMIT 1
        """, (symbol,))
        row = self.cursor.fetchone()
        if row:
            return {
                'symbol': row[0], 'date': row[1], 'open': row[2],
                'high': row[3], 'low': row[4], 'close': row[5], 'volume': row[6]
            }
        return None
    
    def get_n_days_ago(self, symbol: str, days: int) -> Optional[Dict]:
        """Get price from N days ago."""
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days * 2)  # Buffer for weekends
        
        self.cursor.execute("""
            SELECT symbol, date, open, high, low, close, volume
            FROM stock_prices 
            WHERE symbol = %s AND date <= %s
            ORDER BY date DESC LIMIT 1
        """, (symbol, start_date.date()))
        row = self.cursor.fetchone()
        if row:
            return {
                'symbol': row[0], 'date': row[1], 'open': row[2],
                'high': row[3], 'low': row[4], 'close': row[5], 'volume': row[6]
            }
        return None
    
    # ==================== Analysis Queries ====================
    
    def calculate_returns(self, symbol: str, days: int = 30) -> Optional[Dict]:
        """Calculate returns over N days."""
        current = self.get_latest_price(symbol)
        previous = self.get_n_days_ago(symbol, days)
        
        if current and previous:
            daily_return = ((current['close'] - previous['close']) / previous['close']) * 100
            return {
                'symbol': symbol,
                'current_price': current['close'],
                'previous_price': previous['close'],
                'days': days,
                'return_pct': round(daily_return, 2)
            }
        return None
    
    def get_top_gainers(self, days: int = 30, limit: int = 10) -> List[Dict]:
        """Get top N gainers over specified period."""
        self.cursor.execute("""
            SELECT 
                p.symbol,
                s.name,
                p.close as current_price,
                p2.close as previous_price,
                ROUND(((p.close - p2.close) / p2.close) * 100, 2) as return_pct
            FROM stock_prices p
            JOIN stocks s ON p.symbol = s.symbol
            CROSS JOIN LATERAL (
                SELECT close FROM stock_prices p2
                WHERE p2.symbol = p.symbol AND p2.date < p.date
                ORDER BY p2.date DESC LIMIT 1
            ) p2
            WHERE p.date = (SELECT MAX(date) FROM stock_prices)
            ORDER BY return_pct DESC
            LIMIT %s
        """, (limit,))
        return self._rows_to_dicts(self.cursor.fetchall())
    
    def get_top_losers(self, days: int = 30, limit: int = 10) -> List[Dict]:
        """Get top N losers over specified period."""
        self.cursor.execute("""
            SELECT 
                p.symbol,
                s.name,
                p.close as current_price,
                p2.close as previous_price,
                ROUND(((p.close - p2.close) / p2.close) * 100, 2) as return_pct
            FROM stock_prices p
            JOIN stocks s ON p.symbol = s.symbol
            CROSS JOIN LATERAL (
                SELECT close FROM stock_prices p2
                WHERE p2.symbol = p.symbol AND p2.date < p.date
                ORDER BY p2.date DESC LIMIT 1
            ) p2
            WHERE p.date = (SELECT MAX(date) FROM stock_prices)
            ORDER BY return_pct ASC
            LIMIT %s
        """, (limit,))
        return self._rows_to_dicts(self.cursor.fetchall())
    
    def get_volatility(self, symbol: str, days: int = 30) -> Optional[Dict]:
        """Calculate price volatility (standard deviation of daily returns)."""
        self.cursor.execute("""
            SELECT close FROM stock_prices
            WHERE symbol = %s
            ORDER BY date DESC LIMIT %s
        """, (symbol, days))
        prices = [r[0] for r in self.cursor.fetchall()]
        
        if len(prices) < 2:
            return None
        
        # Calculate daily returns
        returns = [(prices[i] - prices[i+1]) / prices[i+1] * 100 
                   for i in range(len(prices)-1)]
        
        mean_return = sum(returns) / len(returns)
        variance = sum((r - mean_return) ** 2 for r in returns) / len(returns)
        std_dev = variance ** 0.5
        
        return {
            'symbol': symbol,
            'days': days,
            'volatility': round(std_dev, 2),
            'mean_return': round(mean_return, 2)
        }
    
    def get_average_volume(self, symbol: str, days: int = 30) -> Optional[Dict]:
        """Get average trading volume."""
        self.cursor.execute("""
            SELECT AVG(volume) as avg_volume, MIN(volume), MAX(volume)
            FROM stock_prices
            WHERE symbol = %s AND date >= CURRENT_DATE - INTERVAL '%s days'
        """, (symbol, days))
        row = self.cursor.fetchone()
        if row:
            return {
                'symbol': symbol,
                'days': days,
                'avg_volume': int(row[0]) if row[0] else None,
                'min_volume': int(row[1]) if row[1] else None,
                'max_volume': int(row[2]) if row[2] else None
            }
        return None
    
    # ==================== Transaction Queries ====================
    
    def get_transactions(self, symbol: str = None, limit: int = 100) -> List[Dict]:
        """Get transaction history."""
        if symbol:
            self.cursor.execute("""
                SELECT symbol, date, price, quantity, type
                FROM transactions 
                WHERE symbol = %s
                ORDER BY date DESC LIMIT %s
            """, (symbol, limit))
        else:
            self.cursor.execute("""
                SELECT symbol, date, price, quantity, type
                FROM transactions 
                ORDER BY date DESC LIMIT %s
            """, (limit,))
        return self._rows_to_dicts(self.cursor.fetchall())
    
    # ==================== Helper Methods ====================
    
    def _rows_to_dicts(self, rows: List[Tuple]) -> List[Dict]:
        """Convert SQL rows to list of dicts."""
        if not rows:
            return []
        # Get column names from cursor
        columns = [desc[0] for desc in self.cursor.description]
        return [dict(zip(columns, row)) for row in rows]


# ==================== Standalone Functions ====================

def query_stock(symbol: str) -> Optional[Dict]:
    """Quick query for a single stock."""
    with StockQuery() as q:
        return q.get_stock_by_symbol(symbol)


def query_price(symbol: str, date: str = None) -> Optional[Dict]:
    """Quick query for stock price."""
    with StockQuery() as q:
        if date:
            return q.get_price_by_symbol(symbol, date)
        return q.get_latest_price(symbol)


def get_market_summary() -> Dict:
    """Get overall market summary."""
    with StockQuery() as q:
        # Total stocks
        q.cursor.execute("SELECT COUNT(*) FROM stocks")
        total_stocks = q.cursor.fetchone()[0]
        
        # Total transactions
        q.cursor.execute("SELECT COUNT(*) FROM transactions")
        total_transactions = q.cursor.fetchone()[0]
        
        # Latest price date
        q.cursor.execute("SELECT MAX(date) FROM stock_prices")
        latest_date = q.cursor.fetchone()[0]
        
        return {
            'total_stocks': total_stocks,
            'total_transactions': total_transactions,
            'latest_price_date': latest_date
        }


def main():
    """Demo usage of query utilities."""
    print("=== Stock Query Utilities Demo ===\n")
    
    with StockQuery() as q:
        # Get all stocks
        stocks = q.get_all_stocks()
        print(f"Total stocks: {len(stocks)}")
        
        # Get latest price for a sample stock
        if stocks:
            sample = stocks[0]['symbol']
            price = q.get_latest_price(sample)
            if price:
                print(f"Latest price for {sample}: ${price['close']}")
            
            # Calculate returns
            returns = q.calculate_returns(sample, 30)
            if returns:
                print(f"30-day return for {sample}: {returns['return_pct']}%")
        
        # Get market summary
        summary = get_market_summary()
        print(f"\nMarket Summary:")
        print(f"  Total Stocks: {summary['total_stocks']}")
        print(f"  Total Transactions: {summary['total_transactions']}")
        print(f"  Latest Price Date: {summary['latest_price_date']}")


if __name__ == '__main__':
    main()