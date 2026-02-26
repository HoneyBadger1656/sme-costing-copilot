#!/usr/bin/env python
import sys
sys.path.insert(0, '.')

from app.core.database import engine
from sqlalchemy import text

# Check if organizations table exists
with engine.connect() as conn:
    result = conn.execute(text('SELECT name FROM sqlite_master WHERE type="table"'))
    tables = [row[0] for row in result]
    print("Available tables:", tables)

    # Check if organizations table exists
    if "organizations" in tables:
        print("✓ organizations table exists")
    else:
        print("✗ organizations table missing")
