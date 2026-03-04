# SME Costing Copilot API Documentation

## Overview

The SME Costing Copilot API provides comprehensive endpoints for managing costing, financial analysis, role-based access control, audit trails, reports, and notifications for Indian SMEs.

**Base URL**: `https://your-domain.com/api`

**Authentication**: All endpoints require Bearer token authentication unless otherwise specified.

```
Authorization: Bearer <your_jwt_token>
```

## Interactive Documentation

FastAPI provides interactive API documentation at:
- **Swagger UI**: `/docs` - Interactive API explorer
- **ReDoc**: `/redoc` - Alternative documentation view
- **OpenAPI Schema**: `/openapi.json` - Machine-readable API specification

## Phase 3 New Endpoints

### Role Management (RBAC)

#### Create Custom Role
```http
POST /api/roles
Authorization: Bearer <token>
Content-Type: application/json
```

**Required Role**: Owner or Admin

**Request Body**:
```json
{
  "name": "string",
  "description": "string",
  "permissions": {
    "read": true,
    "write": false,
    "delete": false,
    "billing": false,
    "user_management": false,
    "reports": true,
    "financials": true,
    "costing": true
  }
}
```

**Response**: `201 Created`
```json
{
  "id": 1,
  "name": "Financial Analyst",
  "description": "Can view and analyze financial data",
  "permissions": {...},
  "created_at": "2026-03-04T10:00:00Z"
}
```

**Error Responses**:
- `400 Bad Request` - Invalid role data
- `403 Forbidden` - Insufficient permissions
- `409 Conflict` - Role name already exists

---

#### List All Roles
```http
GET /api/roles
Authorization: Bearer <token>
```

**Query Parameters**:
- `skip` (integer, optional): Number of records to skip (default: 0)
- `limit` (integer, optional): Maximum records to return (default: 100)

**Response**: `200 OK`
```json
{
  "roles": [
    {
      "id": 1,
      "name": "Owner",
      "description": "Full system access",
      "permissions": {"all": true, "billing": true}
    },
    {
      "id": 2,
      "name": "Admin",
      "description": "Administrative access",
      "permissions": {"all": true, "billing": false}
    }
  ],
  "total": 2
}
```

---

#### Assign Role to User
```http
POST /api/users/{user_id}/roles
Authorization: Bearer <token>
Content-Type: application/json
```

**Required Role**: Owner or Admin

**Path Parameters**:
- `user_id` (integer): User ID

**Request Body**:
```json
{
  "role_id": 2,
  "tenant_id": "org-uuid-here"
}
```

**Response**: `201 Created`
```json
{
  "id": 1,
  "user_id": 123,
  "role_id": 2,
  "tenant_id": "org-uuid-here",
  "assigned_by": 1,
  "assigned_at": "2026-03-04T10:00:00Z"
}
```

**Error Responses**:
- `400 Bad Request` - Invalid role or user
- `403 Forbidden` - Insufficient permissions
- `404 Not Found` - User or role not found
- `409 Conflict` - Role already assigned

---

#### Revoke Role from User
```http
DELETE /api/users/{user_id}/roles/{role_id}
Authorization: Bearer <token>
```

**Required Role**: Owner or Admin

**Path Parameters**:
- `user_id` (integer): User ID
- `role_id` (integer): Role ID

**Response**: `204 No Content`

**Error Responses**:
- `403 Forbidden` - Insufficient permissions or attempting to revoke Owner role
- `404 Not Found` - Role assignment not found

---

#### Get User Roles
```http
GET /api/users/{user_id}/roles
Authorization: Bearer <token>
```

**Path Parameters**:
- `user_id` (integer): User ID

**Response**: `200 OK`
```json
{
  "roles": [
    {
      "id": 1,
      "name": "Owner",
      "description": "Full system access",
      "assigned_at": "2026-03-01T10:00:00Z"
    }
  ]
}
```

---

### Audit Trail

#### Get Audit Logs
```http
GET /api/audit-logs
Authorization: Bearer <token>
```

**Required Role**: Owner or Admin

**Query Parameters**:
- `table_name` (string, optional): Filter by table name
- `action` (string, optional): Filter by action (CREATE, UPDATE, DELETE)
- `user_id` (integer, optional): Filter by user ID
- `start_date` (datetime, optional): Filter by start date (ISO 8601)
- `end_date` (datetime, optional): Filter by end date (ISO 8601)
- `skip` (integer, optional): Pagination offset (default: 0)
- `limit` (integer, optional): Records per page (default: 50, max: 100)

**Response**: `200 OK`
```json
{
  "logs": [
    {
      "id": 1,
      "tenant_id": "org-uuid",
      "user_id": 5,
      "action": "UPDATE",
      "table_name": "orders",
      "record_id": 123,
      "old_values": {"status": "draft"},
      "new_values": {"status": "confirmed"},
      "ip_address": "192.168.1.1",
      "user_agent": "Mozilla/5.0...",
      "created_at": "2026-03-04T14:30:00Z"
    }
  ],
  "total": 1,
  "page": 1,
  "per_page": 50
}
```

**Error Responses**:
- `403 Forbidden` - Insufficient permissions

---

#### Export Audit Logs
```http
GET /api/audit-logs/export
Authorization: Bearer <token>
```

**Required Role**: Owner or Admin

**Query Parameters**:
- `format` (string): Export format (csv, excel)
- `start_date` (datetime, optional): Filter by start date
- `end_date` (datetime, optional): Filter by end date
- All other filters from GET /api/audit-logs

**Response**: `200 OK`
- Content-Type: `text/csv` or `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet`
- File download with audit log data

---

### Report Generation

#### List Report Templates
```http
GET /api/reports/templates
Authorization: Bearer <token>
```

**Required Role**: Accountant, Admin, or Owner

**Response**: `200 OK`
```json
{
  "templates": [
    {
      "id": "financial_statement",
      "name": "Financial Statement",
      "description": "Balance Sheet, P&L, and Cash Flow",
      "supported_formats": ["pdf", "excel"],
      "parameters": {
        "period_type": "monthly|quarterly|yearly",
        "include_charts": "boolean"
      }
    },
    {
      "id": "costing_analysis",
      "name": "Costing Analysis",
      "description": "Product costing breakdown and margin analysis",
      "supported_formats": ["pdf", "excel", "csv"],
      "parameters": {
        "date_range": "object",
        "product_ids": "array"
      }
    }
  ]
}
```

---

#### Generate Report
```http
POST /api/reports/generate
Authorization: Bearer <token>
Content-Type: application/json
```

**Required Role**: Accountant, Admin, or Owner

**Rate Limit**: 10 requests per hour

**Request Body**:
```json
{
  "template_id": "financial_statement",
  "format": "pdf",
  "parameters": {
    "period_type": "monthly",
    "include_charts": true,
    "date_range": {
      "start": "2026-01-01",
      "end": "2026-03-31"
    }
  }
}
```

**Response**: `202 Accepted`
```json
{
  "task_id": "task-uuid-123",
  "status": "queued",
  "message": "Report generation started"
}
```

**Error Responses**:
- `400 Bad Request` - Invalid template or parameters
- `403 Forbidden` - Insufficient permissions
- `429 Too Many Requests` - Rate limit exceeded

---

#### Check Report Status
```http
GET /api/reports/status/{task_id}
Authorization: Bearer <token>
```

**Path Parameters**:
- `task_id` (string): Task ID from generate report response

**Response**: `200 OK`
```json
{
  "task_id": "task-uuid-123",
  "status": "completed",
  "progress": 100,
  "download_url": "https://api.example.com/reports/download/task-uuid-123",
  "expires_at": "2026-03-05T10:00:00Z",
  "error": null
}
```

**Status Values**:
- `queued` - Report generation queued
- `processing` - Report being generated
- `completed` - Report ready for download
- `failed` - Report generation failed

---

#### Create Scheduled Report
```http
POST /api/reports/schedules
Authorization: Bearer <token>
Content-Type: application/json
```

**Required Role**: Accountant, Admin, or Owner

**Request Body**:
```json
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

**Frequency Values**: `daily`, `weekly`, `monthly`, `custom`

**Response**: `201 Created`
```json
{
  "id": 1,
  "template_id": "financial_statement",
  "format": "pdf",
  "frequency": "weekly",
  "next_run_at": "2026-03-10T09:00:00Z",
  "is_active": true,
  "created_at": "2026-03-04T10:00:00Z"
}
```

---

#### List Scheduled Reports
```http
GET /api/reports/schedules
Authorization: Bearer <token>
```

**Response**: `200 OK`
```json
{
  "schedules": [
    {
      "id": 1,
      "template_id": "financial_statement",
      "format": "pdf",
      "frequency": "weekly",
      "next_run_at": "2026-03-10T09:00:00Z",
      "last_run_at": "2026-03-03T09:00:00Z",
      "is_active": true
    }
  ]
}
```

---

#### Cancel Scheduled Report
```http
DELETE /api/reports/schedules/{schedule_id}
Authorization: Bearer <token>
```

**Path Parameters**:
- `schedule_id` (integer): Schedule ID

**Response**: `204 No Content`

---

### Notification Preferences

#### Get Notification Preferences
```http
GET /api/notifications/preferences
Authorization: Bearer <token>
```

**Response**: `200 OK`
```json
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

**Notification Types**:
- `order_evaluation_complete` - Order evaluation finished
- `scenario_analysis_ready` - Scenario analysis completed
- `sync_status` - Integration sync status update
- `low_margin_alert` - Products with margins below threshold
- `overdue_receivables` - Overdue payment alerts

---

#### Update Notification Preferences
```http
PUT /api/notifications/preferences
Authorization: Bearer <token>
Content-Type: application/json
```

**Request Body**:
```json
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

**Response**: `200 OK`
```json
{
  "message": "Preferences updated successfully",
  "preferences": [...]
}
```

---

#### Unsubscribe from Notifications
```http
POST /api/notifications/unsubscribe
```

**Query Parameters**:
- `token` (string): Unsubscribe token from email link

**Response**: `200 OK`
```json
{
  "message": "Successfully unsubscribed from all notifications"
}
```

---

#### Test Email Configuration
```http
POST /api/notifications/test-email
Authorization: Bearer <token>
Content-Type: application/json
```

**Required Role**: Owner or Admin

**Request Body**:
```json
{
  "recipient": "test@example.com"
}
```

**Response**: `200 OK`
```json
{
  "message": "Test email sent successfully"
}
```

---

## Authentication & Authorization

### Role Hierarchy

1. **Owner** - Full system access including billing
2. **Admin** - Administrative access except billing
3. **Accountant** - Financial data and reports access
4. **Viewer** - Read-only access

### Permission Matrix

| Endpoint Category | Owner | Admin | Accountant | Viewer |
|------------------|-------|-------|------------|--------|
| User Management | ✓ | ✓ | ✗ | ✗ |
| Role Management | ✓ | ✓ | ✗ | ✗ |
| Billing | ✓ | ✗ | ✗ | ✗ |
| Financial Data | ✓ | ✓ | ✓ | Read Only |
| Reports | ✓ | ✓ | ✓ | Read Only |
| Costing | ✓ | ✓ | ✓ | Read Only |
| Audit Logs | ✓ | ✓ | ✗ | ✗ |
| Integrations | ✓ | ✓ | ✗ | ✗ |

---

## Error Responses

All error responses follow this format:

```json
{
  "detail": "Error message",
  "type": "ErrorType"
}
```

### Common HTTP Status Codes

- `200 OK` - Request successful
- `201 Created` - Resource created successfully
- `202 Accepted` - Request accepted for processing
- `204 No Content` - Request successful, no content to return
- `400 Bad Request` - Invalid request data
- `401 Unauthorized` - Missing or invalid authentication
- `403 Forbidden` - Insufficient permissions
- `404 Not Found` - Resource not found
- `409 Conflict` - Resource conflict (e.g., duplicate)
- `422 Unprocessable Entity` - Validation error
- `429 Too Many Requests` - Rate limit exceeded
- `500 Internal Server Error` - Server error

---

## Rate Limiting

Rate limits are applied per user/IP address:

- **Report Generation**: 10 requests per hour
- **Email Sending**: 50 requests per hour
- **General API**: 100 requests per minute

Rate limit headers are included in responses:
```
X-RateLimit-Limit: 10
X-RateLimit-Remaining: 7
X-RateLimit-Reset: 1709564400
```

---

## Pagination

List endpoints support pagination with these query parameters:

- `skip` (integer): Number of records to skip (default: 0)
- `limit` (integer): Maximum records to return (default: 50, max: 100)

Response includes pagination metadata:
```json
{
  "data": [...],
  "total": 150,
  "page": 1,
  "per_page": 50,
  "pages": 3
}
```

---

## Filtering & Sorting

Many list endpoints support filtering and sorting:

**Filtering**:
```
GET /api/orders?status=confirmed&client_id=123
```

**Sorting**:
```
GET /api/orders?sort_by=created_at&order=desc
```

---

## Webhooks (Future)

Webhook support for real-time notifications is planned for future releases.

---

## SDK & Client Libraries (Future)

Official SDKs for Python, JavaScript, and other languages are planned.

---

## Support

For API support, contact: support@smecosting.com

For bug reports and feature requests, visit: https://github.com/your-repo/issues
