#!/usr/bin/env python
"""Initialize the database with all tables"""
import sys
sys.path.insert(0, '.')

from app.core.database import engine, Base
from app.models.models import Organization, User, Client, Product, OrderEvaluation

if __name__ == "__main__":
    print("Creating database tables...")
    try:
        Base.metadata.create_all(bind=engine)
        print("✓ Database tables created successfully!")
    except Exception as e:
        print(f"✗ Error creating tables: {e}")
        sys.exit(1)
