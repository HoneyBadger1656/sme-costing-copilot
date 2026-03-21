# Quick Start Guide: Phase 4 Implementation

## Overview

This guide provides a step-by-step approach to implementing Phase 4 (GST & Compliance) features.

## Prerequisites

- Phase 3 completed (RBAC, Audit, Reports, Notifications)
- PostgreSQL database set up
- Redis installed for caching
- Test GST credentials obtained

## Week 1-2: Foundation

### 1. Database Schema Updates

Create migration for GST-related tables:

```python
# Backend/alembic/versions/xxx_add_gst_tables.py

def upgrade():
    # GST Configuration table
    op.create_table(
        'gst_configurations',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('client_id', sa.Integer(), sa.ForeignKey('clients.id')),
        sa.Column('gstin', sa.String(15), nullable=False),
        sa.Column('legal_name', sa.String(255), nullable=False),
        sa.Column('trade_name', sa.String(255)),
        sa.Column('state_code', sa.String(2), nullable=False),
        sa.Column('gst_username', sa.String(255)),
        sa.Column('gst_api_key', sa.Text()),  # Encrypted
        sa.Column('filing_frequency', sa.String(20), default='monthly'),
        sa.Column('created_at', sa.DateTime(), default=datetime.utcnow),
        sa.Column('updated_at', sa.DateTime(), onupdate=datetime.utcnow)
    )
    
    # GST Returns table
    op.create_table(
        'gst_returns',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('client_id', sa.Integer(), sa.ForeignKey('clients.id')),
        sa.Column('return_type', sa.String(20)),  # GSTR1, GSTR3B, GSTR9
        sa.Column('period', sa.String(7)),  # MMYYYY format
        sa.Column('status', sa.String(20)),  # draft, filed, accepted
        sa.Column('filing_date', sa.DateTime()),
        sa.Column('arn', sa.String(50)),  # Acknowledgement Reference Number
        sa.Column('data', sa.JSON()),  # Return data
        sa.Column('created_at', sa.DateTime(), default=datetime.utcnow)
    )
    
    # HSN/SAC Master table
    op.create_table(
        'hsn_sac_master',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('code', sa.String(10), unique=True),
        sa.Column('description', sa.Text()),
        sa.Column('gst_rate', sa.Float()),
        sa.Column('type', sa.String(10)),  # HSN or SAC
        sa.Column('created_at', sa.DateTime(), default=datetime.utcnow)
    )
```


### 2. GST Service Layer

Create GST service for business logic:

```python
# Backend/app/services/gst_service.py

from typing import Dict, List
from datetime import datetime
from sqlalchemy.orm import Session

class GSTService:
    """Service for GST compliance operations"""
    
    def generate_gstr1(self, client_id: int, period: str, db: Session) -> Dict:
        """
        Generate GSTR-1 return from sales invoices
        
        Args:
            client_id: Client ID
            period: Period in MMYYYY format (e.g., "032026")
            db: Database session
            
        Returns:
            GSTR-1 JSON data
        """
        # Get all sales invoices for the period
        invoices = self._get_invoices_for_period(client_id, period, db)
        
        # Group by invoice type (B2B, B2C, exports, etc.)
        b2b_invoices = self._group_b2b_invoices(invoices)
        b2c_invoices = self._group_b2c_invoices(invoices)
        
        # Build GSTR-1 JSON structure
        gstr1_data = {
            "gstin": self._get_gstin(client_id, db),
            "ret_period": period,
            "b2b": b2b_invoices,
            "b2cl": b2c_invoices,  # B2C Large (>2.5L)
            "b2cs": self._summarize_b2c_small(invoices),
            "cdnr": self._get_credit_debit_notes(client_id, period, db),
            "exp": self._get_export_invoices(client_id, period, db),
            "nil": self._get_nil_rated_supplies(client_id, period, db)
        }
        
        return gstr1_data
    
    def generate_gstr3b(self, client_id: int, period: str, db: Session) -> Dict:
        """Generate GSTR-3B return with auto-reconciliation"""
        # Implementation here
        pass
    
    def reconcile_gstr2a_2b(self, client_id: int, period: str, db: Session) -> Dict:
        """Reconcile GSTR-2A with GSTR-2B for input tax credit"""
        # Implementation here
        pass
```

### 3. GST API Integration

Create wrapper for GST Portal API:

```python
# Backend/app/integrations/gst_api.py

import requests
from typing import Dict
import os

class GSTPortalAPI:
    """Wrapper for GST Portal API"""
    
    BASE_URL = os.getenv("GST_API_URL", "https://api.gst.gov.in")
    
    def __init__(self, gstin: str, username: str, api_key: str):
        self.gstin = gstin
        self.username = username
        self.api_key = api_key
        self.session = requests.Session()
    
    def authenticate(self) -> str:
        """Authenticate and get session token"""
        response = self.session.post(
            f"{self.BASE_URL}/taxpayerapi/v1.0/authenticate",
            json={
                "username": self.username,
                "app_key": self.api_key
            }
        )
        response.raise_for_status()
        return response.json()["auth_token"]
    
    def file_gstr1(self, return_data: Dict) -> Dict:
        """File GSTR-1 return"""
        token = self.authenticate()
        response = self.session.post(
            f"{self.BASE_URL}/taxpayerapi/v1.0/returns/gstr1",
            headers={"Authorization": f"Bearer {token}"},
            json=return_data
        )
        response.raise_for_status()
        return response.json()
    
    def get_gstr2a(self, period: str) -> Dict:
        """Fetch GSTR-2A (auto-populated from suppliers' GSTR-1)"""
        token = self.authenticate()
        response = self.session.get(
            f"{self.BASE_URL}/taxpayerapi/v1.0/returns/gstr2a",
            headers={"Authorization": f"Bearer {token}"},
            params={"ret_period": period, "gstin": self.gstin}
        )
        response.raise_for_status()
        return response.json()
```


### 4. API Endpoints

Create GST endpoints:

```python
# Backend/app/api/gst.py

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.api.auth import get_current_user
from app.services.gst_service import GSTService
from app.utils.rbac import require_permission

router = APIRouter()
gst_service = GSTService()

@router.post("/gst/gstr1/generate")
@require_permission("financials")
async def generate_gstr1(
    period: str,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Generate GSTR-1 return for the specified period"""
    try:
        gstr1_data = gst_service.generate_gstr1(
            client_id=current_user.organization_id,
            period=period,
            db=db
        )
        return {"status": "success", "data": gstr1_data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/gst/gstr1/file")
@require_permission("financials")
async def file_gstr1(
    period: str,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """File GSTR-1 return to GST Portal"""
    # Implementation here
    pass

@router.get("/gst/reconciliation")
@require_permission("financials")
async def get_gst_reconciliation(
    period: str,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get GST reconciliation report (2A vs 2B)"""
    # Implementation here
    pass
```

## Week 3-4: E-Invoicing

### 1. E-Invoice Service

```python
# Backend/app/services/einvoice_service.py

import requests
import json
from typing import Dict

class EInvoiceService:
    """Service for e-invoicing via IRP"""
    
    IRP_URL = "https://einvoice1.gst.gov.in"
    
    def generate_irn(self, invoice_data: Dict) -> Dict:
        """
        Generate IRN (Invoice Reference Number) from IRP
        
        Args:
            invoice_data: Invoice data in e-invoice JSON format
            
        Returns:
            IRN, QR code, and signed invoice
        """
        # Step 1: Prepare e-invoice JSON
        einvoice_json = self._prepare_einvoice_json(invoice_data)
        
        # Step 2: Call IRP API
        response = requests.post(
            f"{self.IRP_URL}/eicore/dec/einvoice/generate",
            json=einvoice_json,
            headers=self._get_auth_headers()
        )
        
        if response.status_code != 200:
            raise Exception(f"IRP Error: {response.text}")
        
        result = response.json()
        
        return {
            "irn": result["Irn"],
            "ack_no": result["AckNo"],
            "ack_date": result["AckDt"],
            "signed_invoice": result["SignedInvoice"],
            "signed_qr_code": result["SignedQRCode"]
        }
    
    def cancel_irn(self, irn: str, reason: str) -> Dict:
        """Cancel e-invoice (within 24 hours)"""
        response = requests.post(
            f"{self.IRP_URL}/eicore/dec/einvoice/cancel",
            json={"irn": irn, "cnl_rsn": reason, "cnl_rem": "Cancelled"},
            headers=self._get_auth_headers()
        )
        response.raise_for_status()
        return response.json()
```

## Week 5-6: TReDS Integration

### 1. TReDS Service

```python
# Backend/app/services/treds_service.py

class TReDSService:
    """Service for TReDS invoice financing"""
    
    def upload_invoice(self, invoice_id: int, db: Session) -> Dict:
        """Upload invoice to TReDS platform"""
        # Get invoice details
        invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
        
        # Prepare TReDS payload
        treds_payload = {
            "invoice_no": invoice.invoice_number,
            "invoice_date": invoice.invoice_date.isoformat(),
            "invoice_amount": invoice.total_amount,
            "buyer_gstin": invoice.buyer_gstin,
            "seller_gstin": invoice.seller_gstin,
            "due_date": invoice.due_date.isoformat()
        }
        
        # Upload to TReDS (M1xchange example)
        response = requests.post(
            "https://api.m1xchange.com/v1/invoices/upload",
            json=treds_payload,
            headers={"Authorization": f"Bearer {self.api_key}"}
        )
        
        return response.json()
    
    def get_auction_status(self, treds_invoice_id: str) -> Dict:
        """Get auction status and bids"""
        # Implementation here
        pass
    
    def accept_bid(self, treds_invoice_id: str, bid_id: str) -> Dict:
        """Accept financing bid"""
        # Implementation here
        pass
```

## Testing Strategy

### Unit Tests

```python
# Backend/tests/test_gst_service.py

def test_generate_gstr1():
    """Test GSTR-1 generation"""
    # Create test invoices
    # Generate GSTR-1
    # Assert structure and values
    pass

def test_gst_reconciliation():
    """Test GST reconciliation"""
    # Create mismatched invoices
    # Run reconciliation
    # Assert mismatches detected
    pass
```

### Integration Tests

```python
# Backend/tests/test_gst_integration.py

def test_gst_filing_workflow():
    """Test complete GST filing workflow"""
    # 1. Create invoices
    # 2. Generate GSTR-1
    # 3. Review and approve
    # 4. File to GST Portal (mock)
    # 5. Verify status
    pass
```

## Deployment Checklist

- [ ] PostgreSQL database migrated
- [ ] Redis cache configured
- [ ] GST API credentials obtained
- [ ] E-invoice IRP credentials obtained
- [ ] TReDS platform credentials obtained
- [ ] Environment variables set
- [ ] Database migrations run
- [ ] Tests passing (80%+ coverage)
- [ ] Security audit completed
- [ ] Load testing completed
- [ ] Monitoring and alerts configured
- [ ] Documentation updated
- [ ] Beta testers onboarded

## Next Steps

After Phase 4 completion:
1. Gather feedback from beta testers
2. Fix bugs and improve UX
3. Start Phase 5 (Working Capital & Payments)
4. Begin CA partnership outreach
5. Launch marketing campaigns

