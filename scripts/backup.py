#!/usr/bin/env python3
"""
Database Backup Script
Performs PostgreSQL database backups with rotation support.
"""

import os
import sys
import argparse
import subprocess
from datetime import datetime
from pathlib import Path
import shutil

# Database connection configuration
DB_CONFIG = {
    'host': 'blog.softsnail.com',
    'port': 2432,
    'user': 'reef',
    'password': 'accton123',
    'dbname': 'twsestock'
}

# Default backup directory
DEFAULT_BACKUP_DIR = Path(__file__).parent.parent / 'backups'


class DatabaseBackup:
    def __init__(self, backup_dir: Path = None):
        self.backup_dir = backup_dir or DEFAULT_BACKUP_DIR
        self.backup_dir.mkdir(parents=True, exist_ok=True)
    
    def create_backup(self, backup_name: str = None) -> Path:
        """Create a database backup."""
        if backup_name is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_name = f"twsestock_{timestamp}.sql"
        
        backup_path = self.backup_dir / backup_name
        
        # Build pg_dump command
        env = os.environ.copy()
        env['PGPASSWORD'] = DB_CONFIG['password']
        
        cmd = [
            'pg_dump',
            '-h', DB_CONFIG['host'],
            '-p', str(DB_CONFIG['port']),
            '-U', DB_CONFIG['user'],
            '-d', DB_CONFIG['dbname'],
            '-F', 'c',  # Custom format (compressed)
            '-b',  # Include large objects
            '-v',  # Verbose
            '-f', str(backup_path)
        ]
        
        print(f"Creating backup: {backup_name}")
        print(f"Database: {DB_CONFIG['dbname']}@{DB_CONFIG['host']}:{DB_CONFIG['port']}")
        
        try:
            result = subprocess.run(
                cmd,
                env=env,
                capture_output=True,
                text=True,
                timeout=300
            )
            
            if result.returncode == 0:
                size = backup_path.stat().st_size
                print(f"Backup created successfully: {size:,} bytes")
                return backup_path
            else:
                print(f"Backup failed: {result.stderr}")
                sys.exit(1)
        except FileNotFoundError:
            print("Error: pg_dump not found. Please install PostgreSQL client.")
            sys.exit(1)
        except subprocess.TimeoutExpired:
            print("Error: Backup timed out")
            sys.exit(1)
    
    def list_backups(self):
        """List all available backups."""
        backups = sorted(self.backup_dir.glob('*.sql'), reverse=True)
        
        if not backups:
            print("No backups found.")
            return
        
        print(f"Found {len(backups)} backup(s) in {self.backup_dir}:")
        for b in backups:
            size = b.stat().st_size
            mtime = datetime.fromtimestamp(b.stat().st_mtime)
            print(f"  {b.name} ({size:,} bytes, {mtime.strftime('%Y-%m-%d %H:%M:%S')})")
    
    def restore_backup(self, backup_name: str):
        """Restore a database backup."""
        backup_path = self.backup_dir / backup_name
        
        if not backup_path.exists():
            print(f"Error: Backup not found: {backup_name}")
            sys.exit(1)
        
        env = os.environ.copy()
        env['PGPASSWORD'] = DB_CONFIG['password']
        
        cmd = [
            'pg_restore',
            '-h', DB_CONFIG['host'],
            '-p', str(DB_CONFIG['port']),
            '-U', DB_CONFIG['user'],
            '-d', DB_CONFIG['dbname'],
            '-v',  # Verbose
            '--clean',  # Drop objects before recreating
            str(backup_path)
        ]
        
        print(f"Restoring backup: {backup_name}")
        
        try:
            result = subprocess.run(
                cmd,
                env=env,
                capture_output=True,
                text=True,
                timeout=300
            )
            
            if result.returncode == 0:
                print("Restore completed successfully")
            else:
                print(f"Restore failed: {result.stderr}")
                sys.exit(1)
        except FileNotFoundError:
            print("Error: pg_restore not found. Please install PostgreSQL client.")
            sys.exit(1)
    
    def rotate_backups(self, keep: int = 7):
        """Rotate backups, keeping only the most recent N backups."""
        backups = sorted(self.backup_dir.glob('*.sql'), key=lambda x: x.stat().st_mtime, reverse=True)
        
        if len(backups) <= keep:
            print(f"No rotation needed ({len(backups)} backups, keeping {keep})")
            return
        
        to_delete = backups[keep:]
        print(f"Rotating backups: removing {len(to_delete)} old backup(s)")
        
        for b in to_delete:
            print(f"  Deleting: {b.name}")
            b.unlink()
        
        print(f"Rotation complete. Kept {keep} most recent backups.")
    
    def cleanup_old_backups(self, days: int = 30):
        """Remove backups older than specified days."""
        import time
        
        cutoff = time.time() - (days * 86400)
        backups = list(self.backup_dir.glob('*.sql'))
        
        removed = 0
        for b in backups:
            if b.stat().st_mtime < cutoff:
                print(f"Removing old backup: {b.name}")
                b.unlink()
                removed += 1
        
        print(f"Cleanup complete. Removed {removed} old backup(s).")


def main():
    parser = argparse.ArgumentParser(description='Database Backup Manager')
    parser.add_argument('command', choices=['backup', 'list', 'restore', 'rotate', 'cleanup'],
                       help='Command to execute')
    parser.add_argument('args', nargs='*', help='Additional arguments')
    parser.add_argument('-d', '--backup-dir', type=Path, help='Backup directory')
    parser.add_argument('-k', '--keep', type=int, default=7, help='Number of backups to keep (for rotate)')
    parser.add_argument('--days', type=int, default=30, help='Days for cleanup command')
    
    args = parser.parse_args()
    
    backup = DatabaseBackup(args.backup_dir)
    
    if args.command == 'backup':
        backup_name = args.args[0] if args.args else None
        backup.create_backup(backup_name)
    elif args.command == 'list':
        backup.list_backups()
    elif args.command == 'restore':
        if not args.args:
            print("Error: Backup name required")
            sys.exit(1)
        backup.restore_backup(args.args[0])
    elif args.command == 'rotate':
        backup.rotate_backups(args.keep)
    elif args.command == 'cleanup':
        backup.cleanup_old_backups(args.days)


if __name__ == '__main__':
    main()