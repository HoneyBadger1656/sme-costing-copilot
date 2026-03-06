# Implementation Plan: Phase 3 Essential Missing Features

## Overview

This implementation plan breaks down Phase 3 into discrete coding tasks that build incrementally. The plan follows the existing FastAPI + SQLAlchemy architecture and maintains backward compatibility with all 17 existing tests.

Implementation order prioritizes database foundation first, then RBAC (security layer), audit trail (compliance), reports (business value), and finally notifications (user experience).

## Tasks

- [ ] 1. Database schema enhancements and migration
  - [x] 1.1 Create Alembic migration script for Phase 3 schema changes
    - Create new migration file using `alembic revision -m "phase_3_essential_features"`
    - Add audit fields (created_at, updated_at, created_by, updated_by, deleted_at) to all existing tables
    - Create Role table with fields: id, name, description, permissions (JSON), created_at, updated_at
    - Create UserRole table with fields: id, user_id, role_id, tenant_id, assigned_by, assigned_at, created_at, updated_at
    - Create AuditLog table with fields: id, tenant_id, user_id, action, table_name, record_id, old_values (JSON), new_values (JSON), ip_address, user_agent, created_at
    - Create NotificationPreference table with fields: id, user_id, notification_type, enabled, delivery_method, created_at, updated_at
    - Add all foreign key constraints and unique constraints
    - _Requirements: 1.1, 1.2, 1.6, 1.7, 1.8, 5.1, 5.6, 5.7, 16.1, 19.5, 19.6, 20.1-20.5, 22.1-22.3_

  - [x] 1.2 Add database indexes for performance optimization
    - Create indexes on all foreign key columns
    - Create composite index on (tenant_id, created_at) for all tenant-scoped tables
    - Create index on User.email for authentication queries
    - Create index on (tenant_id, status) for filtered list queries
    - Create indexes on AuditLog: (tenant_id, created_at), (table_name, record_id)
    - Create index on Order.order_date and Invoice.due_date
    - Create index on Product.sku
    - _Requirements: 18.1-18.8_

  - [x] 1.3 Add database integrity constraints
    - Add CHECK constraints for non-negative cost fields
    - Add CHECK constraints for positive quantity fields
    - Add CHECK constraints for percentage fields (0-100 range)
    - Add CHECK constraints for date ranges (end_date >= start_date)
    - Add NOT NULL constraints to required fields
    - Add CHECK constraint for email format validation
    - _Requirements: 19.1-19.8_

  - [x] 1.4 Populate predefined roles and assign to existing users
    - Insert four predefined roles: Owner, Admin, Accountant, Viewer with appropriate permissions
    - Assign Owner role to first user in each tenant
    - Create default notification preferences for existing users
    - _Requirements: 1.3, 1.4, 22.5, 22.6_

  - [x] 1.5 Write migration tests
    - Test migration upgrade and downgrade functions
    - Verify all tables, indexes, and constraints are created
    - Verify data integrity after migration
    - _Requirements: 22.7, 22.8_

- [ ] 2. RBAC foundation - Models and schemas
  - [x] 2.1 Create Role and UserRole SQLAlchemy models
    - Add Role model to Backend/app/models/models.py
    - Add UserRole model with relationships to User, Role, and Tenant
    - Define permissions JSON structure with operation-level granularity
    - Add model methods: has_permission(), get_user_roles()
    - _Requirements: 1.1, 1.2, 1.3, 1.4_

  - [x] 2.2 Create Pydantic schemas for RBAC
    - Create Backend/app/schemas/rbac.py with RoleCreate, RoleResponse, UserRoleCreate, UserRoleResponse schemas
    - Add validation for role names and permission structure
    - Add schema for role assignment requests
    - _Requirements: 1.1, 1.2, 4.1-4.5_

  - [x] 2.3 Update User model with audit fields
    - Add created_at, updated_at, created_by, updated_by, deleted_at fields to User model
    - Add soft delete query methods: active(), with_deleted()
    - Update User model to automatically set timestamps
    - _Requirements: 20.1-20.8, 21.1-21.3_

  - [x] 2.4 Write unit tests for RBAC models
    - Test Role model creation and permission checks
    - Test UserRole relationships and queries
    - Test soft delete functionality on User model
    - _Requirements: 24.1, 24.2_

- [ ] 3. RBAC middleware and decorators
  - [x] 3.1 Create RBAC utility module
    - Create Backend/app/utils/rbac.py
    - Implement get_user_roles(user_id, tenant_id) function
    - Implement check_permission(user, permission) function
    - Implement check_role(user, role_name) function
    - _Requirements: 2.1, 2.2, 2.5, 2.6_

  - [x] 3.2 Implement require_role decorator
    - Create require_role decorator that accepts role names
    - Extract current user and tenant from request context
    - Verify user has required role in current tenant
    - Return HTTP 403 with descriptive error if unauthorized
    - Log all authorization failures
    - _Requirements: 2.1, 2.2, 2.3, 2.7, 2.8, 29.1_

  - [x] 3.3 Implement require_permission decorator
    - Create require_permission decorator that accepts permission names
    - Check user permissions within tenant context
    - Return HTTP 403 with descriptive error if unauthorized
    - Log all authorization failures
    - _Requirements: 2.4, 2.5, 2.6, 2.7, 2.8, 29.1_

  - [x] 3.4 Write unit tests for RBAC decorators
    - Test require_role with valid and invalid roles
    - Test require_permission with various permission combinations
    - Test tenant context isolation
    - Test authorization failure logging
    - _Requirements: 24.1, 24.2_

- [ ] 4. RBAC API endpoints
  - [x] 4.1 Create role management service
    - Create Backend/app/services/rbac_service.py
    - Implement create_role(), get_roles(), get_role_by_id() methods
    - Implement assign_role(), revoke_role(), get_user_roles() methods
    - Add validation to prevent self-modification of Owner role
    - _Requirements: 4.1-4.8_

  - [x] 4.2 Create role management API endpoints
    - Create Backend/app/api/roles.py
    - Implement POST /api/roles (create custom role) - Owner/Admin only
    - Implement GET /api/roles (list all roles in tenant)
    - Implement POST /api/users/{user_id}/roles (assign role) - Owner/Admin only
    - Implement DELETE /api/users/{user_id}/roles/{role_id} (revoke role) - Owner/Admin only
    - Implement GET /api/users/{user_id}/roles (list user's roles)
    - Apply require_role decorators to enforce access control
    - _Requirements: 4.1-4.8_

  - [x] 4.3 Write integration tests for role management API
    - Test role creation, listing, assignment, and revocation workflows
    - Test authorization enforcement on role endpoints
    - Test prevention of self-modification of Owner role
    - Test tenant isolation for role operations
    - _Requirements: 24.2_

- [ ] 5. Apply RBAC to existing endpoints
  - [x] 5.1 Add role checks to financial and costing endpoints
    - Apply require_role decorators to financial data endpoints (Accountant+ access)
    - Apply require_role decorators to costing endpoints (Accountant+ access)
    - Apply require_role decorators to scenario endpoints (Accountant+ access)
    - Ensure Viewer role has read-only access (GET only)
    - _Requirements: 3.1-3.8_

  - [x] 5.2 Add role checks to admin endpoints
    - Apply require_role decorators to user management endpoints (Owner/Admin only)
    - Apply require_role decorators to integration endpoints (Owner/Admin only)
    - Apply require_role decorators to billing endpoints (Owner only)
    - _Requirements: 3.1-3.8_

  - [x] 5.3 Write integration tests for endpoint authorization
    - Test each role's access to various endpoints
    - Test Viewer role cannot perform write operations
    - Test Accountant cannot access admin endpoints
    - Verify all existing tests still pass
    - _Requirements: 23.8, 24.2_

- [ ] 6. Checkpoint - Verify RBAC implementation
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 7. Audit trail system - Models and middleware
  - [x] 7.1 Create AuditLog SQLAlchemy model
    - Add AuditLog model to Backend/app/models/models.py
    - Define JSON structure for old_values and new_values
    - Add indexes on (tenant_id, created_at) and (table_name, record_id)
    - Add query methods: get_record_history(), get_tenant_audit_trail()
    - _Requirements: 5.1-5.8_

  - [x] 7.2 Create audit logging utility
    - Create Backend/app/utils/audit.py
    - Implement log_audit_event(action, table_name, record_id, old_values, new_values, user, request) function
    - Implement sanitize_sensitive_fields() to exclude passwords and tokens
    - Handle audit logging failures gracefully without blocking operations
    - _Requirements: 6.1-6.8_

  - [x] 7.3 Create audit trail middleware
    - Create Backend/app/middleware/audit_middleware.py
    - Intercept all CUD operations (POST, PUT, PATCH, DELETE)
    - Capture old and new values for UPDATE operations
    - Log audit events after successful database commits
    - Extract IP address and user agent from request
    - _Requirements: 6.1-6.8, 29.2_

  - [x] 7.4 Write unit tests for audit logging
    - Test audit event creation for CREATE, UPDATE, DELETE operations
    - Test sensitive field sanitization
    - Test graceful failure handling
    - _Requirements: 24.3, 24.4_

- [ ] 8. Audit trail API endpoints
  - [x] 8.1 Create audit log service
    - Create Backend/app/services/audit_service.py
    - Implement get_audit_logs(filters, pagination) method
    - Implement export_audit_logs(filters, format) method
    - Support filtering by date range, user_id, table_name, action
    - _Requirements: 7.1-7.8_

  - [x] 8.2 Create audit log API endpoints
    - Create Backend/app/api/audit.py
    - Implement GET /api/audit-logs with pagination and filtering
    - Implement GET /api/audit-logs/export for CSV export
    - Apply require_role decorator (Owner/Admin only)
    - _Requirements: 7.1-7.8_

  - [x] 8.3 Write integration tests for audit trail API
    - Test audit log querying with various filters
    - Test audit log export to CSV
    - Test authorization enforcement (Owner/Admin only)
    - Test pagination functionality
    - _Requirements: 24.4_

- [ ] 9. Checkpoint - Verify audit trail implementation
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 10. Report generation foundation
  - [x] 10.1 Install report generation dependencies
    - Add reportlab, weasyprint, openpyxl to Backend/requirements.txt
    - Update requirements file with version constraints
    - _Requirements: 9.1, 10.1_

  - [x] 10.2 Create report template definitions
    - Create Backend/app/services/report_templates.py
    - Define template structure: name, description, data_sources, layout_config, output_formats
    - Create templates for: Financial Statement, Costing Analysis, Order Evaluation, Margin Analysis, Receivables Report
    - Validate data sources reference existing service methods
    - _Requirements: 8.1-8.7_

  - [x] 10.3 Create report data aggregation service
    - Create Backend/app/services/report_data_service.py
    - Implement methods to fetch and aggregate data for each template
    - Implement get_financial_statement_data(), get_costing_analysis_data(), etc.
    - Apply tenant filtering to all data queries
    - _Requirements: 8.1, 8.6_

  - [x] 10.4 Write unit tests for report data aggregation
    - Test data fetching for each report template
    - Test tenant isolation in data queries
    - Test data aggregation calculations
    - _Requirements: 24.5_

- [ ] 11. PDF report generation
  - [x] 11.1 Create PDF generator utility
    - Create Backend/app/utils/pdf_generator.py
    - Implement generate_pdf(template, data, options) function using ReportLab
    - Support tables, charts, and formatted text
    - Include company logo, branding, timestamps, and page numbers
    - Use A4 page size by default
    - _Requirements: 9.1-9.8_

  - [x] 11.2 Create PDF report templates
    - Create PDF layout templates for each report type
    - Define styles for headers, tables, and charts
    - Implement footer with timestamp and page numbers
    - _Requirements: 9.2-9.7_

  - [x] 11.3 Write unit tests for PDF generation
    - Test PDF generation for each report template
    - Test PDF structure and content
    - Test error handling for invalid data
    - _Requirements: 24.5, 24.6_

- [ ] 12. Excel and CSV export
  - [x] 12.1 Create Excel generator utility
    - Create Backend/app/utils/excel_generator.py
    - Implement generate_excel(template, data, options) function using openpyxl
    - Create worksheets for each data table
    - Apply formatting: headers, number formats, column widths
    - Include formulas for calculated fields
    - _Requirements: 10.1-10.5_

  - [x] 12.2 Create CSV generator utility
    - Create Backend/app/utils/csv_generator.py
    - Implement generate_csv(template, data, options) function
    - Use UTF-8 encoding and RFC 4180 escaping
    - Include column headers as first row
    - _Requirements: 10.2, 10.6-10.8_

  - [x] 12.3 Write unit tests for Excel and CSV generation
    - Test Excel generation with multiple worksheets
    - Test CSV generation with special characters
    - Test data formatting and formulas
    - _Requirements: 24.5, 24.6_

- [ ] 13. Report generation API and background tasks
  - [x] 13.1 Create report generation service
    - Create Backend/app/services/report_service.py
    - Implement generate_report(template_id, format, parameters, user) method
    - Implement get_report_status(task_id) method
    - Implement get_report_download_url(task_id) method with 24-hour expiry
    - Validate format and parameters
    - _Requirements: 11.1-11.8_

  - [x] 13.2 Create Celery tasks for report generation
    - Add report generation tasks to Backend/app/tasks.py
    - Implement async_generate_report(template_id, format, parameters, user_id) task
    - Store generated reports in configured storage path
    - Update task status on completion or failure
    - _Requirements: 11.4-11.7_

  - [x] 13.3 Create report generation API endpoints
    - Create Backend/app/api/reports.py
    - Implement POST /api/reports/generate (returns task_id)
    - Implement GET /api/reports/status/{task_id}
    - Implement GET /api/reports/templates (list available templates)
    - Implement GET /api/reports/templates/{template_id} (template details)
    - Apply require_role decorator (Accountant+ access)
    - Add rate limiting to prevent resource exhaustion
    - _Requirements: 8.3-8.5, 11.1-11.8, 30.3_

  - [x] 13.4 Write integration tests for report generation
    - Test report generation workflow end-to-end
    - Test status checking and download URL generation
    - Test authorization enforcement
    - Test rate limiting
    - _Requirements: 24.6_

- [ ] 14. Scheduled reports
  - [x] 14.1 Create scheduled report model and schema
    - Add ReportSchedule model to Backend/app/models/models.py
    - Fields: template_id, format, parameters, frequency, recipients, next_run_at
    - Create Pydantic schemas for schedule creation and response
    - _Requirements: 12.1-12.4_

  - [x] 14.2 Create scheduled report service
    - Create Backend/app/services/scheduled_report_service.py
    - Implement create_schedule(), get_schedules(), delete_schedule() methods
    - Implement execute_scheduled_report(schedule_id) method
    - Validate cron expressions and frequency values
    - _Requirements: 12.1-12.7_

  - [~] 14.3 Create Celery beat tasks for scheduled reports
    - Add periodic task configuration to Backend/app/celery_app.py
    - Implement scheduled report execution task
    - Update next_run_at after each execution
    - Send generated reports via email
    - _Requirements: 12.5, 12.6_

  - [~] 14.4 Create scheduled report API endpoints
    - Add endpoints to Backend/app/api/reports.py
    - Implement POST /api/reports/schedules (create schedule)
    - Implement GET /api/reports/schedules (list schedules)
    - Implement DELETE /api/reports/schedules/{schedule_id} (cancel schedule)
    - Apply require_role decorator (Accountant+ access)
    - _Requirements: 12.1, 12.7, 12.8_

  - [~] 14.5 Write integration tests for scheduled reports
    - Test schedule creation, listing, and deletion
    - Test schedule execution (mock Celery beat)
    - Test authorization enforcement
    - _Requirements: 24.6_

- [ ] 15. Report parsers for round-trip testing
  - [~] 15.1 Create Excel parser utility
    - Create Backend/app/utils/excel_parser.py
    - Implement parse_excel(file_path) function
    - Return structured data matching export format
    - Validate data types and constraints
    - _Requirements: 28.1-28.3, 28.7_

  - [~] 15.2 Create CSV parser utility
    - Create Backend/app/utils/csv_parser.py
    - Implement parse_csv(file_path) function
    - Return structured data matching export format
    - Validate data types and constraints
    - _Requirements: 28.1-28.3, 28.7_

  - [ ] 15.3 Write property-based tests for round-trip consistency
    - **Property 1: Excel round-trip consistency**
    - **Validates: Requirements 28.4, 28.5**
    - Generate random financial data, export to Excel, parse back, verify equivalence
    - Test with various data types and edge cases

  - [ ] 15.4 Write property-based tests for CSV round-trip consistency
    - **Property 2: CSV round-trip consistency**
    - **Validates: Requirements 28.4, 28.6**
    - Generate random costing data, export to CSV, parse back, verify equivalence
    - Test with special characters and edge cases

- [ ] 16. Checkpoint - Verify report generation implementation
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 17. Email notification system foundation
  - [x] 17.1 Install email dependencies
    - Add sendgrid to Backend/requirements.txt
    - Add jinja2 for email templating (if not already present)
    - _Requirements: 13.1_

  - [ ] 17.2 Create email service configuration
    - Update Backend/.env.example with EMAIL_PROVIDER, EMAIL_API_KEY, EMAIL_FROM_ADDRESS
    - Create Backend/app/core/email_config.py for email configuration
    - Validate email configuration on application startup
    - Support SendGrid and AWS SES providers
    - _Requirements: 13.1-13.3, 27.1, 27.2, 27.7_

  - [ ] 17.3 Create email service utility
    - Create Backend/app/services/email_service.py
    - Implement send_email(recipient, subject, body, attachments) method
    - Implement retry logic with exponential backoff (3 retries)
    - Log failed emails and store in failed_emails table
    - _Requirements: 13.4-13.7_

  - [ ] 17.4 Create email test endpoint
    - Add POST /api/notifications/test-email endpoint to verify configuration
    - Apply require_role decorator (Owner/Admin only)
    - _Requirements: 13.8_

  - [ ] 17.5 Write unit tests for email service
    - Test email sending with mock SendGrid client
    - Test retry logic and failure handling
    - Test configuration validation
    - _Requirements: 24.7_

- [ ] 18. Email templates
  - [ ] 18.1 Create email template structure
    - Create Backend/app/templates/emails/ directory
    - Create base email template with branding and layout
    - Set up Jinja2 template engine configuration
    - _Requirements: 14.1, 14.2, 14.8_

  - [ ] 18.2 Create notification email templates
    - Create HTML templates for: order_evaluation_complete, scenario_analysis_ready, sync_status, low_margin_alert, overdue_receivables
    - Include company branding and logo
    - Add action buttons with deep links
    - Add unsubscribe link to all templates
    - Create plain text fallback for each template
    - _Requirements: 14.1-14.7_

  - [ ] 18.3 Create email rendering service
    - Add render_email_template(template_name, context) method to email_service.py
    - Inject dynamic data from context
    - Validate templates on startup
    - _Requirements: 14.2, 14.3, 14.8_

  - [ ] 18.4 Write unit tests for email templates
    - Test template rendering with various contexts
    - Test plain text fallback generation
    - Test template validation
    - _Requirements: 24.7_

- [ ] 19. Notification preferences
  - [x] 19.1 Create NotificationPreference model and schema
    - Add NotificationPreference model to Backend/app/models/models.py
    - Create Pydantic schemas in Backend/app/schemas/notifications.py
    - Define notification types enum
    - _Requirements: 16.1_

  - [ ] 19.2 Create notification preference service
    - Create Backend/app/services/notification_preference_service.py
    - Implement get_preferences(), update_preferences() methods
    - Implement initialize_default_preferences(user, role) method
    - Implement check_notification_enabled(user, notification_type) method
    - _Requirements: 16.2-16.7_

  - [ ] 19.3 Create notification preference API endpoints
    - Create Backend/app/api/notifications.py
    - Implement GET /api/notifications/preferences
    - Implement PUT /api/notifications/preferences
    - Implement POST /api/notifications/unsubscribe (from email link)
    - _Requirements: 16.2, 16.3, 16.8_

  - [ ] 19.4 Write integration tests for notification preferences
    - Test preference retrieval and updates
    - Test default preference initialization
    - Test unsubscribe functionality
    - _Requirements: 24.8_

- [ ] 20. Notification triggers
  - [ ] 20.1 Create notification trigger service
    - Create Backend/app/services/notification_trigger_service.py
    - Implement trigger_order_evaluation_complete(order_id, user_id) method
    - Implement trigger_scenario_analysis_ready(scenario_id, user_id) method
    - Implement trigger_sync_status(integration_name, status, tenant_id) method
    - Check user preferences before sending
    - Queue notifications for background processing
    - Prevent duplicate notifications within 24 hours
    - _Requirements: 15.1-15.8_

  - [ ] 20.2 Integrate notification triggers into existing workflows
    - Add notification trigger to order evaluation completion in Backend/app/services/costing_service.py
    - Add notification trigger to scenario analysis completion in Backend/app/services/scenario_service.py
    - Add notification trigger to sync completion in Backend/app/services/integration_service.py
    - _Requirements: 15.1-15.3_

  - [ ] 20.3 Create Celery tasks for alert notifications
    - Add daily scheduled task for low margin alerts
    - Add daily scheduled task for overdue receivables alerts
    - Run at 9:00 AM tenant local time
    - Send to Accountant, Admin, and Owner roles
    - _Requirements: 15.4-15.6_

  - [ ] 20.4 Write integration tests for notification triggers
    - Test notification sending for each trigger type
    - Test preference checking
    - Test duplicate prevention
    - Test role-based recipient filtering
    - _Requirements: 24.8_

- [ ] 21. Digest email notifications
  - [ ] 21.1 Create digest accumulation service
    - Add digest mode support to notification_preference_service.py
    - Implement accumulate_notification(user_id, notification) method
    - Implement get_accumulated_notifications(user_id) method
    - Exclude urgent notifications from digest accumulation
    - _Requirements: 17.1-17.7_

  - [ ] 21.2 Create digest email template
    - Create digest email HTML template
    - Group notifications by type with summary counts
    - Include links to view full details
    - _Requirements: 17.3-17.5_

  - [ ] 21.3 Create Celery task for digest email delivery
    - Add daily scheduled task to send digest emails
    - Run at user's configured time
    - Clear accumulated notifications after sending
    - _Requirements: 17.2, 17.8_

  - [ ] 21.4 Write integration tests for digest emails
    - Test notification accumulation
    - Test digest email generation and sending
    - Test urgent notification exclusion
    - _Requirements: 24.8_

- [ ] 22. Checkpoint - Verify notification system implementation
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 23. Soft delete implementation
  - [ ] 23.1 Update base query methods for soft delete
    - Update SQLAlchemy query methods to exclude deleted_at IS NOT NULL by default
    - Add with_deleted() query method to include soft-deleted records
    - Add only_deleted() query method to retrieve only soft-deleted records
    - _Requirements: 21.1, 21.2_

  - [ ] 23.2 Update delete operations to use soft delete
    - Modify all DELETE operations to set deleted_at timestamp instead of physical deletion
    - Update created_by and updated_by fields automatically
    - Implement cascade soft delete for dependent records
    - _Requirements: 20.6-20.8, 21.6, 21.7_

  - [ ] 23.3 Create restore functionality
    - Implement restore_record(table, record_id) method
    - Create POST /api/{resource}/{id}/restore endpoints for key resources
    - Apply require_role decorator (Owner/Admin only)
    - _Requirements: 21.3-21.5_

  - [ ] 23.4 Create permanent delete functionality
    - Implement permanent_delete(table, record_id) method
    - Create DELETE /api/{resource}/{id}/permanent endpoints
    - Apply require_role decorator (Owner only)
    - _Requirements: 21.8_

  - [ ] 23.5 Write integration tests for soft delete
    - Test soft delete operations
    - Test query filtering of deleted records
    - Test restore functionality
    - Test permanent delete (Owner only)
    - _Requirements: 24.1_

- [ ] 24. Security hardening
  - [ ] 24.1 Add input validation and sanitization
    - Sanitize all user inputs in report parameters to prevent injection attacks
    - Validate file paths in report generation to prevent directory traversal
    - Validate email addresses before sending notifications
    - _Requirements: 30.1, 30.2, 30.4_

  - [ ] 24.2 Add rate limiting
    - Implement rate limiting for report generation endpoints
    - Implement rate limiting for email sending
    - Configure limits in environment variables
    - _Requirements: 30.3_

  - [ ] 24.3 Add security headers and logging
    - Ensure sensitive data is excluded from audit logs
    - Restrict audit log access to Owner/Admin roles
    - Expire report download URLs after 24 hours
    - Add correlation IDs to all logs
    - _Requirements: 30.5-30.8, 29.6_

  - [ ] 24.4 Write security tests
    - Test input sanitization prevents injection attacks
    - Test rate limiting enforcement
    - Test authorization on sensitive endpoints
    - Test URL expiration
    - _Requirements: 30.1-30.8_

- [ ] 25. Documentation and configuration
  - [x] 25.1 Update API documentation
    - Add OpenAPI/Swagger documentation for all new endpoints
    - Document request/response schemas
    - Document authentication and authorization requirements
    - Include example requests and responses
    - Document error responses and status codes
    - _Requirements: 26.1-26.8_

  - [x] 25.2 Update configuration documentation
    - Update Backend/.env.example with all Phase 3 configuration parameters
    - Document email provider configuration
    - Document report storage configuration
    - Document audit log retention configuration
    - Document rate limiting configuration
    - _Requirements: 27.1-27.8_

  - [x] 25.3 Create usage examples
    - Document role management workflows
    - Document scheduled report configuration
    - Document notification preference management
    - _Requirements: 26.7, 26.8_

- [ ] 26. Integration and final testing
  - [ ] 26.1 Run full test suite
    - Execute all unit tests and verify 100% pass rate
    - Execute all integration tests
    - Verify all 17 existing tests still pass
    - _Requirements: 23.8, 25.6_

  - [ ] 26.2 Measure test coverage
    - Run coverage report
    - Verify minimum 70% overall coverage
    - Verify minimum 80% coverage for RBAC and Audit modules
    - Verify minimum 75% coverage for Report and Notification modules
    - _Requirements: 25.1-25.5_

  - [ ] 26.3 Write property-based tests for audit log integrity
    - **Property 3: Audit log data integrity**
    - **Validates: Requirements 25.8**
    - Verify all CUD operations generate audit logs
    - Verify audit logs contain complete old/new values
    - Verify sensitive fields are excluded

  - [ ] 26.4 Perform backward compatibility testing
    - Test all existing API endpoints with old authentication tokens
    - Verify existing Pydantic schemas unchanged
    - Verify existing service method signatures unchanged
    - Verify no breaking changes to API contracts
    - _Requirements: 23.1-23.7_

  - [ ] 26.5 Perform end-to-end workflow testing
    - Test complete RBAC workflow: create user, assign role, verify access
    - Test complete audit trail workflow: perform operations, query logs, export
    - Test complete report workflow: generate report, check status, download
    - Test complete notification workflow: trigger event, check preferences, send email
    - _Requirements: 24.1-24.8_

- [ ] 27. Final checkpoint - Production readiness verification
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation at major milestones
- Property-based tests validate universal correctness properties
- Unit and integration tests validate specific examples and edge cases
- Implementation follows existing FastAPI + SQLAlchemy patterns
- All new features maintain backward compatibility with existing API clients
- Target: 70%+ overall test coverage, 80%+ for RBAC and Audit modules
