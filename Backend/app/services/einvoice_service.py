import os
import uuid
import hashlib
from datetime import datetime, timedelta
from typing import Dict
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.models import EInvoice, Order, OrderItem, Product, GSTConfiguration, HSNSACMaster, Client
from app.utils.audit import log_audit_event

TURNOVER_THRESHOLD = 50_000_000  # ₹5 crore
MOCK_MODE = os.getenv("MOCK_GOVERNMENT_APIS", "true").lower() == "true"


class EInvoiceService:

    @staticmethod
    def generate_irn(order_id: int, org_id: str, db: Session) -> Dict:
        """
        Generate IRN for an order. Idempotent — returns existing IRN if already generated.
        """
        order = db.query(Order).filter(Order.id == order_id).first()
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")

        # Idempotency guard
        existing = db.query(EInvoice).filter(EInvoice.order_id == order_id).first()
        if existing and existing.status == "generated":
            return {
                "order_id": order_id,
                "irn": existing.irn,
                "ack_no": existing.ack_no,
                "ack_date": existing.ack_date.isoformat() if existing.ack_date else None,
                "status": existing.status,
                "message": "IRN already generated (idempotent response)",
            }

        # Check turnover threshold
        client = db.query(Client).filter(Client.id == order.client_id).first()
        annual_revenue = (client.annual_revenue or 0) if client else 0
        if annual_revenue < TURNOVER_THRESHOLD:
            einvoice = existing or EInvoice(order_id=order_id, organization_id=org_id)
            einvoice.status = "not_applicable"
            if not existing:
                db.add(einvoice)
            db.commit()
            log_audit_event(
                db=db,
                action="CREATE",
                table_name="einvoices",
                record_id=einvoice.id,
                tenant_id=org_id,
                new_values={"status": "not_applicable", "reason": "below_turnover_threshold"},
            )
            return {
                "order_id": order_id,
                "status": "not_applicable",
                "message": "E-invoicing not applicable: annual turnover below ₹5 crore threshold",
            }

        # Build IRP payload
        payload = EInvoiceService._build_irp_payload(order_id, db)

        # Call IRP API (or mock)
        try:
            if MOCK_MODE:
                irp_response = EInvoiceService._mock_irp_generate(payload)
            else:
                irp_response = EInvoiceService._call_irp_api(payload)
        except Exception as e:
            einvoice = existing or EInvoice(order_id=order_id, organization_id=org_id)
            einvoice.status = "failed"
            einvoice.error_message = str(e)
            if not existing:
                db.add(einvoice)
            db.commit()
            log_audit_event(
                db=db,
                action="CREATE",
                table_name="einvoices",
                record_id=einvoice.id,
                tenant_id=org_id,
                new_values={"status": "failed", "error": str(e)},
            )
            raise HTTPException(status_code=502, detail=f"IRP API error: {str(e)}")

        # Store success
        einvoice = existing or EInvoice(order_id=order_id, organization_id=org_id)
        einvoice.irn = irp_response["Irn"]
        einvoice.ack_no = irp_response["AckNo"]
        einvoice.ack_date = (
            datetime.fromisoformat(irp_response["AckDt"])
            if irp_response.get("AckDt")
            else datetime.utcnow()
        )
        einvoice.signed_qr_code = irp_response.get("SignedQRCode", "")
        einvoice.status = "generated"
        einvoice.error_message = None
        if not existing:
            db.add(einvoice)
        db.commit()
        db.refresh(einvoice)

        log_audit_event(
            db=db,
            action="CREATE",
            table_name="einvoices",
            record_id=einvoice.id,
            tenant_id=org_id,
            new_values={"status": "generated", "irn": einvoice.irn, "ack_no": einvoice.ack_no},
        )

        return {
            "order_id": order_id,
            "irn": einvoice.irn,
            "ack_no": einvoice.ack_no,
            "ack_date": einvoice.ack_date.isoformat(),
            "signed_qr_code": einvoice.signed_qr_code,
            "status": "generated",
        }

    @staticmethod
    def cancel_irn(order_id: int, reason: str, org_id: str, db: Session) -> Dict:
        """
        Cancel an IRN. Only allowed within 24 hours of ack_date.
        """
        einvoice = db.query(EInvoice).filter(EInvoice.order_id == order_id).first()
        if not einvoice or einvoice.status != "generated":
            raise HTTPException(status_code=404, detail="No active e-invoice found for this order")

        # 24-hour window check
        if einvoice.ack_date:
            deadline = einvoice.ack_date + timedelta(hours=24)
            if datetime.utcnow() > deadline:
                raise HTTPException(
                    status_code=400,
                    detail=(
                        f"Cancellation window expired. IRN can only be cancelled within 24 hours "
                        f"of acknowledgement. Deadline was {deadline.isoformat()}"
                    ),
                )

        # Call IRP cancellation (or mock)
        try:
            if MOCK_MODE:
                _cancel_response = {"status": "cancelled", "CancelDate": datetime.utcnow().isoformat()}
            else:
                _cancel_response = EInvoiceService._call_irp_cancel(einvoice.irn, reason)
        except Exception as e:
            log_audit_event(
                db=db,
                action="UPDATE",
                table_name="einvoices",
                record_id=einvoice.id,
                tenant_id=org_id,
                new_values={"cancellation_attempt": "failed", "error": str(e)},
            )
            raise HTTPException(status_code=502, detail=f"IRP cancellation error: {str(e)}")

        old_status = einvoice.status
        einvoice.status = "cancelled"
        einvoice.cancellation_reason = reason
        einvoice.cancelled_at = datetime.utcnow()

        # Reset order status to 'invoiced' to allow re-invoicing
        order = db.query(Order).filter(Order.id == order_id).first()
        if order:
            order.status = "invoiced"

        db.commit()

        log_audit_event(
            db=db,
            action="UPDATE",
            table_name="einvoices",
            record_id=einvoice.id,
            tenant_id=org_id,
            old_values={"status": old_status},
            new_values={"status": "cancelled", "reason": reason},
        )

        return {
            "order_id": order_id,
            "irn": einvoice.irn,
            "status": "cancelled",
            "cancelled_at": einvoice.cancelled_at.isoformat(),
            "reason": reason,
        }

    @staticmethod
    def get_einvoice(order_id: int, org_id: str, db: Session) -> Dict:
        einvoice = db.query(EInvoice).filter(
            EInvoice.order_id == order_id,
            EInvoice.organization_id == org_id,
        ).first()
        if not einvoice:
            return {"order_id": order_id, "status": "not_generated"}
        return {
            "id": einvoice.id,
            "order_id": order_id,
            "irn": einvoice.irn,
            "ack_no": einvoice.ack_no,
            "ack_date": einvoice.ack_date.isoformat() if einvoice.ack_date else None,
            "signed_qr_code": einvoice.signed_qr_code,
            "status": einvoice.status,
            "error_message": einvoice.error_message,
            "cancelled_at": einvoice.cancelled_at.isoformat() if einvoice.cancelled_at else None,
            "cancellation_reason": einvoice.cancellation_reason,
        }

    @staticmethod
    def _build_irp_payload(order_id: int, db: Session) -> Dict:
        """Construct IRP schema v1.1 JSON payload."""
        order = db.query(Order).filter(Order.id == order_id).first()
        items = db.query(OrderItem).filter(OrderItem.order_id == order_id).all()
        gst_config = db.query(GSTConfiguration).filter(
            GSTConfiguration.client_id == order.client_id,
            GSTConfiguration.is_active == True,
        ).first()

        seller_gstin = gst_config.gstin if gst_config else "00AAAAA0000A1Z5"
        seller_name = gst_config.legal_name if gst_config else "Seller"

        item_list = []
        for idx, item in enumerate(items, 1):
            product = db.query(Product).filter(Product.id == item.product_id).first()
            hsn = (
                db.query(HSNSACMaster).filter(
                    HSNSACMaster.id == product.hsn_sac_id
                ).first()
                if product and product.hsn_sac_id
                else None
            )
            hsn_code = hsn.code if hsn else "9997"
            igst_rate = hsn.igst_rate if hsn else 18
            total_price = item.total_selling_price or 0
            taxable = total_price / (1 + igst_rate / 100) if igst_rate else total_price
            item_list.append({
                "SlNo": str(idx),
                "PrdDesc": product.name if product else "Product",
                "IsServc": "N",
                "HsnCd": hsn_code,
                "Qty": item.quantity,
                "Unit": product.unit if product else "NOS",
                "UnitPrice": round(item.unit_selling_price or 0, 2),
                "TotAmt": round(total_price, 2),
                "AssAmt": round(taxable, 2),
                "GstRt": igst_rate,
                "IgstAmt": round(taxable * igst_rate / 100, 2),
                "CgstAmt": round(taxable * (igst_rate / 2) / 100, 2),
                "SgstAmt": round(taxable * (igst_rate / 2) / 100, 2),
                "TotItemVal": round(total_price, 2),
            })

        return {
            "Version": "1.1",
            "TranDtls": {"TaxSch": "GST", "SupTyp": "B2B", "RegRev": "N"},
            "DocDtls": {
                "Typ": "INV",
                "No": order.order_number or str(order.id),
                "Dt": (
                    order.order_date.strftime("%d/%m/%Y")
                    if order.order_date
                    else datetime.utcnow().strftime("%d/%m/%Y")
                ),
            },
            "SellerDtls": {
                "Gstin": seller_gstin,
                "LglNm": seller_name,
                "Addr1": "Address Line 1",
                "Loc": "City",
                "Pin": 110001,
                "Stcd": seller_gstin[:2],
            },
            "BuyerDtls": {
                "Gstin": "URP",
                "LglNm": order.customer_name,
                "Pos": seller_gstin[:2],
                "Addr1": "Buyer Address",
                "Loc": "City",
                "Pin": 110001,
                "Stcd": seller_gstin[:2],
            },
            "ItemList": item_list,
            "ValDtls": {
                "AssVal": round(sum(i["AssAmt"] for i in item_list), 2),
                "IgstVal": round(sum(i["IgstAmt"] for i in item_list), 2),
                "CgstVal": round(sum(i["CgstAmt"] for i in item_list), 2),
                "SgstVal": round(sum(i["SgstAmt"] for i in item_list), 2),
                "TotInvVal": round(order.total_selling_price or 0, 2),
            },
        }

    @staticmethod
    def _mock_irp_generate(payload: Dict) -> Dict:
        """Return a realistic mock IRP response."""
        irn = hashlib.sha256(
            f"{payload['DocDtls']['No']}{payload['SellerDtls']['Gstin']}{datetime.utcnow().isoformat()}".encode()
        ).hexdigest()[:64]
        ack_no = f"11{uuid.uuid4().int % 10**16:016d}"
        return {
            "Irn": irn,
            "AckNo": ack_no,
            "AckDt": datetime.utcnow().isoformat(),
            "SignedQRCode": f"MOCK_QR_{irn[:16]}",
            "Status": "1",
        }

    @staticmethod
    def _call_irp_api(payload: Dict) -> Dict:
        """Call real IRP API. Placeholder for production implementation."""
        raise NotImplementedError(
            "Real IRP API integration not yet implemented. Set MOCK_GOVERNMENT_APIS=true for development."
        )

    @staticmethod
    def _call_irp_cancel(irn: str, reason: str) -> Dict:
        """Call real IRP cancellation API. Placeholder for production."""
        raise NotImplementedError("Real IRP cancellation API not yet implemented.")
