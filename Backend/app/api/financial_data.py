# Backend/app/api/financial_data.py
# Financial statement data upload and management

from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime
import pandas as pd
import io
from pydantic import BaseModel

from app.core.database import get_db
from app.api.auth import get_current_user
from app.models.models import User, Client, FinancialStatement, FinancialRatio
from app.services.template_generator import TemplateGenerator

router = APIRouter(tags=["financial_data"])


class UploadResult(BaseModel):
    success: bool
    message: str
    statement_id: int = None
    errors: List[str] = []


# ── Template download endpoints ──────────────────────────────────────

@router.get("/templates/balance-sheet.xlsx")
def download_balance_sheet_template():
    """Download Excel template for balance sheet data"""
    template_data = TemplateGenerator.generate_balance_sheet_template()
    
    return StreamingResponse(
        io.BytesIO(template_data),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=balance_sheet_template.xlsx"}
    )


@router.get("/templates/profit-loss.xlsx")
def download_profit_loss_template():
    """Download Excel template for P&L statement"""
    template_data = TemplateGenerator.generate_profit_loss_template()
    
    return StreamingResponse(
        io.BytesIO(template_data),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=profit_loss_template.xlsx"}
    )


@router.get("/templates/inventory.xlsx")
def download_inventory_template():
    """Download Excel template for inventory data"""
    template_data = TemplateGenerator.generate_inventory_template()
    
    return StreamingResponse(
        io.BytesIO(template_data),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=inventory_template.xlsx"}
    )


@router.get("/templates/balance-sheet")
def download_balance_sheet_template():
    """Download Excel template for balance sheet data"""
    return {
        "template_url": "/api/financial-data/templates/balance-sheet.xlsx",
        "instructions": "Fill in the balance sheet items with your company's data",
        "required_columns": [
            "item_name", "category", "amount", "period_end_date"
        ],
        "categories": {
            "assets": ["current_assets", "fixed_assets", "investments", "other_assets"],
            "liabilities": ["current_liabilities", "long_term_liabilities"],
            "equity": ["share_capital", "reserves", "retained_earnings"]
        }
    }


@router.get("/templates/profit-loss")
def get_profit_loss_template_info():
    """Get P&L template information"""
    return {
        "template_url": "/api/financial-data/templates/profit-loss.xlsx",
        "instructions": "Fill in the income and expense items",
        "required_columns": [
            "item_name", "category", "amount", "period_start_date", "period_end_date"
        ],
        "categories": {
            "revenue": ["sales_revenue", "other_income"],
            "expenses": ["cost_of_goods_sold", "operating_expenses", "interest", "tax"]
        }
    }


@router.get("/templates/inventory")
def get_inventory_template_info():
    """Get inventory template information"""
    return {
        "template_url": "/api/financial-data/templates/inventory.xlsx",
        "instructions": "Fill in your inventory items with quantities and values",
        "required_columns": [
            "item_name", "category", "quantity", "unit", "unit_cost", "total_value", "as_of_date"
        ]
    }


# ── Upload endpoints ──────────────────────────────────────────────────

@router.post("/upload/balance-sheet", response_model=UploadResult)
async def upload_balance_sheet(
    file: UploadFile = File(...),
    client_id: int = Query(...),
    period_start: str = Query(...),
    period_end: str = Query(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Upload balance sheet data from Excel/CSV"""
    
    if not file.filename.endswith(('.xlsx', '.xls', '.csv')):
        raise HTTPException(status_code=400, detail="Only Excel or CSV files allowed")
    
    try:
        content = await file.read()
        
        # Read file
        if file.filename.endswith('.csv'):
            df = pd.read_csv(io.BytesIO(content))
        else:
            df = pd.read_excel(io.BytesIO(content))
        
        # Validate required columns
        required_cols = ['item_name', 'category', 'amount']
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            raise HTTPException(
                status_code=400,
                detail=f"Missing required columns: {', '.join(missing_cols)}"
            )
        
        # Parse and structure data
        financial_data = {
            "assets": {},
            "liabilities": {},
            "equity": {}
        }
        
        errors = []
        
        for idx, row in df.iterrows():
            try:
                item_name = str(row['item_name']).strip()
                category = str(row['category']).strip().lower()
                amount = float(row['amount'])
                
                # Categorize items
                if 'asset' in category:
                    financial_data["assets"][item_name] = amount
                elif 'liabilit' in category:
                    financial_data["liabilities"][item_name] = amount
                elif 'equity' in category or 'capital' in category:
                    financial_data["equity"][item_name] = amount
                else:
                    errors.append(f"Row {idx}: Unknown category '{category}'")
                    
            except Exception as e:
                errors.append(f"Row {idx}: {str(e)}")
        
        # Calculate totals
        total_assets = sum(financial_data["assets"].values())
        total_liabilities = sum(financial_data["liabilities"].values())
        total_equity = sum(financial_data["equity"].values())
        
        financial_data["totals"] = {
            "total_assets": total_assets,
            "total_liabilities": total_liabilities,
            "total_equity": total_equity
        }
        
        # Calculate ratios
        current_assets = sum(v for k, v in financial_data["assets"].items() if 'current' in k.lower())
        current_liabilities = sum(v for k, v in financial_data["liabilities"].items() if 'current' in k.lower())
        
        current_ratio = current_assets / current_liabilities if current_liabilities > 0 else 0
        quick_ratio = (current_assets - financial_data["assets"].get("inventory", 0)) / current_liabilities if current_liabilities > 0 else 0
        debt_equity_ratio = total_liabilities / total_equity if total_equity > 0 else 0
        
        # Create financial statement record
        statement = FinancialStatement(
            client_id=client_id,
            statement_type="balance_sheet",
            period_type="custom",
            period_start=datetime.fromisoformat(period_start),
            period_end=datetime.fromisoformat(period_end),
            financial_data=financial_data,
            current_ratio=current_ratio,
            quick_ratio=quick_ratio,
            debt_equity_ratio=debt_equity_ratio
        )
        
        db.add(statement)
        db.commit()
        db.refresh(statement)
        
        return UploadResult(
            success=True,
            message=f"Balance sheet uploaded successfully. {len(df)} items processed.",
            statement_id=statement.id,
            errors=errors
        )
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Upload failed: {str(e)}")


@router.post("/upload/profit-loss", response_model=UploadResult)
async def upload_profit_loss(
    file: UploadFile = File(...),
    client_id: int = Query(...),
    period_start: str = Query(...),
    period_end: str = Query(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Upload P&L statement data from Excel/CSV"""
    
    if not file.filename.endswith(('.xlsx', '.xls', '.csv')):
        raise HTTPException(status_code=400, detail="Only Excel or CSV files allowed")
    
    try:
        content = await file.read()
        
        # Read file
        if file.filename.endswith('.csv'):
            df = pd.read_csv(io.BytesIO(content))
        else:
            df = pd.read_excel(io.BytesIO(content))
        
        # Validate required columns
        required_cols = ['item_name', 'category', 'amount']
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            raise HTTPException(
                status_code=400,
                detail=f"Missing required columns: {', '.join(missing_cols)}"
            )
        
        # Parse and structure data
        financial_data = {
            "revenue": {},
            "expenses": {},
            "other_income": {}
        }
        
        errors = []
        
        for idx, row in df.iterrows():
            try:
                item_name = str(row['item_name']).strip()
                category = str(row['category']).strip().lower()
                amount = float(row['amount'])
                
                # Categorize items
                if 'revenue' in category or 'sales' in category or 'income' in category:
                    if 'other' in category:
                        financial_data["other_income"][item_name] = amount
                    else:
                        financial_data["revenue"][item_name] = amount
                elif 'expense' in category or 'cost' in category:
                    financial_data["expenses"][item_name] = amount
                else:
                    errors.append(f"Row {idx}: Unknown category '{category}'")
                    
            except Exception as e:
                errors.append(f"Row {idx}: {str(e)}")
        
        # Calculate totals
        total_revenue = sum(financial_data["revenue"].values())
        total_expenses = sum(financial_data["expenses"].values())
        total_other_income = sum(financial_data["other_income"].values())
        
        gross_profit = total_revenue - financial_data["expenses"].get("cost_of_goods_sold", 0)
        net_profit = total_revenue + total_other_income - total_expenses
        
        financial_data["totals"] = {
            "total_revenue": total_revenue,
            "total_expenses": total_expenses,
            "total_other_income": total_other_income,
            "gross_profit": gross_profit,
            "net_profit": net_profit
        }
        
        # Calculate ratios
        gross_margin = (gross_profit / total_revenue * 100) if total_revenue > 0 else 0
        net_margin = (net_profit / total_revenue * 100) if total_revenue > 0 else 0
        
        # Create financial statement record
        statement = FinancialStatement(
            client_id=client_id,
            statement_type="profit_loss",
            period_type="custom",
            period_start=datetime.fromisoformat(period_start),
            period_end=datetime.fromisoformat(period_end),
            financial_data=financial_data,
            gross_margin=gross_margin,
            net_margin=net_margin
        )
        
        db.add(statement)
        db.commit()
        db.refresh(statement)
        
        return UploadResult(
            success=True,
            message=f"P&L statement uploaded successfully. {len(df)} items processed.",
            statement_id=statement.id,
            errors=errors
        )
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Upload failed: {str(e)}")


@router.post("/upload/inventory", response_model=UploadResult)
async def upload_inventory(
    file: UploadFile = File(...),
    client_id: int = Query(...),
    as_of_date: str = Query(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Upload inventory data from Excel/CSV"""
    
    if not file.filename.endswith(('.xlsx', '.xls', '.csv')):
        raise HTTPException(status_code=400, detail="Only Excel or CSV files allowed")
    
    try:
        content = await file.read()
        
        # Read file
        if file.filename.endswith('.csv'):
            df = pd.read_csv(io.BytesIO(content))
        else:
            df = pd.read_excel(io.BytesIO(content))
        
        # Validate required columns
        required_cols = ['item_name', 'quantity', 'unit_cost', 'total_value']
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            raise HTTPException(
                status_code=400,
                detail=f"Missing required columns: {', '.join(missing_cols)}"
            )
        
        # Parse and structure data
        inventory_data = {
            "items": [],
            "summary": {}
        }
        
        errors = []
        total_inventory_value = 0
        
        for idx, row in df.iterrows():
            try:
                item = {
                    "item_name": str(row['item_name']).strip(),
                    "category": str(row.get('category', 'general')).strip(),
                    "quantity": float(row['quantity']),
                    "unit": str(row.get('unit', 'pcs')).strip(),
                    "unit_cost": float(row['unit_cost']),
                    "total_value": float(row['total_value'])
                }
                inventory_data["items"].append(item)
                total_inventory_value += item["total_value"]
                    
            except Exception as e:
                errors.append(f"Row {idx}: {str(e)}")
        
        inventory_data["summary"] = {
            "total_items": len(inventory_data["items"]),
            "total_inventory_value": total_inventory_value,
            "as_of_date": as_of_date
        }
        
        # Create financial statement record for inventory
        statement = FinancialStatement(
            client_id=client_id,
            statement_type="inventory",
            period_type="snapshot",
            period_start=datetime.fromisoformat(as_of_date),
            period_end=datetime.fromisoformat(as_of_date),
            financial_data=inventory_data
        )
        
        db.add(statement)
        db.commit()
        db.refresh(statement)
        
        return UploadResult(
            success=True,
            message=f"Inventory uploaded successfully. {len(df)} items processed.",
            statement_id=statement.id,
            errors=errors
        )
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Upload failed: {str(e)}")


# ── Query endpoints ───────────────────────────────────────────────────

@router.get("/statements")
def list_financial_statements(
    client_id: int,
    statement_type: str = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List all financial statements for a client"""
    query = db.query(FinancialStatement).filter(
        FinancialStatement.client_id == client_id
    )
    
    if statement_type:
        query = query.filter(FinancialStatement.statement_type == statement_type)
    
    statements = query.order_by(FinancialStatement.period_end.desc()).all()
    
    return [
        {
            "id": s.id,
            "statement_type": s.statement_type,
            "period_type": s.period_type,
            "period_start": s.period_start.isoformat(),
            "period_end": s.period_end.isoformat(),
            "current_ratio": s.current_ratio,
            "quick_ratio": s.quick_ratio,
            "debt_equity_ratio": s.debt_equity_ratio,
            "gross_margin": s.gross_margin,
            "net_margin": s.net_margin,
            "created_at": s.created_at.isoformat()
        }
        for s in statements
    ]


@router.get("/statements/{statement_id}")
def get_financial_statement(
    statement_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get detailed financial statement data"""
    statement = db.query(FinancialStatement).filter(
        FinancialStatement.id == statement_id
    ).first()
    
    if not statement:
        raise HTTPException(status_code=404, detail="Statement not found")
    
    return {
        "id": statement.id,
        "client_id": statement.client_id,
        "statement_type": statement.statement_type,
        "period_type": statement.period_type,
        "period_start": statement.period_start.isoformat(),
        "period_end": statement.period_end.isoformat(),
        "financial_data": statement.financial_data,
        "ratios": {
            "current_ratio": statement.current_ratio,
            "quick_ratio": statement.quick_ratio,
            "debt_equity_ratio": statement.debt_equity_ratio,
            "roa": statement.roa,
            "roe": statement.roe,
            "gross_margin": statement.gross_margin,
            "net_margin": statement.net_margin
        },
        "created_at": statement.created_at.isoformat()
    }
