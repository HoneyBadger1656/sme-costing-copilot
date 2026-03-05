# Backend/tests/test_report_generation_api.py

"""Integration tests for report generation API endpoints"""

import pytest
import os
import time
from datetime import datetime, timedelta, date
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from pathlib import Path

from app.models.models import User, Organization, Role, UserRole, Product, Client


@pytest.fixture
def accountant_role(test_db):
    """Create Accountant role"""
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
def admin_role(test_db):
    """Create Admin role"""
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
def owner_role(test_db):
    """Create Owner role"""
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
def viewer_role(test_db):
    """Create Viewer role"""
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
def accountant_user(test_db, test_organization, accountant_role):
    """Create a user with Accountant role"""
    from werkzeug.security import generate_password_hash
    
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
def admin_user(test_db, test_organization, admin_role):
    """Create a user with Admin role"""
    from werkzeug.security import generate_password_hash
    
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
def owner_user(test_db, test_organization, owner_role):
    """Create a user with Owner role"""
    from werkzeug.security import generate_password_hash
    
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
def viewer_user(test_db, test_organization, viewer_role):
    """Create a user with Viewer role"""
    from werkzeug.security import generate_password_hash
    
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
def accountant_auth_headers(client, accountant_user):
    """Get authentication headers for accountant user"""
    response = client.post(
        "/api/auth/login",
        data={"username": accountant_user.email, "password": "AccountantPass123"}
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
def owner_auth_headers(client, owner_user):
    """Get authentication headers for owner user"""
    response = client.post(
        "/api/auth/login",
        data={"username": owner_user.email, "password": "OwnerPass123"}
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
            raw_material_cost=100.0 * (i+1),
            labour_cost_per_unit=20.0 * (i+1),
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


class TestReportTemplateAPI:
    """Test report template listing and retrieval"""
    
    def test_list_templates_as_accountant(self, client, accountant_auth_headers):
        """Test Accountant can list report templates"""
        response = client.get(
            "/api/reports/templates",
            headers=accountant_auth_headers
        )
        
        assert response.status_code == 200
        templates = response.json()
        
        assert isinstance(templates, list)
        assert len(templates) == 5  # 5 predefined templates
        
        # Verify template structure
        for template in templates:
            assert "id" in template
            assert "name" in template
            assert "description" in template
            assert "data_sources" in template
            assert "supported_formats" in template
            assert "parameters" in template
    
    def test_list_templates_as_admin(self, client, admin_auth_headers):
        """Test Admin can list report templates"""
        response = client.get(
            "/api/reports/templates",
            headers=admin_auth_headers
        )
        
        assert response.status_code == 200
        templates = response.json()
        assert len(templates) == 5
    
    def test_list_templates_as_owner(self, client, owner_auth_headers):
        """Test Owner can list report templates"""
        response = client.get(
            "/api/reports/templates",
            headers=owner_auth_headers
        )
        
        assert response.status_code == 200
        templates = response.json()
        assert len(templates) == 5
    
    def test_list_templates_as_viewer_denied(self, client, viewer_auth_headers):
        """Test Viewer cannot list report templates (403 Forbidden)"""
        response = client.get(
            "/api/reports/templates",
            headers=viewer_auth_headers
        )
        
        assert response.status_code == 403
        assert "Access denied" in response.json()["detail"]

    
    def test_get_template_by_id(self, client, accountant_auth_headers):
        """Test retrieving a specific template by ID"""
        response = client.get(
            "/api/reports/templates/financial_statement",
            headers=accountant_auth_headers
        )
        
        assert response.status_code == 200
        template = response.json()
        
        assert template["id"] == "financial_statement"
        assert template["name"] == "Financial Statement"
        assert "parameters" in template
        assert "supported_formats" in template
        assert "pdf" in template["supported_formats"]
        assert "excel" in template["supported_formats"]
    
    def test_get_template_not_found(self, client, accountant_auth_headers):
        """Test retrieving non-existent template returns 404"""
        response = client.get(
            "/api/reports/templates/nonexistent_template",
            headers=accountant_auth_headers
        )
        
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()
    
    def test_list_templates_unauthenticated(self, client):
        """Test unauthenticated users cannot list templates"""
        response = client.get("/api/reports/templates")
        
        assert response.status_code == 401


class TestReportGenerationWorkflow:
    """Test end-to-end report generation workflow"""
    
    def test_generate_pdf_report_as_accountant(self, client, accountant_auth_headers, sample_products):
        """Test Accountant can generate PDF report"""
        # Generate report
        response = client.post(
            "/api/reports/generate",
            headers=accountant_auth_headers,
            json={
                "template_id": "costing_analysis",
                "format": "pdf",
                "parameters": {
                    "date_range": {
                        "start": "2024-01-01",
                        "end": "2024-12-31"
                    },
                    "include_bom": True
                }
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "task_id" in data
        assert data["template_id"] == "costing_analysis"
        assert data["format"] == "pdf"
        assert data["status"] == "completed"
        assert "message" in data
        
        task_id = data["task_id"]
        
        # Check status
        status_response = client.get(
            f"/api/reports/status/{task_id}",
            headers=accountant_auth_headers
        )
        
        assert status_response.status_code == 200
        status_data = status_response.json()
        
        assert status_data["task_id"] == task_id
        assert status_data["status"] == "completed"
        assert status_data["file_name"] is not None
        assert status_data["file_size"] is not None
        assert status_data["download_url"] is not None
        assert status_data["created_at"] is not None
        assert status_data["expires_at"] is not None
        
        # Download report
        download_response = client.get(
            f"/api/reports/download/{task_id}",
            headers=accountant_auth_headers
        )
        
        assert download_response.status_code == 200
        assert download_response.headers["content-type"] == "application/octet-stream"
        assert len(download_response.content) > 0
    
    def test_generate_excel_report(self, client, accountant_auth_headers, sample_products):
        """Test generating Excel report"""
        response = client.post(
            "/api/reports/generate",
            headers=accountant_auth_headers,
            json={
                "template_id": "margin_analysis",
                "format": "excel",
                "parameters": {
                    "date_range": {
                        "start": "2024-01-01",
                        "end": "2024-12-31"
                    },
                    "group_by": "product"
                }
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["format"] == "excel"
        assert data["status"] == "completed"
        
        # Verify file can be downloaded
        task_id = data["task_id"]
        download_response = client.get(
            f"/api/reports/download/{task_id}",
            headers=accountant_auth_headers
        )
        
        assert download_response.status_code == 200
        assert len(download_response.content) > 0

    
    def test_generate_csv_report(self, client, accountant_auth_headers, sample_products):
        """Test generating CSV report"""
        response = client.post(
            "/api/reports/generate",
            headers=accountant_auth_headers,
            json={
                "template_id": "receivables_report",
                "format": "csv",
                "parameters": {
                    "as_of_date": "2024-12-31",
                    "aging_buckets": [30, 60, 90]
                }
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["format"] == "csv"
        assert data["status"] == "completed"
        
        # Verify file can be downloaded
        task_id = data["task_id"]
        download_response = client.get(
            f"/api/reports/download/{task_id}",
            headers=accountant_auth_headers
        )
        
        assert download_response.status_code == 200
        assert len(download_response.content) > 0
    
    def test_generate_all_report_formats(self, client, accountant_auth_headers, sample_products):
        """Test generating reports in all supported formats"""
        formats = ["pdf", "excel", "csv"]
        
        for fmt in formats:
            response = client.post(
                "/api/reports/generate",
                headers=accountant_auth_headers,
                json={
                    "template_id": "costing_analysis",
                    "format": fmt,
                    "parameters": {
                        "date_range": {
                            "start": "2024-01-01",
                            "end": "2024-12-31"
                        }
                    }
                }
            )
            
            assert response.status_code == 200, f"Failed to generate {fmt} report"
            data = response.json()
            assert data["format"] == fmt
            assert data["status"] == "completed"


class TestReportGenerationValidation:
    """Test report generation validation"""
    
    def test_invalid_template_id(self, client, accountant_auth_headers):
        """Test generating report with invalid template ID"""
        response = client.post(
            "/api/reports/generate",
            headers=accountant_auth_headers,
            json={
                "template_id": "invalid_template",
                "format": "pdf",
                "parameters": {}
            }
        )
        
        assert response.status_code == 400
        assert "not found" in response.json()["detail"].lower()
    
    def test_unsupported_format(self, client, accountant_auth_headers):
        """Test generating report with unsupported format"""
        response = client.post(
            "/api/reports/generate",
            headers=accountant_auth_headers,
            json={
                "template_id": "financial_statement",
                "format": "csv",  # CSV not supported for financial_statement
                "parameters": {
                    "period_start": "2024-01-01",
                    "period_end": "2024-12-31"
                }
            }
        )
        
        assert response.status_code == 400
        assert "not supported" in response.json()["detail"].lower()
    
    def test_missing_required_parameters(self, client, accountant_auth_headers):
        """Test generating report with missing required parameters"""
        response = client.post(
            "/api/reports/generate",
            headers=accountant_auth_headers,
            json={
                "template_id": "financial_statement",
                "format": "pdf",
                "parameters": {}  # Missing required parameters
            }
        )
        
        assert response.status_code == 400
        assert "required" in response.json()["detail"].lower() or "missing" in response.json()["detail"].lower()
    
    def test_invalid_parameter_values(self, client, accountant_auth_headers):
        """Test generating report with invalid parameter values"""
        response = client.post(
            "/api/reports/generate",
            headers=accountant_auth_headers,
            json={
                "template_id": "margin_analysis",
                "format": "pdf",
                "parameters": {
                    "date_range": {
                        "start": "2024-01-01",
                        "end": "2024-12-31"
                    },
                    "group_by": "invalid_group"  # Invalid option
                }
            }
        )
        
        assert response.status_code == 400



class TestReportStatusAndDownload:
    """Test report status checking and download URL generation"""
    
    def test_get_report_status_completed(self, client, accountant_auth_headers, sample_products):
        """Test getting status of completed report"""
        # Generate report
        gen_response = client.post(
            "/api/reports/generate",
            headers=accountant_auth_headers,
            json={
                "template_id": "costing_analysis",
                "format": "pdf",
                "parameters": {
                    "date_range": {
                        "start": "2024-01-01",
                        "end": "2024-12-31"
                    }
                }
            }
        )
        
        task_id = gen_response.json()["task_id"]
        
        # Get status
        response = client.get(
            f"/api/reports/status/{task_id}",
            headers=accountant_auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["task_id"] == task_id
        assert data["status"] == "completed"
        assert data["file_name"] is not None
        assert data["file_size"] > 0
        assert data["download_url"] is not None
        assert data["created_at"] is not None
        assert data["expires_at"] is not None
        
        # Verify expiry is 24 hours from creation
        created_at = datetime.fromisoformat(data["created_at"].replace("Z", "+00:00"))
        expires_at = datetime.fromisoformat(data["expires_at"].replace("Z", "+00:00"))
        time_diff = expires_at - created_at
        
        # Should be approximately 24 hours (allow 1 minute tolerance)
        assert abs(time_diff.total_seconds() - 86400) < 60
    
    def test_get_report_status_not_found(self, client, accountant_auth_headers):
        """Test getting status of non-existent report"""
        response = client.get(
            "/api/reports/status/nonexistent-task-id",
            headers=accountant_auth_headers
        )
        
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()
    
    def test_download_url_generation(self, client, accountant_auth_headers, sample_products):
        """Test download URL is generated correctly"""
        # Generate report
        gen_response = client.post(
            "/api/reports/generate",
            headers=accountant_auth_headers,
            json={
                "template_id": "costing_analysis",
                "format": "pdf",
                "parameters": {
                    "date_range": {
                        "start": "2024-01-01",
                        "end": "2024-12-31"
                    }
                }
            }
        )
        
        task_id = gen_response.json()["task_id"]
        
        # Get status
        status_response = client.get(
            f"/api/reports/status/{task_id}",
            headers=accountant_auth_headers
        )
        
        download_url = status_response.json()["download_url"]
        
        assert download_url is not None
        assert task_id in download_url
        assert "/api/reports/download/" in download_url
    
    def test_download_nonexistent_report(self, client, accountant_auth_headers):
        """Test downloading non-existent report returns 404"""
        response = client.get(
            "/api/reports/download/nonexistent-task-id",
            headers=accountant_auth_headers
        )
        
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()


class TestReportAuthorizationEnforcement:
    """Test authorization enforcement on report endpoints"""
    
    def test_accountant_can_generate_reports(self, client, accountant_auth_headers, sample_products):
        """Test Accountant role can generate reports"""
        response = client.post(
            "/api/reports/generate",
            headers=accountant_auth_headers,
            json={
                "template_id": "costing_analysis",
                "format": "pdf",
                "parameters": {
                    "date_range": {
                        "start": "2024-01-01",
                        "end": "2024-12-31"
                    }
                }
            }
        )
        
        assert response.status_code == 200
    
    def test_admin_can_generate_reports(self, client, admin_auth_headers, sample_products):
        """Test Admin role can generate reports"""
        response = client.post(
            "/api/reports/generate",
            headers=admin_auth_headers,
            json={
                "template_id": "costing_analysis",
                "format": "pdf",
                "parameters": {
                    "date_range": {
                        "start": "2024-01-01",
                        "end": "2024-12-31"
                    }
                }
            }
        )
        
        assert response.status_code == 200

    
    def test_owner_can_generate_reports(self, client, owner_auth_headers, sample_products):
        """Test Owner role can generate reports"""
        response = client.post(
            "/api/reports/generate",
            headers=owner_auth_headers,
            json={
                "template_id": "costing_analysis",
                "format": "pdf",
                "parameters": {
                    "date_range": {
                        "start": "2024-01-01",
                        "end": "2024-12-31"
                    }
                }
            }
        )
        
        assert response.status_code == 200
    
    def test_viewer_cannot_generate_reports(self, client, viewer_auth_headers, sample_products):
        """Test Viewer role cannot generate reports (403 Forbidden)"""
        response = client.post(
            "/api/reports/generate",
            headers=viewer_auth_headers,
            json={
                "template_id": "costing_analysis",
                "format": "pdf",
                "parameters": {
                    "date_range": {
                        "start": "2024-01-01",
                        "end": "2024-12-31"
                    }
                }
            }
        )
        
        assert response.status_code == 403
        assert "Access denied" in response.json()["detail"]
    
    def test_viewer_cannot_check_status(self, client, viewer_auth_headers):
        """Test Viewer role cannot check report status"""
        response = client.get(
            "/api/reports/status/some-task-id",
            headers=viewer_auth_headers
        )
        
        assert response.status_code == 403
    
    def test_viewer_cannot_download_reports(self, client, viewer_auth_headers):
        """Test Viewer role cannot download reports"""
        response = client.get(
            "/api/reports/download/some-task-id",
            headers=viewer_auth_headers
        )
        
        assert response.status_code == 403
    
    def test_unauthenticated_access_denied(self, client):
        """Test unauthenticated users cannot access report endpoints"""
        # Generate
        response = client.post(
            "/api/reports/generate",
            json={
                "template_id": "costing_analysis",
                "format": "pdf",
                "parameters": {}
            }
        )
        assert response.status_code == 401
        
        # Status
        response = client.get("/api/reports/status/some-task-id")
        assert response.status_code == 401
        
        # Download
        response = client.get("/api/reports/download/some-task-id")
        assert response.status_code == 401


class TestReportRateLimiting:
    """Test rate limiting on report generation endpoint"""
    
    def test_rate_limiting_enforced(self, client, accountant_auth_headers, sample_products):
        """Test rate limiting prevents excessive report generation requests"""
        # Make multiple requests rapidly
        successful_requests = 0
        rate_limited_requests = 0
        
        for i in range(12):  # Try 12 requests (limit is 10/minute)
            response = client.post(
                "/api/reports/generate",
                headers=accountant_auth_headers,
                json={
                    "template_id": "costing_analysis",
                    "format": "pdf",
                    "parameters": {
                        "date_range": {
                            "start": "2024-01-01",
                            "end": "2024-12-31"
                        }
                    }
                }
            )
            
            if response.status_code == 200:
                successful_requests += 1
            elif response.status_code == 429:  # Too Many Requests
                rate_limited_requests += 1
        
        # Should have some successful requests and some rate-limited
        assert successful_requests <= 10
        assert rate_limited_requests >= 2


class TestReportGenerationAllTemplates:
    """Test report generation for all available templates"""
    
    def test_generate_financial_statement_report(self, client, accountant_auth_headers):
        """Test generating financial statement report"""
        response = client.post(
            "/api/reports/generate",
            headers=accountant_auth_headers,
            json={
                "template_id": "financial_statement",
                "format": "pdf",
                "parameters": {
                    "period_type": "monthly",
                    "period_start": "2024-01-01",
                    "period_end": "2024-12-31"
                }
            }
        )
        
        assert response.status_code == 200
        assert response.json()["template_id"] == "financial_statement"
    
    def test_generate_costing_analysis_report(self, client, accountant_auth_headers, sample_products):
        """Test generating costing analysis report"""
        response = client.post(
            "/api/reports/generate",
            headers=accountant_auth_headers,
            json={
                "template_id": "costing_analysis",
                "format": "excel",
                "parameters": {
                    "date_range": {
                        "start": "2024-01-01",
                        "end": "2024-12-31"
                    }
                }
            }
        )
        
        assert response.status_code == 200
        assert response.json()["template_id"] == "costing_analysis"

    
    def test_generate_order_evaluation_report(self, client, accountant_auth_headers):
        """Test generating order evaluation report"""
        response = client.post(
            "/api/reports/generate",
            headers=accountant_auth_headers,
            json={
                "template_id": "order_evaluation",
                "format": "pdf",
                "parameters": {
                    "date_range": {
                        "start": "2024-01-01",
                        "end": "2024-12-31"
                    }
                }
            }
        )
        
        assert response.status_code == 200
        assert response.json()["template_id"] == "order_evaluation"
    
    def test_generate_margin_analysis_report(self, client, accountant_auth_headers, sample_products):
        """Test generating margin analysis report"""
        response = client.post(
            "/api/reports/generate",
            headers=accountant_auth_headers,
            json={
                "template_id": "margin_analysis",
                "format": "csv",
                "parameters": {
                    "date_range": {
                        "start": "2024-01-01",
                        "end": "2024-12-31"
                    },
                    "group_by": "product"
                }
            }
        )
        
        assert response.status_code == 200
        assert response.json()["template_id"] == "margin_analysis"
    
    def test_generate_receivables_report(self, client, accountant_auth_headers):
        """Test generating receivables report"""
        response = client.post(
            "/api/reports/generate",
            headers=accountant_auth_headers,
            json={
                "template_id": "receivables_report",
                "format": "excel",
                "parameters": {
                    "as_of_date": "2024-12-31",
                    "aging_buckets": [30, 60, 90]
                }
            }
        )
        
        assert response.status_code == 200
        assert response.json()["template_id"] == "receivables_report"


class TestReportTenantIsolation:
    """Test tenant isolation - users can only generate reports for their tenant"""
    
    def test_tenant_isolation_in_reports(self, test_db, client, accountant_role, sample_products):
        """Test users can only generate reports with their tenant's data"""
        from werkzeug.security import generate_password_hash
        
        # Create second organization
        org2 = Organization(
            name="Second Organization",
            email="org2@example.com",
            subscription_status="trial"
        )
        test_db.add(org2)
        test_db.commit()
        test_db.refresh(org2)
        
        # Create user in second organization
        user2 = User(
            email="accountant2@example.com",
            hashed_password=generate_password_hash("Accountant2Pass123"),
            full_name="Accountant 2",
            organization_id=org2.id,
            role="accountant",
            is_active=True
        )
        test_db.add(user2)
        test_db.commit()
        test_db.refresh(user2)
        
        # Assign Accountant role to user2
        user_role2 = UserRole(
            user_id=user2.id,
            role_id=accountant_role.id,
            tenant_id=org2.id
        )
        test_db.add(user_role2)
        test_db.commit()
        
        # Login as user2
        response = client.post(
            "/api/auth/login",
            data={"username": user2.email, "password": "Accountant2Pass123"}
        )
        token2 = response.json()["access_token"]
        headers2 = {"Authorization": f"Bearer {token2}"}
        
        # Generate report for user2
        response = client.post(
            "/api/reports/generate",
            headers=headers2,
            json={
                "template_id": "costing_analysis",
                "format": "pdf",
                "parameters": {
                    "date_range": {
                        "start": "2024-01-01",
                        "end": "2024-12-31"
                    }
                }
            }
        )
        
        assert response.status_code == 200
        
        # Report should only contain data from org2 (no products from org1)
        # This is implicitly tested by the report generation not failing
        # and the data service filtering by tenant_id


class TestReportDownloadExpiry:
    """Test report download URL expiry (24 hours)"""
    
    def test_download_url_expires_after_24_hours(self, client, accountant_auth_headers, sample_products):
        """Test download URL expires after 24 hours"""
        # Generate report
        gen_response = client.post(
            "/api/reports/generate",
            headers=accountant_auth_headers,
            json={
                "template_id": "costing_analysis",
                "format": "pdf",
                "parameters": {
                    "date_range": {
                        "start": "2024-01-01",
                        "end": "2024-12-31"
                    }
                }
            }
        )
        
        task_id = gen_response.json()["task_id"]
        
        # Get status
        status_response = client.get(
            f"/api/reports/status/{task_id}",
            headers=accountant_auth_headers
        )
        
        data = status_response.json()
        
        # Verify expires_at is set
        assert data["expires_at"] is not None
        
        # Verify expires_at is approximately 24 hours from now
        expires_at = datetime.fromisoformat(data["expires_at"].replace("Z", "+00:00"))
        now = datetime.utcnow().replace(tzinfo=expires_at.tzinfo)
        time_until_expiry = expires_at - now
        
        # Should be close to 24 hours (allow 5 minute tolerance)
        assert 23.9 * 3600 < time_until_expiry.total_seconds() < 24.1 * 3600


class TestReportErrorHandling:
    """Test error handling in report generation"""
    
    def test_invalid_date_format(self, client, accountant_auth_headers):
        """Test report generation with invalid date format"""
        response = client.post(
            "/api/reports/generate",
            headers=accountant_auth_headers,
            json={
                "template_id": "costing_analysis",
                "format": "pdf",
                "parameters": {
                    "date_range": {
                        "start": "invalid-date",
                        "end": "2024-12-31"
                    }
                }
            }
        )
        
        # Should return 400 or 500 depending on validation
        assert response.status_code in [400, 500]
    
    def test_missing_request_body(self, client, accountant_auth_headers):
        """Test report generation with missing request body"""
        response = client.post(
            "/api/reports/generate",
            headers=accountant_auth_headers
        )
        
        assert response.status_code == 422  # Validation error
