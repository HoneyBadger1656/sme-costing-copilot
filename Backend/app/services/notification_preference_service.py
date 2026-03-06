# backend/app/services/notification_preference_service.py

"""
Notification preference service.

This service manages user notification preferences including:
- Getting and updating user preferences
- Initializing default preferences for new users
- Checking if notifications are enabled for specific types

Requirements: 16.2-16.7
"""

from typing import Dict, List, Optional, Any
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.models.models import NotificationPreference, User, UserRole
from app.logging_config import get_logger

logger = get_logger(__name__)


class NotificationPreferenceService:
    """Service for managing notification preferences"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_preferences(self, user_id: int) -> List[NotificationPreference]:
        """
        Get all notification preferences for a user.
        
        Args:
            user_id: User ID
        
        Returns:
            List of notification preferences
        """
        preferences = self.db.query(NotificationPreference).filter(
            NotificationPreference.user_id == user_id
        ).all()
        
        logger.debug(
            "preferences_retrieved",
            user_id=user_id,
            count=len(preferences)
        )
        
        return preferences
    
    def get_preference(
        self,
        user_id: int,
        notification_type: str
    ) -> Optional[NotificationPreference]:
        """
        Get a specific notification preference for a user.
        
        Args:
            user_id: User ID
            notification_type: Type of notification
        
        Returns:
            Notification preference or None if not found
        """
        preference = self.db.query(NotificationPreference).filter(
            and_(
                NotificationPreference.user_id == user_id,
                NotificationPreference.notification_type == notification_type
            )
        ).first()
        
        return preference
    
    def update_preferences(
        self,
        user_id: int,
        preferences: Dict[str, Dict[str, any]]
    ) -> List[NotificationPreference]:
        """
        Update notification preferences for a user.
        
        Args:
            user_id: User ID
            preferences: Dictionary mapping notification types to preference settings
                        Format: {notification_type: {enabled: bool, delivery_method: str}}
        
        Returns:
            Updated list of notification preferences
        """
        updated_preferences = []
        
        for notification_type, settings in preferences.items():
            # Get or create preference
            preference = self.get_preference(user_id, notification_type)
            
            if preference is None:
                preference = NotificationPreference(
                    user_id=user_id,
                    notification_type=notification_type
                )
                self.db.add(preference)
            
            # Update settings
            if 'enabled' in settings:
                preference.enabled = settings['enabled']
            if 'delivery_method' in settings:
                preference.delivery_method = settings['delivery_method']
            
            updated_preferences.append(preference)
        
        self.db.commit()
        
        logger.info(
            "preferences_updated",
            user_id=user_id,
            updated_count=len(updated_preferences)
        )
        
        return updated_preferences
    
    def initialize_default_preferences(
        self,
        user_id: int,
        role_name: Optional[str] = None
    ) -> List[NotificationPreference]:
        """
        Initialize default notification preferences for a new user.
        
        Default preferences vary by role:
        - Owner/Admin: All notifications enabled
        - Accountant: Financial and costing notifications enabled
        - Viewer: Only essential notifications enabled
        
        Args:
            user_id: User ID
            role_name: User's primary role name (optional)
        
        Returns:
            List of created notification preferences
        """
        # Define default preferences by role
        if role_name in ['Owner', 'Admin']:
            default_types = [
                'order_evaluation_complete',
                'scenario_analysis_ready',
                'sync_status',
                'low_margin_alert',
                'overdue_receivables'
            ]
        elif role_name == 'Accountant':
            default_types = [
                'order_evaluation_complete',
                'scenario_analysis_ready',
                'low_margin_alert',
                'overdue_receivables'
            ]
        else:  # Viewer or no role
            default_types = [
                'order_evaluation_complete',
                'scenario_analysis_ready'
            ]
        
        preferences = []
        
        for notification_type in default_types:
            # Check if preference already exists
            existing = self.get_preference(user_id, notification_type)
            if existing is not None:
                continue
            
            preference = NotificationPreference(
                user_id=user_id,
                notification_type=notification_type,
                enabled=True,
                delivery_method='email'
            )
            self.db.add(preference)
            preferences.append(preference)
        
        self.db.commit()
        
        logger.info(
            "default_preferences_initialized",
            user_id=user_id,
            role_name=role_name,
            count=len(preferences)
        )
        
        return preferences
    
    def check_notification_enabled(
        self,
        user_id: int,
        notification_type: str
    ) -> bool:
        """
        Check if a notification type is enabled for a user.
        
        Args:
            user_id: User ID
            notification_type: Type of notification
        
        Returns:
            True if notification is enabled, False otherwise
        """
        preference = self.get_preference(user_id, notification_type)
        
        if preference is None:
            # If no preference exists, default to disabled
            logger.debug(
                "notification_preference_not_found",
                user_id=user_id,
                notification_type=notification_type,
                default_enabled=False
            )
            return False
        
        return preference.enabled
    
    def disable_all_notifications(self, user_id: int) -> int:
        """
        Disable all notifications for a user (unsubscribe).
        
        Args:
            user_id: User ID
        
        Returns:
            Number of preferences updated
        """
        count = self.db.query(NotificationPreference).filter(
            NotificationPreference.user_id == user_id
        ).update({NotificationPreference.enabled: False})
        
        self.db.commit()
        
        logger.info(
            "all_notifications_disabled",
            user_id=user_id,
            count=count
        )
        
        return count
    
    def get_users_with_notification_enabled(
        self,
        notification_type: str,
        tenant_id: int
    ) -> List[int]:
        """
        Get all user IDs in a tenant who have a specific notification type enabled.
        
        Args:
            notification_type: Type of notification
            tenant_id: Tenant ID
        
        Returns:
            List of user IDs
        """
        # Join with User to filter by tenant
        user_ids = self.db.query(NotificationPreference.user_id).join(
            User, User.id == NotificationPreference.user_id
        ).filter(
            and_(
                NotificationPreference.notification_type == notification_type,
                NotificationPreference.enabled == True,
                User.organization_id == tenant_id
            )
        ).all()
        
        user_ids = [uid[0] for uid in user_ids]
        
        logger.debug(
            "users_with_notification_enabled",
            notification_type=notification_type,
            tenant_id=tenant_id,
            count=len(user_ids)
        )
        
        return user_ids
    
    def get_users_by_role_with_notification(
        self,
        notification_type: str,
        tenant_id: int,
        role_names: List[str]
    ) -> List[int]:
        """
        Get user IDs with specific roles who have a notification type enabled.
        
        Args:
            notification_type: Type of notification
            tenant_id: Tenant ID
            role_names: List of role names to filter by
        
        Returns:
            List of user IDs
        """
        # Join with User and UserRole to filter by tenant and role
        user_ids = self.db.query(NotificationPreference.user_id).join(
            User, User.id == NotificationPreference.user_id
        ).join(
            UserRole, UserRole.user_id == User.id
        ).filter(
            and_(
                NotificationPreference.notification_type == notification_type,
                NotificationPreference.enabled == True,
                User.tenant_id == tenant_id,
                UserRole.tenant_id == tenant_id,
                UserRole.role_id.in_(
                    self.db.query(UserRole.role_id).filter(
                        UserRole.role_id.in_(
                            self.db.query(UserRole.role_id).join(
                                User, User.id == UserRole.user_id
                            ).filter(User.tenant_id == tenant_id)
                        )
                    )
                )
            )
        ).distinct().all()
        
        user_ids = [uid[0] for uid in user_ids]
        
        logger.debug(
            "users_by_role_with_notification",
            notification_type=notification_type,
            tenant_id=tenant_id,
            role_names=role_names,
            count=len(user_ids)
        )
        
        return user_ids



class DigestAccumulationService:
    """
    Service for accumulating notifications for digest emails.
    
    Requirements: 17.1-17.7
    """
    
    def __init__(self, db: Session):
        self.db = db
        self._digest_cache: Dict[int, List[Dict[str, Any]]] = {}
    
    def accumulate_notification(
        self,
        user_id: int,
        notification: Dict[str, Any]
    ) -> None:
        """
        Accumulate a notification for digest email.
        
        Urgent notifications are excluded from digest accumulation.
        
        Args:
            user_id: User ID
            notification: Notification data
        """
        # Check if notification is urgent (should be sent immediately)
        urgent_types = ['sync_status']  # Sync failures should be immediate
        
        if notification.get('type') in urgent_types:
            logger.debug(
                "urgent_notification_excluded_from_digest",
                user_id=user_id,
                notification_type=notification.get('type')
            )
            return
        
        # Add to cache
        if user_id not in self._digest_cache:
            self._digest_cache[user_id] = []
        
        notification['accumulated_at'] = datetime.utcnow()
        self._digest_cache[user_id].append(notification)
        
        logger.debug(
            "notification_accumulated",
            user_id=user_id,
            notification_type=notification.get('type'),
            total_accumulated=len(self._digest_cache[user_id])
        )
    
    def get_accumulated_notifications(
        self,
        user_id: int
    ) -> List[Dict[str, Any]]:
        """
        Get all accumulated notifications for a user.
        
        Args:
            user_id: User ID
        
        Returns:
            List of accumulated notifications
        """
        notifications = self._digest_cache.get(user_id, [])
        
        logger.debug(
            "accumulated_notifications_retrieved",
            user_id=user_id,
            count=len(notifications)
        )
        
        return notifications
    
    def clear_accumulated_notifications(
        self,
        user_id: int
    ) -> int:
        """
        Clear accumulated notifications for a user after digest is sent.
        
        Args:
            user_id: User ID
        
        Returns:
            Number of notifications cleared
        """
        count = len(self._digest_cache.get(user_id, []))
        
        if user_id in self._digest_cache:
            del self._digest_cache[user_id]
        
        logger.info(
            "accumulated_notifications_cleared",
            user_id=user_id,
            count=count
        )
        
        return count
    
    def get_digest_summary(
        self,
        user_id: int
    ) -> Dict[str, Any]:
        """
        Get summary of accumulated notifications grouped by type.
        
        Args:
            user_id: User ID
        
        Returns:
            Dictionary with notification counts by type
        """
        notifications = self.get_accumulated_notifications(user_id)
        
        # Group by type
        summary = {}
        for notification in notifications:
            notification_type = notification.get('type', 'unknown')
            if notification_type not in summary:
                summary[notification_type] = {
                    'count': 0,
                    'notifications': []
                }
            summary[notification_type]['count'] += 1
            summary[notification_type]['notifications'].append(notification)
        
        return summary
