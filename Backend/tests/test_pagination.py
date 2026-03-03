"""Tests for pagination utilities"""

import pytest
from app.utils.pagination import paginate, create_paginated_response, PaginationParams
from app.models.models import Client


class TestPagination:
    """Test pagination functionality"""
    
    def test_pagination_params_validation(self):
        """Test PaginationParams validation"""
        params = PaginationParams(skip=-10, limit=0)
        params.validate_params()
        
        assert params.skip == 0  # Negative skip corrected to 0
        assert params.limit == 1  # Zero limit corrected to 1
    
    def test_pagination_params_max_limit(self):
        """Test that max limit is enforced"""
        params = PaginationParams(skip=0, limit=2000)
        params.validate_params()
        
        assert params.limit == 1000  # Capped at max limit
    
    def test_paginate_basic(self, test_db, test_user, test_organization):
        """Test basic pagination"""
        from app.models.models import Client
        
        # Create multiple clients
        for i in range(15):
            client = Client(
                user_id=test_user.id,
                organization_id=test_organization.id,
                business_name=f"Business {i}",
                email=f"business{i}@example.com"
            )
            test_db.add(client)
        test_db.commit()
        
        # Test pagination
        query = test_db.query(Client).filter(
            Client.organization_id == test_organization.id
        )
        
        items, total = paginate(query, skip=0, limit=10)
        
        assert total == 15
        assert len(items) == 10
    
    def test_paginate_second_page(self, test_db, test_user, test_organization):
        """Test getting second page"""
        from app.models.models import Client
        
        # Create multiple clients
        for i in range(15):
            client = Client(
                user_id=test_user.id,
                organization_id=test_organization.id,
                business_name=f"Business {i}",
                email=f"business{i}@example.com"
            )
            test_db.add(client)
        test_db.commit()
        
        query = test_db.query(Client).filter(
            Client.organization_id == test_organization.id
        )
        
        items, total = paginate(query, skip=10, limit=10)
        
        assert total == 15
        assert len(items) == 5  # Only 5 items on second page
    
    def test_create_paginated_response(self):
        """Test creating paginated response"""
        items = [1, 2, 3, 4, 5]
        total = 25
        skip = 10
        limit = 5
        
        response = create_paginated_response(items, total, skip, limit)
        
        assert response["total"] == 25
        assert response["items"] == items
        assert response["skip"] == 10
        assert response["limit"] == 5
        assert response["page"] == 3  # (10 / 5) + 1
        assert response["total_pages"] == 5  # ceil(25 / 5)
        assert response["has_next"] is True  # 10 + 5 < 25
        assert response["has_prev"] is True  # 10 > 0
    
    def test_paginated_response_first_page(self):
        """Test paginated response for first page"""
        items = [1, 2, 3]
        response = create_paginated_response(items, 10, skip=0, limit=3)
        
        assert response["page"] == 1
        assert response["has_prev"] is False
        assert response["has_next"] is True
    
    def test_paginated_response_last_page(self):
        """Test paginated response for last page"""
        items = [1, 2]
        response = create_paginated_response(items, 10, skip=9, limit=3)
        
        assert response["has_next"] is False
        assert response["has_prev"] is True
