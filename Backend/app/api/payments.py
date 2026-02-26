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

# Initialize Razorpay
razorpay_client = razorpay.Client(
    auth=(os.getenv("RAZORPAY_KEY_ID"), os.getenv("RAZORPAY_KEY_SECRET"))
)

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
