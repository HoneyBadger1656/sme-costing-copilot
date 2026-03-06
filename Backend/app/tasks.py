"""Background tasks using Celery"""

from app.celery_app import celery_app
from app.core.database import SessionLocal
from app.services.integration_service import TallyIntegration, ZohoIntegration
from app.models.models import Client, IntegrationSync
from app.logging_config import get_logger
from datetime import datetime

logger = get_logger(__name__)


@celery_app.task(bind=True, name="sync_tally_ledgers")
def sync_tally_ledgers_task(self, client_id: int, tally_config: dict):
    """
    Background task to sync Tally ledgers
    
    Args:
        client_id: Client ID
        tally_config: Tally configuration dict with url, port, company_name
        
    Returns:
        Dict with sync results
    """
    db = SessionLocal()
    sync_record = None
    
    try:
        # Create sync record
        sync_record = IntegrationSync(
            client_id=client_id,
            integration_type="tally",
            sync_direction="pull",
            entity_type="ledger",
            status="running",
            started_at=datetime.utcnow()
        )
        db.add(sync_record)
        db.commit()
        
        logger.info("tally_sync_started", client_id=client_id, task_id=self.request.id)
        
        # Fetch ledgers from Tally
        ledgers = TallyIntegration.fetch_ledgers(
            tally_config["url"],
            tally_config["port"],
            tally_config["company_name"]
        )
        
        if not ledgers:
            sync_record.status = "failed"
            sync_record.error_message = "No ledgers found or connection failed"
            sync_record.completed_at = datetime.utcnow()
            db.commit()
            return {"success": False, "message": "No ledgers found"}
        
        # Sync to database
        result = TallyIntegration.sync_ledgers_to_db(db, client_id, ledgers)
        
        # Update sync record
        sync_record.status = "success"
        sync_record.records_synced = result.get("synced", 0)
        sync_record.completed_at = datetime.utcnow()
        db.commit()
        
        logger.info("tally_sync_completed", client_id=client_id, records=result.get("synced", 0))
        
        return {
            "success": True,
            "records_synced": result.get("synced", 0),
            "message": "Tally sync completed successfully"
        }
        
    except Exception as e:
        logger.exception("tally_sync_failed", client_id=client_id, error=str(e))
        
        if sync_record:
            sync_record.status = "failed"
            sync_record.error_message = str(e)
            sync_record.completed_at = datetime.utcnow()
            db.commit()
        
        return {
            "success": False,
            "message": f"Tally sync failed: {str(e)}"
        }
    finally:
        db.close()


@celery_app.task(bind=True, name="sync_zoho_invoices")
def sync_zoho_invoices_task(self, client_id: int, organization_id: str):
    """
    Background task to sync Zoho invoices
    
    Args:
        client_id: Client ID
        organization_id: Zoho organization ID
        
    Returns:
        Dict with sync results
    """
    db = SessionLocal()
    sync_record = None
    
    try:
        # Get client tokens
        client = db.query(Client).filter(Client.id == client_id).first()
        if not client or not client.zoho_tokens:
            return {"success": False, "message": "Zoho not connected"}
        
        # Create sync record
        sync_record = IntegrationSync(
            client_id=client_id,
            integration_type="zoho",
            sync_direction="pull",
            entity_type="invoice",
            status="running",
            started_at=datetime.utcnow()
        )
        db.add(sync_record)
        db.commit()
        
        logger.info("zoho_sync_started", client_id=client_id, task_id=self.request.id)
        
        access_token = client.zoho_tokens.get("access_token")
        
        # Fetch invoices
        invoices = ZohoIntegration.fetch_invoices(access_token, organization_id)
        
        if not invoices:
            sync_record.status = "failed"
            sync_record.error_message = "No invoices found"
            sync_record.completed_at = datetime.utcnow()
            db.commit()
            return {"success": False, "message": "No invoices found"}
        
        # Sync to database
        result = ZohoIntegration.sync_invoices_to_db(db, client_id, invoices)
        
        # Update sync record
        sync_record.status = "success"
        sync_record.records_synced = result.get("synced", 0)
        sync_record.completed_at = datetime.utcnow()
        db.commit()
        
        logger.info("zoho_sync_completed", client_id=client_id, records=result.get("synced", 0))
        
        return {
            "success": True,
            "records_synced": result.get("synced", 0),
            "message": "Zoho sync completed successfully"
        }
        
    except Exception as e:
        logger.exception("zoho_sync_failed", client_id=client_id, error=str(e))
        
        if sync_record:
            sync_record.status = "failed"
            sync_record.error_message = str(e)
            sync_record.completed_at = datetime.utcnow()
            db.commit()
        
        return {
            "success": False,
            "message": f"Zoho sync failed: {str(e)}"
        }
    finally:
        db.close()


@celery_app.task(bind=True, name="generate_financial_report")
def generate_financial_report_task(self, client_id: int, report_type: str, period_start: str, period_end: str):
    """
    Background task to generate financial reports
    
    Args:
        client_id: Client ID
        report_type: Type of report (balance_sheet, profit_loss, cash_flow)
        period_start: Start date (ISO format)
        period_end: End date (ISO format)
        
    Returns:
        Dict with report generation results
    """
    db = SessionLocal()
    
    try:
        logger.info("report_generation_started", 
                   client_id=client_id, 
                   report_type=report_type,
                   task_id=self.request.id)
        
        # TODO: Implement report generation logic
        # This would involve:
        # 1. Fetching financial data
        # 2. Calculating ratios and metrics
        # 3. Generating PDF/Excel
        # 4. Storing in database or S3
        
        logger.info("report_generation_completed", client_id=client_id)
        
        return {
            "success": True,
            "message": "Report generated successfully",
            "report_type": report_type
        }
        
    except Exception as e:
        logger.exception("report_generation_failed", client_id=client_id, error=str(e))
        return {
            "success": False,
            "message": f"Report generation failed: {str(e)}"
        }
    finally:
        db.close()


@celery_app.task(bind=True, name="async_generate_report")
def async_generate_report_task(
    self,
    template_id: str,
    format: str,
    parameters: dict,
    tenant_id: int,
    user_id: int
):
    """
    Background task to generate reports asynchronously.
    
    Args:
        template_id: Report template ID
        format: Output format (pdf, excel, csv)
        parameters: Report parameters
        tenant_id: Tenant ID
        user_id: User ID requesting the report
        
    Returns:
        Dict with report generation results
    """
    from app.services.report_service import ReportService
    
    db = SessionLocal()
    
    try:
        logger.info(
            "async_report_generation_started",
            template_id=template_id,
            format=format,
            tenant_id=tenant_id,
            user_id=user_id,
            task_id=self.request.id
        )
        
        # Generate report
        report_service = ReportService(db)
        result = report_service.generate_report(
            template_id=template_id,
            format=format,
            parameters=parameters,
            tenant_id=tenant_id,
            user_id=user_id
        )
        
        logger.info(
            "async_report_generation_completed",
            template_id=template_id,
            tenant_id=tenant_id,
            task_id=result["task_id"]
        )
        
        return {
            "success": True,
            "task_id": result["task_id"],
            "file_name": result["file_name"],
            "file_size": result["file_size"],
            "message": "Report generated successfully"
        }
        
    except Exception as e:
        logger.exception(
            "async_report_generation_failed",
            template_id=template_id,
            tenant_id=tenant_id,
            error=str(e)
        )
        return {
            "success": False,
            "message": f"Report generation failed: {str(e)}"
        }
    finally:
        db.close()



@celery_app.task(bind=True, name="execute_due_scheduled_reports")
def execute_due_scheduled_reports_task(self):
    """
    Periodic task to execute scheduled reports that are due.
    Runs every minute to check for reports that need to be executed.
    
    Returns:
        Dict with execution results
    """
    from app.services.scheduled_report_service import ScheduledReportService
    from app.models.models import ReportSchedule
    from datetime import datetime
    
    db = SessionLocal()
    
    try:
        logger.info("checking_due_scheduled_reports", task_id=self.request.id)
        
        # Query for schedules that are due
        now = datetime.utcnow()
        due_schedules = db.query(ReportSchedule).filter(
            ReportSchedule.is_active == True,
            ReportSchedule.next_run_at <= now
        ).all()
        
        if not due_schedules:
            logger.debug("no_due_scheduled_reports")
            return {
                "success": True,
                "message": "No due scheduled reports",
                "executed": 0
            }
        
        logger.info("found_due_scheduled_reports", count=len(due_schedules))
        
        executed_count = 0
        failed_count = 0
        
        # Execute each due schedule
        for schedule in due_schedules:
            try:
                scheduled_report_service = ScheduledReportService(db)
                result = scheduled_report_service.execute_scheduled_report(schedule.id)
                
                # Send report via email (placeholder for now)
                # TODO: Implement email sending when email service is ready (tasks 17.2-17.5)
                send_scheduled_report_email_task.delay(
                    schedule_id=schedule.id,
                    report_result=result,
                    recipients=schedule.recipients
                )
                
                executed_count += 1
                
                logger.info(
                    "scheduled_report_executed_successfully",
                    schedule_id=schedule.id,
                    template_id=schedule.template_id,
                    tenant_id=schedule.tenant_id
                )
                
            except Exception as e:
                failed_count += 1
                logger.error(
                    "scheduled_report_execution_failed",
                    schedule_id=schedule.id,
                    error=str(e),
                    exc_info=True
                )
                # Continue with next schedule even if one fails
                continue
        
        logger.info(
            "scheduled_reports_execution_completed",
            executed=executed_count,
            failed=failed_count
        )
        
        return {
            "success": True,
            "message": f"Executed {executed_count} scheduled reports, {failed_count} failed",
            "executed": executed_count,
            "failed": failed_count
        }
        
    except Exception as e:
        logger.exception("scheduled_reports_check_failed", error=str(e))
        return {
            "success": False,
            "message": f"Scheduled reports check failed: {str(e)}"
        }
    finally:
        db.close()


@celery_app.task(bind=True, name="send_scheduled_report_email")
def send_scheduled_report_email_task(
    self,
    schedule_id: int,
    report_result: dict,
    recipients: list
):
    """
    Background task to send scheduled report via email.
    
    This is a placeholder implementation until the email service is fully implemented
    (tasks 17.2-17.5). Currently logs the email sending action.
    
    Args:
        schedule_id: Schedule ID
        report_result: Report generation result dict
        recipients: List of recipient email addresses
        
    Returns:
        Dict with email sending results
    """
    try:
        logger.info(
            "sending_scheduled_report_email",
            schedule_id=schedule_id,
            recipients=recipients,
            task_id=self.request.id
        )
        
        # TODO: Implement actual email sending when email service is ready
        # This will be implemented in tasks 17.2-17.5
        # For now, we just log the action
        
        # Placeholder logic:
        # 1. Get report file path from report_result
        # 2. Prepare email with report attachment
        # 3. Send email to all recipients
        # 4. Handle failures and retries
        
        logger.info(
            "scheduled_report_email_placeholder",
            schedule_id=schedule_id,
            recipients=recipients,
            message="Email service not yet implemented. Report generated successfully but not sent."
        )
        
        return {
            "success": True,
            "message": "Email sending placeholder - email service not yet implemented",
            "recipients": recipients,
            "schedule_id": schedule_id
        }
        
    except Exception as e:
        logger.exception(
            "scheduled_report_email_failed",
            schedule_id=schedule_id,
            error=str(e)
        )
        return {
            "success": False,
            "message": f"Email sending failed: {str(e)}"
        }



@celery_app.task(bind=True, name="send_low_margin_alerts")
def send_low_margin_alerts_task(self):
    """
    Daily scheduled task to send low margin alerts.
    
    Runs at 9:00 AM tenant local time.
    Sends alerts to Accountant, Admin, and Owner roles.
    
    Requirements: 15.4-15.6
    """
    db = SessionLocal()
    
    try:
        from app.models.models import Product, Tenant
        from app.services.notification_trigger_service import NotificationTriggerService
        from sqlalchemy import and_
        
        logger.info("low_margin_alerts_task_started", task_id=self.request.id)
        
        # Get all tenants
        tenants = db.query(Tenant).all()
        
        total_alerts_sent = 0
        
        for tenant in tenants:
            # Get products with low margins for this tenant
            # Assuming margin threshold of 15%
            margin_threshold = 15.0
            
            low_margin_products = db.query(Product).filter(
                and_(
                    Product.tenant_id == tenant.id,
                    Product.margin_percentage < margin_threshold
                )
            ).all()
            
            if not low_margin_products:
                continue
            
            # Calculate revenue impact
            revenue_impact = sum(
                p.selling_price * 100  # Estimate based on selling price
                for p in low_margin_products
            )
            
            # Prepare alert data
            alert_data = {
                'product_count': len(low_margin_products),
                'margin_threshold': margin_threshold,
                'revenue_impact': revenue_impact,
                'products': [
                    {
                        'name': p.name,
                        'current_margin': p.margin_percentage,
                        'target_margin': 20.0  # Target margin
                    }
                    for p in low_margin_products[:10]  # Top 10 products
                ],
                'products_url': '/products'
            }
            
            # Trigger notifications
            trigger_service = NotificationTriggerService(db)
            sent_count = trigger_service.trigger_low_margin_alert(
                tenant_id=tenant.id,
                alert_data=alert_data
            )
            
            total_alerts_sent += sent_count
            
            logger.info(
                "low_margin_alerts_sent",
                tenant_id=tenant.id,
                product_count=len(low_margin_products),
                alerts_sent=sent_count
            )
        
        logger.info(
            "low_margin_alerts_task_completed",
            task_id=self.request.id,
            total_alerts_sent=total_alerts_sent
        )
        
        return {
            "success": True,
            "total_alerts_sent": total_alerts_sent
        }
        
    except Exception as e:
        logger.exception(
            "low_margin_alerts_task_failed",
            error=str(e),
            task_id=self.request.id
        )
        raise
    finally:
        db.close()


@celery_app.task(bind=True, name="send_overdue_receivables_alerts")
def send_overdue_receivables_alerts_task(self):
    """
    Daily scheduled task to send overdue receivables alerts.
    
    Runs at 9:00 AM tenant local time.
    Sends alerts to Accountant, Admin, and Owner roles.
    
    Requirements: 15.4-15.6
    """
    db = SessionLocal()
    
    try:
        from app.models.models import Invoice, Tenant
        from app.services.notification_trigger_service import NotificationTriggerService
        from sqlalchemy import and_
        from datetime import datetime, timedelta
        
        logger.info("overdue_receivables_alerts_task_started", task_id=self.request.id)
        
        # Get all tenants
        tenants = db.query(Tenant).all()
        
        total_alerts_sent = 0
        
        for tenant in tenants:
            # Get overdue invoices for this tenant
            today = datetime.utcnow().date()
            
            overdue_invoices = db.query(Invoice).filter(
                and_(
                    Invoice.tenant_id == tenant.id,
                    Invoice.due_date < today,
                    Invoice.status != 'paid'
                )
            ).all()
            
            if not overdue_invoices:
                continue
            
            # Calculate totals
            total_overdue = sum(inv.amount for inv in overdue_invoices)
            
            # Find oldest invoice
            oldest_invoice = min(overdue_invoices, key=lambda inv: inv.due_date)
            oldest_invoice_days = (today - oldest_invoice.due_date).days
            
            # Prepare alert data
            alert_data = {
                'invoice_count': len(overdue_invoices),
                'total_overdue': total_overdue,
                'oldest_invoice_days': oldest_invoice_days,
                'invoices': [
                    {
                        'client_name': inv.client.name if inv.client else 'Unknown',
                        'invoice_number': inv.invoice_number,
                        'amount': inv.amount,
                        'days_overdue': (today - inv.due_date).days
                    }
                    for inv in overdue_invoices[:10]  # Top 10 invoices
                ],
                'invoices_url': '/invoices'
            }
            
            # Trigger notifications
            trigger_service = NotificationTriggerService(db)
            sent_count = trigger_service.trigger_overdue_receivables(
                tenant_id=tenant.id,
                alert_data=alert_data
            )
            
            total_alerts_sent += sent_count
            
            logger.info(
                "overdue_receivables_alerts_sent",
                tenant_id=tenant.id,
                invoice_count=len(overdue_invoices),
                alerts_sent=sent_count
            )
        
        logger.info(
            "overdue_receivables_alerts_task_completed",
            task_id=self.request.id,
            total_alerts_sent=total_alerts_sent
        )
        
        return {
            "success": True,
            "total_alerts_sent": total_alerts_sent
        }
        
    except Exception as e:
        logger.exception(
            "overdue_receivables_alerts_task_failed",
            error=str(e),
            task_id=self.request.id
        )
        raise
    finally:
        db.close()



@celery_app.task(bind=True, name="send_digest_emails")
def send_digest_emails_task(self):
    """
    Daily scheduled task to send digest emails.
    
    Runs at user's configured time (default 6:00 PM).
    Sends accumulated notifications in a single digest email.
    
    Requirements: 17.2, 17.8
    """
    db = SessionLocal()
    
    try:
        from app.models.models import User, NotificationPreference
        from app.services.notification_preference_service import DigestAccumulationService
        from app.services.email_service import EmailService
        from datetime import datetime, timedelta
        
        logger.info("digest_emails_task_started", task_id=self.request.id)
        
        # Get digest accumulation service
        digest_service = DigestAccumulationService(db)
        email_service = EmailService()
        
        # Get all users with digest mode enabled
        # For now, we'll get all users and check their preferences
        users = db.query(User).all()
        
        total_digests_sent = 0
        
        for user in users:
            # Get accumulated notifications
            notifications = digest_service.get_accumulated_notifications(user.id)
            
            if not notifications:
                continue
            
            # Get digest summary
            summary = digest_service.get_digest_summary(user.id)
            
            # Prepare template context
            period_end = datetime.utcnow()
            period_start = period_end - timedelta(days=1)
            
            context = {
                'user_name': user.email.split('@')[0],
                'total_count': len(notifications),
                'period_start': period_start,
                'period_end': period_end,
                'dashboard_url': '/dashboard',
                'order_evaluations': summary.get('order_evaluation_complete', {}),
                'scenario_analyses': summary.get('scenario_analysis_ready', {}),
                'low_margin_alerts': summary.get('low_margin_alert', {}),
                'overdue_receivables': summary.get('overdue_receivables', {})
            }
            
            try:
                # Send digest email
                email_service.send_notification(
                    recipients=[user.email],
                    template_name='digest',
                    context=context,
                    subject='Your Daily Digest - SME Costing Copilot'
                )
                
                # Clear accumulated notifications
                digest_service.clear_accumulated_notifications(user.id)
                
                total_digests_sent += 1
                
                logger.info(
                    "digest_email_sent",
                    user_id=user.id,
                    notification_count=len(notifications)
                )
                
            except Exception as e:
                logger.exception(
                    "digest_email_send_failed",
                    error=str(e),
                    user_id=user.id
                )
        
        logger.info(
            "digest_emails_task_completed",
            task_id=self.request.id,
            total_digests_sent=total_digests_sent
        )
        
        return {
            "success": True,
            "total_digests_sent": total_digests_sent
        }
        
    except Exception as e:
        logger.exception(
            "digest_emails_task_failed",
            error=str(e),
            task_id=self.request.id
        )
        raise
    finally:
        db.close()
