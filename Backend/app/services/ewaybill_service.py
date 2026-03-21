import math
import os
import uuid
from datetime import datetime, timedelta
from typing import Dict, List

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.models import EWayBill, Transporter, Order, Client
from app.utils.audit import log_audit_event

GOODS_VALUE_THRESHOLD = 50_000  # ₹50,000
MOCK_MODE = os.getenv("MOCK_GOVERNMENT_APIS", "true").lower() == "true"


class EWayBillService:

    @staticmethod
    def _compute_validity_days(distance_km: int, transport_mode: str) -> int:
        """
        Compute e-way bill validity in days.
        Road: max(1, ceil(distance_km / 200))
        Others: 1 day minimum
        """
        if transport_mode.lower() == "road":
            return max(1, math.ceil(distance_km / 200))
        return 1

    @staticmethod
    def generate_ewb(order_id: int, transporter_data: Dict, org_id: str, db: Session) -> Dict:
        """
        Generate an e-way bill for an order.
        transporter_data: {transporter_gstin, vehicle_number, transport_mode, distance_km}
        """
        order = db.query(Order).filter(Order.id == order_id).first()
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")

        goods_value = order.total_selling_price or 0

        # Check threshold
        if goods_value <= GOODS_VALUE_THRESHOLD:
            ewb = EWayBill(
                order_id=order_id,
                organization_id=org_id,
                status="not_required",
                distance_km=transporter_data.get("distance_km", 0),
                transport_mode=transporter_data.get("transport_mode", "road"),
            )
            db.add(ewb)
            db.commit()
            db.refresh(ewb)
            log_audit_event(
                db=db, action="CREATE", table_name="ewaybills",
                record_id=ewb.id, tenant_id=org_id,
                new_values={"status": "not_required", "reason": "goods_value_below_50000"},
            )
            return {
                "order_id": order_id,
                "status": "not_required",
                "message": "E-way bill not required: goods value \u2264 \u20b950,000",
            }

        transport_mode = transporter_data.get("transport_mode", "road")
        distance_km = int(transporter_data.get("distance_km", 1))
        validity_days = EWayBillService._compute_validity_days(distance_km, transport_mode)

        # Call NIC API or mock
        try:
            if MOCK_MODE:
                nic_response = EWayBillService._mock_nic_generate(order, transporter_data)
            else:
                nic_response = EWayBillService._call_nic_api(order, transporter_data)
        except Exception as e:
            raise HTTPException(status_code=502, detail=f"NIC API error: {str(e)}")

        generated_at = datetime.utcnow()
        valid_until = generated_at + timedelta(days=validity_days)

        ewb = EWayBill(
            order_id=order_id,
            organization_id=org_id,
            ewb_number=nic_response["ewb_number"],
            generated_at=generated_at,
            valid_until=valid_until,
            transporter_gstin=transporter_data.get("transporter_gstin"),
            vehicle_number=transporter_data.get("vehicle_number"),
            transport_mode=transport_mode,
            distance_km=distance_km,
            status="active",
        )
        db.add(ewb)
        db.commit()
        db.refresh(ewb)

        log_audit_event(
            db=db, action="CREATE", table_name="ewaybills",
            record_id=ewb.id, tenant_id=org_id,
            new_values={
                "ewb_number": ewb.ewb_number,
                "status": "active",
                "valid_until": valid_until.isoformat(),
            },
        )

        return {
            "order_id": order_id,
            "ewb_id": ewb.id,
            "ewb_number": ewb.ewb_number,
            "generated_at": generated_at.isoformat(),
            "valid_until": valid_until.isoformat(),
            "validity_days": validity_days,
            "status": "active",
        }

    @staticmethod
    def cancel_ewb(order_id: int, reason: str, org_id: str, db: Session) -> Dict:
        """Cancel an e-way bill. Only allowed within 24 hours of generation."""
        ewb = db.query(EWayBill).filter(
            EWayBill.order_id == order_id,
            EWayBill.status == "active",
        ).first()
        if not ewb:
            raise HTTPException(status_code=404, detail="No active e-way bill found for this order")

        if ewb.generated_at:
            deadline = ewb.generated_at + timedelta(hours=24)
            if datetime.utcnow() > deadline:
                raise HTTPException(
                    status_code=400,
                    detail=(
                        f"Cancellation window expired. E-way bill can only be cancelled within 24 hours. "
                        f"Deadline was {deadline.isoformat()}"
                    ),
                )

        try:
            if MOCK_MODE:
                pass  # Mock always succeeds
            else:
                EWayBillService._call_nic_cancel(ewb.ewb_number, reason)
        except Exception as e:
            raise HTTPException(status_code=502, detail=f"NIC cancellation error: {str(e)}")

        old_status = ewb.status
        ewb.status = "cancelled"
        ewb.cancellation_reason = reason
        db.commit()

        log_audit_event(
            db=db, action="UPDATE", table_name="ewaybills",
            record_id=ewb.id, tenant_id=org_id,
            old_values={"status": old_status},
            new_values={"status": "cancelled", "reason": reason},
        )

        return {
            "order_id": order_id,
            "ewb_number": ewb.ewb_number,
            "status": "cancelled",
            "reason": reason,
        }

    @staticmethod
    def get_ewb(order_id: int, org_id: str, db: Session) -> Dict:
        ewb = (
            db.query(EWayBill)
            .filter(
                EWayBill.order_id == order_id,
                EWayBill.organization_id == org_id,
            )
            .order_by(EWayBill.created_at.desc())
            .first()
        )
        if not ewb:
            return {"order_id": order_id, "status": "not_generated"}
        return {
            "id": ewb.id,
            "order_id": order_id,
            "ewb_number": ewb.ewb_number,
            "generated_at": ewb.generated_at.isoformat() if ewb.generated_at else None,
            "valid_until": ewb.valid_until.isoformat() if ewb.valid_until else None,
            "transporter_gstin": ewb.transporter_gstin,
            "vehicle_number": ewb.vehicle_number,
            "transport_mode": ewb.transport_mode,
            "distance_km": ewb.distance_km,
            "status": ewb.status,
            "cancellation_reason": ewb.cancellation_reason,
        }

    @staticmethod
    def check_expiring_ewbs(db: Session) -> List[Dict]:
        """Find EWayBills expiring within 6 hours. Called by Celery task."""
        now = datetime.utcnow()
        expiry_threshold = now + timedelta(hours=6)
        expiring = (
            db.query(EWayBill)
            .filter(
                EWayBill.status == "active",
                EWayBill.valid_until <= expiry_threshold,
                EWayBill.valid_until > now,
            )
            .all()
        )
        return [
            {
                "ewb_id": ewb.id,
                "order_id": ewb.order_id,
                "ewb_number": ewb.ewb_number,
                "valid_until": ewb.valid_until.isoformat(),
                "organization_id": ewb.organization_id,
            }
            for ewb in expiring
        ]

    @staticmethod
    def list_transporters(org_id: str, db: Session) -> List[Dict]:
        transporters = (
            db.query(Transporter)
            .filter(
                Transporter.organization_id == org_id,
                Transporter.is_active == True,
            )
            .all()
        )
        return [
            {
                "id": t.id,
                "name": t.name,
                "gstin": t.gstin,
                "vehicle_number": t.vehicle_number,
                "is_active": t.is_active,
            }
            for t in transporters
        ]

    @staticmethod
    def add_transporter(org_id: str, data: Dict, db: Session) -> Dict:
        transporter = Transporter(
            organization_id=org_id,
            name=data["name"],
            gstin=data.get("gstin"),
            vehicle_number=data.get("vehicle_number"),
            is_active=True,
        )
        db.add(transporter)
        db.commit()
        db.refresh(transporter)
        return {
            "id": transporter.id,
            "name": transporter.name,
            "gstin": transporter.gstin,
            "vehicle_number": transporter.vehicle_number,
        }

    @staticmethod
    def _mock_nic_generate(order: Order, transporter_data: Dict) -> Dict:
        ewb_number = f"EWB{uuid.uuid4().int % 10**12:012d}"
        return {"ewb_number": ewb_number, "status": "generated"}

    @staticmethod
    def _call_nic_api(order: Order, transporter_data: Dict) -> Dict:
        raise NotImplementedError(
            "Real NIC API not yet implemented. Set MOCK_GOVERNMENT_APIS=true."
        )

    @staticmethod
    def _call_nic_cancel(ewb_number: str, reason: str) -> Dict:
        raise NotImplementedError(
            "Real NIC cancellation API not yet implemented."
        )
