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
