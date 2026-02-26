#!/usr/bin/env python
"""Check database tables"""
import sqlite3

db_path = r'c:\Users\csp\OneDrive\Desktop\SAI\sme-costing-copilot\test.db'

try:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Get all tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    
    print(f"✓ Database connected: {db_path}")
    print(f"✓ Found {len(tables)} tables:")
    
    if len(tables) == 0:
        print("  ✗ NO TABLES FOUND - Database is empty!")
    else:
        for table in tables:
            cursor.execute(f"SELECT COUNT(*) FROM {table[0]};")
            count = cursor.fetchone()[0]
            print(f"  - {table[0]} ({count} rows)")
    
    conn.close()
except Exception as e:
    print(f"✗ Error: {e}")
