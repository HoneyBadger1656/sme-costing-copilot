# backend/app/models/models.py

from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text, Boolean, JSON, Enum
from sqlalchemy.orm import relationship
from datetime import datetime
from typing import Optional
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
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    updated_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    deleted_at = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True)
    
    organization = relationship("Organization", back_populates="users")
    clients = relationship("Client", back_populates="user")
    
    @staticmethod
    def active(query):
        """Filter to return only non-deleted (active) users"""
        return query.filter(User.deleted_at.is_(None))
    
    @staticmethod
    def with_deleted(query):
        """Return all users including soft-deleted ones"""
        return query
    
    def soft_delete(self, deleted_by_user_id: Optional[int] = None):
        """Soft delete this user by setting deleted_at timestamp"""
        self.deleted_at = datetime.utcnow()
        if deleted_by_user_id:
            self.updated_by = deleted_by_user_id
        self.updated_at = datetime.utcnow()


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

    client = relationship("Client")


class Role(Base):
    """Role-Based Access Control roles"""
    __tablename__ = "roles"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, unique=True)
    description = Column(Text)
    permissions = Column(JSON, nullable=False)  # JSON structure with operation-level granularity
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user_roles = relationship("UserRole", back_populates="role", cascade="all, delete-orphan")
    
    def has_permission(self, permission: str) -> bool:
        """
        Check if this role has a specific permission.
        
        Args:
            permission: Permission name to check (e.g., 'billing', 'user_management', 'reports')
        
        Returns:
            bool: True if role has the permission, False otherwise
        """
        if not self.permissions:
            return False
        
        # Check for 'all' permission (Owner/Admin roles)
        if self.permissions.get('all', False):
            # If checking for billing, verify it's explicitly allowed
            if permission == 'billing':
                return self.permissions.get('billing', False)
            return True
        
        # Check for read_only mode (Viewer role)
        if self.permissions.get('read_only', False):
            # Viewer has read access but no write/delete/admin permissions
            if permission in ['write', 'delete', 'billing', 'user_management']:
                return False
            return True
        
        # Check specific permission
        return self.permissions.get(permission, False)


class UserRole(Base):
    """User role assignments within tenants"""
    __tablename__ = "user_roles"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    role_id = Column(Integer, ForeignKey("roles.id", ondelete="CASCADE"), nullable=False, index=True)
    tenant_id = Column(String(255), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    assigned_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    assigned_at = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", foreign_keys=[user_id], backref="user_roles")
    role = relationship("Role", back_populates="user_roles")
    tenant = relationship("Organization", foreign_keys=[tenant_id])
    assigner = relationship("User", foreign_keys=[assigned_by])
    
    # Unique constraint on (user_id, role_id, tenant_id)
    __table_args__ = (
        {'extend_existing': True}
    )
    
    @staticmethod
    def get_user_roles(db, user_id: int, tenant_id: str):
        """
        Get all roles for a user within a specific tenant.
        
        Args:
            db: Database session
            user_id: User ID
            tenant_id: Tenant/Organization ID
        
        Returns:
            List of Role objects assigned to the user in the tenant
        """
        from sqlalchemy.orm import joinedload
        
        user_roles = db.query(UserRole).options(
            joinedload(UserRole.role)
        ).filter(
            UserRole.user_id == user_id,
            UserRole.tenant_id == tenant_id
        ).all()
        
        return [ur.role for ur in user_roles]
    
    def has_permission(self, db, permission: str) -> bool:
        """
        Check if the user has a specific permission through this role assignment.
        
        Args:
            db: Database session
            permission: Permission name to check
        
        Returns:
            bool: True if user has the permission, False otherwise
        """
        if not self.role:
            # Load role if not already loaded
            role = db.query(Role).filter(Role.id == self.role_id).first()
            if not role:
                return False
            return role.has_permission(permission)
        
        return self.role.has_permission(permission)


    class AuditLog(Base):
        """Audit trail for all CUD operations"""
        __tablename__ = "audit_logs"

        id = Column(Integer, primary_key=True, index=True)
        tenant_id = Column(String(255), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
        user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
        action = Column(String(20), nullable=False)  # CREATE, UPDATE, DELETE
        table_name = Column(String(100), nullable=False, index=True)
        record_id = Column(Integer, nullable=False)
        old_values = Column(JSON, nullable=True)  # Previous state for UPDATE/DELETE
        new_values = Column(JSON, nullable=True)  # New state for CREATE/UPDATE
        ip_address = Column(String(45), nullable=True)
        user_agent = Column(String(500), nullable=True)
        created_at = Column(DateTime, default=datetime.utcnow, index=True)

        # Relationships
        tenant = relationship("Organization", foreign_keys=[tenant_id])
        user = relationship("User", foreign_keys=[user_id])

        # Composite indexes defined in migration
        __table_args__ = (
            {'extend_existing': True}
        )

        @staticmethod
        def get_record_history(db, table_name: str, record_id: int, tenant_id: str):
            """
            Get audit history for a specific record.

            Args:
                db: Database session
                table_name: Name of the table
                record_id: ID of the record
                tenant_id: Tenant/Organization ID

            Returns:
                List of AuditLog entries for the record, ordered by created_at desc
            """
            return db.query(AuditLog).filter(
                AuditLog.table_name == table_name,
                AuditLog.record_id == record_id,
                AuditLog.tenant_id == tenant_id
            ).order_by(AuditLog.created_at.desc()).all()

        @staticmethod
        def get_tenant_audit_trail(db, tenant_id: str, limit: int = 100, offset: int = 0):
            """
            Get audit trail for a tenant with pagination.

            Args:
                db: Database session
                tenant_id: Tenant/Organization ID
                limit: Maximum number of records to return
                offset: Number of records to skip

            Returns:
                List of AuditLog entries for the tenant, ordered by created_at desc
            """
            return db.query(AuditLog).filter(
                AuditLog.tenant_id == tenant_id
            ).order_by(AuditLog.created_at.desc()).limit(limit).offset(offset).all()




    class AuditLog(Base):
        """Audit trail for all CUD operations"""
        __tablename__ = "audit_logs"

        id = Column(Integer, primary_key=True, index=True)
        tenant_id = Column(String(255), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
        user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
        action = Column(String(20), nullable=False)  # CREATE, UPDATE, DELETE
        table_name = Column(String(100), nullable=False, index=True)
        record_id = Column(Integer, nullable=False)
        old_values = Column(JSON, nullable=True)  # Previous state for UPDATE/DELETE
        new_values = Column(JSON, nullable=True)  # New state for CREATE/UPDATE
        ip_address = Column(String(45), nullable=True)
        user_agent = Column(String(500), nullable=True)
        created_at = Column(DateTime, default=datetime.utcnow, index=True)

        # Relationships
        tenant = relationship("Organization", foreign_keys=[tenant_id])
        user = relationship("User", foreign_keys=[user_id])

        # Composite indexes defined in migration
        __table_args__ = (
            {'extend_existing': True}
        )

        @staticmethod
        def get_record_history(db, table_name: str, record_id: int, tenant_id: str):
            """
            Get audit history for a specific record.

            Args:
                db: Database session
                table_name: Name of the table
                record_id: ID of the record
                tenant_id: Tenant/Organization ID

            Returns:
                List of AuditLog entries for the record, ordered by created_at desc
            """
            return db.query(AuditLog).filter(
                AuditLog.table_name == table_name,
                AuditLog.record_id == record_id,
                AuditLog.tenant_id == tenant_id
            ).order_by(AuditLog.created_at.desc()).all()

        @staticmethod
        def get_tenant_audit_trail(db, tenant_id: str, limit: int = 100, offset: int = 0):
            """
            Get audit trail for a tenant with pagination.

            Args:
                db: Database session
                tenant_id: Tenant/Organization ID
                limit: Maximum number of records to return
                offset: Number of records to skip

            Returns:
                List of AuditLog entries for the tenant, ordered by created_at desc
            """
            return db.query(AuditLog).filter(
                AuditLog.tenant_id == tenant_id
            ).order_by(AuditLog.created_at.desc()).limit(limit).offset(offset).all()





class AuditLog(Base):
    """Audit trail for all CUD operations"""
    __tablename__ = "audit_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(String(255), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    action = Column(String(20), nullable=False)  # CREATE, UPDATE, DELETE
    table_name = Column(String(100), nullable=False, index=True)
    record_id = Column(Integer, nullable=False)
    old_values = Column(JSON, nullable=True)  # Previous state for UPDATE/DELETE
    new_values = Column(JSON, nullable=True)  # New state for CREATE/UPDATE
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(String(500), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    
    # Relationships
    tenant = relationship("Organization", foreign_keys=[tenant_id])
    user = relationship("User", foreign_keys=[user_id])
    
    # Composite indexes defined in migration
    __table_args__ = (
        {'extend_existing': True}
    )
    
    @staticmethod
    def get_record_history(db, table_name: str, record_id: int, tenant_id: str):
        """
        Get audit history for a specific record.
        
        Args:
            db: Database session
            table_name: Name of the table
            record_id: ID of the record
            tenant_id: Tenant/Organization ID
        
        Returns:
            List of AuditLog entries for the record, ordered by created_at desc
        """
        return db.query(AuditLog).filter(
            AuditLog.table_name == table_name,
            AuditLog.record_id == record_id,
            AuditLog.tenant_id == tenant_id
        ).order_by(AuditLog.created_at.desc()).all()
    
    @staticmethod
    def get_tenant_audit_trail(db, tenant_id: str, limit: int = 100, offset: int = 0):
        """
        Get audit trail for a tenant with pagination.
        
        Args:
            db: Database session
            tenant_id: Tenant/Organization ID
            limit: Maximum number of records to return
            offset: Number of records to skip
        
        Returns:
            List of AuditLog entries for the tenant, ordered by created_at desc
        """
        return db.query(AuditLog).filter(
            AuditLog.tenant_id == tenant_id
        ).order_by(AuditLog.created_at.desc()).limit(limit).offset(offset).all()


class NotificationPreference(Base):
    """User notification preferences"""
    __tablename__ = "notification_preferences"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    notification_type = Column(String(100), nullable=False)  # order_evaluation_complete, scenario_analysis_ready, etc.
    enabled = Column(Boolean, nullable=False, default=True)
    delivery_method = Column(String(50), nullable=False, default="email")  # email, sms, push
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", foreign_keys=[user_id])
    
    # Unique constraint on (user_id, notification_type) defined in migration
    __table_args__ = (
        {'extend_existing': True}
    )


class ReportSchedule(Base):
    """Scheduled report generation configuration"""
    __tablename__ = "report_schedules"
    
    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(String(255), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    template_id = Column(String(100), nullable=False)  # financial_statement, costing_analysis, etc.
    format = Column(String(20), nullable=False)  # pdf, excel, csv
    parameters = Column(JSON, nullable=True)  # Report-specific parameters
    frequency = Column(String(50), nullable=False)  # daily, weekly, monthly, custom
    cron_expression = Column(String(100), nullable=True)  # For custom schedules
    recipients = Column(JSON, nullable=False)  # List of email addresses
    next_run_at = Column(DateTime, nullable=False)
    last_run_at = Column(DateTime, nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    tenant = relationship("Organization", foreign_keys=[tenant_id])
    user = relationship("User", foreign_keys=[user_id])
    
    __table_args__ = (
        {'extend_existing': True}
    )
