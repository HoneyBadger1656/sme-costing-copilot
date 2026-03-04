# Phase 3 Usage Examples

This document provides practical examples for using Phase 3 features: RBAC, Audit Trail, Reports, and Notifications.

## Role Management

### Creating a Custom Role

```python
POST /api/roles
Authorization: Bearer <token>
Content-Type: application/json

{
  "name": "Financial Analyst",
  "description": "Can view and analyze financial data but cannot modify",
  "permissions": {
    "read": true,
    "write": false,
    "delete": false,
    "reports": true,
    "financials": true,
    "costing": true
  }
}
```

### Assigning a Role to a User

```python
POST /api/users/123/roles
Authorization: Bearer <token>
Content-Type: application/json

{
  "role_id": 2,
  "tenant_id": "org-uuid-here"
}
```

### Listing User Roles

```python
GET /api/users/123/roles
Authorization: Bearer <token>

Response:
{
  "roles": [
    {
      "id": 1,
      "name": "Owner",
      "description": "Full system access",
      "assigned_at": "2026-03-01T10:00:00Z"
    },
    {
      "id": 2,
      "name": "Accountant",
      "description": "Financial data access",
      "assigned_at": "2026-03-02T14:30:00Z"
    }
  ]
}
```

### Revoking a Role

```python
DELETE /api/users/123/roles/2
Authorization: Bearer <token>
```

## Scheduled Reports

### Creating a Weekly Financial Report

```python
POST /api/reports/schedules
Authorization: Bearer <token>
Content-Type: application/json

{
  "template_id": "financial_statement",
  "format": "pdf",
  "frequency": "weekly",
  "parameters": {
    "period_type": "monthly",
    "include_charts": true
  },
  "recipients": [
    "cfo@company.com",
    "accountant@company.com"
  ]
}
```

### Creating a Daily Margin Analysis Report

```python
POST /api/reports/schedules
Authorization: Bearer <token>
Content-Type: application/json

{
  "template_id": "margin_analysis",
  "format": "excel",
  "frequency": "daily",
  "parameters": {
    "min_margin_threshold": 15,
    "include_product_breakdown": true
  },
  "recipients": [
    "sales@company.com"
  ]
}
```

### Listing Scheduled Reports

```python
GET /api/reports/schedules
Authorization: Bearer <token>

Response:
{
  "schedules": [
    {
      "id": 1,
      "template_id": "financial_statement",
      "format": "pdf",
      "frequency": "weekly",
      "next_run_at": "2026-03-10T09:00:00Z",
      "is_active": true
    }
  ]
}
```

### Canceling a Scheduled Report

```python
DELETE /api/reports/schedules/1
Authorization: Bearer <token>
```

## Notification Preferences

### Getting User Notification Preferences

```python
GET /api/notifications/preferences
Authorization: Bearer <token>

Response:
{
  "preferences": [
    {
      "notification_type": "order_evaluation_complete",
      "enabled": true,
      "delivery_method": "email"
    },
    {
      "notification_type": "low_margin_alert",
      "enabled": true,
      "delivery_method": "email"
    },
    {
      "notification_type": "overdue_receivables",
      "enabled": false,
      "delivery_method": "email"
    }
  ]
}
```

### Updating Notification Preferences

```python
PUT /api/notifications/preferences
Authorization: Bearer <token>
Content-Type: application/json

{
  "preferences": [
    {
      "notification_type": "order_evaluation_complete",
      "enabled": true,
      "delivery_method": "email"
    },
    {
      "notification_type": "low_margin_alert",
      "enabled": false,
      "delivery_method": "email"
    }
  ]
}
```

### Unsubscribing from Notifications (via email link)

```python
POST /api/notifications/unsubscribe?token=<unsubscribe_token>

Response:
{
  "message": "Successfully unsubscribed from all notifications"
}
```

## Role-Based Access Examples

### Viewer Role Access

```python
# Viewer can read data
GET /api/orders
Authorization: Bearer <viewer_token>
✓ Success

# Viewer cannot create orders
POST /api/orders
Authorization: Bearer <viewer_token>
✗ 403 Forbidden: "Insufficient permissions"
```

### Accountant Role Access

```python
# Accountant can access financial endpoints
GET /api/financials/statements
Authorization: Bearer <accountant_token>
✓ Success

POST /api/reports/generate
Authorization: Bearer <accountant_token>
✓ Success

# Accountant cannot access admin endpoints
POST /api/users
Authorization: Bearer <accountant_token>
✗ 403 Forbidden: "Requires Owner or Admin role"
```

### Admin Role Access

```python
# Admin can manage users
POST /api/users
Authorization: Bearer <admin_token>
✓ Success

# Admin can assign roles
POST /api/users/123/roles
Authorization: Bearer <admin_token>
✓ Success

# Admin cannot access billing (Owner only)
GET /api/billing/invoices
Authorization: Bearer <admin_token>
✗ 403 Forbidden: "Requires Owner role"
```

## Report Generation Workflow

### Step 1: Generate a Report

```python
POST /api/reports/generate
Authorization: Bearer <token>
Content-Type: application/json

{
  "template_id": "costing_analysis",
  "format": "pdf",
  "parameters": {
    "date_range": {
      "start": "2026-01-01",
      "end": "2026-03-31"
    },
    "include_charts": true
  }
}

Response:
{
  "task_id": "task-uuid-123",
  "status": "queued",
  "message": "Report generation started"
}
```

### Step 2: Check Report Status

```python
GET /api/reports/status/task-uuid-123
Authorization: Bearer <token>

Response:
{
  "task_id": "task-uuid-123",
  "status": "completed",
  "progress": 100,
  "download_url": "https://api.example.com/reports/download/task-uuid-123",
  "expires_at": "2026-03-05T10:00:00Z"
}
```

### Step 3: Download the Report

```python
GET /api/reports/download/task-uuid-123
Authorization: Bearer <token>

# Returns PDF/Excel/CSV file
```

## Audit Trail Queries

### Viewing Audit Logs

```python
GET /api/audit-logs?table_name=orders&action=UPDATE&start_date=2026-03-01
Authorization: Bearer <owner_token>

Response:
{
  "logs": [
    {
      "id": 1,
      "user_id": 5,
      "action": "UPDATE",
      "table_name": "orders",
      "record_id": 123,
      "old_values": {"status": "draft"},
      "new_values": {"status": "confirmed"},
      "created_at": "2026-03-04T14:30:00Z"
    }
  ],
  "total": 1,
  "page": 1,
  "per_page": 50
}
```

### Exporting Audit Logs

```python
GET /api/audit-logs/export?format=csv&start_date=2026-01-01&end_date=2026-03-31
Authorization: Bearer <owner_token>

# Returns CSV file with audit log data
```

## Error Handling Examples

### Insufficient Permissions

```python
POST /api/roles
Authorization: Bearer <viewer_token>

Response: 403 Forbidden
{
  "detail": "Insufficient permissions. Requires Owner or Admin role."
}
```

### Rate Limit Exceeded

```python
POST /api/reports/generate
Authorization: Bearer <token>

Response: 429 Too Many Requests
{
  "detail": "Rate limit exceeded. Maximum 10 reports per hour."
}
```

### Invalid Report Parameters

```python
POST /api/reports/generate
Authorization: Bearer <token>
Content-Type: application/json

{
  "template_id": "invalid_template",
  "format": "pdf"
}

Response: 400 Bad Request
{
  "detail": "Invalid template_id. Available templates: financial_statement, costing_analysis, margin_analysis, receivables_report"
}
```
