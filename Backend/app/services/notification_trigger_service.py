# backend/app/services/notification_trigger_service.py

"""
Notification trigger service.

This service handles triggering notifications for various business events:
- Order evaluation completion
- Scenario analysis completion
- Integration sync status
- Low margin alerts
- Overdue receivables alerts

Requirements: 15.1-15.8
"""

from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.models.models import User, NotificationPreference
from app.services.notification_preference_service import NotificationPreferenceService
from app.services.email_service import EmailService
from app.logging_config import get_logger

logger = get_logger(__name__)


class NotificationTriggerService:
    """Service for triggering business event notifications"""
    
    def __init__(self, db: Session):
        self.db = db
        self.preference_service = NotificationPreferenceService(db)
        self.email_service = EmailService()
        self._notification_cache: Dict[str, datetime] = {}
    
    def _check_duplicate_prevention(
        self,
        user_id: int,
        notification_type: str,
        hours: int = 24
    ) -> bool:
        """
        Check if a notification was recently sent to prevent duplicates.
        
        Args:
            user_id: User ID
            notification_type: Type of notification
            hours: Hours to check for duplicates (default 24)
        
        Returns:
            True if notification can be sent, False if duplicate
        """
        cache_key = f"{user_id}:{notification_type}"
        
        if cache_key in self._notification_cache:
            last_sent = self._notification_cache[cache_key]
            cutoff = datetime.utcnow() - timedelta(hours=hours)
            
            if last_sent > cutoff:
                logger.debug(
                    "duplicate_notification_prevented",
                    user_id=user_id,
                    notification_type=notification_type,
                    last_sent=last_sent
                )
                return False
        
        return True
    
    def _record_notification_sent(
        self,
        user_id: int,
        notification_type: str
    ) -> None:
        """
        Record that a notification was sent for duplicate prevention.
        
        Args:
            user_id: User ID
            notification_type: Type of notification
        """
        cache_key = f"{user_id}:{notification_type}"
        self._notification_cache[cache_key] = datetime.utcnow()
    
    def _get_user_email(self, user_id: int) -> Optional[str]:
        """
        Get user's email address.
        
        Args:
            user_id: User ID
        
        Returns:
            Email address or None if not found
        """
        user = self.db.query(User).filter(User.id == user_id).first()
        return user.email if user else None
    
    def trigger_order_evaluation_complete(
        self,
        order_id: int,
        user_id: int,
        order_data: Dict[str, Any]
    ) -> bool:
        """
        Trigger notification for order evaluation completion.
        
        Args:
            order_id: Order ID
            user_id: User ID who should receive notification
            order_data: Order evaluation data
        
        Returns:
            True if notification sent successfully, False otherwise
        """
        notification_type = 'order_evaluation_complete'
        
        # Check if user has this notification enabled
        if not self.preference_service.check_notification_enabled(user_id, notification_type):
            logger.debug(
                "notification_disabled",
                user_id=user_id,
                notification_type=notification_type
            )
            return False
        
        # Check for duplicates
        if not self._check_duplicate_prevention(user_id, notification_type):
            return False
        
        # Get user email
        email = self._get_user_email(user_id)
        if not email:
            logger.error(
                "user_email_not_found",
                user_id=user_id
            )
            return False
        
        # Prepare template context
        context = {
            'user_name': order_data.get('user_name', 'User'),
            'order_name': order_data.get('order_name', f'Order #{order_id}'),
            'order_id': order_id,
            'total_cost': order_data.get('total_cost', 0),
            'margin_percentage': order_data.get('margin_percentage', 0),
            'status': order_data.get('status', 'Completed'),
            'order_url': order_data.get('order_url', f'/orders/{order_id}'),
            'insights': order_data.get('insights', [])
        }
        
        try:
            # Send notification
            self.email_service.send_notification(
                recipients=[email],
                template_name=notification_type,
                context=context
            )
            
            # Record notification sent
            self._record_notification_sent(user_id, notification_type)
            
            logger.info(
                "notification_sent",
                user_id=user_id,
                notification_type=notification_type,
                order_id=order_id
            )
            
            return True
            
        except Exception as e:
            logger.exception(
                "notification_send_failed",
                error=str(e),
                user_id=user_id,
                notification_type=notification_type
            )
            return False
    
    def trigger_scenario_analysis_ready(
        self,
        scenario_id: int,
        user_id: int,
        scenario_data: Dict[str, Any]
    ) -> bool:
        """
        Trigger notification for scenario analysis completion.
        
        Args:
            scenario_id: Scenario ID
            user_id: User ID who should receive notification
            scenario_data: Scenario analysis data
        
        Returns:
            True if notification sent successfully, False otherwise
        """
        notification_type = 'scenario_analysis_ready'
        
        # Check if user has this notification enabled
        if not self.preference_service.check_notification_enabled(user_id, notification_type):
            logger.debug(
                "notification_disabled",
                user_id=user_id,
                notification_type=notification_type
            )
            return False
        
        # Check for duplicates
        if not self._check_duplicate_prevention(user_id, notification_type):
            return False
        
        # Get user email
        email = self._get_user_email(user_id)
        if not email:
            logger.error(
                "user_email_not_found",
                user_id=user_id
            )
            return False
        
        # Prepare template context
        context = {
            'user_name': scenario_data.get('user_name', 'User'),
            'scenario_name': scenario_data.get('scenario_name', f'Scenario #{scenario_id}'),
            'scenario_id': scenario_id,
            'scenario_count': scenario_data.get('scenario_count', 1),
            'best_option': scenario_data.get('best_option', 'N/A'),
            'potential_savings': scenario_data.get('potential_savings', 0),
            'scenario_url': scenario_data.get('scenario_url', f'/scenarios/{scenario_id}'),
            'recommendations': scenario_data.get('recommendations', [])
        }
        
        try:
            # Send notification
            self.email_service.send_notification(
                recipients=[email],
                template_name=notification_type,
                context=context
            )
            
            # Record notification sent
            self._record_notification_sent(user_id, notification_type)
            
            logger.info(
                "notification_sent",
                user_id=user_id,
                notification_type=notification_type,
                scenario_id=scenario_id
            )
            
            return True
            
        except Exception as e:
            logger.exception(
                "notification_send_failed",
                error=str(e),
                user_id=user_id,
                notification_type=notification_type
            )
            return False
    
    def trigger_sync_status(
        self,
        integration_name: str,
        status: str,
        tenant_id: int,
        sync_data: Dict[str, Any]
    ) -> int:
        """
        Trigger notification for integration sync status.
        
        Sends to all users in tenant with Owner or Admin role.
        
        Args:
            integration_name: Name of integration
            status: Sync status ('success' or 'failed')
            tenant_id: Tenant ID
            sync_data: Sync status data
        
        Returns:
            Number of notifications sent
        """
        notification_type = 'sync_status'
        
        # Get all users in tenant with notification enabled
        user_ids = self.preference_service.get_users_with_notification_enabled(
            notification_type,
            tenant_id
        )
        
        if not user_ids:
            logger.debug(
                "no_users_with_notification_enabled",
                notification_type=notification_type,
                tenant_id=tenant_id
            )
            return 0
        
        sent_count = 0
        
        for user_id in user_ids:
            # Check for duplicates
            if not self._check_duplicate_prevention(user_id, notification_type, hours=1):
                continue
            
            # Get user email
            email = self._get_user_email(user_id)
            if not email:
                continue
            
            # Get user name
            user = self.db.query(User).filter(User.id == user_id).first()
            user_name = user.email.split('@')[0] if user else 'User'
            
            # Prepare template context
            context = {
                'user_name': user_name,
                'integration_name': integration_name,
                'status': status,
                'integration_url': sync_data.get('integration_url', '/integrations')
            }
            
            # Add status-specific fields
            if status == 'success':
                context.update({
                    'records_synced': sync_data.get('records_synced', 0),
                    'sync_duration': sync_data.get('sync_duration', 'N/A'),
                    'completed_at': sync_data.get('completed_at', datetime.utcnow()),
                    'sync_summary': sync_data.get('sync_summary', [])
                })
            else:
                context.update({
                    'error_message': sync_data.get('error_message', 'Unknown error'),
                    'failed_at': sync_data.get('failed_at', datetime.utcnow())
                })
            
            try:
                # Send notification
                self.email_service.send_notification(
                    recipients=[email],
                    template_name=notification_type,
                    context=context
                )
                
                # Record notification sent
                self._record_notification_sent(user_id, notification_type)
                
                sent_count += 1
                
            except Exception as e:
                logger.exception(
                    "notification_send_failed",
                    error=str(e),
                    user_id=user_id,
                    notification_type=notification_type
                )
        
        logger.info(
            "sync_status_notifications_sent",
            notification_type=notification_type,
            tenant_id=tenant_id,
            sent_count=sent_count
        )
        
        return sent_count
    
    def trigger_low_margin_alert(
        self,
        tenant_id: int,
        alert_data: Dict[str, Any]
    ) -> int:
        """
        Trigger low margin alert notification.
        
        Sends to Accountant, Admin, and Owner roles in tenant.
        
        Args:
            tenant_id: Tenant ID
            alert_data: Alert data with products
        
        Returns:
            Number of notifications sent
        """
        notification_type = 'low_margin_alert'
        
        # Get all users in tenant with notification enabled
        user_ids = self.preference_service.get_users_with_notification_enabled(
            notification_type,
            tenant_id
        )
        
        if not user_ids:
            logger.debug(
                "no_users_with_notification_enabled",
                notification_type=notification_type,
                tenant_id=tenant_id
            )
            return 0
        
        sent_count = 0
        
        for user_id in user_ids:
            # Check for duplicates (daily alert)
            if not self._check_duplicate_prevention(user_id, notification_type, hours=24):
                continue
            
            # Get user email
            email = self._get_user_email(user_id)
            if not email:
                continue
            
            # Get user name
            user = self.db.query(User).filter(User.id == user_id).first()
            user_name = user.email.split('@')[0] if user else 'User'
            
            # Prepare template context
            context = {
                'user_name': user_name,
                'product_count': alert_data.get('product_count', 0),
                'margin_threshold': alert_data.get('margin_threshold', 15.0),
                'revenue_impact': alert_data.get('revenue_impact', 0),
                'alert_date': datetime.utcnow(),
                'products': alert_data.get('products', []),
                'products_url': alert_data.get('products_url', '/products')
            }
            
            try:
                # Send notification
                self.email_service.send_notification(
                    recipients=[email],
                    template_name=notification_type,
                    context=context
                )
                
                # Record notification sent
                self._record_notification_sent(user_id, notification_type)
                
                sent_count += 1
                
            except Exception as e:
                logger.exception(
                    "notification_send_failed",
                    error=str(e),
                    user_id=user_id,
                    notification_type=notification_type
                )
        
        logger.info(
            "low_margin_alert_notifications_sent",
            notification_type=notification_type,
            tenant_id=tenant_id,
            sent_count=sent_count
        )
        
        return sent_count
    
    def trigger_overdue_receivables(
        self,
        tenant_id: int,
        alert_data: Dict[str, Any]
    ) -> int:
        """
        Trigger overdue receivables alert notification.
        
        Sends to Accountant, Admin, and Owner roles in tenant.
        
        Args:
            tenant_id: Tenant ID
            alert_data: Alert data with invoices
        
        Returns:
            Number of notifications sent
        """
        notification_type = 'overdue_receivables'
        
        # Get all users in tenant with notification enabled
        user_ids = self.preference_service.get_users_with_notification_enabled(
            notification_type,
            tenant_id
        )
        
        if not user_ids:
            logger.debug(
                "no_users_with_notification_enabled",
                notification_type=notification_type,
                tenant_id=tenant_id
            )
            return 0
        
        sent_count = 0
        
        for user_id in user_ids:
            # Check for duplicates (daily alert)
            if not self._check_duplicate_prevention(user_id, notification_type, hours=24):
                continue
            
            # Get user email
            email = self._get_user_email(user_id)
            if not email:
                continue
            
            # Get user name
            user = self.db.query(User).filter(User.id == user_id).first()
            user_name = user.email.split('@')[0] if user else 'User'
            
            # Prepare template context
            context = {
                'user_name': user_name,
                'invoice_count': alert_data.get('invoice_count', 0),
                'total_overdue': alert_data.get('total_overdue', 0),
                'oldest_invoice_days': alert_data.get('oldest_invoice_days', 0),
                'alert_date': datetime.utcnow(),
                'invoices': alert_data.get('invoices', []),
                'invoices_url': alert_data.get('invoices_url', '/invoices')
            }
            
            try:
                # Send notification
                self.email_service.send_notification(
                    recipients=[email],
                    template_name=notification_type,
                    context=context
                )
                
                # Record notification sent
                self._record_notification_sent(user_id, notification_type)
                
                sent_count += 1
                
            except Exception as e:
                logger.exception(
                    "notification_send_failed",
                    error=str(e),
                    user_id=user_id,
                    notification_type=notification_type
                )
        
        logger.info(
            "overdue_receivables_notifications_sent",
            notification_type=notification_type,
            tenant_id=tenant_id,
            sent_count=sent_count
        )
        
        return sent_count
