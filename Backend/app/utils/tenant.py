"""Multi-tenancy isolation utilities"""

from sqlalchemy.orm import Session, Query
from typing import TypeVar, Type
from app.models.models import User

T = TypeVar('T')


class TenantFilter:
    """
    Tenant-aware query wrapper that automatically filters by organization_id
    Prevents data leakage between organizations
    """
    
    def __init__(self, db: Session, user: User):
        self.db = db
        self.organization_id = user.organization_id
        self.user_id = user.id
        
        if not self.organization_id:
            raise ValueError("User must be associated with an organization")
    
    def query(self, model: Type[T]) -> Query:
        """
        Create a query that's automatically filtered by organization_id
        
        Args:
            model: SQLAlchemy model class
            
        Returns:
            Query filtered by organization_id
            
        Raises:
            AttributeError: If model doesn't have organization_id field
        """
        if not hasattr(model, 'organization_id'):
            raise AttributeError(f"{model.__name__} does not have organization_id field")
        
        return self.db.query(model).filter(
            model.organization_id == self.organization_id
        )
    
    def get_by_id(self, model: Type[T], record_id: int) -> T:
        """
        Get a single record by ID with tenant isolation
        
        Args:
            model: SQLAlchemy model class
            record_id: Record ID to fetch
            
        Returns:
            Model instance or None
        """
        return self.query(model).filter(model.id == record_id).first()
    
    def verify_access(self, record) -> bool:
        """
        Verify that a record belongs to the current tenant
        
        Args:
            record: Model instance to check
            
        Returns:
            True if record belongs to tenant, False otherwise
        """
        if not hasattr(record, 'organization_id'):
            return False
        return record.organization_id == self.organization_id
