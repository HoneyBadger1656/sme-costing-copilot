"""
GST Service Layer — GSTR-1/3B generation, ITC reconciliation, compliance calendar.
"""
from __future__ import annotations

import calendar
import re
from datetime import date, datetime, timedelta
from typing import Dict, List, Tuple

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.models import (
    Client,
    GSTConfiguration,
    GSTReconciliation,
    GSTReturn,
    HSNSACMaster,
    Ledger,
    Order,
    OrderItem,
    Product,
)
from app.utils.audit import log_audit_event, get_model_dict


class GSTService:
    # ------------------------------------------------------------------
    # 1. GSTIN Validation
    # ------------------------------------------------------------------

    @staticmethod
    def validate_gstin(gstin: str) -> Tuple[bool, str]:
        """
        Validate a 15-character GSTIN.

        Format: SS PPPPPPPPPX E Z C
          SS  — state code (01–37)
          PPPPPPPPPX — PAN (5 alpha + 4 numeric + 1 alpha)
          E  — entity code (alphanumeric)
          Z  — always literal 'Z'
          C  — check digit (alphanumeric)

        Returns (True, "") on success or (False, "<error description>") on failure.
        """
        if not isinstance(gstin, str) or len(gstin) != 15:
            return False, "GSTIN must be exactly 15 characters"

        gstin = gstin.upper()

        # Positions 1-2: state code numeric 01-37
        state_code = gstin[0:2]
        if not state_code.isdigit() or not (1 <= int(state_code) <= 37):
            return False, f"Invalid state code '{state_code}': must be numeric between 01 and 37"

        # Positions 3-7: first 5 chars of PAN — alphabetic
        pan_alpha1 = gstin[2:7]
        if not pan_alpha1.isalpha():
            return False, f"Invalid PAN segment (positions 3-7) '{pan_alpha1}': must be 5 alphabetic characters"

        # Positions 8-11: next 4 chars of PAN — numeric
        pan_numeric = gstin[7:11]
        if not pan_numeric.isdigit():
            return False, f"Invalid PAN segment (positions 8-11) '{pan_numeric}': must be 4 numeric digits"

        # Position 12: last char of PAN — alphabetic
        pan_alpha2 = gstin[11]
        if not pan_alpha2.isalpha():
            return False, f"Invalid PAN segment (position 12) '{pan_alpha2}': must be 1 alphabetic character"

        # Position 13: entity code — alphanumeric
        entity_code = gstin[12]
        if not entity_code.isalnum():
            return False, f"Invalid entity code (position 13) '{entity_code}': must be alphanumeric"

        # Position 14: must be 'Z'
        if gstin[13] != "Z":
            return False, f"Invalid character at position 14 '{gstin[13]}': must be 'Z'"

        # Position 15: check digit — alphanumeric
        check_digit = gstin[14]
        if not check_digit.isalnum():
            return False, f"Invalid check digit (position 15) '{check_digit}': must be alphanumeric"

        return True, ""

    # ------------------------------------------------------------------
    # 2. GSTR-1 Generation
    # ------------------------------------------------------------------

    @staticmethod
    def generate_gstr1(
        client_id: int, period: str, org_id: str, db: Session
    ) -> Dict:
        """
        Compile all invoiced/completed Orders for the period into a GSTR-1 return.

        period format: MMYYYY  e.g. "012025"
        """
        # Parse period
        try:
            mm = int(period[:2])
            yyyy = int(period[2:])
            start_date = datetime(yyyy, mm, 1)
            last_day = calendar.monthrange(yyyy, mm)[1]
            end_date = datetime(yyyy, mm, last_day, 23, 59, 59)
        except (ValueError, IndexError):
            raise HTTPException(status_code=400, detail=f"Invalid period format '{period}': expected MMYYYY")

        # Get GST config for client
        gst_config = (
            db.query(GSTConfiguration)
            .filter(
                GSTConfiguration.client_id == client_id,
                GSTConfiguration.organization_id == org_id,
                GSTConfiguration.is_active == True,
            )
            .first()
        )
        client_gstin = gst_config.gstin if gst_config else ""
        client_state_code = gst_config.state_code if gst_config else "00"

        # Query orders for the period
        orders = (
            db.query(Order)
            .filter(
                Order.client_id == client_id,
                Order.status.in_(["invoiced", "completed"]),
                Order.order_date >= start_date,
                Order.order_date <= end_date,
            )
            .all()
        )

        b2b_invoices: List[Dict] = []
        b2cs_invoices: List[Dict] = []
        b2cl_invoices: List[Dict] = []
        hsn_summary: Dict[str, Dict] = {}
        validation_report: List[Dict] = []

        for order in orders:
            items = (
                db.query(OrderItem)
                .filter(OrderItem.order_id == order.id)
                .all()
            )

            order_lines = []
            order_valid = True

            for item in items:
                product = db.query(Product).filter(Product.id == item.product_id).first()
                if not product or not product.hsn_sac_id:
                    validation_report.append({
                        "order_id": order.id,
                        "order_number": order.order_number,
                        "issue": "Missing HSN/SAC code on product",
                        "product_id": item.product_id,
                    })
                    order_valid = False
                    continue

                hsn = db.query(HSNSACMaster).filter(HSNSACMaster.id == product.hsn_sac_id).first()
                if not hsn:
                    validation_report.append({
                        "order_id": order.id,
                        "order_number": order.order_number,
                        "issue": "HSN/SAC master record not found",
                        "hsn_sac_id": product.hsn_sac_id,
                    })
                    order_valid = False
                    continue

                line_total = item.total_selling_price or 0
                igst_rate = hsn.igst_rate or 0
                cgst_rate = hsn.cgst_rate or 0
                sgst_rate = hsn.sgst_rate or 0

                # Back-calculate taxable value from inclusive price
                taxable_value = line_total / (1 + igst_rate / 100) if igst_rate else line_total
                cgst = taxable_value * cgst_rate / 100
                sgst = taxable_value * sgst_rate / 100
                igst = taxable_value * igst_rate / 100

                order_lines.append({
                    "hsn_code": hsn.code,
                    "description": product.name,
                    "quantity": item.quantity,
                    "unit": product.unit,
                    "taxable_value": round(taxable_value, 2),
                    "cgst_rate": cgst_rate,
                    "sgst_rate": sgst_rate,
                    "igst_rate": igst_rate,
                    "cgst": round(cgst, 2),
                    "sgst": round(sgst, 2),
                    "igst": round(igst, 2),
                })

                # Accumulate HSN summary
                if hsn.code not in hsn_summary:
                    hsn_summary[hsn.code] = {
                        "hsn_code": hsn.code,
                        "description": hsn.description,
                        "uqc": product.unit,
                        "total_quantity": 0,
                        "total_value": 0,
                        "taxable_value": 0,
                        "cgst": 0,
                        "sgst": 0,
                        "igst": 0,
                    }
                hsn_summary[hsn.code]["total_quantity"] += item.quantity
                hsn_summary[hsn.code]["total_value"] += line_total
                hsn_summary[hsn.code]["taxable_value"] += round(taxable_value, 2)
                hsn_summary[hsn.code]["cgst"] += round(cgst, 2)
                hsn_summary[hsn.code]["sgst"] += round(sgst, 2)
                hsn_summary[hsn.code]["igst"] += round(igst, 2)

            if not order_valid or not order_lines:
                continue

            order_total = order.total_selling_price or 0
            order_taxable = sum(l["taxable_value"] for l in order_lines)
            order_cgst = sum(l["cgst"] for l in order_lines)
            order_sgst = sum(l["sgst"] for l in order_lines)
            order_igst = sum(l["igst"] for l in order_lines)

            # Determine B2B vs B2C classification
            # Check if buyer has GSTIN via GSTConfiguration
            buyer_config = (
                db.query(GSTConfiguration)
                .filter(
                    GSTConfiguration.client_id == client_id,
                    GSTConfiguration.organization_id == org_id,
                    GSTConfiguration.is_active == True,
                )
                .first()
            )
            # For simplicity: if the order's client has a GST config with a GSTIN, treat as B2B
            # Otherwise classify by amount
            buyer_gstin = buyer_config.gstin if buyer_config else None

            invoice_entry = {
                "order_id": order.id,
                "order_number": order.order_number,
                "invoice_date": order.order_date.strftime("%d-%m-%Y") if order.order_date else "",
                "customer_name": order.customer_name,
                "taxable_value": round(order_taxable, 2),
                "cgst": round(order_cgst, 2),
                "sgst": round(order_sgst, 2),
                "igst": round(order_igst, 2),
                "total_value": round(order_total, 2),
                "items": order_lines,
            }

            if buyer_gstin:
                invoice_entry["buyer_gstin"] = buyer_gstin
                b2b_invoices.append(invoice_entry)
            elif order_total > 250000:
                invoice_entry["state_code"] = client_state_code
                b2cl_invoices.append(invoice_entry)
            else:
                invoice_entry["state_code"] = client_state_code
                b2cs_invoices.append(invoice_entry)

        # Aggregate B2CS by state
        b2cs_by_state: Dict[str, Dict] = {}
        for inv in b2cs_invoices:
            sc = inv.get("state_code", "00")
            if sc not in b2cs_by_state:
                b2cs_by_state[sc] = {
                    "state_code": sc,
                    "taxable_value": 0,
                    "cgst": 0,
                    "sgst": 0,
                    "igst": 0,
                    "invoices": [],
                }
            b2cs_by_state[sc]["taxable_value"] += inv["taxable_value"]
            b2cs_by_state[sc]["cgst"] += inv["cgst"]
            b2cs_by_state[sc]["sgst"] += inv["sgst"]
            b2cs_by_state[sc]["igst"] += inv["igst"]
            b2cs_by_state[sc]["invoices"].append(inv)

        json_data = {
            "gstin": client_gstin,
            "fp": period,
            "b2b": b2b_invoices,
            "b2cs": list(b2cs_by_state.values()),
            "b2cl": b2cl_invoices,
            "exp": [],
            "nil": [],
            "hsn": {"data": list(hsn_summary.values())},
        }

        # Store in GSTReturn
        gst_return = GSTReturn(
            client_id=client_id,
            organization_id=org_id,
            return_type="GSTR1",
            period=period,
            filing_status="draft",
            return_data=json_data,
        )
        db.add(gst_return)
        db.commit()
        db.refresh(gst_return)

        # Audit log
        log_audit_event(
            db=db,
            action="CREATE",
            table_name="gst_returns",
            record_id=gst_return.id,
            tenant_id=org_id,
            new_values={"return_type": "GSTR1", "period": period, "filing_status": "draft"},
        )

        return {
            "return_id": gst_return.id,
            "filing_status": "draft",
            "return_data": json_data,
            "validation_report": validation_report,
        }

    # ------------------------------------------------------------------
    # 3. GSTR-3B Generation
    # ------------------------------------------------------------------

    @staticmethod
    def generate_gstr3b(
        client_id: int, period: str, org_id: str, db: Session
    ) -> Dict:
        """
        Generate GSTR-3B for a period. Requires GSTR-1 to exist first.
        """
        # Check GSTR-1 exists
        gstr1 = (
            db.query(GSTReturn)
            .filter(
                GSTReturn.client_id == client_id,
                GSTReturn.organization_id == org_id,
                GSTReturn.return_type == "GSTR1",
                GSTReturn.period == period,
            )
            .first()
        )
        if not gstr1:
            raise HTTPException(
                status_code=400,
                detail=f"GSTR-1 for period {period} must be generated before GSTR-3B",
            )

        # Get GST config
        gst_config = (
            db.query(GSTConfiguration)
            .filter(
                GSTConfiguration.client_id == client_id,
                GSTConfiguration.organization_id == org_id,
                GSTConfiguration.is_active == True,
            )
            .first()
        )
        client_gstin = gst_config.gstin if gst_config else ""

        # Sum output tax from GSTR-1 data
        return_data = gstr1.return_data or {}
        total_cgst = 0.0
        total_sgst = 0.0
        total_igst = 0.0
        total_taxable = 0.0

        def _sum_section(invoices: List[Dict]) -> None:
            nonlocal total_cgst, total_sgst, total_igst, total_taxable
            for inv in invoices:
                total_cgst += inv.get("cgst", 0)
                total_sgst += inv.get("sgst", 0)
                total_igst += inv.get("igst", 0)
                total_taxable += inv.get("taxable_value", 0)

        _sum_section(return_data.get("b2b", []))
        for state_entry in return_data.get("b2cs", []):
            total_cgst += state_entry.get("cgst", 0)
            total_sgst += state_entry.get("sgst", 0)
            total_igst += state_entry.get("igst", 0)
            total_taxable += state_entry.get("taxable_value", 0)
        _sum_section(return_data.get("b2cl", []))

        # Get reconciled ITC
        reconciliation = (
            db.query(GSTReconciliation)
            .filter(
                GSTReconciliation.client_id == client_id,
                GSTReconciliation.organization_id == org_id,
                GSTReconciliation.period == period,
            )
            .order_by(GSTReconciliation.created_at.desc())
            .first()
        )
        eligible_itc = 0.0
        if reconciliation and reconciliation.reconciliation_result:
            eligible_itc = reconciliation.reconciliation_result.get("matched_itc", 0) or 0.0

        net_gst_payable = (total_cgst + total_sgst + total_igst) - eligible_itc
        cgst_payable = max(0, total_cgst - eligible_itc / 3)
        sgst_payable = max(0, total_sgst - eligible_itc / 3)
        igst_payable = max(0, total_igst - eligible_itc / 3)

        json_data = {
            "gstin": client_gstin,
            "fp": period,
            "sup_details": {
                "osup_det": {
                    "txval": round(total_taxable, 2),
                    "iamt": round(total_igst, 2),
                    "camt": round(total_cgst, 2),
                    "samt": round(total_sgst, 2),
                }
            },
            "itc_elg": {
                "itc_avl": [{"ty": "IMPG", "iamt": round(eligible_itc, 2)}]
            },
            "intr_ltfee": {},
            "tt_val": {
                "camt": round(cgst_payable, 2),
                "samt": round(sgst_payable, 2),
                "iamt": round(igst_payable, 2),
            },
        }

        gst_return = GSTReturn(
            client_id=client_id,
            organization_id=org_id,
            return_type="GSTR3B",
            period=period,
            filing_status="draft",
            return_data=json_data,
        )
        db.add(gst_return)
        db.commit()
        db.refresh(gst_return)

        log_audit_event(
            db=db,
            action="CREATE",
            table_name="gst_returns",
            record_id=gst_return.id,
            tenant_id=org_id,
            new_values={"return_type": "GSTR3B", "period": period, "filing_status": "draft"},
        )

        return {
            "return_id": gst_return.id,
            "filing_status": "draft",
            "net_gst_payable": round(net_gst_payable, 2),
            "return_data": json_data,
        }

    # ------------------------------------------------------------------
    # 4. Submit for Review
    # ------------------------------------------------------------------

    @staticmethod
    def submit_for_review(return_id: int, org_id: str, db: Session) -> Dict:
        """
        Advance a draft GSTReturn to 'under_review'.
        """
        gst_return = (
            db.query(GSTReturn)
            .filter(
                GSTReturn.id == return_id,
                GSTReturn.organization_id == org_id,
            )
            .first()
        )
        if not gst_return:
            raise HTTPException(status_code=404, detail="GST return not found")

        if gst_return.filing_status != "draft":
            raise HTTPException(
                status_code=400,
                detail=f"Cannot submit for review: current status is '{gst_return.filing_status}', expected 'draft'",
            )

        old_values = get_model_dict(gst_return)
        gst_return.filing_status = "under_review"
        gst_return.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(gst_return)

        log_audit_event(
            db=db,
            action="UPDATE",
            table_name="gst_returns",
            record_id=gst_return.id,
            tenant_id=org_id,
            old_values=old_values,
            new_values={"filing_status": "under_review"},
        )

        return {
            "return_id": gst_return.id,
            "return_type": gst_return.return_type,
            "period": gst_return.period,
            "filing_status": gst_return.filing_status,
            "return_data": gst_return.return_data,
        }

    # ------------------------------------------------------------------
    # 5. ITC Reconciliation
    # ------------------------------------------------------------------

    @staticmethod
    def reconcile_itc(
        client_id: int,
        period: str,
        org_id: str,
        gstr2_data: Dict,
        db: Session,
    ) -> Dict:
        """
        Match GSTR-2A/2B supplier invoices against Ledger entries.

        gstr2_data structure:
        {
            "data": [
                {
                    "supplier_gstin": "...",
                    "invoice_number": "...",
                    "invoice_date": "...",
                    "taxable_value": 1000,
                    "igst": 180,
                    "cgst": 0,
                    "sgst": 0
                },
                ...
            ]
        }
        """
        supplier_invoices = gstr2_data.get("data", [])

        # Build ledger lookup: party_name containing supplier GSTIN → ledger entries
        ledger_entries = (
            db.query(Ledger)
            .filter(
                Ledger.client_id == client_id,
                Ledger.ledger_type == "payable",
            )
            .all()
        )

        # Index ledger by (gstin_in_party_name, reference_id) for best-effort matching
        ledger_by_gstin: Dict[str, List[Ledger]] = {}
        for entry in ledger_entries:
            party = (entry.party_name or "").upper()
            # Try to extract a GSTIN-like pattern from party_name or notes
            gstin_matches = re.findall(r"[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z][0-9A-Z]Z[0-9A-Z]", party)
            if not gstin_matches and entry.notes:
                gstin_matches = re.findall(
                    r"[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z][0-9A-Z]Z[0-9A-Z]",
                    (entry.notes or "").upper(),
                )
            for g in gstin_matches:
                ledger_by_gstin.setdefault(g, []).append(entry)

        matched = []
        mismatched = []
        missing_in_books = []
        matched_itc = 0.0
        mismatched_itc = 0.0
        missing_itc = 0.0

        matched_ledger_ids = set()

        for inv in supplier_invoices:
            supplier_gstin = (inv.get("supplier_gstin") or "").upper()
            invoice_number = inv.get("invoice_number") or ""
            gstr2_amount = (
                (inv.get("igst") or 0)
                + (inv.get("cgst") or 0)
                + (inv.get("sgst") or 0)
            )

            # Find matching ledger entries for this supplier
            candidates = ledger_by_gstin.get(supplier_gstin, [])
            best_match: Ledger | None = None
            for candidate in candidates:
                ref = str(candidate.reference_id or "")
                notes = (candidate.notes or "").upper()
                if invoice_number and (invoice_number.upper() in notes or invoice_number == ref):
                    best_match = candidate
                    break

            if best_match is None:
                missing_in_books.append({
                    "supplier_gstin": supplier_gstin,
                    "invoice_number": invoice_number,
                    "gstr2_amount": gstr2_amount,
                    "status": "missing_in_books",
                })
                missing_itc += gstr2_amount
            else:
                ledger_amount = best_match.amount or 0
                diff = abs(gstr2_amount - ledger_amount)
                matched_ledger_ids.add(best_match.id)
                if diff <= 1:
                    matched.append({
                        "supplier_gstin": supplier_gstin,
                        "invoice_number": invoice_number,
                        "gstr2_amount": gstr2_amount,
                        "ledger_amount": ledger_amount,
                        "difference": round(diff, 2),
                        "status": "matched",
                    })
                    matched_itc += gstr2_amount
                else:
                    mismatched.append({
                        "supplier_gstin": supplier_gstin,
                        "invoice_number": invoice_number,
                        "gstr2_amount": gstr2_amount,
                        "ledger_amount": ledger_amount,
                        "difference": round(diff, 2),
                        "status": "mismatched",
                    })
                    mismatched_itc += gstr2_amount

        # Ledger entries with no matching gstr2 record
        missing_in_gstr2 = []
        for entry in ledger_entries:
            if entry.id not in matched_ledger_ids:
                # Only flag entries that have a GSTIN in party_name (i.e., GST-relevant)
                party = (entry.party_name or "").upper()
                gstin_matches = re.findall(r"[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z][0-9A-Z]Z[0-9A-Z]", party)
                if gstin_matches:
                    missing_in_gstr2.append({
                        "ledger_id": entry.id,
                        "party_name": entry.party_name,
                        "amount": entry.amount,
                        "status": "missing_in_gstr2",
                    })

        reconciliation_result = {
            "matched": matched,
            "mismatched": mismatched,
            "missing_in_books": missing_in_books,
            "missing_in_gstr2": missing_in_gstr2,
            "matched_itc": round(matched_itc, 2),
            "mismatched_itc": round(mismatched_itc, 2),
            "missing_itc": round(missing_itc, 2),
        }

        recon = GSTReconciliation(
            client_id=client_id,
            organization_id=org_id,
            period=period,
            source="2B",
            raw_data=gstr2_data,
            reconciliation_result=reconciliation_result,
        )
        db.add(recon)
        db.commit()
        db.refresh(recon)

        return {
            "reconciliation_id": recon.id,
            "matched_count": len(matched),
            "mismatched_count": len(mismatched),
            "missing_count": len(missing_in_books),
            "matched_itc": round(matched_itc, 2),
            "mismatched_itc": round(mismatched_itc, 2),
            "missing_itc": round(missing_itc, 2),
            "details": matched + mismatched + missing_in_books,
        }

    # ------------------------------------------------------------------
    # 6. Compliance Calendar
    # ------------------------------------------------------------------

    @staticmethod
    def get_compliance_calendar(
        client_id: int, org_id: str, db: Session
    ) -> List[Dict]:
        """
        Return filing due dates for the next 12 months.

        Monthly filers:
          GSTR-1 due 11th of following month
          GSTR-3B due 20th of following month

        Quarterly filers:
          Both due last day of month following quarter end
          (Mar→Apr 30, Jun→Jul 31, Sep→Oct 31, Dec→Jan 31)
        """
        gst_config = (
            db.query(GSTConfiguration)
            .filter(
                GSTConfiguration.client_id == client_id,
                GSTConfiguration.organization_id == org_id,
                GSTConfiguration.is_active == True,
            )
            .first()
        )
        filing_frequency = gst_config.filing_frequency if gst_config else "monthly"

        today = date.today()
        calendar_entries: List[Dict] = []

        # Generate for next 12 months
        for month_offset in range(12):
            # Compute the filing month (the month whose return is due)
            filing_month = today.month + month_offset
            filing_year = today.year + (filing_month - 1) // 12
            filing_month = ((filing_month - 1) % 12) + 1
            period = f"{filing_month:02d}{filing_year}"

            if filing_frequency == "quarterly":
                # Only generate entries for quarter-end months
                if filing_month not in (3, 6, 9, 12):
                    continue
                # Due date: last day of month following quarter end
                due_month = filing_month + 1 if filing_month < 12 else 1
                due_year = filing_year if filing_month < 12 else filing_year + 1
                last_day_due = calendar.monthrange(due_year, due_month)[1]
                due_date = date(due_year, due_month, last_day_due)

                for return_type in ("GSTR1", "GSTR3B"):
                    existing = (
                        db.query(GSTReturn)
                        .filter(
                            GSTReturn.client_id == client_id,
                            GSTReturn.organization_id == org_id,
                            GSTReturn.return_type == return_type,
                            GSTReturn.period == period,
                        )
                        .first()
                    )
                    calendar_entries.append({
                        "return_type": return_type,
                        "period": period,
                        "due_date": due_date.isoformat(),
                        "filing_status": existing.filing_status if existing else "not_generated",
                        "is_overdue": today > due_date and (not existing or existing.filing_status not in ("filed", "accepted")),
                    })
            else:
                # Monthly: following month
                due_month_gstr1 = filing_month + 1 if filing_month < 12 else 1
                due_year_gstr1 = filing_year if filing_month < 12 else filing_year + 1
                due_date_gstr1 = date(due_year_gstr1, due_month_gstr1, 11)
                due_date_gstr3b = date(due_year_gstr1, due_month_gstr1, 20)

                for return_type, due_date in (("GSTR1", due_date_gstr1), ("GSTR3B", due_date_gstr3b)):
                    existing = (
                        db.query(GSTReturn)
                        .filter(
                            GSTReturn.client_id == client_id,
                            GSTReturn.organization_id == org_id,
                            GSTReturn.return_type == return_type,
                            GSTReturn.period == period,
                        )
                        .first()
                    )
                    calendar_entries.append({
                        "return_type": return_type,
                        "period": period,
                        "due_date": due_date.isoformat(),
                        "filing_status": existing.filing_status if existing else "not_generated",
                        "is_overdue": today > due_date and (not existing or existing.filing_status not in ("filed", "accepted")),
                    })

        return calendar_entries
