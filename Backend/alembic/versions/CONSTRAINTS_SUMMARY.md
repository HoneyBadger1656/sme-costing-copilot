# Database Integrity Constraints Summary

This document summarizes the CHECK constraints added to the Phase 3 migration (2e90ac41f1ba_phase_3_essential_features.py) to enforce data integrity at the database level.

## Requirements Coverage

These constraints implement Requirements 19.1-19.8 from the Phase 3 specification.

## Constraints Added

### 1. Non-Negative Cost Fields (Requirement 19.1)

**Products Table:**
- `ck_products_raw_material_cost_non_negative`: Ensures raw_material_cost >= 0
- `ck_products_labour_cost_non_negative`: Ensures labour_cost_per_unit >= 0

**BOM Items Table:**
- `ck_bom_items_unit_cost_non_negative`: Ensures unit_cost >= 0

**Orders Table:**
- `ck_orders_total_cost_non_negative`: Ensures total_cost >= 0
- `ck_orders_total_selling_price_non_negative`: Ensures total_selling_price >= 0
- `ck_orders_amount_paid_non_negative`: Ensures amount_paid >= 0
- `ck_orders_working_capital_blocked_non_negative`: Ensures working_capital_blocked >= 0

**Order Items Table:**
- `ck_order_items_unit_cost_non_negative`: Ensures unit_cost IS NULL OR unit_cost >= 0
- `ck_order_items_unit_selling_price_non_negative`: Ensures unit_selling_price IS NULL OR unit_selling_price >= 0
- `ck_order_items_total_cost_non_negative`: Ensures total_cost IS NULL OR total_cost >= 0
- `ck_order_items_total_selling_price_non_negative`: Ensures total_selling_price IS NULL OR total_selling_price >= 0

**Clients Table:**
- `ck_clients_annual_revenue_non_negative`: Ensures annual_revenue IS NULL OR annual_revenue >= 0
- `ck_clients_current_debtors_non_negative`: Ensures current_debtors IS NULL OR current_debtors >= 0

**Ledgers Table:**
- `ck_ledgers_amount_non_negative`: Ensures amount >= 0

### 2. Positive Quantity Fields (Requirement 19.2)

**BOM Items Table:**
- `ck_bom_items_quantity_positive`: Ensures quantity > 0

**Order Items Table:**
- `ck_order_items_quantity_positive`: Ensures quantity > 0

### 3. Percentage Fields (0-100 Range) (Requirement 19.3)

**Products Table:**
- `ck_products_overhead_percentage_range`: Ensures overhead_percentage >= 0 AND overhead_percentage <= 100
- `ck_products_target_margin_percentage_range`: Ensures target_margin_percentage >= 0 AND target_margin_percentage <= 100
- `ck_products_tax_rate_range`: Ensures tax_rate >= 0 AND tax_rate <= 100

**Orders Table:**
- `ck_orders_margin_percentage_range`: Ensures margin_percentage >= 0 AND margin_percentage <= 100

**Order Evaluations Table:**
- `ck_order_evaluations_profitability_score_range`: Ensures profitability_score IS NULL OR (profitability_score >= 0 AND profitability_score <= 100)

**Financial Statements Table:**
- `ck_financial_statements_gross_margin_range`: Ensures gross_margin IS NULL OR (gross_margin >= 0 AND gross_margin <= 100)
- `ck_financial_statements_net_margin_range`: Ensures net_margin IS NULL OR (net_margin >= 0 AND net_margin <= 100)

### 4. Date Range Constraints (Requirement 19.4)

**Financial Statements Table:**
- `ck_financial_statements_period_dates`: Ensures period_end >= period_start

### 5. NOT NULL Constraints (Requirement 19.5)

NOT NULL constraints are already enforced in the SQLAlchemy model definitions with `nullable=False`. No additional migration changes needed.

### 6. Email Format Validation (Requirement 19.7)

**Users Table:**
- `ck_users_email_format`: Ensures email LIKE '%@%.%'

**Organizations Table:**
- `ck_organizations_email_format`: Ensures email IS NULL OR email LIKE '%@%.%'

**Clients Table:**
- `ck_clients_email_format`: Ensures email IS NULL OR email LIKE '%@%.%'

### 7. Additional Business Logic Constraints

**Clients Table:**
- `ck_clients_average_credit_days_positive`: Ensures average_credit_days > 0

**Orders Table:**
- `ck_orders_credit_days_positive`: Ensures credit_days > 0

## SQLite Compatibility

All constraints use SQLite-compatible syntax:
- Batch mode operations for ALTER TABLE statements
- Simple LIKE pattern matching for email validation
- Standard SQL CHECK constraint syntax

## Downgrade Support

The downgrade() function properly removes all constraints in reverse order of creation, ensuring clean rollback capability.

## Testing

Constraints have been tested to verify:
1. Invalid data is rejected (negative costs, invalid percentages, etc.)
2. Valid data is accepted
3. NULL handling works correctly for nullable fields
4. Email format validation works as expected

## Notes

- Requirement 19.6 (UNIQUE constraints on natural keys) is not implemented in this migration as the Product.sku field does not exist in the current schema
- All constraints use descriptive names following the pattern: `ck_{table}_{field}_{constraint_type}`
- Nullable fields include NULL checks in their constraints (e.g., `field IS NULL OR field >= 0`)
