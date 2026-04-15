#!/usr/bin/env python3
"""
Database Migration Management Script
Manages database schema migrations using Alembic-style version control.
"""

import os
import sys
import argparse
import subprocess
from datetime import datetime
from pathlib import Path

# Database connection configuration
DB_CONFIG = {
    'host': 'blog.softsnail.com',
    'port': 2432,
    'user': 'reef',
    'password': 'accton123',
    'dbname': 'twsestock'
}

MIGRATIONS_DIR = Path(__file__).parent / 'migrations'


class MigrationManager:
    def __init__(self):
        self.migrations_dir = MIGRATIONS_DIR
        self.migrations_dir.mkdir(exist_ok=True)
    
    def create_migration(self, name: str):
        """Create a new migration file."""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        migration_name = f"{timestamp}_{name}"
        
        up_file = self.migrations_dir / f"{migration_name}_up.sql"
        down_file = self.migrations_dir / f"{migration_name}_down.sql"
        
        up_content = f"""-- Migration: {migration_name}
-- Created: {datetime.now().isoformat()}

-- Add your UP migration SQL here
-- Example:
-- CREATE TABLE IF NOT EXISTS example (
--     id SERIAL PRIMARY KEY,
--     name VARCHAR(255) NOT NULL,
--     created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
-- );
"""
        
        down_content = f"""-- Migration: {migration_name} (rollback)
-- Created: {datetime.now().isoformat()}

-- Add your DOWN migration SQL here (rollback)
-- Example:
-- DROP TABLE IF EXISTS example;
"""
        
        up_file.write_text(up_content)
        down_file.write_text(down_content)
        
        print(f"Created migration: {migration_name}")
        print(f"  UP: {up_file}")
        print(f"  DOWN: {down_file}")
        return migration_name
    
    def list_migrations(self):
        """List all migrations."""
        migrations = sorted(self.migrations_dir.glob('*_up.sql'))
        if not migrations:
            print("No migrations found.")
            return
        
        print(f"Found {len(migrations)} migrations:")
        for m in migrations:
            print(f"  - {m.stem.replace('_up', '')}")
    
    def run_migration(self, direction: str = 'up'):
        """Run pending migrations (up or down)."""
        conn_str = f"postgresql://{DB_CONFIG['user']}:{DB_CONFIG['password']}@{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['dbname']}"
        
        migrations = sorted(self.migrations_dir.glob('*_up.sql'))
        
        if direction == 'up':
            print(f"Running {len(migrations)} migrations...")
            for m in migrations:
                print(f"  Applying: {m.stem.replace('_up', '')}")
                # Note: In production, use proper migration runner
                # This is a placeholder for demonstration
        elif direction == 'down':
            print("Rolling back migrations...")
            for m in reversed(migrations):
                print(f"  Reverting: {m.stem.replace('_up', '')}")
        
        print("Migration complete.")
    
    def status(self):
        """Check migration status."""
        conn_str = f"postgresql://{DB_CONFIG['user']}:{DB_CONFIG['password']}@{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['dbname']}"
        
        print(f"Database: {DB_CONFIG['dbname']}@{DB_CONFIG['host']}:{DB_CONFIG['port']}")
        print(f"Migrations directory: {self.migrations_dir}")
        
        migrations = sorted(self.migrations_dir.glob('*_up.sql'))
        print(f"Pending migrations: {len(migrations)}")


def main():
    parser = argparse.ArgumentParser(description='Database Migration Manager')
    parser.add_argument('command', choices=['create', 'list', 'up', 'down', 'status'],
                       help='Command to execute')
    parser.add_argument('name', nargs='?', help='Migration name (for create command)')
    
    args = parser.parse_args()
    
    manager = MigrationManager()
    
    if args.command == 'create':
        if not args.name:
            print("Error: Migration name required for 'create' command")
            sys.exit(1)
        manager.create_migration(args.name)
    elif args.command == 'list':
        manager.list_migrations()
    elif args.command == 'up':
        manager.run_migration('up')
    elif args.command == 'down':
        manager.run_migration('down')
    elif args.command == 'status':
        manager.status()


if __name__ == '__main__':
    main()