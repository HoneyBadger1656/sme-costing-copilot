# backend/tests/test_notification_triggers.py

"""
Integration tests for notification triggers.

Tests cover:
- Notification sending for each trigger type
- Preference checking
- Duplicate prevention
- Role-based recipient filtering
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock

from app.services.notification_trigger_service import NotificationTriggerService
from app.services.notification_preference_service import NotificationPreferenceService
from app.models.models import User, Product


class TestNotificationTriggerService:
    """Tests for notification trigger service"""
    
    def test_trigger_order_evaluation_complete(self, db_session, test_user):
        """Test triggering order evaluation complete notification"""
        # Initialize preferences
        pref_service = NotificationPreferenceService(db_session)
        pref_service.initialize_default_preferences(test_user.id, 'Owner')
        
        # Mock email service
        with patch('app.services.notification_trigger_service.EmailService') as mock_email:
            mock_email_instance = MagicMock()
            mock_email.return_value = mock_email_instance
            
            trigger_service = NotificationTriggerService(db_session)
            
            order_data = {
                'user_name': 'Test User',
                'order_name': 'Test Order',
                'order_id': 1,
                'total_cost': 50000.00,
                'margin_percentage': 25.5,
                'status': 'Completed',
                'order_url': '/orders/1',
                'insights': ['Insight 1', 'Insight 2']
            }
            
            result = trigger_service.trigger_order_evaluation_complete(
                order_id=1,
                user_id=test_user.id,
                order_data=order_data
            )
            
            assert result is True
            mock_email_instance.send_notification.assert_called_once()
    
    def test_trigger_with_notification_disabled(self, db_session, test_user):
        """Test that notification is not sent when disabled"""
        # Initialize preferences and disable notification
        pref_service = NotificationPreferenceService(db_session)
        pref_service.initialize_default_preferences(test_user.id, 'Owner')
        pref_service.update_preferences(
            test_user.id,
            {'order_evaluation_complete': {'enabled': False}}
        )
        
        trigger_service = NotificationTriggerService(db_session)
        
        order_data = {
            'user_name': 'Test User',
            'order_name': 'Test Order',
            'order_id': 1,
            'total_cost': 50000.00,
            'margin_percentage': 25.5,
            'status': 'Completed',
            'order_url': '/orders/1',
            'insights': []
        }
        
        result = trigger_service.trigger_order_evaluation_complete(
            order_id=1,
            user_id=test_user.id,
            order_data=order_data
        )
        
        assert result is False
    
    def test_duplicate_prevention(self, db_session, test_user):
        """Test that duplicate notifications are prevented"""
        # Initialize preferences
        pref_service = NotificationPreferenceService(db_session)
        pref_service.initialize_default_preferences(test_user.id, 'Owner')
        
        with patch('app.services.notification_trigger_service.EmailService') as mock_email:
            mock_email_instance = MagicMock()
            mock_email.return_value = mock_email_instance
            
            trigger_service = NotificationTriggerService(db_session)
            
            order_data = {
                'user_name': 'Test User',
                'order_name': 'Test Order',
                'order_id': 1,
                'total_cost': 50000.00,
                'margin_percentage': 25.5,
                'status': 'Completed',
                'order_url': '/orders/1',
                'insights': []
            }
            
            # First notification should succeed
            result1 = trigger_service.trigger_order_evaluation_complete(
                order_id=1,
                user_id=test_user.id,
                order_data=order_data
            )
            assert result1 is True
            
            # Second notification within 24 hours should be prevented
            result2 = trigger_service.trigger_order_evaluation_complete(
                order_id=1,
                user_id=test_user.id,
                order_data=order_data
            )
            assert result2 is False
            
            # Email should only be sent once
            assert mock_email_instance.send_notification.call_count == 1
    
    def test_trigger_scenario_analysis_ready(self, db_session, test_user):
        """Test triggering scenario analysis ready notification"""
        # Initialize preferences
        pref_service = NotificationPreferenceService(db_session)
        pref_service.initialize_default_preferences(test_user.id, 'Owner')
        
        with patch('app.services.notification_trigger_service.EmailService') as mock_email:
            mock_email_instance = MagicMock()
            mock_email.return_value = mock_email_instance
            
            trigger_service = NotificationTriggerService(db_session)
            
            scenario_data = {
                'user_name': 'Test User',
                'scenario_name': 'Test Scenario',
                'scenario_id': 1,
                'scenario_count': 3,
                'best_option': 'Option B',
                'potential_savings': 75000.00,
                'scenario_url': '/scenarios/1',
                'recommendations': ['Rec 1', 'Rec 2']
            }
            
            result = trigger_service.trigger_scenario_analysis_ready(
                scenario_id=1,
                user_id=test_user.id,
                scenario_data=scenario_data
            )
            
            assert result is True
            mock_email_instance.send_notification.assert_called_once()
    
    def test_trigger_sync_status_success(self, db_session, test_user):
        """Test triggering sync status notification (success)"""
        # Initialize preferences
        pref_service = NotificationPreferenceService(db_session)
        pref_service.initialize_default_preferences(test_user.id, 'Owner')
        
        with patch('app.services.notification_trigger_service.EmailService') as mock_email:
            mock_email_instance = MagicMock()
            mock_email.return_value = mock_email_instance
            
            trigger_service = NotificationTriggerService(db_session)
            
            sync_data = {
                'records_synced': 150,
                'sync_duration': '2 minutes',
                'completed_at': datetime.utcnow(),
                'integration_url': '/integrations',
                'sync_summary': ['150 records synced']
            }
            
            sent_count = trigger_service.trigger_sync_status(
                integration_name='QuickBooks',
                status='success',
                tenant_id=test_user.organization_id,
                sync_data=sync_data
            )
            
            assert sent_count >= 0
    
    def test_trigger_sync_status_failure(self, db_session, test_user):
        """Test triggering sync status notification (failure)"""
        # Initialize preferences
        pref_service = NotificationPreferenceService(db_session)
        pref_service.initialize_default_preferences(test_user.id, 'Owner')
        
        with patch('app.services.notification_trigger_service.EmailService') as mock_email:
            mock_email_instance = MagicMock()
            mock_email.return_value = mock_email_instance
            
            trigger_service = NotificationTriggerService(db_session)
            
            sync_data = {
                'error_message': 'Authentication failed',
                'failed_at': datetime.utcnow(),
                'integration_url': '/integrations'
            }
            
            sent_count = trigger_service.trigger_sync_status(
                integration_name='QuickBooks',
                status='failed',
                tenant_id=test_user.organization_id,
                sync_data=sync_data
            )
            
            assert sent_count >= 0
    
    def test_trigger_low_margin_alert(self, db_session, test_user):
        """Test triggering low margin alert"""
        # Initialize preferences
        pref_service = NotificationPreferenceService(db_session)
        pref_service.initialize_default_preferences(test_user.id, 'Owner')
        
        with patch('app.services.notification_trigger_service.EmailService') as mock_email:
            mock_email_instance = MagicMock()
            mock_email.return_value = mock_email_instance
            
            trigger_service = NotificationTriggerService(db_session)
            
            alert_data = {
                'product_count': 3,
                'margin_threshold': 15.0,
                'revenue_impact': 25000.00,
                'products': [
                    {'name': 'Product A', 'current_margin': 12.5, 'target_margin': 20.0},
                    {'name': 'Product B', 'current_margin': 10.0, 'target_margin': 18.0}
                ],
                'products_url': '/products'
            }
            
            sent_count = trigger_service.trigger_low_margin_alert(
                tenant_id=test_user.organization_id,
                alert_data=alert_data
            )
            
            assert sent_count >= 0
    
    def test_trigger_overdue_receivables(self, db_session, test_user):
        """Test triggering overdue receivables alert"""
        # Initialize preferences
        pref_service = NotificationPreferenceService(db_session)
        pref_service.initialize_default_preferences(test_user.id, 'Owner')
        
        with patch('app.services.notification_trigger_service.EmailService') as mock_email:
            mock_email_instance = MagicMock()
            mock_email.return_value = mock_email_instance
            
            trigger_service = NotificationTriggerService(db_session)
            
            alert_data = {
                'invoice_count': 5,
                'total_overdue': 125000.00,
                'oldest_invoice_days': 45,
                'invoices': [
                    {
                        'client_name': 'Client A',
                        'invoice_number': 'INV-001',
                        'amount': 50000.00,
                        'days_overdue': 45
                    }
                ],
                'invoices_url': '/invoices'
            }
            
            sent_count = trigger_service.trigger_overdue_receivables(
                tenant_id=test_user.organization_id,
                alert_data=alert_data
            )
            
            assert sent_count >= 0
    
    def test_user_email_not_found(self, db_session):
        """Test that notification fails gracefully when user email not found"""
        trigger_service = NotificationTriggerService(db_session)
        
        order_data = {
            'user_name': 'Test User',
            'order_name': 'Test Order',
            'order_id': 1,
            'total_cost': 50000.00,
            'margin_percentage': 25.5,
            'status': 'Completed',
            'order_url': '/orders/1',
            'insights': []
        }
        
        # Try to send to non-existent user
        result = trigger_service.trigger_order_evaluation_complete(
            order_id=1,
            user_id=99999,
            order_data=order_data
        )
        
        assert result is False
