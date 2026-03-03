"""Client schemas with validation"""

from pydantic import BaseModel, EmailStr, Field, field_validator, ConfigDict
from typing import Optional
from datetime import datetime


class ClientCreate(BaseModel):
    """Schema for creating a new client"""
    business_name: str = Field(..., min_length=2, max_length=255, description="Business name")
    email: Optional[EmailStr] = Field(None, description="Client email")
    phone: Optional[str] = Field(None, max_length=20, description="Client phone number")
    industry: Optional[str] = Field(None, max_length=100, description="Industry sector")
    annual_revenue: Optional[float] = Field(None, ge=0, description="Annual revenue")
    current_debtors: Optional[float] = Field(None, ge=0, description="Current debtors amount")
    average_credit_days: Optional[int] = Field(30, ge=0, le=365, description="Average credit days")
    
    @field_validator('phone')
    @classmethod
    def validate_phone(cls, v: Optional[str]) -> Optional[str]:
        """Validate phone number format"""
        if v is None:
            return v
        # Remove spaces and dashes
        cleaned = v.replace(' ', '').replace('-', '')
        if not cleaned.isdigit():
            raise ValueError('Phone number must contain only digits, spaces, or dashes')
        if len(cleaned) < 10 or len(cleaned) > 15:
            raise ValueError('Phone number must be between 10 and 15 digits')
        return v


class ClientUpdate(BaseModel):
    """Schema for updating a client"""
    business_name: Optional[str] = Field(None, min_length=2, max_length=255)
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(None, max_length=20)
    industry: Optional[str] = Field(None, max_length=100)
    annual_revenue: Optional[float] = Field(None, ge=0)
    current_debtors: Optional[float] = Field(None, ge=0)
    average_credit_days: Optional[int] = Field(None, ge=0, le=365)


class ClientResponse(BaseModel):
    """Schema for client response"""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    business_name: str
    email: Optional[str]
    phone: Optional[str]
    industry: Optional[str]
    annual_revenue: Optional[float]
    current_debtors: Optional[float]
    average_credit_days: int
    created_at: datetime
