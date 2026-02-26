from sqlalchemy import Column, String, DateTime, ForeignKey, Integer, Numeric, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import uuid
from datetime import datetime

from app.core.database import Base

class Organization(Base):
    __tablename__ = "organizations"
    
    id = Column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(255), nullable=False)
    email = Column(String(255), nullable=False, unique=True)
    phone = Column(String(20))
    subscription_status = Column(String(50), default="trial")
    subscription_plan = Column(String(50))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    users = relationship("User", back_populates="organization")
    clients = relationship("Client", back_populates="organization")

class User(Base):
    __tablename__ = "users"
    
    id = Column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4()))
    organization_id = Column(UUID(as_uuid=False), ForeignKey("organizations.id"))
    email = Column(String(255), nullable=False, unique=True)
    password_hash = Column(String(255), nullable=False)
    name = Column(String(255))
    role = Column(String(50), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    organization = relationship("Organization", back_populates="users")

class Client(Base):
    __tablename__ = "clients"
    
    id = Column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4()))
    organization_id = Column(UUID(as_uuid=False), ForeignKey("organizations.id"))
    business_name = Column(String(255), nullable=False)
    email = Column(String(255))
    phone = Column(String(20))
    industry = Column(String(100))
    annual_revenue = Column(Numeric(15, 2))
    current_debtors = Column(Numeric(15, 2), default=0)
    average_credit_days = Column(Integer, default=30)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    organization = relationship("Organization", back_populates="clients")
    products = relationship("Product", back_populates="client")
    evaluations = relationship("OrderEvaluation", back_populates="client")

class Product(Base):
    __tablename__ = "products"
    
    id = Column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4()))
    client_id = Column(UUID(as_uuid=False), ForeignKey("clients.id"))
    product_name = Column(String(255), nullable=False)
    selling_price = Column(Numeric(10, 2))
    cost_price = Column(Numeric(10, 2))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    client = relationship("Client", back_populates="products")

class OrderEvaluation(Base):
    __tablename__ = "order_evaluations"
    
    id = Column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4()))
    client_id = Column(UUID(as_uuid=False), ForeignKey("clients.id"))
    evaluated_by = Column(UUID(as_uuid=False), ForeignKey("users.id"))
    customer_name = Column(String(255))
    product_name = Column(String(255))
    quantity = Column(Numeric(10, 2))
    proposed_price = Column(Numeric(10, 2))
    proposed_credit_days = Column(Integer)
    contribution_margin = Column(Numeric(10, 2))
    margin_percentage = Column(Numeric(5, 2))
    working_capital_impact = Column(Numeric(15, 2))
    decision = Column(String(50))
    reasons = Column(Text)
    recommendation = Column(Text)
    ai_explanation = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    client = relationship("Client", back_populates="evaluations")
