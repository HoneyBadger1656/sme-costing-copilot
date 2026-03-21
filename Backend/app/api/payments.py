from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
import razorpay
import os
import hmac
import hashlib

from app.core.database import get_db
from app.models.models import Organization, User
from app.api.auth import get_current_user
from pydantic import BaseModel

router = APIRouter()

# Initialize Razorpay (may be None if keys not configured)
razorpay_client = None
try:
    rp_key = os.getenv("RAZORPAY_KEY_ID")
    rp_secret = os.getenv("RAZORPAY_KEY_SECRET")
    if rp_key and rp_secret:
        razorpay_client = razorpay.Client(auth=(rp_key, rp_secret))
except Exception:
    pass

# Schemas
class SubscriptionCreate(BaseModel):
    plan: str  # starter, growth, pro

class SubscriptionResponse(BaseModel):
    subscription_id: str
    plan_id: str
    status: str
    short_url: str

# Endpoints
@router.post("/create-subscription", response_model=SubscriptionResponse)
def create_subscription(
    request: SubscriptionCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Plan mapping
    plans = {
        "starter": {
            "amount": 99900,  # ₹999 in paise
            "period": "monthly",
            "interval": 1
        },
        "growth": {
            "amount": 249900,  # ₹2,499 in paise
            "period": "monthly",
            "interval": 1
        },
        "pro": {
            "amount": 499900,  # ₹4,999 in paise
            "period": "monthly",
            "interval": 1
        }
    }
    
    if request.plan not in plans:
        raise HTTPException(status_code=400, detail="Invalid plan")
    
    plan_config = plans[request.plan]
    
    # Create or get Razorpay plan
    try:
        # Create plan if doesn't exist
        plan = razorpay_client.plan.create({
            "period": plan_config["period"],
            "interval": plan_config["interval"],
            "item": {
                "name": f"SME Copilot {request.plan.title()} Plan",
                "amount": plan_config["amount"],
                "currency": "INR"
            }
        })
        
        # Create subscription
        subscription = razorpay_client.subscription.create({
            "plan_id": plan["id"],
            "total_count": 12,  # 12 months
            "customer_notify": 1,
            "notes": {
                "organization_id": str(current_user.organization_id),
                "user_id": str(current_user.id)
            }
        })
        
        # Update organization
        org = db.query(Organization).filter(
            Organization.id == current_user.organization_id
        ).first()
        org.subscription_plan = request.plan
        org.subscription_status = "pending"
        db.commit()
        
        return {
            "subscription_id": subscription["id"],
            "plan_id": plan["id"],
            "status": subscription["status"],
            "short_url": subscription["short_url"]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/webhook")
async def razorpay_webhook(request: Request, db: Session = Depends(get_db)):
    # Get request body
    body = await request.body()
    
    # Verify webhook signature
    signature = request.headers.get("X-Razorpay-Signature")
    webhook_secret = os.getenv("RAZORPAY_WEBHOOK_SECRET")
    
    # Verify
    expected_signature = hmac.new(
        webhook_secret.encode(),
        body,
        hashlib.sha256
    ).hexdigest()
    
    if signature != expected_signature:
        raise HTTPException(status_code=400, detail="Invalid signature")
    
    # Process event
    event = await request.json()
    
    if event["event"] == "subscription.charged":
        # Payment successful
        org_id = event["payload"]["subscription"]["entity"]["notes"]["organization_id"]
        
        org = db.query(Organization).filter(Organization.id == org_id).first()
        if org:
            org.subscription_status = "active"
            db.commit()
    
    elif event["event"] == "subscription.cancelled":
        # Subscription cancelled
        org_id = event["payload"]["subscription"]["entity"]["notes"]["organization_id"]
        
        org = db.query(Organization).filter(Organization.id == org_id).first()
        if org:
            org.subscription_status = "cancelled"
            db.commit()
    
    return {"status": "ok"}

@router.get("/subscription-status")
def get_subscription_status(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    org = db.query(Organization).filter(
        Organization.id == current_user.organization_id
    ).first()
    
    return {
        "plan": org.subscription_plan,
        "status": org.subscription_status,
        "trial_active": org.subscription_status == "trial"
    }


# ── Invoice Payment endpoints (Task 10) ───────────────────────────────────────
from fastapi.responses import Response
from datetime import datetime, date
from app.services.invoice_payment_service import InvoicePaymentService

@router.post("/invoice-link/{order_id}")
def create_invoice_payment_link(
    order_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    from app.utils.rbac import require_role
    require_role(current_user, ["accountant", "admin", "owner"])
    return InvoicePaymentService.create_payment_link(order_id, db)


@router.get("/invoice-link/{order_id}")
def get_invoice_payment_link(
    order_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    from app.utils.rbac import require_role
    require_role(current_user, ["viewer", "accountant", "admin", "owner"])
    return InvoicePaymentService.get_payment_link(order_id, db)


@router.post("/upi-qr/{order_id}")
def generate_upi_qr(
    order_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    from app.utils.rbac import require_role
    require_role(current_user, ["accountant", "admin", "owner"])
    qr_bytes = InvoicePaymentService.generate_upi_qr(order_id, db)
    return Response(content=qr_bytes, media_type="image/png")


@router.get("/analytics")
def get_payment_analytics(
    start_date: date = None,
    end_date: date = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    from app.utils.rbac import require_role
    require_role(current_user, ["accountant", "admin", "owner"])
    start = datetime.combine(start_date, datetime.min.time()) if start_date else None
    end = datetime.combine(end_date, datetime.max.time()) if end_date else None
    return InvoicePaymentService.get_payment_analytics(
        current_user.organization_id, start, end, db
    )


@router.post("/invoice-webhook")
async def invoice_payment_webhook(request: Request, db: Session = Depends(get_db)):
    """Razorpay webhook for payment.captured events — HMAC verified."""
    body = await request.body()
    signature = request.headers.get("X-Razorpay-Signature", "")
    webhook_secret = os.getenv("RAZORPAY_WEBHOOK_SECRET", "")

    if webhook_secret:
        expected = hmac.new(
            webhook_secret.encode(), body, hashlib.sha256
        ).hexdigest()
        if not hmac.compare_digest(signature, expected):
            raise HTTPException(status_code=400, detail="Invalid webhook signature")

    import json as _json
    event = _json.loads(body)

    if event.get("event") == "payment.captured":
        payment_entity = event["payload"]["payment"]["entity"]
        payment_id = payment_entity["id"]
        order_id_str = payment_entity.get("notes", {}).get("order_id")
        amount_paise = payment_entity.get("amount", 0)
        if order_id_str:
            InvoicePaymentService.reconcile_payment(
                razorpay_payment_id=payment_id,
                order_id=int(order_id_str),
                amount=amount_paise / 100,
                db=db,
            )

    return {"status": "ok"}
