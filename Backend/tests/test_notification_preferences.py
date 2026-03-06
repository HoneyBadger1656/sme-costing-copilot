# backend/tests/test_notification_preferences.py

"""
Integration tests for notification preferences.

Tests cover:
- Preference retrieval and updates
- Default preference initialization
- Unsubscribe functionality
"""

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.models.models import User, NotificationPreference
from app.services.notification_preference_service import NotificationPreferenceService


class TestNotificationPreferenceService:
    """Tests for notification preference service"""
    
    def test_initialize_default_preferences_owner(self, db_session, test_user):
        """Test initializing default preferences for Owner role"""
        service = NotificationPreferenceService(db_session)
        
        preferences = service.initialize_default_preferences(
            test_user.id,
            role_name='Owner'
        )
        
        # Owner should have all notification types enabled
        assert len(preferences) == 5
        notification_types = [p.notification_type for p in preferences]
        assert 'order_evaluation_complete' in notification_types
        assert 'scenario_analysis_ready' in notification_types
        assert 'sync_status' in notification_types
        assert 'low_margin_alert' in notification_types
        assert 'overdue_receivables' in notification_types
        
        # All should be enabled
        for pref in preferences:
            assert pref.enabled is True
            assert pref.delivery_method == 'email'
    
    def test_initialize_default_preferences_accountant(self, db_session, test_user):
        """Test initializing default preferences for Accountant role"""
        service = NotificationPreferenceService(db_session)
        
        preferences = service.initialize_default_preferences(
            test_user.id,
            role_name='Accountant'
        )
        
        # Accountant should have 4 notification types (no sync_status)
        assert len(preferences) == 4
        notification_types = [p.notification_type for p in preferences]
        assert 'order_evaluation_complete' in notification_types
        assert 'scenario_analysis_ready' in notification_types
        assert 'low_margin_alert' in notification_types
        assert 'overdue_receivables' in notification_types
        assert 'sync_status' not in notification_types
    
    def test_initialize_default_preferences_viewer(self, db_session, test_user):
        """Test initializing default preferences for Viewer role"""
        service = NotificationPreferenceService(db_session)
        
        preferences = service.initialize_default_preferences(
            test_user.id,
            role_name='Viewer'
        )
        
        # Viewer should have only 2 notification types
        assert len(preferences) == 2
        notification_types = [p.notification_type for p in preferences]
        assert 'order_evaluation_complete' in notification_types
        assert 'scenario_analysis_ready' in notification_types
    
    def test_get_preferences(self, db_session, test_user):
        """Test getting user preferences"""
        service = NotificationPreferenceService(db_session)
        
        # Initialize preferences
        service.initialize_default_preferences(test_user.id, 'Owner')
        
        # Get preferences
        preferences = service.get_preferences(test_user.id)
        
        assert len(preferences) == 5
    
    def test_update_preferences(self, db_session, test_user):
        """Test updating user preferences"""
        service = NotificationPreferenceService(db_session)
        
        # Initialize preferences
        service.initialize_default_preferences(test_user.id, 'Owner')
        
        # Update preferences
        updates = {
            'order_evaluation_complete': {'enabled': False},
            'low_margin_alert': {'enabled': True, 'delivery_method': 'email'}
        }
        
        updated = service.update_preferences(test_user.id, updates)
        
        assert len(updated) == 2
        
        # Verify updates
        pref = service.get_preference(test_user.id, 'order_evaluation_complete')
        assert pref.enabled is False
    
    def test_check_notification_enabled(self, db_session, test_user):
        """Test checking if notification is enabled"""
        service = NotificationPreferenceService(db_session)
        
        # Initialize preferences
        service.initialize_default_preferences(test_user.id, 'Owner')
        
        # Check enabled notification
        assert service.check_notification_enabled(
            test_user.id,
            'order_evaluation_complete'
        ) is True
        
        # Disable notification
        service.update_preferences(
            test_user.id,
            {'order_evaluation_complete': {'enabled': False}}
        )
        
        # Check disabled notification
        assert service.check_notification_enabled(
            test_user.id,
            'order_evaluation_complete'
        ) is False
        
        # Check non-existent notification
        assert service.check_notification_enabled(
            test_user.id,
            'nonexistent_type'
        ) is False
    
    def test_disable_all_notifications(self, db_session, test_user):
        """Test disabling all notifications (unsubscribe)"""
        service = NotificationPreferenceService(db_session)
        
        # Initialize preferences
        service.initialize_default_preferences(test_user.id, 'Owner')
        
        # Disable all
        count = service.disable_all_notifications(test_user.id)
        
        assert count == 5
        
        # Verify all are disabled
        preferences = service.get_preferences(test_user.id)
        for pref in preferences:
            assert pref.enabled is False


class TestNotificationPreferenceAPI:
    """Integration tests for notification preference API endpoints"""
    
    def test_get_preferences_endpoint(self, client: TestClient, auth_headers, db_session, test_user):
        """Test GET /api/notifications/preferences endpoint"""
        # Initialize preferences
        service = NotificationPreferenceService(db_session)
        service.initialize_default_preferences(test_user.id, 'Owner')
        
        response = client.get(
            "/api/notifications/preferences",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert 'preferences' in data
        assert len(data['preferences']) == 5
    
    def test_update_preferences_endpoint(self, client: TestClient, auth_headers, db_session, test_user):
        """Test PUT /api/notifications/preferences endpoint"""
        # Initialize preferences
        service = NotificationPreferenceService(db_session)
        service.initialize_default_preferences(test_user.id, 'Owner')
        
        # Update preferences
        update_data = {
            "preferences": {
                "order_evaluation_complete": {"enabled": False},
                "low_margin_alert": {"enabled": True, "delivery_method": "email"}
            }
        }
        
        response = client.put(
            "/api/notifications/preferences",
            json=update_data,
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert 'preferences' in data
        
        # Verify updates
        response = client.get(
            "/api/notifications/preferences",
            headers=auth_headers
        )
        
        preferences = response.json()['preferences']
        order_pref = next(
            (p for p in preferences if p['notification_type'] == 'order_evaluation_complete'),
            None
        )
        assert order_pref is not None
        assert order_pref['enabled'] is False
    
    def test_unsubscribe_endpoint(self, client: TestClient, db_session, test_user):
        """Test POST /api/notifications/unsubscribe endpoint"""
        # Initialize preferences
        service = NotificationPreferenceService(db_session)
        service.initialize_default_preferences(test_user.id, 'Owner')
        
        # Unsubscribe
        response = client.post(
            f"/api/notifications/unsubscribe?user_id={test_user.id}"
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data['success'] is True
        assert data['preferences_disabled'] == 5
        
        # Verify all preferences are disabled
        preferences = service.get_preferences(test_user.id)
        for pref in preferences:
            assert pref.enabled is False
    
    def test_unsubscribe_nonexistent_user(self, client: TestClient):
        """Test unsubscribe with nonexistent user"""
        response = client.post(
            "/api/notifications/unsubscribe?user_id=99999"
        )
        
        assert response.status_code == 404
    
    def test_get_preferences_requires_auth(self, client: TestClient):
        """Test that getting preferences requires authentication"""
        response = client.get("/api/notifications/preferences")
        
        assert response.status_code == 401
    
    def test_update_preferences_requires_auth(self, client: TestClient):
        """Test that updating preferences requires authentication"""
        response = client.put(
            "/api/notifications/preferences",
            json={"preferences": {}}
        )
        
        assert response.status_code == 401
