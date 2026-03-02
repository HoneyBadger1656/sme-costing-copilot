# backend/app/models/models.py

from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text, Boolean, JSON, Enum
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
import uuid

from app.core.database import Base

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255))
    role = Column(String(50), default="ca")  # ca, sme_owner
    organization_id = Column(String(255), ForeignKey("organizations.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)
    
    organization = relationship("Organization", back_populates="users")
    clients = relationship("Client", back_populates="user")


class Organization(Base):
    __tablename__ = "organizations"
    
    id = Column(String(255), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(255), nullable=False)
    email = Column(String(255))
    subscription_plan = Column(String(50), default="trial")
    subscription_status = Column(String(50), default="trial")  # trial, active, cancelled, expired
    created_at = Column(DateTime, default=datetime.utcnow)
    
    users = relationship("User", back_populates="organization")


class Client(Base):
    __tablename__ = "clients"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    organization_id = Column(String(255), ForeignKey("organizations.id"))
    business_name = Column(String(255), nullable=False)
    email = Column(String(255))
    phone = Column(String(20))
    industry = Column(String(100))
    annual_revenue = Column(Float)
    current_debtors = Column(Float)
    average_credit_days = Column(Integer, default=30)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Integration credentials (encrypted)
    tally_config = Column(JSON)  # {url, port, company_id}
    zoho_tokens = Column(JSON)   # {access_token, refresh_token, expires_at}
    
    user = relationship("User", back_populates="clients")
    organization = relationship("Organization")
    products = relationship("Product", back_populates="client")
    orders = relationship("Order", back_populates="client")
    ledgers = relationship("Ledger", back_populates="client")
    financial_statements = relationship("FinancialStatement", back_populates="client")
    financial_ratios = relationship("FinancialRatio", back_populates="client")


class Product(Base):
    __tablename__ = "products"
    
    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=False)
    name = Column(String(255), nullable=False)
    category = Column(String(100))
    unit = Column(String(50), default="pcs")  # pcs, kg, litre, etc.
    
    # Costing inputs
    raw_material_cost = Column(Float, default=0)
    labour_cost_per_unit = Column(Float, default=0)
    overhead_percentage = Column(Float, default=10)  # % of direct cost
    
    # Pricing rules
    target_margin_percentage = Column(Float, default=20)
    tax_rate = Column(Float, default=18)  # GST %
    
    created_at = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)
    
    client = relationship("Client", back_populates="products")
    bom_items = relationship("BOMItem", back_populates="product")
    order_items = relationship("OrderItem", back_populates="product")


class BOMItem(Base):
    """Bill of Materials - detailed cost breakdown"""
    __tablename__ = "bom_items"
    
    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    component_name = Column(String(255), nullable=False)
    quantity = Column(Float, nullable=False)
    unit = Column(String(50), default="pcs")
    unit_cost = Column(Float, nullable=False)
    notes = Column(Text)
    
    product = relationship("Product", back_populates="bom_items")


class Order(Base):
    __tablename__ = "orders"
    
    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=False)
    order_number = Column(String(100), unique=True, index=True)
    customer_name = Column(String(255), nullable=False)
    order_date = Column(DateTime, default=datetime.utcnow)
    
    # Costing results
    total_cost = Column(Float, default=0)
    total_selling_price = Column(Float, default=0)
    gross_margin = Column(Float, default=0)
    margin_percentage = Column(Float, default=0)
    
    # Credit terms
    credit_days = Column(Integer, default=30)
    payment_status = Column(String(50), default="pending")  # pending, partial, paid
    amount_paid = Column(Float, default=0)
    due_date = Column(DateTime)
    
    # Working capital impact
    working_capital_blocked = Column(Float, default=0)
    
    status = Column(String(50), default="draft")  # draft, confirmed, invoiced, completed
    created_at = Column(DateTime, default=datetime.utcnow)
    
    client = relationship("Client", back_populates="orders")
    items = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")
    evaluation = relationship("OrderEvaluation", back_populates="order", uselist=False)


class OrderItem(Base):
    __tablename__ = "order_items"
    
    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    quantity = Column(Float, nullable=False)
    
    # Computed at order time
    unit_cost = Column(Float)
    unit_selling_price = Column(Float)
    total_cost = Column(Float)
    total_selling_price = Column(Float)
    margin = Column(Float)
    
    order = relationship("Order", back_populates="items")
    product = relationship("Product", back_populates="order_items")


class OrderEvaluation(Base):
    """AI-generated evaluation and recommendations"""
    __tablename__ = "order_evaluations"
    
    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False, unique=True)
    
    # Automated analysis
    profitability_score = Column(Float)  # 0-100
    risk_level = Column(String(50))  # low, medium, high
    recommendations = Column(Text)
    margin_analysis = Column(Text)
    working_capital_impact = Column(Text)
    
    # Decision support
    should_accept = Column(Boolean)
    suggested_changes = Column(JSON)  # [{field: "credit_days", current: 60, suggested: 45, reason: "..."}]
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    order = relationship("Order", back_populates="evaluation")


class Scenario(Base):
    """What-if analysis scenarios"""
    __tablename__ = "scenarios"
    
    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    
    # Base case (current state)
    base_data = Column(JSON)  # snapshot of key metrics
    
    # Changes to apply
    changes = Column(JSON)  # {raw_material_cost: -10, credit_days: +15, ...}
    
    # Computed impact
    impact_summary = Column(JSON)  # {revenue_change: +5%, margin_change: -2%, wc_change: +50000}
    
    created_at = Column(DateTime, default=datetime.utcnow)


class Ledger(Base):
    """Simple financial ledger for receivables/payables"""
    __tablename__ = "ledgers"
    
    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=False)
    ledger_type = Column(String(50), nullable=False)  # receivable, payable
    party_name = Column(String(255), nullable=False)  # customer or vendor name
    
    amount = Column(Float, nullable=False)
    transaction_date = Column(DateTime, default=datetime.utcnow)
    due_date = Column(DateTime)
    status = Column(String(50), default="outstanding")  # outstanding, paid
    payment_date = Column(DateTime)
    
    reference_type = Column(String(50))  # order, purchase, expense
    reference_id = Column(Integer)
    
    notes = Column(Text)
    
    client = relationship("Client", back_populates="ledgers")


class IntegrationSync(Base):
    """Track sync status with Tally/Zoho"""
    __tablename__ = "integration_syncs"
    
    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=False)
    integration_type = Column(String(50), nullable=False)  # tally, zoho
    sync_direction = Column(String(50))  # push, pull
    entity_type = Column(String(50))  # ledger, invoice, payment
    
    status = Column(String(50))  # success, failed, partial
    records_synced = Column(Integer, default=0)
    error_message = Column(Text)
    
    started_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime)


class FinancialStatement(Base):
    """Financial statements - Balance Sheet, P&L, Cash Flow"""
    __tablename__ = "financial_statements"
    
    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=False)
    statement_type = Column(String(50), nullable=False)  # balance_sheet, profit_loss, cash_flow
    period_type = Column(String(20), nullable=False)  # monthly, quarterly, yearly
    period_start = Column(DateTime, nullable=False)
    period_end = Column(DateTime, nullable=False)
    
    # Financial data
    financial_data = Column(JSON, nullable=False)  # structured financial data
    
    # Computed metrics
    current_ratio = Column(Float)
    quick_ratio = Column(Float)
    debt_equity_ratio = Column(Float)
    roa = Column(Float)
    roe = Column(Float)
    gross_margin = Column(Float)
    net_margin = Column(Float)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    client = relationship("Client")


class FinancialRatio(Base):
    """Stored financial ratios for historical tracking"""
    __tablename__ = "financial_ratios"
    
    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=False)
    statement_id = Column(Integer, ForeignKey("financial_statements.id"))
    
    # Ratio categories
    ratio_category = Column(String(50), nullable=False)  # liquidity, solvency, profitability, efficiency
    ratio_name = Column(String(100), nullable=False)
    ratio_value = Column(Float, nullable=False)
    
    # Benchmarking
    industry_average = Column(Float)
    benchmark_source = Column(String(100))  # industry_report, custom
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    client = relationship("Client")
    statement = relationship("FinancialStatement")


class ChatMessage(Base):
    """AI assistant conversation history"""
    __tablename__ = "chat_messages"
    
    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=False)
    role = Column(String(20), nullable=False)  # user, assistant
    content = Column(Text, nullable=False)
    
    # Metadata for context
    query_type = Column(String(100))  # financial_query, costing_query, general
    data_retrieved = Column(JSON)  # relevant data used to answer
    
    created_at = Column(DateTime, default=datetime.utcnow)
