# File: backend/app/api/data_upload.py
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
from typing import List
import pandas as pd
import io
from datetime import datetime
from pydantic import BaseModel

from app.core.database import get_db
from app.models.models import Client, User
from app.api.auth import get_current_user
from app.api.clients import ClientCreate  # Reuse schema

router = APIRouter()

class UploadResult(BaseModel):
    total_rows: int
    created: int
    errors: List[str]
    skipped: int

@router.post("/clients/csv", response_model=UploadResult)
async def upload_clients_csv(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="Only CSV files allowed")
    
    try:
        content = await file.read()
        df = pd.read_csv(io.BytesIO(content))
        
        required_cols = ['business_name', 'email', 'industry']
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            raise HTTPException(
                status_code=400, 
                detail=f"Missing columns: {', '.join(missing_cols)}"
            )
        
        created_count = 0
        errors = []
        skipped = 0
        
        for idx, row in df.iterrows():
            try:
                # Check if email exists
                existing = db.query(Client).filter(
                    Client.email == str(row['email']),
                    Client.organization_id == current_user.organization_id
                ).first()
                
                if existing:
                    skipped += 1
                    continue
                
                client_data = ClientCreate(
                    business_name=str(row['business_name']),
                    email=str(row['email']),
                    industry=str(row.get('industry', 'manufacturing')),
                    phone=str(row.get('phone', '')) if 'phone' in row else None,
                    annual_revenue=float(row.get('annual_revenue', 0)) if 'annual_revenue' in row else None,
                    current_debtors=float(row.get('current_debtors', 0)) if 'current_debtors' in row else None,
                    average_credit_days=int(row.get('average_credit_days', 30)) if 'average_credit_days' in row else None
                )
                
                # Create client
                client = Client(
                    id=uuid.uuid4(),
                    **client_data.dict(),
                    organization_id=current_user.organization_id
                )
                db.add(client)
                created_count += 1
                
            except Exception as e:
                errors.append(f"Row {idx}: {str(e)}")
        
        db.commit()
        return UploadResult(
            total_rows=len(df),
            created=created_count,
            errors=errors,
            skipped=skipped
        )
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Upload failed: {str(e)}")

@router.post("/clients/excel", response_model=UploadResult)
async def upload_clients_excel(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not file.filename.endswith(('.xlsx', '.xls')):
        raise HTTPException(status_code=400, detail="Only Excel files allowed")
    
    try:
        content = await file.read()
        df = pd.read_excel(io.BytesIO(content))
        
        # Same logic as CSV
        required_cols = ['business_name', 'email', 'industry']
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            raise HTTPException(
                status_code=400, 
                detail=f"Missing columns: {', '.join(missing_cols)}"
            )
        
        created_count = 0
        errors = []
        skipped = 0
        
        for idx, row in df.iterrows():
            try:
                existing = db.query(Client).filter(
                    Client.email == str(row['email']),
                    Client.organization_id == current_user.organization_id
                ).first()
                
                if existing:
                    skipped += 1
                    continue
                
                client_data = ClientCreate(
                    business_name=str(row['business_name']),
                    email=str(row['email']),
                    industry=str(row.get('industry', 'manufacturing')),
                    phone=str(row.get('phone', '')) if pd.notna(row.get('phone')) else None,
                    annual_revenue=float(row.get('annual_revenue', 0)) if pd.notna(row.get('annual_revenue')) else None,
                    current_debtors=float(row.get('current_debtors', 0)) if pd.notna(row.get('current_debtors')) else None,
                    average_credit_days=int(row.get('average_credit_days', 30)) if pd.notna(row.get('average_credit_days')) else None
                )
                
                client = Client(
                    id=uuid.uuid4(),
                    **client_data.dict(),
                    organization_id=current_user.organization_id
                )
                db.add(client)
                created_count += 1
                
            except Exception as e:
                errors.append(f"Row {idx}: {str(e)}")
        
        db.commit()
        return UploadResult(
            total_rows=len(df),
            created=created_count,
            errors=errors,
            skipped=skipped
        )
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Upload failed: {str(e)}")
