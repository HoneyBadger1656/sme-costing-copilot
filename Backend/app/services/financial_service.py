# backend/app/services/financial_service.py

from sqlalchemy.orm import Session
from sqlalchemy import func, extract
from app.models.models import Order, Ledger, Client, CreditLimit
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from math import ceil
from app.utils.audit import log_audit_event

class FinancialService:
    
    @staticmethod
    def get_profitability_summary(
        db: Session,
        client_id: int,
        start_date: datetime = None,
        end_date: datetime = None
    ) -> Dict:
        """Calculate order-wise and period profitability"""
        
        if not start_date:
            start_date = datetime.utcnow() - timedelta(days=30)
        if not end_date:
            end_date = datetime.utcnow()
        
        # Get orders in period
        orders = db.query(Order).filter(
            Order.client_id == client_id,
            Order.order_date >= start_date,
            Order.order_date <= end_date,
            Order.status != "draft"
        ).all()
        
        total_revenue = sum(o.total_selling_price for o in orders)
        total_cost = sum(o.total_cost for o in orders)
        gross_profit = total_revenue - total_cost
        
        avg_margin = (gross_profit / total_revenue * 100) if total_revenue > 0 else 0
        
        # Group by customer
        customer_profitability = {}
        for order in orders:
            if order.customer_name not in customer_profitability:
                customer_profitability[order.customer_name] = {
                    "revenue": 0,
                    "cost": 0,
                    "margin": 0,
                    "order_count": 0
                }
            
            customer_profitability[order.customer_name]["revenue"] += order.total_selling_price
            customer_profitability[order.customer_name]["cost"] += order.total_cost
            customer_profitability[order.customer_name]["order_count"] += 1
        
        # Calculate margins
        for customer in customer_profitability:
            data = customer_profitability[customer]
            data["margin"] = data["revenue"] - data["cost"]
            data["margin_percent"] = (data["margin"] / data["revenue"] * 100) if data["revenue"] > 0 else 0
        
        # Sort by margin
        top_customers = sorted(
            customer_profitability.items(),
            key=lambda x: x[1]["margin"],
            reverse=True
        )[:10]
        
        return {
            "period": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat()
            },
            "summary": {
                "total_revenue": round(total_revenue, 2),
                "total_cost": round(total_cost, 2),
                "gross_profit": round(gross_profit, 2),
                "margin_percentage": round(avg_margin, 2),
                "order_count": len(orders)
            },
            "top_customers": [
                {
                    "name": name,
                    "revenue": round(data["revenue"], 2),
                    "margin": round(data["margin"], 2),
                    "margin_percent": round(data["margin_percent"], 2),
                    "order_count": data["order_count"]
                }
                for name, data in top_customers
            ]
        }
    
    @staticmethod
    def get_receivables_summary(db: Session, client_id: int) -> Dict:
        """Get outstanding receivables analysis"""
        
        # Outstanding ledger entries
        outstanding = db.query(Ledger).filter(
            Ledger.client_id == client_id,
            Ledger.ledger_type == "receivable",
            Ledger.status == "outstanding"
        ).all()
        
        total_outstanding = sum(l.amount for l in outstanding)
        
        # Age analysis
        now = datetime.utcnow()
        age_buckets = {
            "0-30": 0,
            "31-60": 0,
            "61-90": 0,
            "90+": 0
        }
        
        overdue_items = []
        
        for ledger in outstanding:
            days_old = (now - ledger.transaction_date).days
            
            if days_old <= 30:
                age_buckets["0-30"] += ledger.amount
            elif days_old <= 60:
                age_buckets["31-60"] += ledger.amount
            elif days_old <= 90:
                age_buckets["61-90"] += ledger.amount
            else:
                age_buckets["90+"] += ledger.amount
            
            # Overdue check
            if ledger.due_date and now > ledger.due_date:
                overdue_items.append({
                    "party_name": ledger.party_name,
                    "amount": round(ledger.amount, 2),
                    "due_date": ledger.due_date.isoformat(),
                    "days_overdue": (now - ledger.due_date).days
                })
        
        # Sort by days overdue
        overdue_items.sort(key=lambda x: x["days_overdue"], reverse=True)
        
        return {
            "total_outstanding": round(total_outstanding, 2),
            "age_analysis": {k: round(v, 2) for k, v in age_buckets.items()},
            "overdue_count": len(overdue_items),
            "overdue_amount": round(sum(i["amount"] for i in overdue_items), 2),
            "top_overdue": overdue_items[:10]
        }
    
    @staticmethod
    def get_payables_summary(db: Session, client_id: int) -> Dict:
        """Get outstanding payables analysis"""
        
        outstanding = db.query(Ledger).filter(
            Ledger.client_id == client_id,
            Ledger.ledger_type == "payable",
            Ledger.status == "outstanding"
        ).all()
        
        total_outstanding = sum(l.amount for l in outstanding)
        
        # Age analysis
        now = datetime.utcnow()
        age_buckets = {
            "0-30": 0,
            "31-60": 0,
            "61-90": 0,
            "90+": 0
        }
        
        due_soon = []
        
        for ledger in outstanding:
            days_old = (now - ledger.transaction_date).days
            
            if days_old <= 30:
                age_buckets["0-30"] += ledger.amount
            elif days_old <= 60:
                age_buckets["31-60"] += ledger.amount
            elif days_old <= 90:
                age_buckets["61-90"] += ledger.amount
            else:
                age_buckets["90+"] += ledger.amount
            
            # Due in next 7 days
            if ledger.due_date:
                days_until_due = (ledger.due_date - now).days
                if 0 <= days_until_due <= 7:
                    due_soon.append({
                        "party_name": ledger.party_name,
                        "amount": round(ledger.amount, 2),
                        "due_date": ledger.due_date.isoformat(),
                        "days_until_due": days_until_due
                    })
        
        due_soon.sort(key=lambda x: x["days_until_due"])
        
        return {
            "total_outstanding": round(total_outstanding, 2),
            "age_analysis": {k: round(v, 2) for k, v in age_buckets.items()},
            "due_in_7_days": round(sum(i["amount"] for i in due_soon), 2),
            "upcoming_payments": due_soon
        }
    
    @staticmethod
    def get_cash_flow_forecast(db: Session, client_id: int, days: int = 30) -> Dict:
        """Simple cash flow forecast based on receivables and payables"""
        
        now = datetime.utcnow()
        forecast_end = now + timedelta(days=days)
        
        # Expected cash inflows (receivables due in period)
        inflows = db.query(Ledger).filter(
            Ledger.client_id == client_id,
            Ledger.ledger_type == "receivable",
            Ledger.status == "outstanding",
            Ledger.due_date >= now,
            Ledger.due_date <= forecast_end
        ).all()
        
        # Expected cash outflows (payables due in period)
        outflows = db.query(Ledger).filter(
            Ledger.client_id == client_id,
            Ledger.ledger_type == "payable",
            Ledger.status == "outstanding",
            Ledger.due_date >= now,
            Ledger.due_date <= forecast_end
        ).all()
        
        total_inflow = sum(l.amount for l in inflows)
        total_outflow = sum(l.amount for l in outflows)
        net_cash_flow = total_inflow - total_outflow
        
        return {
            "forecast_period_days": days,
            "expected_inflows": round(total_inflow, 2),
            "expected_outflows": round(total_outflow, 2),
            "net_cash_flow": round(net_cash_flow, 2),
            "cash_position": "positive" if net_cash_flow > 0 else "negative",
            "recommendation": FinancialService._cash_flow_recommendation(net_cash_flow, total_outflow)
        }
    
    @staticmethod
    def _cash_flow_recommendation(net_flow: float, outflows: float) -> str:
        """Generate cash flow recommendation"""
        if net_flow < 0:
            return f"⚠ Negative cash flow of ₹{abs(net_flow):,.0f} expected. Arrange credit line or accelerate collections to cover ₹{outflows:,.0f} in payments."
        elif net_flow < outflows * 0.2:
            return f"⚠ Cash flow is tight (₹{net_flow:,.0f} surplus). Monitor closely and delay non-essential payments if needed."
        else:
            return f"✓ Healthy cash surplus of ₹{net_flow:,.0f} expected. Good liquidity position."

    @staticmethod
    def calculate_current_ratio(current_assets: float, current_liabilities: float) -> float:
        """Calculate current ratio"""
        if current_liabilities == 0:
            raise ValueError("Current liabilities cannot be zero")
        return round(current_assets / current_liabilities, 2)
    
    @staticmethod
    def calculate_quick_ratio(current_assets: float, inventory: float, current_liabilities: float) -> float:
        """Calculate quick ratio (acid test ratio)"""
        if current_liabilities == 0:
            raise ValueError("Current liabilities cannot be zero")
        quick_assets = current_assets - inventory
        return round(quick_assets / current_liabilities, 2)
    
    @staticmethod
    def calculate_debt_equity_ratio(total_debt: float, total_equity: float) -> float:
        """Calculate debt to equity ratio"""
        if total_equity == 0:
            raise ValueError("Total equity cannot be zero")
        return round(total_debt / total_equity, 2)
    
    @staticmethod
    def calculate_gross_margin(revenue: float, cogs: float) -> float:
        """Calculate gross margin percentage"""
        if revenue == 0:
            return 0.0
        gross_profit = revenue - cogs
        return round((gross_profit / revenue) * 100, 2)
    
    @staticmethod
    def calculate_net_margin(revenue: float, net_income: float) -> float:
        """Calculate net margin percentage"""
        if revenue == 0:
            return 0.0
        return round((net_income / revenue) * 100, 2)
    
    @staticmethod
    def calculate_roa(net_income: float, total_assets: float) -> float:
        """Calculate return on assets percentage"""
        if total_assets == 0:
            raise ValueError("Total assets cannot be zero")
        return round((net_income / total_assets) * 100, 2)
    
    @staticmethod
    def calculate_roe(net_income: float, total_equity: float) -> float:
        """Calculate return on equity percentage"""
        if total_equity == 0:
            raise ValueError("Total equity cannot be zero")
        return round((net_income / total_equity) * 100, 2)
    
    @staticmethod
    def calculate_working_capital(current_assets: float, current_liabilities: float) -> float:
        """Calculate working capital"""
        return round(current_assets - current_liabilities, 2)
    
    @staticmethod
    def calculate_cash_conversion_cycle(
        days_inventory_outstanding: int,
        days_sales_outstanding: int,
        days_payables_outstanding: int
    ) -> int:
        """Calculate cash conversion cycle in days"""
        return days_inventory_outstanding + days_sales_outstanding - days_payables_outstanding

    # ── Task 6 additions ──────────────────────────────────────────────────────

    @staticmethod
    def get_aging_report(client_id: int, db: Session) -> Dict:
        """Receivables aging with per-bucket drill-down and percentages."""
        outstanding = db.query(Ledger).filter(
            Ledger.client_id == client_id,
            Ledger.ledger_type == "receivable",
            Ledger.status == "outstanding"
        ).all()

        now = datetime.utcnow()
        buckets: Dict[str, List] = {"0-30": [], "31-60": [], "61-90": [], "90+": []}

        for l in outstanding:
            days_old = (now - l.transaction_date).days
            entry = {
                "id": l.id,
                "party_name": l.party_name,
                "amount": round(l.amount, 2),
                "transaction_date": l.transaction_date.isoformat(),
                "due_date": l.due_date.isoformat() if l.due_date else None,
                "days_old": days_old,
                "reference_type": l.reference_type,
                "reference_id": l.reference_id,
            }
            if days_old <= 30:
                buckets["0-30"].append(entry)
            elif days_old <= 60:
                buckets["31-60"].append(entry)
            elif days_old <= 90:
                buckets["61-90"].append(entry)
            else:
                buckets["90+"].append(entry)

        total = sum(l.amount for l in outstanding)

        bucket_summary = {}
        for key, entries in buckets.items():
            bucket_total = sum(e["amount"] for e in entries)
            bucket_summary[key] = {
                "total": round(bucket_total, 2),
                "percentage": round(bucket_total / total * 100, 1) if total else 0,
                "count": len(entries),
                "entries": entries,
            }

        return {
            "client_id": client_id,
            "total_outstanding": round(total, 2),
            "buckets": bucket_summary,
            "generated_at": now.isoformat(),
        }

    @staticmethod
    def get_working_capital_cycle(client_id: int, period_days: int, db: Session) -> Dict:
        """Compute DSO, DPO, DIO, CCC for current and prior period."""
        now = datetime.utcnow()
        period_start = now - timedelta(days=period_days)
        prior_start = period_start - timedelta(days=period_days)

        def _compute(start: datetime, end: datetime) -> Dict:
            orders = db.query(Order).filter(
                Order.client_id == client_id,
                Order.order_date >= start,
                Order.order_date <= end,
                Order.status != "draft",
            ).all()

            revenue = sum(o.total_selling_price for o in orders)
            cogs = sum(o.total_cost for o in orders)

            # DSO: avg receivables / (revenue / period_days)
            avg_receivables = db.query(func.avg(Ledger.amount)).filter(
                Ledger.client_id == client_id,
                Ledger.ledger_type == "receivable",
                Ledger.transaction_date >= start,
                Ledger.transaction_date <= end,
            ).scalar() or 0

            # DPO: avg payables / (cogs / period_days)
            avg_payables = db.query(func.avg(Ledger.amount)).filter(
                Ledger.client_id == client_id,
                Ledger.ledger_type == "payable",
                Ledger.transaction_date >= start,
                Ledger.transaction_date <= end,
            ).scalar() or 0

            daily_revenue = revenue / period_days if period_days else 0
            daily_cogs = cogs / period_days if period_days else 0

            dso = round(avg_receivables / daily_revenue, 1) if daily_revenue else 0
            dpo = round(avg_payables / daily_cogs, 1) if daily_cogs else 0
            # DIO approximated from working_capital_blocked (inventory proxy)
            avg_wc_blocked = sum(o.working_capital_blocked for o in orders) / len(orders) if orders else 0
            dio = round(avg_wc_blocked / daily_cogs, 1) if daily_cogs else 0
            ccc = round(dio + dso - dpo, 1)

            return {"dso": dso, "dpo": dpo, "dio": dio, "ccc": ccc,
                    "revenue": round(revenue, 2), "cogs": round(cogs, 2)}

        current = _compute(period_start, now)
        prior = _compute(prior_start, period_start)

        def _delta(curr, prev):
            return round(curr - prev, 1)

        return {
            "period_days": period_days,
            "current": current,
            "prior": prior,
            "delta": {
                "dso": _delta(current["dso"], prior["dso"]),
                "dpo": _delta(current["dpo"], prior["dpo"]),
                "dio": _delta(current["dio"], prior["dio"]),
                "ccc": _delta(current["ccc"], prior["ccc"]),
            },
        }

    @staticmethod
    def get_collection_efficiency(org_id: str, db: Session) -> Dict:
        """Per-client collection efficiency score and classification."""
        clients = db.query(Client).filter(Client.organization_id == org_id).all()
        results = []

        for client in clients:
            receivables = db.query(Ledger).filter(
                Ledger.client_id == client.id,
                Ledger.ledger_type == "receivable",
            ).all()

            total_invoiced = sum(l.amount for l in receivables)
            if total_invoiced == 0:
                continue

            collected_on_time = sum(
                l.amount for l in receivables
                if l.status == "paid"
                and l.payment_date is not None
                and l.due_date is not None
                and l.payment_date <= l.due_date
            )

            score = round(collected_on_time / total_invoiced * 100, 1)

            if score >= 90:
                classification = "Excellent"
            elif score >= 75:
                classification = "Good"
            elif score >= 50:
                classification = "Fair"
            else:
                classification = "Poor"

            results.append({
                "client_id": client.id,
                "client_name": client.name,
                "score": score,
                "classification": classification,
                "total_invoiced": round(total_invoiced, 2),
                "collected_on_time": round(collected_on_time, 2),
            })

        results.sort(key=lambda x: x["score"])
        return {"clients": results, "total_clients": len(results)}

    @staticmethod
    def set_credit_limit(client_id: int, amount: float, user_id: int, db: Session) -> Dict:
        """Upsert CreditLimit record and log audit entry."""
        existing = db.query(CreditLimit).filter(CreditLimit.client_id == client_id).first()
        client = db.query(Client).filter(Client.id == client_id).first()
        if not client:
            raise ValueError(f"Client {client_id} not found")

        if existing:
            old_amount = existing.limit_amount
            existing.limit_amount = amount
            existing.updated_at = datetime.utcnow()
            db.commit()
            log_audit_event(
                db=db, action="UPDATE", table_name="credit_limits",
                record_id=existing.id, tenant_id=client.organization_id,
                user_id=user_id,
                old_values={"limit_amount": old_amount},
                new_values={"limit_amount": amount},
            )
            return {"id": existing.id, "client_id": client_id, "limit_amount": amount, "action": "updated"}
        else:
            cl = CreditLimit(
                client_id=client_id,
                organization_id=client.organization_id,
                limit_amount=amount,
                created_by=user_id,
            )
            db.add(cl)
            db.commit()
            db.refresh(cl)
            log_audit_event(
                db=db, action="CREATE", table_name="credit_limits",
                record_id=cl.id, tenant_id=client.organization_id,
                user_id=user_id,
                new_values={"client_id": client_id, "limit_amount": amount},
            )
            return {"id": cl.id, "client_id": client_id, "limit_amount": amount, "action": "created"}

    @staticmethod
    def check_credit_limit(client_id: int, order_amount: float, db: Session) -> Dict:
        """Return credit utilization and whether the order would exceed the limit."""
        cl = db.query(CreditLimit).filter(CreditLimit.client_id == client_id).first()
        if not cl:
            return {
                "limit": None, "utilization": 0, "available": None,
                "would_exceed": False, "warning_80pct": False,
                "has_limit": False,
            }

        outstanding = db.query(func.sum(Ledger.amount)).filter(
            Ledger.client_id == client_id,
            Ledger.ledger_type == "receivable",
            Ledger.status == "outstanding",
        ).scalar() or 0

        utilization = round(outstanding, 2)
        available = round(cl.limit_amount - utilization, 2)
        would_exceed = (utilization + order_amount) > cl.limit_amount
        warning_80pct = utilization >= cl.limit_amount * 0.8

        return {
            "limit": cl.limit_amount,
            "utilization": utilization,
            "available": available,
            "would_exceed": would_exceed,
            "warning_80pct": warning_80pct,
            "has_limit": True,
        }

    @staticmethod
    def get_cash_flow_forecast(db: Session, client_id: int, days: int = 30) -> Dict:
        """Cash flow forecast with daily time-series and cumulative balance."""
        now = datetime.utcnow()
        forecast_end = now + timedelta(days=days)

        inflows = db.query(Ledger).filter(
            Ledger.client_id == client_id,
            Ledger.ledger_type == "receivable",
            Ledger.status == "outstanding",
            Ledger.due_date >= now,
            Ledger.due_date <= forecast_end,
        ).all()

        outflows = db.query(Ledger).filter(
            Ledger.client_id == client_id,
            Ledger.ledger_type == "payable",
            Ledger.status == "outstanding",
            Ledger.due_date >= now,
            Ledger.due_date <= forecast_end,
        ).all()

        # Build daily buckets
        daily: Dict[str, Dict] = {}
        for i in range(days + 1):
            day = (now + timedelta(days=i)).date().isoformat()
            daily[day] = {"projected_inflow": 0.0, "projected_outflow": 0.0}

        for l in inflows:
            day = l.due_date.date().isoformat()
            if day in daily:
                daily[day]["projected_inflow"] += l.amount

        for l in outflows:
            day = l.due_date.date().isoformat()
            if day in daily:
                daily[day]["projected_outflow"] += l.amount

        # Build time-series with cumulative balance
        time_series = []
        cumulative = 0.0
        negative_dates = []
        for day, vals in sorted(daily.items()):
            net = vals["projected_inflow"] - vals["projected_outflow"]
            cumulative += net
            point = {
                "date": day,
                "projected_inflow": round(vals["projected_inflow"], 2),
                "projected_outflow": round(vals["projected_outflow"], 2),
                "net_cash_flow": round(net, 2),
                "cumulative_balance": round(cumulative, 2),
                "is_negative": cumulative < 0,
            }
            time_series.append(point)
            if cumulative < 0:
                negative_dates.append(day)

        total_inflow = sum(l.amount for l in inflows)
        total_outflow = sum(l.amount for l in outflows)
        net_cash_flow = total_inflow - total_outflow

        return {
            "forecast_period_days": days,
            "expected_inflows": round(total_inflow, 2),
            "expected_outflows": round(total_outflow, 2),
            "net_cash_flow": round(net_cash_flow, 2),
            "cash_position": "positive" if net_cash_flow >= 0 else "negative",
            "negative_balance_dates": negative_dates,
            "time_series": time_series,
            "recommendation": FinancialService._cash_flow_recommendation(net_cash_flow, total_outflow),
        }
