# backend/app/api/notifications.py

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional

from app.core.database import get_db
from app.models.models import User, NotificationPreference
from app.api.auth import get_current_user
from app.services.email_service import EmailService
from app.services.notification_preference_service import NotificationPreferenceService
from app.core.email_config import get_email_config
from app.utils.rbac import require_role
from app.logging_config import get_logger

logger = get_logger(__name__)
router = APIRouter()


class TestEmailRequest(BaseModel):
    """Request schema for test email"""
    recipient: str = Field(..., description="Test email recipient address")


class TestEmailResponse(BaseModel):
    """Response schema for test email"""
    success: bool
    message: str
    config_status: Dict[str, Any]


@router.post("/test-email", response_model=TestEmailResponse)
def test_email_configuration(
    request: TestEmailRequest,
    current_user: User = Depends(require_role("Owner", "Admin")),
    db: Session = Depends(get_db)
):
    """
    Test email service configuration by sending a test email.
    
    Requires Owner or Admin role.
    
    Args:
        request: Test email request with recipient address
        current_user: Authenticated user
        db: Database session
    
    Returns:
        Test result with configuration status
    """
    try:
        logger.info(
            "test_email_requested",
            recipient=request.recipient,
            user_id=current_user.id
        )
        
        # Get email configuration
        email_config = get_email_config()
        
        if email_config is None:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Email service is not configured. Please set EMAIL_API_KEY and EMAIL_FROM_ADDRESS."
            )
        
        # Create email service
        email_service = EmailService()
        
        # Get configuration status
        config_status = email_service.test_configuration()
        
        # Send test email
        try:
            result = email_service.send_email(
                recipients=[request.recipient],
                subject="SME Costing Copilot - Email Configuration Test",
                body=f"""
Hello,

This is a test email from SME Costing Copilot to verify your email configuration.

Configuration Details:
- Provider: {email_config.provider}
- From Address: {email_config.from_address}
- From Name: {email_config.from_name}
- Rate Limit: {email_config.rate_limit_per_hour} emails/hour

If you received this email, your email service is configured correctly!

Best regards,
SME Costing Copilot Team
                """.strip(),
                html_body=f"""
<html>
<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
    <h2 style="color: #2c3e50;">Email Configuration Test</h2>
    <p>Hello,</p>
    <p>This is a test email from <strong>SME Costing Copilot</strong> to verify your email configuration.</p>
    
    <h3 style="color: #34495e;">Configuration Details:</h3>
    <ul>
        <li><strong>Provider:</strong> {email_config.provider}</li>
        <li><strong>From Address:</strong> {email_config.from_address}</li>
        <li><strong>From Name:</strong> {email_config.from_name}</li>
        <li><strong>Rate Limit:</strong> {email_config.rate_limit_per_hour} emails/hour</li>
    </ul>
    
    <p style="color: #27ae60; font-weight: bold;">
        ✓ If you received this email, your email service is configured correctly!
    </p>
    
    <hr style="border: none; border-top: 1px solid #ecf0f1; margin: 20px 0;">
    <p style="color: #7f8c8d; font-size: 0.9em;">
        Best regards,<br>
        SME Costing Copilot Team
    </p>
</body>
</html>
                """.strip()
            )
            
            logger.info(
                "test_email_sent_successfully",
                recipient=request.recipient,
                user_id=current_user.id,
                provider=email_config.provider
            )
            
            return TestEmailResponse(
                success=True,
                message=f"Test email sent successfully to {request.recipient}",
                config_status=config_status
            )
            
        except Exception as e:
            logger.error(
                "test_email_send_failed",
                error=str(e),
                recipient=request.recipient,
                user_id=current_user.id
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to send test email: {str(e)}"
            )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(
            "test_email_error",
            error=str(e),
            user_id=current_user.id
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to test email configuration"
        )



class NotificationPreferenceResponse(BaseModel):
    """Response schema for notification preference"""
    notification_type: str
    enabled: bool
    delivery_method: str


class UpdatePreferencesRequest(BaseModel):
    """Request schema for updating notification preferences"""
    preferences: Dict[str, Dict[str, Any]] = Field(
        ...,
        description="Dictionary mapping notification types to settings"
    )


class PreferencesListResponse(BaseModel):
    """Response schema for list of preferences"""
    preferences: List[NotificationPreferenceResponse]


@router.get("/preferences", response_model=PreferencesListResponse)
def get_notification_preferences(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get notification preferences for the current user.
    
    Returns:
        List of notification preferences
    """
    try:
        service = NotificationPreferenceService(db)
        preferences = service.get_preferences(current_user.id)
        
        return PreferencesListResponse(
            preferences=[
                NotificationPreferenceResponse(
                    notification_type=pref.notification_type,
                    enabled=pref.enabled,
                    delivery_method=pref.delivery_method
                )
                for pref in preferences
            ]
        )
        
    except Exception as e:
        logger.exception(
            "get_preferences_error",
            error=str(e),
            user_id=current_user.id
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve notification preferences"
        )


@router.put("/preferences", response_model=PreferencesListResponse)
def update_notification_preferences(
    request: UpdatePreferencesRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update notification preferences for the current user.
    
    Args:
        request: Preference update request
        current_user: Authenticated user
        db: Database session
    
    Returns:
        Updated list of notification preferences
    """
    try:
        service = NotificationPreferenceService(db)
        preferences = service.update_preferences(
            current_user.id,
            request.preferences
        )
        
        logger.info(
            "preferences_updated_via_api",
            user_id=current_user.id,
            updated_count=len(preferences)
        )
        
        return PreferencesListResponse(
            preferences=[
                NotificationPreferenceResponse(
                    notification_type=pref.notification_type,
                    enabled=pref.enabled,
                    delivery_method=pref.delivery_method
                )
                for pref in preferences
            ]
        )
        
    except Exception as e:
        logger.exception(
            "update_preferences_error",
            error=str(e),
            user_id=current_user.id
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update notification preferences"
        )


@router.post("/unsubscribe")
def unsubscribe_from_notifications(
    user_id: int = Query(..., description="User ID to unsubscribe"),
    token: Optional[str] = Query(None, description="Unsubscribe token (optional)"),
    db: Session = Depends(get_db)
):
    """
    Unsubscribe a user from all notifications.
    
    This endpoint can be called from an email unsubscribe link without authentication.
    In production, you should validate the token parameter to prevent abuse.
    
    Args:
        user_id: User ID to unsubscribe
        token: Optional unsubscribe token for validation
        db: Database session
    
    Returns:
        Success message
    """
    try:
        # TODO: In production, validate the token to ensure it's a legitimate unsubscribe request
        # For now, we'll allow any unsubscribe request
        
        # Verify user exists
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        service = NotificationPreferenceService(db)
        count = service.disable_all_notifications(user_id)
        
        logger.info(
            "user_unsubscribed",
            user_id=user_id,
            preferences_disabled=count
        )
        
        return {
            "success": True,
            "message": f"Successfully unsubscribed from all notifications",
            "preferences_disabled": count
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(
            "unsubscribe_error",
            error=str(e),
            user_id=user_id
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to unsubscribe from notifications"
        )
