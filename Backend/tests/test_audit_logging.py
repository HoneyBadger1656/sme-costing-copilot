# Backend/tests/test_audit_logging.py

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
from fastapi import Request
from sqlalchemy.orm import Session

from app.utils.audit import (
    sanitize_sensitive_fields,
    log_audit_event,
    get_model_dict,
    log_create,
    log_update,
    log_delete,
    SENSITIVE_FIELDS
)
from app.models.models import AuditLog, User
from app.middleware.audit_middleware import AuditMiddleware


class TestSanitizeSensitiveFields:
    """Test sensitive field sanitization functionality."""
    
    def test_sanitize_simple_sensitive_fields(self):
        """Test sanitization of simple sensitive fields."""
        data = {
            "username": "testuser",
            "password": "secret123",
            "email": "test@example.com",
            "access_token": "token123"
        }
        
        result = sanitize_sensitive_fields(data)
        
        assert result["username"] == "testuser"
        assert result["password"] == "***REDACTED***"
        assert result["email"] == "test@example.com"
        assert result["access_token"] == "***REDACTED***"
    
    def test_sanitize_nested_sensitive_fields(self):
        """Test sanitization of nested sensitive fields."""
        data = {
            "user": {
                "name": "John Doe",
                "hashed_password": "hashed123",
                "profile": {
                    "api_key": "key123",
                    "public_info": "visible"
                }
            },
            "config": {
                "zoho_tokens": {"access": "token", "refresh": "refresh"},
                "public_setting": "value"
            }
        }
        
        result = sanitize_sensitive_fields(data)
        
        assert result["user"]["name"] == "John Doe"
        assert result["user"]["hashed_password"] == "***REDACTED***"
        assert result["user"]["profile"]["api_key"] == "***REDACTED***"
        assert result["user"]["profile"]["public_info"] == "visible"
        assert result["config"]["zoho_tokens"] == "***REDACTED***"
        assert result["config"]["public_setting"] == "value"
    
    def test_sanitize_list_with_sensitive_fields(self):
        """Test sanitization of lists containing sensitive fields."""
        data = {
            "users": [
                {"name": "User1", "password": "pass1"},
                {"name": "User2", "secret_key": "secret2"}
            ],
            "tokens": ["token1", "token2"]
        }
        
        result = sanitize_sensitive_fields(data)
        
        assert result["users"][0]["name"] == "User1"
        assert result["users"][0]["password"] == "***REDACTED***"
        assert result["users"][1]["name"] == "User2"
        assert result["users"][1]["secret_key"] == "***REDACTED***"
        assert result["tokens"] == ["token1", "token2"]  # Non-dict items unchanged
    
    def test_sanitize_empty_or_none_data(self):
        """Test sanitization with empty or None data."""
        assert sanitize_sensitive_fields(None) is None
        assert sanitize_sensitive_fields({}) == {}
        assert sanitize_sensitive_fields({"key": None}) == {"key": None}
    
    def test_sanitize_case_insensitive(self):
        """Test that sanitization is case insensitive."""
        data = {
            "PASSWORD": "secret",
            "Access_Token": "token",
            "api_KEY": "key"
        }
        
        result = sanitize_sensitive_fields(data)
        
        assert result["PASSWORD"] == "***REDACTED***"
        assert result["Access_Token"] == "***REDACTED***"
        assert result["api_KEY"] == "***REDACTED***"


class TestGetModelDict:
    """Test model to dictionary conversion."""
    
    def test_get_model_dict_with_user(self):
        """Test converting User model to dictionary."""
        # Create a mock user with datetime field
        user = Mock()
        user.__table__ = Mock()
        
        # Create mock columns with proper name attributes
        col_id = Mock()
        col_id.name = "id"
        col_email = Mock()
        col_email.name = "email"
        col_created_at = Mock()
        col_created_at.name = "created_at"
        col_is_active = Mock()
        col_is_active.name = "is_active"
        
        user.__table__.columns = [col_id, col_email, col_created_at, col_is_active]
        
        # Set up attribute values
        user.id = 1
        user.email = "test@example.com"
        user.created_at = datetime(2023, 1, 1, 12, 0, 0)
        user.is_active = True
        
        result = get_model_dict(user)
        
        assert result["id"] == 1
        assert result["email"] == "test@example.com"
        assert result["created_at"] == "2023-01-01T12:00:00"
        assert result["is_active"] is True
    
    def test_get_model_dict_with_none(self):
        """Test converting None to dictionary."""
        result = get_model_dict(None)
        assert result == {}
    
    def test_get_model_dict_with_complex_objects(self):
        """Test converting model with complex object attributes."""
        model = Mock()
        model.__table__ = Mock()
        
        # Create mock columns with proper name attributes
        col_id = Mock()
        col_id.name = "id"
        col_complex = Mock()
        col_complex.name = "complex_obj"
        
        model.__table__.columns = [col_id, col_complex]
        
        # Create a complex object that will be converted to string
        complex_obj = type('ComplexObj', (), {'__dict__': {"nested": "value"}})()
        
        model.id = 1
        model.complex_obj = complex_obj
        
        result = get_model_dict(model)
        
        assert result["id"] == 1
        assert isinstance(result["complex_obj"], str)  # Should be converted to string


class TestLogAuditEvent:
    """Test audit event logging functionality."""
    
    @pytest.fixture
    def mock_db(self):
        """Create a mock database session."""
        db = Mock(spec=Session)
        return db
    
    @pytest.fixture
    def mock_request(self):
        """Create a mock FastAPI request."""
        request = Mock(spec=Request)
        request.headers = {
            "X-Forwarded-For": "192.168.1.1, 10.0.0.1",
            "User-Agent": "Mozilla/5.0 Test Browser"
        }
        request.client = Mock()
        request.client.host = "127.0.0.1"
        return request
    
    def test_log_audit_event_create_success(self, mock_db, mock_request):
        """Test successful CREATE audit event logging."""
        new_values = {"name": "Test Product", "price": 100.0}
        
        with patch('app.utils.audit.AuditLog') as mock_audit_log:
            mock_audit_instance = Mock()
            mock_audit_log.return_value = mock_audit_instance
            
            result = log_audit_event(
                db=mock_db,
                action="CREATE",
                table_name="products",
                record_id=1,
                tenant_id="tenant123",
                user_id=42,
                new_values=new_values,
                request=mock_request
            )
            
            # Verify AuditLog was created with correct parameters
            mock_audit_log.assert_called_once()
            call_kwargs = mock_audit_log.call_args[1]
            
            assert call_kwargs["tenant_id"] == "tenant123"
            assert call_kwargs["user_id"] == 42
            assert call_kwargs["action"] == "CREATE"
            assert call_kwargs["table_name"] == "products"
            assert call_kwargs["record_id"] == 1
            assert call_kwargs["old_values"] is None
            assert call_kwargs["new_values"] == new_values
            assert call_kwargs["ip_address"] == "192.168.1.1"
            assert call_kwargs["user_agent"] == "Mozilla/5.0 Test Browser"
            
            # Verify database operations
            mock_db.add.assert_called_once_with(mock_audit_instance)
            mock_db.commit.assert_called_once()
            
            assert result == mock_audit_instance
    
    def test_log_audit_event_update_with_sensitive_data(self, mock_db, mock_request):
        """Test UPDATE audit event with sensitive data sanitization."""
        old_values = {"name": "Old Product", "api_key": "secret123"}
        new_values = {"name": "New Product", "api_key": "newsecret456"}
        
        with patch('app.utils.audit.AuditLog') as mock_audit_log:
            mock_audit_instance = Mock()
            mock_audit_log.return_value = mock_audit_instance
            
            result = log_audit_event(
                db=mock_db,
                action="UPDATE",
                table_name="products",
                record_id=1,
                tenant_id="tenant123",
                user_id=42,
                old_values=old_values,
                new_values=new_values,
                request=mock_request
            )
            
            # Verify sensitive data was sanitized
            call_kwargs = mock_audit_log.call_args[1]
            assert call_kwargs["old_values"]["name"] == "Old Product"
            assert call_kwargs["old_values"]["api_key"] == "***REDACTED***"
            assert call_kwargs["new_values"]["name"] == "New Product"
            assert call_kwargs["new_values"]["api_key"] == "***REDACTED***"
    
    def test_log_audit_event_delete_success(self, mock_db, mock_request):
        """Test successful DELETE audit event logging."""
        old_values = {"name": "Deleted Product", "price": 100.0}
        
        with patch('app.utils.audit.AuditLog') as mock_audit_log:
            mock_audit_instance = Mock()
            mock_audit_log.return_value = mock_audit_instance
            
            result = log_audit_event(
                db=mock_db,
                action="DELETE",
                table_name="products",
                record_id=1,
                tenant_id="tenant123",
                user_id=42,
                old_values=old_values,
                request=mock_request
            )
            
            # Verify AuditLog was created with correct parameters
            call_kwargs = mock_audit_log.call_args[1]
            assert call_kwargs["action"] == "DELETE"
            assert call_kwargs["old_values"] == old_values
            assert call_kwargs["new_values"] is None
    
    def test_log_audit_event_without_request(self, mock_db):
        """Test audit event logging without request object."""
        with patch('app.utils.audit.AuditLog') as mock_audit_log:
            mock_audit_instance = Mock()
            mock_audit_log.return_value = mock_audit_instance
            
            result = log_audit_event(
                db=mock_db,
                action="CREATE",
                table_name="products",
                record_id=1,
                tenant_id="tenant123",
                user_id=42,
                new_values={"name": "Test"},
                request=None
            )
            
            # Verify IP and user agent are None
            call_kwargs = mock_audit_log.call_args[1]
            assert call_kwargs["ip_address"] is None
            assert call_kwargs["user_agent"] is None
    
    def test_log_audit_event_with_long_user_agent(self, mock_db, mock_request):
        """Test audit event logging with very long user agent."""
        long_user_agent = "A" * 600  # Longer than 500 char limit
        mock_request.headers = {"User-Agent": long_user_agent}
        
        with patch('app.utils.audit.AuditLog') as mock_audit_log:
            mock_audit_instance = Mock()
            mock_audit_log.return_value = mock_audit_instance
            
            result = log_audit_event(
                db=mock_db,
                action="CREATE",
                table_name="products",
                record_id=1,
                tenant_id="tenant123",
                new_values={"name": "Test"},
                request=mock_request
            )
            
            # Verify user agent was truncated
            call_kwargs = mock_audit_log.call_args[1]
            assert len(call_kwargs["user_agent"]) == 500
            assert call_kwargs["user_agent"].endswith("...")
    
    def test_log_audit_event_database_error_handling(self, mock_db, mock_request):
        """Test graceful handling of database errors."""
        mock_db.add.side_effect = Exception("Database error")
        
        with patch('app.utils.audit.AuditLog') as mock_audit_log:
            mock_audit_instance = Mock()
            mock_audit_log.return_value = mock_audit_instance
            
            # Should not raise exception
            result = log_audit_event(
                db=mock_db,
                action="CREATE",
                table_name="products",
                record_id=1,
                tenant_id="tenant123",
                new_values={"name": "Test"},
                request=mock_request
            )
            
            # Should return None on error
            assert result is None
            
            # Should attempt rollback
            mock_db.rollback.assert_called_once()
    
    def test_log_audit_event_commit_error_handling(self, mock_db, mock_request):
        """Test graceful handling of commit errors."""
        mock_db.commit.side_effect = Exception("Commit error")
        
        with patch('app.utils.audit.AuditLog') as mock_audit_log:
            mock_audit_instance = Mock()
            mock_audit_log.return_value = mock_audit_instance
            
            result = log_audit_event(
                db=mock_db,
                action="CREATE",
                table_name="products",
                record_id=1,
                tenant_id="tenant123",
                new_values={"name": "Test"},
                request=mock_request
            )
            
            assert result is None
            mock_db.rollback.assert_called_once()


class TestAuditHelperFunctions:
    """Test audit helper functions (log_create, log_update, log_delete)."""
    
    @pytest.fixture
    def mock_db(self):
        return Mock(spec=Session)
    
    @pytest.fixture
    def mock_request(self):
        request = Mock(spec=Request)
        request.headers = {}
        request.client = Mock()
        request.client.host = "127.0.0.1"
        return request
    
    def test_log_create(self, mock_db, mock_request):
        """Test log_create helper function."""
        with patch('app.utils.audit.log_audit_event') as mock_log_audit:
            mock_log_audit.return_value = Mock()
            
            result = log_create(
                db=mock_db,
                table_name="products",
                record_id=1,
                tenant_id="tenant123",
                new_values={"name": "New Product"},
                user_id=42,
                request=mock_request
            )
            
            mock_log_audit.assert_called_once_with(
                db=mock_db,
                action="CREATE",
                table_name="products",
                record_id=1,
                tenant_id="tenant123",
                user_id=42,
                old_values=None,
                new_values={"name": "New Product"},
                request=mock_request
            )
    
    def test_log_update(self, mock_db, mock_request):
        """Test log_update helper function."""
        with patch('app.utils.audit.log_audit_event') as mock_log_audit:
            mock_log_audit.return_value = Mock()
            
            result = log_update(
                db=mock_db,
                table_name="products",
                record_id=1,
                tenant_id="tenant123",
                old_values={"name": "Old Product"},
                new_values={"name": "Updated Product"},
                user_id=42,
                request=mock_request
            )
            
            mock_log_audit.assert_called_once_with(
                db=mock_db,
                action="UPDATE",
                table_name="products",
                record_id=1,
                tenant_id="tenant123",
                user_id=42,
                old_values={"name": "Old Product"},
                new_values={"name": "Updated Product"},
                request=mock_request
            )
    
    def test_log_delete(self, mock_db, mock_request):
        """Test log_delete helper function."""
        with patch('app.utils.audit.log_audit_event') as mock_log_audit:
            mock_log_audit.return_value = Mock()
            
            result = log_delete(
                db=mock_db,
                table_name="products",
                record_id=1,
                tenant_id="tenant123",
                old_values={"name": "Deleted Product"},
                user_id=42,
                request=mock_request
            )
            
            mock_log_audit.assert_called_once_with(
                db=mock_db,
                action="DELETE",
                table_name="products",
                record_id=1,
                tenant_id="tenant123",
                user_id=42,
                old_values={"name": "Deleted Product"},
                new_values=None,
                request=mock_request
            )


class TestAuditMiddleware:
    """Test audit middleware functionality."""
    
    @pytest.fixture
    def middleware(self):
        """Create audit middleware instance."""
        app = Mock()
        return AuditMiddleware(app)
    
    def test_extract_table_name(self, middleware):
        """Test table name extraction from URL path."""
        assert middleware._extract_table_name(["api", "clients", "123"]) == "clients"
        assert middleware._extract_table_name(["api", "products"]) == "products"
        assert middleware._extract_table_name(["api", "orders", "456", "items"]) == "orders"
        assert middleware._extract_table_name(["api", "unknown"]) == ""
        assert middleware._extract_table_name([]) == ""
    
    def test_map_method_to_action(self, middleware):
        """Test HTTP method to audit action mapping."""
        assert middleware._map_method_to_action("POST") == "CREATE"
        assert middleware._map_method_to_action("PUT") == "UPDATE"
        assert middleware._map_method_to_action("PATCH") == "UPDATE"
        assert middleware._map_method_to_action("DELETE") == "DELETE"
        assert middleware._map_method_to_action("GET") == "UNKNOWN"
    
    def test_extract_record_id(self, middleware):
        """Test record ID extraction from URL path."""
        assert middleware._extract_record_id(["api", "clients", "123"], "PUT") == 123
        assert middleware._extract_record_id(["api", "products", "456", "edit"], "PATCH") == 456
        assert middleware._extract_record_id(["api", "clients"], "POST") == 0
        assert middleware._extract_record_id(["api", "clients", "abc"], "PUT") == 0
    
    @pytest.mark.asyncio
    async def test_middleware_skips_get_requests(self, middleware):
        """Test that middleware skips GET requests."""
        request = Mock()
        request.method = "GET"
        request.url.path = "/api/clients"
        
        # Create an async mock for call_next
        async def mock_call_next(req):
            response = Mock()
            response.status_code = 200
            return response
        
        response = await middleware.dispatch(request, mock_call_next)
        
        assert response.status_code == 200
        # No audit logging should occur for GET requests
    
    @pytest.mark.asyncio
    async def test_middleware_skips_non_audited_paths(self, middleware):
        """Test that middleware skips non-audited paths."""
        request = Mock()
        request.method = "POST"
        request.url.path = "/api/health"
        
        # Create an async mock for call_next
        async def mock_call_next(req):
            response = Mock()
            response.status_code = 200
            return response
        
        response = await middleware.dispatch(request, mock_call_next)
        
        assert response.status_code == 200
        # No audit logging should occur for non-audited paths
    
    @pytest.mark.asyncio
    async def test_middleware_skips_failed_requests(self, middleware):
        """Test that middleware skips failed requests (non-2xx status)."""
        request = Mock()
        request.method = "POST"
        request.url.path = "/api/clients"
        
        # Mock async body method
        async def mock_body():
            return b'{"name": "Test Client"}'
        request.body = mock_body
        
        # Create an async mock for call_next
        async def mock_call_next(req):
            response = Mock()
            response.status_code = 400  # Bad request
            return response
        
        with patch('app.middleware.audit_middleware.get_db'):
            response = await middleware.dispatch(request, mock_call_next)
        
        assert response.status_code == 400
        # No audit logging should occur for failed requests
    
    @pytest.mark.asyncio
    async def test_middleware_handles_audit_logging_errors(self, middleware):
        """Test that middleware handles audit logging errors gracefully."""
        request = Mock()
        request.method = "POST"
        request.url.path = "/api/clients"
        
        # Mock async body method
        async def mock_body():
            return b'{"name": "Test Client"}'
        request.body = mock_body
        request.state.tenant_id = "tenant123"
        request.state.user_id = 42
        
        # Create an async mock for call_next
        async def mock_call_next(req):
            response = Mock()
            response.status_code = 201
            return response
        
        # Mock get_db to raise an exception
        with patch('app.middleware.audit_middleware.get_db') as mock_get_db:
            mock_get_db.side_effect = Exception("Database connection error")
            
            # Should not raise exception
            response = await middleware.dispatch(request, mock_call_next)
            
            assert response.status_code == 201


class TestAuditLoggingIntegration:
    """Integration tests for audit logging with real database operations."""
    
    def test_audit_logging_with_real_audit_log_model(self, test_db, test_organization):
        """Test audit logging creates real AuditLog records."""
        # Create test data
        new_values = {
            "name": "Test Product",
            "price": 100.0,
            "description": "A test product"
        }
        
        # Log audit event
        audit_log = log_audit_event(
            db=test_db,
            action="CREATE",
            table_name="products",
            record_id=1,
            tenant_id=test_organization.id,
            user_id=None,
            new_values=new_values
        )
        
        # Verify audit log was created
        assert audit_log is not None
        assert audit_log.id is not None
        assert audit_log.tenant_id == test_organization.id
        assert audit_log.action == "CREATE"
        assert audit_log.table_name == "products"
        assert audit_log.record_id == 1
        assert audit_log.new_values == new_values
        assert audit_log.old_values is None
        assert audit_log.created_at is not None
        
        # Verify it's in the database
        db_audit_log = test_db.query(AuditLog).filter(AuditLog.id == audit_log.id).first()
        assert db_audit_log is not None
        assert db_audit_log.action == "CREATE"
    
    def test_audit_logging_with_sensitive_data_in_database(self, test_db, test_organization):
        """Test that sensitive data is properly sanitized in database."""
        sensitive_data = {
            "username": "testuser",
            "password": "secret123",
            "api_key": "key123",
            "public_info": "visible"
        }
        
        audit_log = log_audit_event(
            db=test_db,
            action="CREATE",
            table_name="users",
            record_id=1,
            tenant_id=test_organization.id,
            new_values=sensitive_data
        )
        
        # Verify sensitive data was sanitized in database
        assert audit_log.new_values["username"] == "testuser"
        assert audit_log.new_values["password"] == "***REDACTED***"
        assert audit_log.new_values["api_key"] == "***REDACTED***"
        assert audit_log.new_values["public_info"] == "visible"
        
        # Verify in database query
        db_audit_log = test_db.query(AuditLog).filter(AuditLog.id == audit_log.id).first()
        assert db_audit_log.new_values["password"] == "***REDACTED***"
        assert db_audit_log.new_values["api_key"] == "***REDACTED***"