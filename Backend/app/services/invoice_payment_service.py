import io
import os
import hmac
import hashlib
from datetime import datetime, timedelta
from typing import Dict, List
from urllib.parse import urlencode

import razorpay
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.models import (
    InvoicePaymentLink, PaymentReminder, Order, Client, Ledger, Organization
)
from app.utils.audit import log_audit_event

# Razorpay client (lazy init)
_razorpay_client = None


def _get_razorpay_client():
    global _razorpay_client
    if _razorpay_client is None:
        key = os.getenv("RAZORPAY_KEY_ID")
        secret = os.getenv("RAZORPAY_KEY_SECRET")
        if key and secret:
            _razorpay_client = razorpay.Client(auth=(key, secret))
    return _razorpay_client


class InvoicePaymentService:

    @staticmethod
    def create_payment_link(order_id: int, org_id: str, db: Session) -> Dict:
        """Create a Razorpay payment link for an outstanding invoice."""
        order = db.query(Order).filter(Order.id == order_id).first()
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")

        if order.payment_status == "paid":
            raise HTTPException(status_code=409, detail="Order is already fully paid")

        outstanding = (order.total_selling_price or 0) - (order.amount_paid or 0)
        if outstanding <= 0:
            raise HTTPException(status_code=409, detail="No outstanding amount for this order")

        # Expire any existing active links
        existing_links = db.query(InvoicePaymentLink).filter(
            InvoicePaymentLink.order_id == order_id,
            InvoicePaymentLink.status == "created",
        ).all()
        for link in existing_links:
            link.status = "cancelled"

        expires_at = datetime.utcnow() + timedelta(hours=24)

        # Create Razorpay payment link
        rp = _get_razorpay_client()
        short_url = None
        razorpay_link_id = None

        if rp:
            try:
                client = db.query(Client).filter(Client.id == order.client_id).first()
                rp_link = rp.payment_link.create({
                    "amount": int(outstanding * 100),  # paise
                    "currency": "INR",
                    "description": f"Payment for Order {order.order_number}",
                    "customer": {
                        "name": order.customer_name,
                        "email": client.email if client else "",
                    },
                    "expire_by": int(expires_at.timestamp()),
                    "reminder_enable": False,
                    "notes": {"order_id": str(order_id), "org_id": org_id},
                })
                razorpay_link_id = rp_link.get("id")
                short_url = rp_link.get("short_url")
            except Exception as e:
                raise HTTPException(status_code=502, detail=f"Razorpay error: {str(e)}")
        else:
            # Mock for development
            razorpay_link_id = f"plink_mock_{order_id}_{int(datetime.utcnow().timestamp())}"
            short_url = f"https://rzp.io/mock/{razorpay_link_id}"

        payment_link = InvoicePaymentLink(
            order_id=order_id,
            organization_id=org_id,
            razorpay_link_id=razorpay_link_id,
            short_url=short_url,
            amount=outstanding,
            status="created",
            expires_at=expires_at,
        )
        db.add(payment_link)
        db.commit()
        db.refresh(payment_link)

        log_audit_event(
            db=db,
            action="CREATE",
            table_name="invoice_payment_links",
            record_id=payment_link.id,
            tenant_id=org_id,
            new_values={
                "order_id": order_id,
                "amount": outstanding,
                "razorpay_link_id": razorpay_link_id,
            },
        )

        # Send email to client (best-effort)
        try:
            client = db.query(Client).filter(Client.id == order.client_id).first()
            if client and client.email:
                from app.services.email_service import EmailService
                email_svc = EmailService()
                email_svc.send_email(
                    recipients=[client.email],
                    subject=f"Payment Request: Order {order.order_number}",
                    body=(
                        f"Dear {order.customer_name},\n\n"
                        f"Please pay \u20b9{outstanding:,.2f} for Order {order.order_number}.\n"
                        f"Payment Link: {short_url}\n"
                        f"This link expires in 24 hours.\n\nThank you."
                    ),
                )
        except Exception:
            pass  # Don't fail if email fails

        return {
            "payment_link_id": payment_link.id,
            "razorpay_link_id": razorpay_link_id,
            "short_url": short_url,
            "amount": outstanding,
            "expires_at": expires_at.isoformat(),
            "status": "created",
        }

    @staticmethod
    def get_payment_link(order_id: int, org_id: str, db: Session) -> Dict:
        """Get the most recent payment link for an order."""
        link = (
            db.query(InvoicePaymentLink)
            .filter(
                InvoicePaymentLink.order_id == order_id,
                InvoicePaymentLink.organization_id == org_id,
            )
            .order_by(InvoicePaymentLink.created_at.desc())
            .first()
        )
        if not link:
            return {"order_id": order_id, "status": "no_link"}
        return {
            "id": link.id,
            "order_id": order_id,
            "razorpay_link_id": link.razorpay_link_id,
            "short_url": link.short_url,
            "amount": link.amount,
            "status": link.status,
            "expires_at": link.expires_at.isoformat() if link.expires_at else None,
            "paid_at": link.paid_at.isoformat() if link.paid_at else None,
        }

    @staticmethod
    def generate_upi_qr(order_id: int, org_id: str, db: Session) -> bytes:
        """Generate a UPI QR code PNG for an order. Returns raw bytes."""
        try:
            import qrcode
        except ImportError:
            raise HTTPException(status_code=500, detail="qrcode library not installed")

        order = db.query(Order).filter(Order.id == order_id).first()
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")

        outstanding = (order.total_selling_price or 0) - (order.amount_paid or 0)

        # Get org UPI VPA
        org = db.query(Organization).filter(Organization.id == org_id).first()
        vpa = os.getenv("ORGANIZATION_UPI_VPA", "merchant@upi")
        payee_name = org.name if org else "Merchant"

        params = {
            "pa": vpa,
            "pn": payee_name,
            "am": f"{outstanding:.2f}",
            "tn": order.order_number or str(order_id),
            "cu": "INR",
        }
        upi_link = f"upi://pay?{urlencode(params)}"

        qr = qrcode.QRCode(version=1, box_size=10, border=4)
        qr.add_data(upi_link)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")

        buf = io.BytesIO()
        img.save(buf, format="PNG")
        return buf.getvalue()

    @staticmethod
    def reconcile_payment(
        razorpay_payment_id: str,
        order_id: int,
        amount: float,
        payment_timestamp: datetime,
        org_id: str,
        db: Session,
    ) -> Dict:
        """
        Reconcile a captured payment. Idempotent by razorpay_payment_id.
        """
        # Idempotency check
        existing_link = (
            db.query(InvoicePaymentLink)
            .filter(InvoicePaymentLink.razorpay_payment_id == razorpay_payment_id)
            .first()
        )
        if existing_link:
            return {
                "status": "already_processed",
                "order_id": order_id,
                "razorpay_payment_id": razorpay_payment_id,
            }

        order = db.query(Order).filter(Order.id == order_id).first()
        if not order:
            return {"status": "order_not_found", "order_id": order_id}

        # Update order payment
        order.amount_paid = (order.amount_paid or 0) + amount
        if order.amount_paid >= (order.total_selling_price or 0):
            order.payment_status = "paid"
        else:
            order.payment_status = "partial"

        # Update payment link record
        link = (
            db.query(InvoicePaymentLink)
            .filter(
                InvoicePaymentLink.order_id == order_id,
                InvoicePaymentLink.status == "created",
            )
            .order_by(InvoicePaymentLink.created_at.desc())
            .first()
        )
        if link:
            link.status = "paid"
            link.paid_at = payment_timestamp
            link.razorpay_payment_id = razorpay_payment_id

        # Create Ledger entry if fully paid
        if order.payment_status == "paid":
            ledger_entry = Ledger(
                client_id=order.client_id,
                ledger_type="receivable",
                party_name=order.customer_name,
                amount=order.total_selling_price,
                status="paid",
                payment_date=payment_timestamp,
                reference_type="order",
                reference_id=order_id,
                notes=f"Payment via Razorpay: {razorpay_payment_id}",
            )
            db.add(ledger_entry)

            # Cancel pending reminders
            db.query(PaymentReminder).filter(
                PaymentReminder.order_id == order_id,
                PaymentReminder.status == "pending",
            ).update({"status": "cancelled"})

        db.commit()

        log_audit_event(
            db=db,
            action="UPDATE",
            table_name="orders",
            record_id=order_id,
            tenant_id=org_id,
            new_values={
                "amount_paid": order.amount_paid,
                "payment_status": order.payment_status,
                "razorpay_payment_id": razorpay_payment_id,
            },
        )

        return {
            "status": "reconciled",
            "order_id": order_id,
            "razorpay_payment_id": razorpay_payment_id,
            "amount_paid": order.amount_paid,
            "payment_status": order.payment_status,
        }

    @staticmethod
    def get_payment_analytics(
        org_id: str, start_date: datetime, end_date: datetime, db: Session
    ) -> Dict:
        """Return payment analytics for the org within a date range."""
        orders = (
            db.query(Order)
            .join(Client, Order.client_id == Client.id)
            .filter(
                Client.organization_id == org_id,
                Order.order_date >= start_date,
                Order.order_date <= end_date,
                Order.status.in_(["invoiced", "completed"]),
            )
            .all()
        )

        total_invoiced = sum(o.total_selling_price or 0 for o in orders)
        total_collected = sum(o.amount_paid or 0 for o in orders)
        total_outstanding = total_invoiced - total_collected
        collection_rate = (
            (total_collected / total_invoiced * 100) if total_invoiced > 0 else 0
        )

        # Aging breakdown (by due_date)
        now = datetime.utcnow()
        aging: Dict[str, float] = {"0-30": 0, "31-60": 0, "61-90": 0, "90+": 0}
        for order in orders:
            if order.payment_status == "paid":
                continue
            outstanding = (order.total_selling_price or 0) - (order.amount_paid or 0)
            if outstanding <= 0:
                continue
            if order.due_date and now > order.due_date:
                days_overdue = (now - order.due_date).days
                if days_overdue <= 30:
                    aging["0-30"] += outstanding
                elif days_overdue <= 60:
                    aging["31-60"] += outstanding
                elif days_overdue <= 90:
                    aging["61-90"] += outstanding
                else:
                    aging["90+"] += outstanding

        # Daily collections time-series
        daily_collections: Dict[str, float] = {}
        for order in orders:
            if order.amount_paid and order.amount_paid > 0:
                day_key = (
                    order.order_date.strftime("%Y-%m-%d")
                    if order.order_date
                    else "unknown"
                )
                daily_collections[day_key] = (
                    daily_collections.get(day_key, 0) + (order.amount_paid or 0)
                )
        daily_series = [
            {"date": k, "amount": round(v, 2)}
            for k, v in sorted(daily_collections.items())
        ]

        # Top 10 customers by outstanding
        customer_outstanding: Dict[str, float] = {}
        for order in orders:
            outstanding = (order.total_selling_price or 0) - (order.amount_paid or 0)
            if outstanding > 0:
                customer_outstanding[order.customer_name] = (
                    customer_outstanding.get(order.customer_name, 0) + outstanding
                )
        top_10 = sorted(
            customer_outstanding.items(), key=lambda x: x[1], reverse=True
        )[:10]

        return {
            "total_invoiced": round(total_invoiced, 2),
            "total_collected": round(total_collected, 2),
            "total_outstanding": round(total_outstanding, 2),
            "collection_rate": round(collection_rate, 2),
            "aging_breakdown": {k: round(v, 2) for k, v in aging.items()},
            "daily_collections": daily_series,
            "top_customers_by_outstanding": [
                {"customer_name": name, "outstanding": round(amount, 2)}
                for name, amount in top_10
            ],
        }
