# backend/tests/test_digest_emails.py

"""
Integration tests for digest emails.

Tests cover:
- Notification accumulation
- Digest email generation and sending
- Urgent notification exclusion
"""

import pytest
from datetime import datetime

from app.services.notification_preference_service import DigestAccumulationService


class TestDigestAccumulationService:
    """Tests for digest accumulation service"""
    
    def test_accumulate_notification(self, db_session, test_user):
        """Test accumulating notifications"""
        service = DigestAccumulationService(db_session)
        
        notification = {
            'type': 'order_evaluation_complete',
            'order_name': 'Test Order',
            'order_id': 1,
            'margin_percentage': 25.5
        }
        
        service.accumulate_notification(test_user.id, notification)
        
        accumulated = service.get_accumulated_notifications(test_user.id)
        assert len(accumulated) == 1
        assert accumulated[0]['type'] == 'order_evaluation_complete'
    
    def test_accumulate_multiple_notifications(self, db_session, test_user):
        """Test accumulating multiple notifications"""
        service = DigestAccumulationService(db_session)
        
        notifications = [
            {'type': 'order_evaluation_complete', 'order_id': 1},
            {'type': 'scenario_analysis_ready', 'scenario_id': 1},
            {'type': 'low_margin_alert', 'product_count': 3}
        ]
        
        for notification in notifications:
            service.accumulate_notification(test_user.id, notification)
        
        accumulated = service.get_accumulated_notifications(test_user.id)
        assert len(accumulated) == 3
    
    def test_urgent_notification_excluded(self, db_session, test_user):
        """Test that urgent notifications are excluded from digest"""
        service = DigestAccumulationService(db_session)
        
        # Urgent notification (sync_status)
        urgent_notification = {
            'type': 'sync_status',
            'status': 'failed'
        }
        
        service.accumulate_notification(test_user.id, urgent_notification)
        
        accumulated = service.get_accumulated_notifications(test_user.id)
        assert len(accumulated) == 0  # Urgent notifications not accumulated
    
    def test_get_digest_summary(self, db_session, test_user):
        """Test getting digest summary grouped by type"""
        service = DigestAccumulationService(db_session)
        
        notifications = [
            {'type': 'order_evaluation_complete', 'order_id': 1},
            {'type': 'order_evaluation_complete', 'order_id': 2},
            {'type': 'scenario_analysis_ready', 'scenario_id': 1},
            {'type': 'low_margin_alert', 'product_count': 3}
        ]
        
        for notification in notifications:
            service.accumulate_notification(test_user.id, notification)
        
        summary = service.get_digest_summary(test_user.id)
        
        assert 'order_evaluation_complete' in summary
        assert summary['order_evaluation_complete']['count'] == 2
        assert 'scenario_analysis_ready' in summary
        assert summary['scenario_analysis_ready']['count'] == 1
        assert 'low_margin_alert' in summary
        assert summary['low_margin_alert']['count'] == 1
    
    def test_clear_accumulated_notifications(self, db_session, test_user):
        """Test clearing accumulated notifications"""
        service = DigestAccumulationService(db_session)
        
        notifications = [
            {'type': 'order_evaluation_complete', 'order_id': 1},
            {'type': 'scenario_analysis_ready', 'scenario_id': 1}
        ]
        
        for notification in notifications:
            service.accumulate_notification(test_user.id, notification)
        
        # Verify accumulated
        accumulated = service.get_accumulated_notifications(test_user.id)
        assert len(accumulated) == 2
        
        # Clear
        count = service.clear_accumulated_notifications(test_user.id)
        assert count == 2
        
        # Verify cleared
        accumulated = service.get_accumulated_notifications(test_user.id)
        assert len(accumulated) == 0
    
    def test_multiple_users_separate_accumulation(self, db_session, test_user):
        """Test that notifications are accumulated separately per user"""
        from app.models.models import User
        
        # Create second user
        user2 = User(
            email="user2@example.com",
            hashed_password="hashed",
            organization_id=test_user.organization_id
        )
        db_session.add(user2)
        db_session.commit()
        
        service = DigestAccumulationService(db_session)
        
        # Accumulate for first user
        service.accumulate_notification(
            test_user.id,
            {'type': 'order_evaluation_complete', 'order_id': 1}
        )
        
        # Accumulate for second user
        service.accumulate_notification(
            user2.id,
            {'type': 'scenario_analysis_ready', 'scenario_id': 1}
        )
        
        # Verify separate accumulation
        user1_notifications = service.get_accumulated_notifications(test_user.id)
        user2_notifications = service.get_accumulated_notifications(user2.id)
        
        assert len(user1_notifications) == 1
        assert len(user2_notifications) == 1
        assert user1_notifications[0]['type'] == 'order_evaluation_complete'
        assert user2_notifications[0]['type'] == 'scenario_analysis_ready'
    
    def test_empty_digest_summary(self, db_session, test_user):
        """Test digest summary with no accumulated notifications"""
        service = DigestAccumulationService(db_session)
        
        summary = service.get_digest_summary(test_user.id)
        
        assert summary == {}
    
    def test_notification_timestamp(self, db_session, test_user):
        """Test that accumulated_at timestamp is added"""
        service = DigestAccumulationService(db_session)
        
        notification = {
            'type': 'order_evaluation_complete',
            'order_id': 1
        }
        
        service.accumulate_notification(test_user.id, notification)
        
        accumulated = service.get_accumulated_notifications(test_user.id)
        assert 'accumulated_at' in accumulated[0]
        assert isinstance(accumulated[0]['accumulated_at'], datetime)
