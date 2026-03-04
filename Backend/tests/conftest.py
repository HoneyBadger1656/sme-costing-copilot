"""Pytest configuration and fixtures"""

import pytest
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

# Set DEBUG mode for tests to disable TrustedHostMiddleware
os.environ["DEBUG"] = "true"

from app.core.database import Base, get_db
from app.main import app
from app.models.models import User, Organization, Client, Product

# Test database URL
TEST_DATABASE_URL = "sqlite:///./test.db"

@pytest.fixture(scope="function")
def test_db():
    """Create a test database for each test"""
    engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    # Create tables
    Base.metadata.create_all(bind=engine)
    
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        # Drop all tables after test
        Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="function")
def client(test_db):
    """Create a test client with test database"""
    def override_get_db():
        try:
            yield test_db
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()

@pytest.fixture
def test_organization(test_db):
    """Create a test organization"""
    org = Organization(
        name="Test Organization",
        email="test@example.com",
        subscription_status="trial"
    )
    test_db.add(org)
    test_db.commit()
    test_db.refresh(org)
    return org

@pytest.fixture
def test_user(test_db, test_organization):
    """Create a test user"""
    from werkzeug.security import generate_password_hash
    
    user = User(
        email="testuser@example.com",
        hashed_password=generate_password_hash("TestPassword123"),
        full_name="Test User",
        organization_id=test_organization.id,
        role="admin",
        is_active=True
    )
    test_db.add(user)
    test_db.commit()
    test_db.refresh(user)
    return user

@pytest.fixture
def test_client_data(test_db, test_user):
    """Create a test client"""
    client = Client(
        user_id=test_user.id,
        organization_id=test_user.organization_id,
        business_name="Test Business",
        email="business@example.com",
        phone="1234567890",
        industry="Manufacturing",
        annual_revenue=1000000.0,
        current_debtors=50000.0,
        average_credit_days=30
    )
    test_db.add(client)
    test_db.commit()
    test_db.refresh(client)
    return client

@pytest.fixture
def test_product(test_db, test_client_data):
    """Create a test product"""
    product = Product(
        client_id=test_client_data.id,
        name="Test Product",
        category="Electronics",
        unit="pcs",
        raw_material_cost=100.0,
        labour_cost_per_unit=20.0,
        overhead_percentage=10.0,
        target_margin_percentage=20.0,
        tax_rate=18.0,
        is_active=True
    )
    test_db.add(product)
    test_db.commit()
    test_db.refresh(product)
    return product

@pytest.fixture
def auth_headers(client, test_user):
    """Get authentication headers for test user"""
    response = client.post(
        "/api/auth/login",
        data={"username": test_user.email, "password": "TestPassword123"}
    )
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
