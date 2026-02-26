# backend/migrations/create_tables.py

from app.core.database import engine, Base
from app.models.models import (
    User, Client, Product, BOMItem, Order, OrderItem,
    OrderEvaluation, Scenario, Ledger, IntegrationSync, ChatMessage
)

def create_all_tables():
    """Create all tables in the database"""
    Base.metadata.create_all(bind=engine)
    print("✓ All tables created successfully")

if __name__ == "__main__":
    create_all_tables()
