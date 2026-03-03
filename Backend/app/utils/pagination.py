"""Pagination utilities for API endpoints"""

from typing import Generic, TypeVar, List, Optional
from pydantic import BaseModel
from sqlalchemy.orm import Query
from math import ceil

T = TypeVar('T')


class PaginationParams(BaseModel):
    """Standard pagination parameters"""
    skip: int = 0
    limit: int = 100
    
    def validate_params(self):
        """Validate pagination parameters"""
        if self.skip < 0:
            self.skip = 0
        if self.limit < 1:
            self.limit = 1
        if self.limit > 1000:  # Max limit to prevent abuse
            self.limit = 1000


class PaginatedResponse(BaseModel, Generic[T]):
    """Standard paginated response format"""
    total: int
    items: List[T]
    skip: int
    limit: int
    page: int
    total_pages: int
    has_next: bool
    has_prev: bool
    
    class Config:
        arbitrary_types_allowed = True


def paginate(
    query: Query,
    skip: int = 0,
    limit: int = 100,
    max_limit: int = 1000
) -> tuple[List, int]:
    """
    Apply pagination to a SQLAlchemy query
    
    Args:
        query: SQLAlchemy query to paginate
        skip: Number of records to skip
        limit: Maximum number of records to return
        max_limit: Maximum allowed limit (prevents abuse)
        
    Returns:
        Tuple of (items, total_count)
    """
    # Validate parameters
    skip = max(0, skip)
    limit = max(1, min(limit, max_limit))
    
    # Get total count
    total = query.count()
    
    # Apply pagination
    items = query.offset(skip).limit(limit).all()
    
    return items, total


def create_paginated_response(
    items: List[T],
    total: int,
    skip: int,
    limit: int
) -> dict:
    """
    Create a standardized paginated response
    
    Args:
        items: List of items for current page
        total: Total number of items
        skip: Number of items skipped
        limit: Maximum items per page
        
    Returns:
        Dictionary with pagination metadata
    """
    page = (skip // limit) + 1 if limit > 0 else 1
    total_pages = ceil(total / limit) if limit > 0 else 1
    
    return {
        "total": total,
        "items": items,
        "skip": skip,
        "limit": limit,
        "page": page,
        "total_pages": total_pages,
        "has_next": skip + limit < total,
        "has_prev": skip > 0
    }
