"""Tests for tenant isolation utilities"""

import pytest
from app.utils.tenant import TenantFilter
from app.models.models import Client


class TestTenantFilter:
    """Test tenant isolation functionality"""
    
    def test_tenant_filter_initialization(self, test_db, test_user):
        """Test TenantFilter initialization"""
        tenant = TenantFilter(test_db, test_user)
        assert tenant.organization_id == test_user.organization_id
        assert tenant.user_id == test_user.id
    
    def test_tenant_filter_query(self, test_db, test_user, test_client_data):
        """Test tenant-filtered query"""
        tenant = TenantFilter(test_db, test_user)
        clients = tenant.query(Client).all()
        
        # Should only return clients from user's organization
        assert len(clients) == 1
        assert clients[0].organization_id == test_user.organization_id
    
    def test_tenant_filter_get_by_id(self, test_db, test_user, test_client_data):
        """Test getting record by ID with tenant isolation"""
        tenant = TenantFilter(test_db, test_user)
        client = tenant.get_by_id(Client, test_client_data.id)
        
        assert client is not None
        assert client.id == test_client_data.id
        assert client.organization_id == test_user.organization_id
    
    def test_tenant_filter_blocks_other_org(self, test_db, test_user):
        """Test that tenant filter blocks access to other organizations"""
        # Create a client in a different organization
        from app.models.models import Organization, Client
        
        other_org = Organization(
            name="Other Organization",
            email="other@example.com",
            subscription_status="trial"
        )
        test_db.add(other_org)
        test_db.flush()
        
        other_client = Client(
            user_id=test_user.id,
            organization_id=other_org.id,
            business_name="Other Business",
            email="other@business.com"
        )
        test_db.add(other_client)
        test_db.commit()
        
        # Try to access with tenant filter
        tenant = TenantFilter(test_db, test_user)
        result = tenant.get_by_id(Client, other_client.id)
        
        # Should not be able to access client from other organization
        assert result is None
    
    def test_tenant_filter_verify_access(self, test_db, test_user, test_client_data):
        """Test verify_access method"""
        tenant = TenantFilter(test_db, test_user)
        
        # Should have access to own organization's data
        assert tenant.verify_access(test_client_data) is True
        
        # Create client from different organization
        from app.models.models import Organization, Client
        
        other_org = Organization(
            name="Other Org",
            email="other@org.com",
            subscription_status="trial"
        )
        test_db.add(other_org)
        test_db.flush()
        
        other_client = Client(
            user_id=test_user.id,
            organization_id=other_org.id,
            business_name="Other",
            email="other@test.com"
        )
        test_db.add(other_client)
        test_db.commit()
        
        # Should not have access
        assert tenant.verify_access(other_client) is False
    
    def test_tenant_filter_no_organization(self, test_db):
        """Test that TenantFilter raises error for user without organization"""
        from app.models.models import User
        from werkzeug.security import generate_password_hash
        
        user_no_org = User(
            email="noorg@example.com",
            hashed_password=generate_password_hash("password"),
            full_name="No Org User",
            organization_id=None,
            role="admin"
        )
        test_db.add(user_no_org)
        test_db.commit()
        
        with pytest.raises(ValueError, match="User must be associated with an organization"):
            TenantFilter(test_db, user_no_org)
