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

# Role-based fixtures for security testing
@pytest.fixture
def owner_role(test_db):
    """Create Owner role"""
    from app.models.models import Role
    role = Role(
        name="Owner",
        description="Full system access including billing",
        permissions={"all": True, "billing": True}
    )
    test_db.add(role)
    test_db.commit()
    test_db.refresh(role)
    return role

@pytest.fixture
def admin_role(test_db):
    """Create Admin role"""
    from app.models.models import Role
    role = Role(
        name="Admin",
        description="All access except billing",
        permissions={"all": True, "billing": False}
    )
    test_db.add(role)
    test_db.commit()
    test_db.refresh(role)
    return role

@pytest.fixture
def accountant_role(test_db):
    """Create Accountant role"""
    from app.models.models import Role
    role = Role(
        name="Accountant",
        description="Access to financial data and reports",
        permissions={"financial": True, "reports": True}
    )
    test_db.add(role)
    test_db.commit()
    test_db.refresh(role)
    return role

@pytest.fixture
def viewer_role(test_db):
    """Create Viewer role"""
    from app.models.models import Role
    role = Role(
        name="Viewer",
        description="Read-only access",
        permissions={"read_only": True}
    )
    test_db.add(role)
    test_db.commit()
    test_db.refresh(role)
    return role

@pytest.fixture
def owner_user(test_db, test_organization, owner_role):
    """Create a user with Owner role"""
    from werkzeug.security import generate_password_hash
    from app.models.models import UserRole
    
    user = User(
        email="owner@example.com",
        hashed_password=generate_password_hash("OwnerPass123"),
        full_name="Owner User",
        organization_id=test_organization.id,
        role="admin",
        is_active=True
    )
    test_db.add(user)
    test_db.commit()
    test_db.refresh(user)
    
    # Assign Owner role
    user_role = UserRole(
        user_id=user.id,
        role_id=owner_role.id,
        tenant_id=test_organization.id
    )
    test_db.add(user_role)
    test_db.commit()
    
    return user

@pytest.fixture
def admin_user(test_db, test_organization, admin_role):
    """Create a user with Admin role"""
    from werkzeug.security import generate_password_hash
    from app.models.models import UserRole
    
    user = User(
        email="admin@example.com",
        hashed_password=generate_password_hash("AdminPass123"),
        full_name="Admin User",
        organization_id=test_organization.id,
        role="admin",
        is_active=True
    )
    test_db.add(user)
    test_db.commit()
    test_db.refresh(user)
    
    # Assign Admin role
    user_role = UserRole(
        user_id=user.id,
        role_id=admin_role.id,
        tenant_id=test_organization.id
    )
    test_db.add(user_role)
    test_db.commit()
    
    return user

@pytest.fixture
def accountant_user(test_db, test_organization, accountant_role):
    """Create a user with Accountant role"""
    from werkzeug.security import generate_password_hash
    from app.models.models import UserRole
    
    user = User(
        email="accountant@example.com",
        hashed_password=generate_password_hash("AccountantPass123"),
        full_name="Accountant User",
        organization_id=test_organization.id,
        role="accountant",
        is_active=True
    )
    test_db.add(user)
    test_db.commit()
    test_db.refresh(user)
    
    # Assign Accountant role
    user_role = UserRole(
        user_id=user.id,
        role_id=accountant_role.id,
        tenant_id=test_organization.id
    )
    test_db.add(user_role)
    test_db.commit()
    
    return user

@pytest.fixture
def viewer_user(test_db, test_organization, viewer_role):
    """Create a user with Viewer role"""
    from werkzeug.security import generate_password_hash
    from app.models.models import UserRole
    
    user = User(
        email="viewer@example.com",
        hashed_password=generate_password_hash("ViewerPass123"),
        full_name="Viewer User",
        organization_id=test_organization.id,
        role="viewer",
        is_active=True
    )
    test_db.add(user)
    test_db.commit()
    test_db.refresh(user)
    
    # Assign Viewer role
    user_role = UserRole(
        user_id=user.id,
        role_id=viewer_role.id,
        tenant_id=test_organization.id
    )
    test_db.add(user_role)
    test_db.commit()
    
    return user

@pytest.fixture
def owner_auth_headers(client, owner_user):
    """Get authentication headers for owner user"""
    response = client.post(
        "/api/auth/login",
        data={"username": owner_user.email, "password": "OwnerPass123"}
    )
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

@pytest.fixture
def admin_auth_headers(client, admin_user):
    """Get authentication headers for admin user"""
    response = client.post(
        "/api/auth/login",
        data={"username": admin_user.email, "password": "AdminPass123"}
    )
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

@pytest.fixture
def accountant_auth_headers(client, accountant_user):
    """Get authentication headers for accountant user"""
    response = client.post(
        "/api/auth/login",
        data={"username": accountant_user.email, "password": "AccountantPass123"}
    )
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

@pytest.fixture
def viewer_auth_headers(client, viewer_user):
    """Get authentication headers for viewer user"""
    response = client.post(
        "/api/auth/login",
        data={"username": viewer_user.email, "password": "ViewerPass123"}
    )
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

@pytest.fixture
def sample_products(test_db, test_client_data):
    """Create sample products for testing"""
    products = []
    for i in range(3):
        product = Product(
            client_id=test_client_data.id,
            name=f"Test Product {i+1}",
            category="Electronics",
            unit="pcs",
            raw_material_cost=100.0 + i * 10,
            labour_cost_per_unit=20.0 + i * 5,
            overhead_percentage=10.0,
            target_margin_percentage=20.0,
            tax_rate=18.0,
            is_active=True
        )
        test_db.add(product)
        products.append(product)
    test_db.commit()
    for product in products:
        test_db.refresh(product)
    return products

@pytest.fixture
def db_session(test_db):
    """Alias for test_db to match common naming convention"""
    return test_db
