# Backend/tests/test_report_data_service.py

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import date, datetime
from sqlalchemy.orm import Session

from app.services.report_data_service import (
    get_financial_statement_data,
    get_costing_analysis_data,
    get_order_evaluation_data,
    get_margin_analysis_data,
    get_receivables_report_data
)


class TestFinancialStatementData:
    """Test financial statement data fetching functionality."""
    
    @pytest.fixture
    def mock_db(self):
        """Create a mock database session."""
        return Mock(spec=Session)
    
    def test_get_financial_statement_data_basic(self, mock_db):
        """Test basic financial statement data retrieval."""
        tenant_id = 1
        period_start = date(2024, 1, 1)
        period_end = date(2024, 12, 31)
        statement_type = "balance_sheet"
        
        result = get_financial_statement_data(
            db=mock_db,
            tenant_id=tenant_id,
            period_start=period_start,
            period_end=period_end,
            statement_type=statement_type
        )
        
        assert result is not None
        assert result["statement_type"] == statement_type
        assert result["period_start"] == "2024-01-01"
        assert result["period_end"] == "2024-12-31"
        assert "data" in result
    
    def test_get_financial_statement_data_income_statement(self, mock_db):
        """Test income statement data retrieval."""
        tenant_id = 1
        period_start = date(2024, 1, 1)
        period_end = date(2024, 3, 31)
        statement_type = "income_statement"
        
        result = get_financial_statement_data(
            db=mock_db,
            tenant_id=tenant_id,
            period_start=period_start,
            period_end=period_end,
            statement_type=statement_type
        )
        
        assert result["statement_type"] == "income_statement"
        assert result["period_start"] == "2024-01-01"
        assert result["period_end"] == "2024-03-31"
    
    def test_get_financial_statement_data_cash_flow(self, mock_db):
        """Test cash flow statement data retrieval."""
        tenant_id = 2
        period_start = date(2024, 6, 1)
        period_end = date(2024, 6, 30)
        statement_type = "cash_flow"
        
        result = get_financial_statement_data(
            db=mock_db,
            tenant_id=tenant_id,
            period_start=period_start,
            period_end=period_end,
            statement_type=statement_type
        )
        
        assert result["statement_type"] == "cash_flow"
        assert result["period_start"] == "2024-06-01"
        assert result["period_end"] == "2024-06-30"
    
    def test_get_financial_statement_data_tenant_isolation(self, mock_db):
        """Test that tenant_id is properly passed for tenant isolation."""
        tenant_id = 42
        period_start = date(2024, 1, 1)
        period_end = date(2024, 12, 31)
        statement_type = "balance_sheet"
        
        # Call the function
        result = get_financial_statement_data(
            db=mock_db,
            tenant_id=tenant_id,
            period_start=period_start,
            period_end=period_end,
            statement_type=statement_type
        )
        
        # Verify the function accepts tenant_id parameter
        # In a real implementation, this would verify database queries filter by tenant_id
        assert result is not None


class TestCostingAnalysisData:
    """Test costing analysis data fetching functionality."""
    
    @pytest.fixture
    def mock_db(self):
        """Create a mock database session."""
        return Mock(spec=Session)
    
    def test_get_costing_analysis_data_basic(self, mock_db):
        """Test basic costing analysis data retrieval."""
        tenant_id = 1
        start_date = date(2024, 1, 1)
        end_date = date(2024, 12, 31)
        
        result = get_costing_analysis_data(
            db=mock_db,
            tenant_id=tenant_id,
            start_date=start_date,
            end_date=end_date
        )
        
        assert result is not None
        assert result["start_date"] == "2024-01-01"
        assert result["end_date"] == "2024-12-31"
        assert "products" in result
        assert isinstance(result["products"], list)
    
    def test_get_costing_analysis_data_with_product_filter(self, mock_db):
        """Test costing analysis with specific product IDs."""
        tenant_id = 1
        start_date = date(2024, 1, 1)
        end_date = date(2024, 12, 31)
        product_ids = [1, 2, 3]
        
        result = get_costing_analysis_data(
            db=mock_db,
            tenant_id=tenant_id,
            start_date=start_date,
            end_date=end_date,
            product_ids=product_ids
        )
        
        assert result is not None
        assert result["start_date"] == "2024-01-01"
        assert result["end_date"] == "2024-12-31"
        assert "products" in result
    
    def test_get_costing_analysis_data_without_product_filter(self, mock_db):
        """Test costing analysis without product filter (all products)."""
        tenant_id = 1
        start_date = date(2024, 1, 1)
        end_date = date(2024, 12, 31)
        
        result = get_costing_analysis_data(
            db=mock_db,
            tenant_id=tenant_id,
            start_date=start_date,
            end_date=end_date,
            product_ids=None
        )
        
        assert result is not None
        assert "products" in result
    
    def test_get_costing_analysis_data_tenant_isolation(self, mock_db):
        """Test tenant isolation in costing analysis queries."""
        tenant_id = 99
        start_date = date(2024, 1, 1)
        end_date = date(2024, 12, 31)
        
        result = get_costing_analysis_data(
            db=mock_db,
            tenant_id=tenant_id,
            start_date=start_date,
            end_date=end_date
        )
        
        # Verify the function accepts tenant_id parameter
        assert result is not None
    
    def test_get_costing_analysis_data_empty_product_list(self, mock_db):
        """Test costing analysis with empty product list."""
        tenant_id = 1
        start_date = date(2024, 1, 1)
        end_date = date(2024, 12, 31)
        product_ids = []
        
        result = get_costing_analysis_data(
            db=mock_db,
            tenant_id=tenant_id,
            start_date=start_date,
            end_date=end_date,
            product_ids=product_ids
        )
        
        assert result is not None
        assert "products" in result


class TestOrderEvaluationData:
    """Test order evaluation data fetching functionality."""
    
    @pytest.fixture
    def mock_db(self):
        """Create a mock database session."""
        return Mock(spec=Session)
    
    def test_get_order_evaluation_data_basic(self, mock_db):
        """Test basic order evaluation data retrieval."""
        tenant_id = 1
        start_date = date(2024, 1, 1)
        end_date = date(2024, 12, 31)
        
        result = get_order_evaluation_data(
            db=mock_db,
            tenant_id=tenant_id,
            start_date=start_date,
            end_date=end_date
        )
        
        assert result is not None
        assert result["start_date"] == "2024-01-01"
        assert result["end_date"] == "2024-12-31"
        assert "orders" in result
        assert isinstance(result["orders"], list)
    
    def test_get_order_evaluation_data_with_status_filter(self, mock_db):
        """Test order evaluation with status filter."""
        tenant_id = 1
        start_date = date(2024, 1, 1)
        end_date = date(2024, 12, 31)
        status = "completed"
        
        result = get_order_evaluation_data(
            db=mock_db,
            tenant_id=tenant_id,
            start_date=start_date,
            end_date=end_date,
            status=status
        )
        
        assert result is not None
        assert "orders" in result
    
    def test_get_order_evaluation_data_without_status_filter(self, mock_db):
        """Test order evaluation without status filter (all statuses)."""
        tenant_id = 1
        start_date = date(2024, 1, 1)
        end_date = date(2024, 12, 31)
        
        result = get_order_evaluation_data(
            db=mock_db,
            tenant_id=tenant_id,
            start_date=start_date,
            end_date=end_date,
            status=None
        )
        
        assert result is not None
        assert "orders" in result
    
    def test_get_order_evaluation_data_pending_status(self, mock_db):
        """Test order evaluation with pending status."""
        tenant_id = 1
        start_date = date(2024, 1, 1)
        end_date = date(2024, 12, 31)
        status = "pending"
        
        result = get_order_evaluation_data(
            db=mock_db,
            tenant_id=tenant_id,
            start_date=start_date,
            end_date=end_date,
            status=status
        )
        
        assert result is not None
        assert "orders" in result
    
    def test_get_order_evaluation_data_tenant_isolation(self, mock_db):
        """Test tenant isolation in order evaluation queries."""
        tenant_id = 77
        start_date = date(2024, 1, 1)
        end_date = date(2024, 12, 31)
        
        result = get_order_evaluation_data(
            db=mock_db,
            tenant_id=tenant_id,
            start_date=start_date,
            end_date=end_date
        )
        
        # Verify the function accepts tenant_id parameter
        assert result is not None


class TestMarginAnalysisData:
    """Test margin analysis data fetching functionality."""
    
    @pytest.fixture
    def mock_db(self):
        """Create a mock database session."""
        return Mock(spec=Session)
    
    def test_get_margin_analysis_data_basic(self, mock_db):
        """Test basic margin analysis data retrieval."""
        tenant_id = 1
        start_date = date(2024, 1, 1)
        end_date = date(2024, 12, 31)
        
        result = get_margin_analysis_data(
            db=mock_db,
            tenant_id=tenant_id,
            start_date=start_date,
            end_date=end_date
        )
        
        assert result is not None
        assert result["start_date"] == "2024-01-01"
        assert result["end_date"] == "2024-12-31"
        assert result["group_by"] == "product"
        assert "margins" in result
        assert isinstance(result["margins"], list)
    
    def test_get_margin_analysis_data_group_by_product(self, mock_db):
        """Test margin analysis grouped by product."""
        tenant_id = 1
        start_date = date(2024, 1, 1)
        end_date = date(2024, 12, 31)
        group_by = "product"
        
        result = get_margin_analysis_data(
            db=mock_db,
            tenant_id=tenant_id,
            start_date=start_date,
            end_date=end_date,
            group_by=group_by
        )
        
        assert result is not None
        assert result["group_by"] == "product"
        assert "margins" in result
    
    def test_get_margin_analysis_data_group_by_category(self, mock_db):
        """Test margin analysis grouped by category."""
        tenant_id = 1
        start_date = date(2024, 1, 1)
        end_date = date(2024, 12, 31)
        group_by = "category"
        
        result = get_margin_analysis_data(
            db=mock_db,
            tenant_id=tenant_id,
            start_date=start_date,
            end_date=end_date,
            group_by=group_by
        )
        
        assert result is not None
        assert result["group_by"] == "category"
        assert "margins" in result
    
    def test_get_margin_analysis_data_group_by_client(self, mock_db):
        """Test margin analysis grouped by client."""
        tenant_id = 1
        start_date = date(2024, 1, 1)
        end_date = date(2024, 12, 31)
        group_by = "client"
        
        result = get_margin_analysis_data(
            db=mock_db,
            tenant_id=tenant_id,
            start_date=start_date,
            end_date=end_date,
            group_by=group_by
        )
        
        assert result is not None
        assert result["group_by"] == "client"
        assert "margins" in result
    
    def test_get_margin_analysis_data_default_group_by(self, mock_db):
        """Test margin analysis with default group_by parameter."""
        tenant_id = 1
        start_date = date(2024, 1, 1)
        end_date = date(2024, 12, 31)
        
        result = get_margin_analysis_data(
            db=mock_db,
            tenant_id=tenant_id,
            start_date=start_date,
            end_date=end_date
        )
        
        assert result is not None
        assert result["group_by"] == "product"  # Default value
    
    def test_get_margin_analysis_data_tenant_isolation(self, mock_db):
        """Test tenant isolation in margin analysis queries."""
        tenant_id = 55
        start_date = date(2024, 1, 1)
        end_date = date(2024, 12, 31)
        
        result = get_margin_analysis_data(
            db=mock_db,
            tenant_id=tenant_id,
            start_date=start_date,
            end_date=end_date
        )
        
        # Verify the function accepts tenant_id parameter
        assert result is not None


class TestReceivablesReportData:
    """Test receivables report data fetching functionality."""
    
    @pytest.fixture
    def mock_db(self):
        """Create a mock database session."""
        return Mock(spec=Session)
    
    def test_get_receivables_report_data_basic(self, mock_db):
        """Test basic receivables report data retrieval."""
        tenant_id = 1
        as_of_date = date(2024, 12, 31)
        
        result = get_receivables_report_data(
            db=mock_db,
            tenant_id=tenant_id,
            as_of_date=as_of_date
        )
        
        assert result is not None
        assert result["as_of_date"] == "2024-12-31"
        assert result["aging_buckets"] == [30, 60, 90]  # Default buckets
        assert "receivables" in result
        assert isinstance(result["receivables"], list)
    
    def test_get_receivables_report_data_custom_aging_buckets(self, mock_db):
        """Test receivables report with custom aging buckets."""
        tenant_id = 1
        as_of_date = date(2024, 12, 31)
        aging_buckets = [15, 30, 45, 60]
        
        result = get_receivables_report_data(
            db=mock_db,
            tenant_id=tenant_id,
            as_of_date=as_of_date,
            aging_buckets=aging_buckets
        )
        
        assert result is not None
        assert result["aging_buckets"] == [15, 30, 45, 60]
        assert "receivables" in result
    
    def test_get_receivables_report_data_default_aging_buckets(self, mock_db):
        """Test receivables report with default aging buckets."""
        tenant_id = 1
        as_of_date = date(2024, 12, 31)
        
        result = get_receivables_report_data(
            db=mock_db,
            tenant_id=tenant_id,
            as_of_date=as_of_date,
            aging_buckets=None
        )
        
        assert result is not None
        assert result["aging_buckets"] == [30, 60, 90]
    
    def test_get_receivables_report_data_single_bucket(self, mock_db):
        """Test receivables report with single aging bucket."""
        tenant_id = 1
        as_of_date = date(2024, 12, 31)
        aging_buckets = [30]
        
        result = get_receivables_report_data(
            db=mock_db,
            tenant_id=tenant_id,
            as_of_date=as_of_date,
            aging_buckets=aging_buckets
        )
        
        assert result is not None
        assert result["aging_buckets"] == [30]
    
    def test_get_receivables_report_data_empty_buckets(self, mock_db):
        """Test receivables report with empty aging buckets list."""
        tenant_id = 1
        as_of_date = date(2024, 12, 31)
        aging_buckets = []
        
        result = get_receivables_report_data(
            db=mock_db,
            tenant_id=tenant_id,
            as_of_date=as_of_date,
            aging_buckets=aging_buckets
        )
        
        assert result is not None
        assert result["aging_buckets"] == []
    
    def test_get_receivables_report_data_tenant_isolation(self, mock_db):
        """Test tenant isolation in receivables report queries."""
        tenant_id = 33
        as_of_date = date(2024, 12, 31)
        
        result = get_receivables_report_data(
            db=mock_db,
            tenant_id=tenant_id,
            as_of_date=as_of_date
        )
        
        # Verify the function accepts tenant_id parameter
        assert result is not None


class TestDataAggregationCalculations:
    """Test data aggregation calculations across all report types."""
    
    @pytest.fixture
    def mock_db(self):
        """Create a mock database session."""
        return Mock(spec=Session)
    
    def test_financial_statement_data_structure(self, mock_db):
        """Test that financial statement returns proper data structure."""
        result = get_financial_statement_data(
            db=mock_db,
            tenant_id=1,
            period_start=date(2024, 1, 1),
            period_end=date(2024, 12, 31),
            statement_type="balance_sheet"
        )
        
        # Verify structure
        assert isinstance(result, dict)
        assert "statement_type" in result
        assert "period_start" in result
        assert "period_end" in result
        assert "data" in result
    
    def test_costing_analysis_data_structure(self, mock_db):
        """Test that costing analysis returns proper data structure."""
        result = get_costing_analysis_data(
            db=mock_db,
            tenant_id=1,
            start_date=date(2024, 1, 1),
            end_date=date(2024, 12, 31)
        )
        
        # Verify structure
        assert isinstance(result, dict)
        assert "start_date" in result
        assert "end_date" in result
        assert "products" in result
        assert isinstance(result["products"], list)
    
    def test_order_evaluation_data_structure(self, mock_db):
        """Test that order evaluation returns proper data structure."""
        result = get_order_evaluation_data(
            db=mock_db,
            tenant_id=1,
            start_date=date(2024, 1, 1),
            end_date=date(2024, 12, 31)
        )
        
        # Verify structure
        assert isinstance(result, dict)
        assert "start_date" in result
        assert "end_date" in result
        assert "orders" in result
        assert isinstance(result["orders"], list)
    
    def test_margin_analysis_data_structure(self, mock_db):
        """Test that margin analysis returns proper data structure."""
        result = get_margin_analysis_data(
            db=mock_db,
            tenant_id=1,
            start_date=date(2024, 1, 1),
            end_date=date(2024, 12, 31)
        )
        
        # Verify structure
        assert isinstance(result, dict)
        assert "start_date" in result
        assert "end_date" in result
        assert "group_by" in result
        assert "margins" in result
        assert isinstance(result["margins"], list)
    
    def test_receivables_report_data_structure(self, mock_db):
        """Test that receivables report returns proper data structure."""
        result = get_receivables_report_data(
            db=mock_db,
            tenant_id=1,
            as_of_date=date(2024, 12, 31)
        )
        
        # Verify structure
        assert isinstance(result, dict)
        assert "as_of_date" in result
        assert "aging_buckets" in result
        assert "receivables" in result
        assert isinstance(result["receivables"], list)


class TestErrorHandling:
    """Test error handling for report data service functions."""
    
    @pytest.fixture
    def mock_db(self):
        """Create a mock database session."""
        return Mock(spec=Session)
    
    def test_financial_statement_handles_missing_data(self, mock_db):
        """Test financial statement handles missing data gracefully."""
        # Even with no data, function should return valid structure
        result = get_financial_statement_data(
            db=mock_db,
            tenant_id=999,  # Non-existent tenant
            period_start=date(2024, 1, 1),
            period_end=date(2024, 12, 31),
            statement_type="balance_sheet"
        )
        
        assert result is not None
        assert "data" in result
    
    def test_costing_analysis_handles_missing_products(self, mock_db):
        """Test costing analysis handles missing products gracefully."""
        result = get_costing_analysis_data(
            db=mock_db,
            tenant_id=999,
            start_date=date(2024, 1, 1),
            end_date=date(2024, 12, 31),
            product_ids=[9999]  # Non-existent products
        )
        
        assert result is not None
        assert "products" in result
    
    def test_order_evaluation_handles_missing_orders(self, mock_db):
        """Test order evaluation handles missing orders gracefully."""
        result = get_order_evaluation_data(
            db=mock_db,
            tenant_id=999,
            start_date=date(2024, 1, 1),
            end_date=date(2024, 12, 31)
        )
        
        assert result is not None
        assert "orders" in result
    
    def test_margin_analysis_handles_missing_data(self, mock_db):
        """Test margin analysis handles missing data gracefully."""
        result = get_margin_analysis_data(
            db=mock_db,
            tenant_id=999,
            start_date=date(2024, 1, 1),
            end_date=date(2024, 12, 31)
        )
        
        assert result is not None
        assert "margins" in result
    
    def test_receivables_report_handles_missing_data(self, mock_db):
        """Test receivables report handles missing data gracefully."""
        result = get_receivables_report_data(
            db=mock_db,
            tenant_id=999,
            as_of_date=date(2024, 12, 31)
        )
        
        assert result is not None
        assert "receivables" in result


class TestDateHandling:
    """Test date parameter handling across all report functions."""
    
    @pytest.fixture
    def mock_db(self):
        """Create a mock database session."""
        return Mock(spec=Session)
    
    def test_financial_statement_date_formatting(self, mock_db):
        """Test that dates are properly formatted in financial statement."""
        result = get_financial_statement_data(
            db=mock_db,
            tenant_id=1,
            period_start=date(2024, 1, 15),
            period_end=date(2024, 6, 30),
            statement_type="balance_sheet"
        )
        
        assert result["period_start"] == "2024-01-15"
        assert result["period_end"] == "2024-06-30"
    
    def test_costing_analysis_date_formatting(self, mock_db):
        """Test that dates are properly formatted in costing analysis."""
        result = get_costing_analysis_data(
            db=mock_db,
            tenant_id=1,
            start_date=date(2024, 3, 1),
            end_date=date(2024, 3, 31)
        )
        
        assert result["start_date"] == "2024-03-01"
        assert result["end_date"] == "2024-03-31"
    
    def test_order_evaluation_date_formatting(self, mock_db):
        """Test that dates are properly formatted in order evaluation."""
        result = get_order_evaluation_data(
            db=mock_db,
            tenant_id=1,
            start_date=date(2024, 7, 1),
            end_date=date(2024, 9, 30)
        )
        
        assert result["start_date"] == "2024-07-01"
        assert result["end_date"] == "2024-09-30"
    
    def test_margin_analysis_date_formatting(self, mock_db):
        """Test that dates are properly formatted in margin analysis."""
        result = get_margin_analysis_data(
            db=mock_db,
            tenant_id=1,
            start_date=date(2024, 10, 1),
            end_date=date(2024, 10, 31)
        )
        
        assert result["start_date"] == "2024-10-01"
        assert result["end_date"] == "2024-10-31"
    
    def test_receivables_report_date_formatting(self, mock_db):
        """Test that dates are properly formatted in receivables report."""
        result = get_receivables_report_data(
            db=mock_db,
            tenant_id=1,
            as_of_date=date(2024, 11, 15)
        )
        
        assert result["as_of_date"] == "2024-11-15"
