# Requirements Document

## Introduction

Phase 4 extends the SME Costing Copilot with GST compliance automation, e-invoicing, e-way bill management, invoice-level payment collection, and a working capital dashboard. These features address the most critical compliance and cash flow needs of Indian SMEs. The system builds on the existing FastAPI + SQLAlchemy backend, Next.js frontend, Celery task queue, and Razorpay integration from Phases 1–3.

## Glossary

- **GST_Module**: The subsystem responsible for GST return generation, reconciliation, and filing status tracking.
- **GSTR1_Generator**: The component that compiles B2B, B2C, export, and nil-rated invoice data into a GSTR-1 return.
- **GSTR3B_Generator**: The component that auto-populates GSTR-3B fields from invoice and ITC data.
- **GSP_Client**: The GST Suvidha Provider API client (ClearTax or mock) used to submit returns.
- **ITC_Reconciler**: The component that compares GSTR-2A/2B data against purchase records to identify ITC mismatches.
- **HSN_Master**: The master data table of HSN/SAC codes with associated GST rates.
- **EInvoice_Service**: The subsystem that generates IRN numbers and QR codes for B2B invoices via the IRP API.
- **IRP**: Invoice Registration Portal — the government portal for e-invoice registration.
- **IRN**: Invoice Reference Number — the unique identifier assigned by IRP to a registered e-invoice.
- **EWayBill_Service**: The subsystem that generates and manages e-way bills for goods movement.
- **Payment_Service**: The subsystem that creates Razorpay payment links and UPI QR codes for individual invoices.
- **Reminder_Scheduler**: The Celery-based component that sends payment reminder notifications at configured intervals.
- **WorkingCapital_Service**: The subsystem that computes receivables aging, cash flow forecasts, working capital cycle, and credit utilization.
- **Organization**: An existing multi-tenant entity representing an SME firm (maps to the organizations table).
- **Client**: An existing entity representing a customer/business managed by the Organization (maps to the clients table).
- **Order**: An existing entity representing a sales order/invoice (maps to the orders table).
- **Ledger**: An existing entity representing receivable or payable entries (maps to the ledgers table).
- **GSTIN**: Goods and Services Tax Identification Number — a 15-character alphanumeric identifier assigned to GST-registered businesses.
- **Filing_Status**: The lifecycle state of a GST return: draft, under_review, filed, accepted, rejected.
- **Turnover_Threshold**: The annual turnover limit (₹5 crore) above which e-invoicing is mandatory for B2B transactions.
- **UPI**: Unified Payments Interface — India's real-time payment system.
- **DIO**: Days Inventory Outstanding — average days to sell inventory.
- **DSO**: Days Sales Outstanding — average days to collect receivables.
- **DPO**: Days Payable Outstanding — average days to pay suppliers.

## Requirements

---

### Requirement 1: GSTIN Configuration per Client

**User Story:** As an Accountant, I want to store and manage GSTIN details for each client, so that GST returns and e-invoices are generated with accurate taxpayer information.

#### Acceptance Criteria

1. THE GST_Module SHALL store GSTIN, legal name, state code, filing frequency (monthly/quarterly), and registration type (regular, composition, SEZ) per Client.
2. WHEN a GSTIN is saved, THE GST_Module SHALL validate that the GSTIN matches the 15-character format: 2-digit state code + 10-character PAN + 1-digit entity code + 1 check digit.
3. IF a GSTIN fails format validation, THEN THE GST_Module SHALL return a descriptive error identifying the invalid segment.
4. WHEN a GSTIN is created or updated, THE GST_Module SHALL record the change in the audit log with the previous and new values.
5. THE GST_Module SHALL enforce that only users with the Accountant, Admin, or Owner role can create or update GSTIN configuration.
6. THE GST_Module SHALL enforce that only users with the Viewer role or above can read GSTIN configuration.
7. THE GST_Module SHALL associate each GSTIN configuration record with an organization_id for multi-tenant isolation.

---

### Requirement 2: HSN/SAC Master Data

**User Story:** As an Accountant, I want a master table of HSN/SAC codes with GST rates, so that invoices and returns use correct tax classifications.

#### Acceptance Criteria

1. THE HSN_Master SHALL store HSN code, SAC code, description, CGST rate, SGST rate, IGST rate, and cess rate for each entry.
2. THE HSN_Master SHALL allow an Admin or Owner to create, update, and deactivate HSN/SAC entries.
3. WHEN a Product is created or updated, THE GST_Module SHALL allow linking the Product to an HSN_Master entry.
4. WHEN an HSN code is provided, THE HSN_Master SHALL validate that the code is 4, 6, or 8 digits as per GST rules.
5. IF an HSN code does not exist in the master, THEN THE HSN_Master SHALL return an error before saving the Product link.
6. THE HSN_Master SHALL be pre-seeded with common HSN/SAC codes for manufacturing and services sectors.

---

### Requirement 3: GSTR-1 Generation

**User Story:** As an Accountant, I want to generate a GSTR-1 return from existing invoice data, so that I can file outward supply details with the GST portal.

#### Acceptance Criteria

1. WHEN an Accountant requests GSTR-1 generation for a period, THE GSTR1_Generator SHALL compile all Orders with status "invoiced" or "completed" within that period for the specified Client.
2. THE GSTR1_Generator SHALL classify each invoice into the correct GSTR-1 section: B2B (registered buyer), B2C large (unregistered, >₹2.5 lakh), B2C small (unregistered, ≤₹2.5 lakh), exports, or nil-rated/exempt.
3. THE GSTR1_Generator SHALL compute taxable value, CGST, SGST, IGST, and cess for each invoice line using the linked HSN_Master rates.
4. THE GSTR1_Generator SHALL aggregate B2C small invoices by state as required by the GSTR-1 format.
5. WHEN GSTR-1 generation is complete, THE GSTR1_Generator SHALL set the Filing_Status to "draft" and store the return data linked to the Client and period.
6. THE GSTR1_Generator SHALL produce a JSON export in the GST portal-compatible format.
7. THE GSTR1_Generator SHALL produce an Excel export of the GSTR-1 summary for human review.
8. IF an invoice is missing an HSN code or buyer GSTIN for a B2B transaction, THEN THE GSTR1_Generator SHALL flag the invoice as incomplete and exclude it from the return, listing all flagged invoices in a validation report.
9. WHEN GSTR-1 data is generated, THE GST_Module SHALL require an explicit "Submit for Review" action before the Filing_Status advances to "under_review".
10. THE GST_Module SHALL enforce that only Accountant, Admin, or Owner roles can generate or submit GSTR-1.

---

### Requirement 4: GSTR-3B Generation

**User Story:** As an Accountant, I want to auto-populate GSTR-3B fields from invoice and ITC data, so that I can file the monthly summary return accurately.

#### Acceptance Criteria

1. WHEN an Accountant requests GSTR-3B generation for a period, THE GSTR3B_Generator SHALL aggregate outward taxable supplies, zero-rated supplies, and exempt supplies from the corresponding GSTR-1 data.
2. THE GSTR3B_Generator SHALL aggregate eligible ITC from purchase records and reconciled GSTR-2B data for the same period.
3. THE GSTR3B_Generator SHALL compute net GST payable as (output tax liability) minus (eligible ITC).
4. WHEN GSTR-3B generation is complete, THE GSTR3B_Generator SHALL set the Filing_Status to "draft" and store the return linked to the Client and period.
5. THE GSTR3B_Generator SHALL produce a JSON export in the GST portal-compatible format.
6. IF the GSTR-1 for the same period has not been generated, THEN THE GSTR3B_Generator SHALL return an error requiring GSTR-1 to be generated first.
7. THE GST_Module SHALL require an explicit "Submit for Review" action before GSTR-3B Filing_Status advances to "under_review".

---

### Requirement 5: GST Reconciliation Dashboard (ITC)

**User Story:** As an Accountant, I want to compare GSTR-2A/2B data against my purchase records, so that I can identify ITC mismatches before filing.

#### Acceptance Criteria

1. WHEN a GSTR-2A or GSTR-2B file is uploaded, THE ITC_Reconciler SHALL parse the JSON file and store the supplier invoice records linked to the Client and period.
2. THE ITC_Reconciler SHALL match uploaded supplier invoices against purchase Ledger entries using supplier GSTIN and invoice number as the matching key.
3. THE ITC_Reconciler SHALL classify each record as: matched, mismatched (amount differs by more than ₹1), or missing (present in 2A/2B but not in books, or vice versa).
4. THE ITC_Reconciler SHALL display a reconciliation summary showing total matched ITC, total mismatched ITC, and total missing ITC.
5. WHEN a mismatch is identified, THE ITC_Reconciler SHALL display the supplier GSTIN, invoice number, 2A/2B amount, books amount, and difference.
6. THE ITC_Reconciler SHALL allow an Accountant to mark a mismatch as "accepted" or "disputed" with a note.
7. THE ITC_Reconciler SHALL export the reconciliation report as Excel.
8. THE ITC_Reconciler SHALL produce a round-trip consistent result: parsing a GSTR-2A JSON file, storing it, and re-exporting it SHALL produce data equivalent to the original input for all matched fields.

---

### Requirement 6: GST Filing Status Tracking

**User Story:** As an Owner, I want to track the filing status of each GST return, so that I can ensure compliance deadlines are met.

#### Acceptance Criteria

1. THE GST_Module SHALL maintain a Filing_Status lifecycle for each return: draft → under_review → filed → accepted (or rejected).
2. WHEN a return is submitted to the GSP_Client, THE GST_Module SHALL update the Filing_Status to "filed" and store the acknowledgement number and timestamp.
3. IF the GSP_Client returns a rejection, THEN THE GST_Module SHALL update the Filing_Status to "rejected" and store the rejection reason.
4. THE GST_Module SHALL display a compliance calendar showing due dates for GSTR-1 and GSTR-3B for each filing frequency (monthly: 11th and 20th of following month; quarterly: last day of month following quarter end).
5. WHEN a return due date is 7 days away and the Filing_Status is still "draft", THE GST_Module SHALL send an email notification to users with the Accountant, Admin, or Owner role.
6. THE GST_Module SHALL log every Filing_Status transition in the audit log.

---

### Requirement 7: E-Invoice IRN Generation

**User Story:** As an Accountant, I want to generate IRN numbers for B2B invoices, so that the business complies with mandatory e-invoicing regulations.

#### Acceptance Criteria

1. WHEN an Order with a registered B2B buyer is marked "invoiced" and the Organization's annual turnover exceeds the Turnover_Threshold, THE EInvoice_Service SHALL automatically trigger IRN generation via the IRP API.
2. THE EInvoice_Service SHALL construct the e-invoice JSON payload in the IRP-specified schema (version 1.1) from the Order, OrderItem, and GSTIN configuration data.
3. WHEN the IRP API returns a successful response, THE EInvoice_Service SHALL store the IRN, acknowledgement number, acknowledgement date, and signed QR code string against the Order.
4. THE EInvoice_Service SHALL embed the QR code in the PDF invoice generated for the Order.
5. IF the IRP API returns an error, THEN THE EInvoice_Service SHALL store the error code and message, set the e-invoice status to "failed", and notify the Accountant by email.
6. THE EInvoice_Service SHALL prevent duplicate IRN generation: WHEN an Order already has a valid IRN, THE EInvoice_Service SHALL return the existing IRN without calling the IRP API again.
7. WHERE the Organization's turnover is below the Turnover_Threshold, THE EInvoice_Service SHALL skip IRN generation and mark the invoice as "e-invoice not applicable".
8. THE EInvoice_Service SHALL support a mock IRP mode for development and testing environments, controlled by an environment variable.

---

### Requirement 8: E-Invoice Cancellation

**User Story:** As an Accountant, I want to cancel an e-invoice within 24 hours of generation, so that I can correct errors before the cancellation window closes.

#### Acceptance Criteria

1. WHEN an Accountant requests cancellation of an e-invoice, THE EInvoice_Service SHALL verify that the cancellation request is within 24 hours of the IRN acknowledgement timestamp.
2. IF the cancellation request is outside the 24-hour window, THEN THE EInvoice_Service SHALL reject the request with an error message stating the cancellation deadline.
3. WHEN a cancellation is submitted to the IRP API and succeeds, THE EInvoice_Service SHALL update the e-invoice status to "cancelled" and store the cancellation reason and timestamp.
4. WHEN an e-invoice is cancelled, THE EInvoice_Service SHALL update the linked Order status to "invoiced" (not completed) to allow re-invoicing.
5. THE EInvoice_Service SHALL log every cancellation attempt and outcome in the audit log.

---

### Requirement 9: E-Way Bill Generation

**User Story:** As an Accountant, I want to generate e-way bills from invoices for goods movement above ₹50,000, so that the business complies with GST transportation rules.

#### Acceptance Criteria

1. WHEN an Order with goods value exceeding ₹50,000 is confirmed for dispatch, THE EWayBill_Service SHALL allow generation of an e-way bill linked to that Order.
2. THE EWayBill_Service SHALL collect transporter GSTIN, vehicle number, transport mode (road/rail/air/ship), and distance (km) as required inputs for e-way bill generation.
3. WHEN an e-way bill is generated successfully, THE EWayBill_Service SHALL store the e-way bill number, generated date, validity expiry date, and transporter details against the Order.
4. THE EWayBill_Service SHALL compute the validity period: 1 day per 200 km for road transport, with a minimum of 1 day.
5. WHEN an e-way bill is within 6 hours of expiry, THE EWayBill_Service SHALL send an email alert to the Accountant and Owner.
6. THE EWayBill_Service SHALL support e-way bill cancellation within 24 hours of generation, following the same cancellation rules as e-invoices.
7. THE EWayBill_Service SHALL maintain a vehicle and transporter master per Organization to avoid re-entering details for repeat transporters.
8. IF the goods value is ₹50,000 or below, THEN THE EWayBill_Service SHALL mark the Order as "e-way bill not required" without generating a bill.

---

### Requirement 10: Invoice Payment Links

**User Story:** As an Owner, I want to generate Razorpay payment links for individual invoices, so that customers can pay outstanding invoices online.

#### Acceptance Criteria

1. WHEN an Accountant or Owner requests a payment link for an Order, THE Payment_Service SHALL create a Razorpay payment link for the outstanding amount (total_selling_price minus amount_paid).
2. THE Payment_Service SHALL set the payment link expiry to 24 hours for standard payment pages.
3. THE Payment_Service SHALL store the Razorpay payment link ID, short URL, amount, currency (INR), and expiry timestamp against the Order.
4. WHEN a payment link is created, THE Payment_Service SHALL send the link to the customer's email address stored on the Order's Client record.
5. THE Payment_Service SHALL prevent creation of a payment link for an Order with payment_status "paid".
6. IF a payment link has expired, THEN THE Payment_Service SHALL allow the Accountant or Owner to generate a new link, invalidating the previous one.

---

### Requirement 11: UPI QR Code Generation

**User Story:** As an Accountant, I want to generate a UPI QR code for an invoice, so that customers can pay instantly via any UPI app.

#### Acceptance Criteria

1. WHEN a UPI QR code is requested for an Order, THE Payment_Service SHALL generate a UPI deep link in the format `upi://pay?pa=[vpa]&pn=[name]&am=[amount]&tn=[reference]&cu=INR` and encode it as a QR code image.
2. THE Payment_Service SHALL embed the UPI QR code in the PDF invoice for the Order.
3. THE Payment_Service SHALL set UPI QR code validity to 15 minutes from generation time.
4. WHEN a UPI QR code expires, THE Payment_Service SHALL allow regeneration on demand.
5. THE Payment_Service SHALL store the UPI VPA (Virtual Payment Address) at the Organization level for reuse across invoices.

---

### Requirement 12: Payment Webhook and Auto-Reconciliation

**User Story:** As an Accountant, I want payments received via Razorpay to automatically reconcile with the corresponding invoice and ledger, so that I don't have to manually update records.

#### Acceptance Criteria

1. WHEN the Payment_Service receives a Razorpay `payment.captured` webhook event, THE Payment_Service SHALL verify the webhook signature using HMAC-SHA256 with the Razorpay webhook secret.
2. IF the webhook signature is invalid, THEN THE Payment_Service SHALL return HTTP 400 and log the failed verification attempt.
3. WHEN a valid `payment.captured` event is received, THE Payment_Service SHALL update the linked Order's amount_paid and recompute payment_status as "partial" (if amount_paid < total_selling_price) or "paid" (if amount_paid >= total_selling_price).
4. WHEN an Order payment_status changes to "paid", THE Payment_Service SHALL create a corresponding Ledger entry of type "receivable" with status "paid" and payment_date set to the webhook event timestamp.
5. WHEN payment reconciliation is complete, THE Payment_Service SHALL log the reconciliation action in the audit log with the Razorpay payment ID, amount, and Order ID.
6. THE Payment_Service SHALL handle idempotent webhook delivery: WHEN the same Razorpay payment ID is received more than once, THE Payment_Service SHALL skip reprocessing and return HTTP 200.

---

### Requirement 13: Payment Reminder Scheduling

**User Story:** As an Owner, I want automated payment reminders sent to customers before and after the due date, so that I can reduce overdue receivables without manual follow-up.

#### Acceptance Criteria

1. THE Reminder_Scheduler SHALL send a payment reminder email to the customer 3 days before the Order due_date (D-3) if payment_status is not "paid".
2. THE Reminder_Scheduler SHALL send a payment reminder email to the customer 1 day before the Order due_date (D-1) if payment_status is not "paid".
3. THE Reminder_Scheduler SHALL send an overdue notice email to the customer 1 day after the Order due_date (D+1) if payment_status is not "paid".
4. WHEN a reminder is sent, THE Reminder_Scheduler SHALL include the invoice number, outstanding amount, due date, and the active payment link URL in the email body.
5. WHEN an Order payment_status changes to "paid", THE Reminder_Scheduler SHALL cancel all pending reminders for that Order.
6. THE Reminder_Scheduler SHALL log each reminder sent in the audit log with the Order ID, reminder type (D-3, D-1, D+1), and timestamp.
7. WHERE an Organization has disabled payment reminders in notification preferences, THE Reminder_Scheduler SHALL skip reminder sending for all Orders in that Organization.

---

### Requirement 14: Payment Analytics Dashboard

**User Story:** As an Owner, I want a payment analytics dashboard, so that I can monitor collection performance and outstanding balances at a glance.

#### Acceptance Criteria

1. THE Payment_Service SHALL expose an API endpoint that returns total invoiced amount, total collected amount, total outstanding amount, and collection rate percentage for a given date range and Client.
2. THE Payment_Service SHALL return a breakdown of outstanding invoices by aging bucket: 0–30 days, 31–60 days, 61–90 days, and 90+ days overdue.
3. THE Payment_Service SHALL return a time-series of daily collections for the selected period, suitable for rendering a line chart.
4. THE Payment_Service SHALL return the top 10 customers by outstanding balance.
5. WHEN the dashboard data is requested, THE Payment_Service SHALL return results within 3 seconds for datasets up to 10,000 orders.
6. THE Payment_Service SHALL enforce that only Accountant, Admin, and Owner roles can access payment analytics.

---

### Requirement 15: Receivables Aging Report

**User Story:** As an Owner, I want a receivables aging report with drill-down by customer, so that I can prioritize collection efforts.

#### Acceptance Criteria

1. THE WorkingCapital_Service SHALL compute receivables aging by reading outstanding Ledger entries of type "receivable" and classifying them into buckets: 0–30 days, 31–60 days, 61–90 days, and 90+ days past due_date.
2. THE WorkingCapital_Service SHALL return aging data aggregated at the Client level and drilled down to individual Ledger entries within each bucket.
3. THE WorkingCapital_Service SHALL compute the total outstanding amount per aging bucket and the percentage of total receivables each bucket represents.
4. THE WorkingCapital_Service SHALL expose an API endpoint returning the aging data as JSON for frontend chart rendering.
5. THE WorkingCapital_Service SHALL support export of the aging report as Excel and PDF.
6. WHEN aging data is requested, THE WorkingCapital_Service SHALL return results within 2 seconds for up to 5,000 ledger entries.

---

### Requirement 16: Cash Flow Forecast Visualization

**User Story:** As an Owner, I want a 30/60/90-day cash flow forecast with a visual chart, so that I can anticipate liquidity gaps and plan accordingly.

#### Acceptance Criteria

1. THE WorkingCapital_Service SHALL compute a 30-day, 60-day, and 90-day cash flow forecast by projecting inflows from outstanding receivable Ledger entries (by due_date) and outflows from outstanding payable Ledger entries (by due_date).
2. THE WorkingCapital_Service SHALL return a daily time-series of projected net cash position for the selected forecast horizon.
3. THE WorkingCapital_Service SHALL identify and flag dates where the projected cumulative cash position falls below zero.
4. THE WorkingCapital_Service SHALL expose an API endpoint returning the forecast as JSON with daily data points: date, projected_inflow, projected_outflow, net_cash_flow, cumulative_balance.
5. WHEN the forecast is requested, THE WorkingCapital_Service SHALL return results within 2 seconds for up to 5,000 ledger entries.
6. THE WorkingCapital_Service SHALL enforce that only Accountant, Admin, and Owner roles can access cash flow forecasts.

---

### Requirement 17: Working Capital Cycle Computation

**User Story:** As an Owner, I want to see my working capital cycle (DIO + DSO - DPO), so that I can understand how long cash is tied up in operations.

#### Acceptance Criteria

1. THE WorkingCapital_Service SHALL compute DSO as (average outstanding receivables / average daily revenue) using Order and Ledger data for the selected period.
2. THE WorkingCapital_Service SHALL compute DPO as (average outstanding payables / average daily cost of goods) using Ledger payable data for the selected period.
3. THE WorkingCapital_Service SHALL compute DIO as (average inventory value / average daily cost of goods sold) using BOMItem and Order data for the selected period.
4. THE WorkingCapital_Service SHALL compute the Cash Conversion Cycle as DIO + DSO - DPO.
5. THE WorkingCapital_Service SHALL return the current period values alongside the prior period values for trend comparison.
6. THE WorkingCapital_Service SHALL expose an API endpoint returning DIO, DSO, DPO, and CCC as JSON.

---

### Requirement 18: Credit Limit per Customer

**User Story:** As an Owner, I want to set a credit limit per customer and track utilization, so that I can control credit risk exposure.

#### Acceptance Criteria

1. THE WorkingCapital_Service SHALL allow an Admin or Owner to set a credit limit (in INR) per Client record.
2. THE WorkingCapital_Service SHALL compute current credit utilization as the sum of all outstanding receivable Ledger entries for that Client.
3. WHEN a new Order is confirmed for a Client, THE WorkingCapital_Service SHALL check if the Order's total_selling_price plus current utilization exceeds the credit limit.
4. IF the credit limit would be exceeded, THEN THE WorkingCapital_Service SHALL display a warning to the Accountant or Owner before the Order is confirmed, requiring explicit acknowledgement to proceed.
5. THE WorkingCapital_Service SHALL display credit limit, current utilization, and available credit for each Client on the client detail page.
6. WHEN credit utilization exceeds 80% of the credit limit, THE WorkingCapital_Service SHALL send an email notification to the Owner.

---

### Requirement 19: Collection Efficiency Score

**User Story:** As an Owner, I want a collection efficiency score per customer, so that I can identify customers with poor payment behaviour.

#### Acceptance Criteria

1. THE WorkingCapital_Service SHALL compute a collection efficiency score per Client as: (amount collected on or before due date / total invoiced amount) × 100, for the selected period.
2. THE WorkingCapital_Service SHALL classify each Client's score as: Excellent (≥90%), Good (75–89%), Fair (50–74%), or Poor (<50%).
3. THE WorkingCapital_Service SHALL return the collection efficiency score and classification for each Client via an API endpoint.
4. THE WorkingCapital_Service SHALL return a ranked list of Clients by collection efficiency score, from lowest to highest.
5. THE WorkingCapital_Service SHALL compute the score using only Orders with payment_status "paid" or "partial" and due_date in the past.

---

### Requirement 20: Multi-Tenancy and RBAC Enforcement

**User Story:** As a system administrator, I want all Phase 4 data to be isolated by organization and protected by role-based access control, so that one tenant cannot access another tenant's compliance or financial data.

#### Acceptance Criteria

1. THE GST_Module, EInvoice_Service, EWayBill_Service, Payment_Service, and WorkingCapital_Service SHALL associate every new database record with an organization_id column.
2. WHEN any Phase 4 API endpoint is called, THE system SHALL filter all database queries by the organization_id of the authenticated user.
3. IF a request attempts to access a record belonging to a different organization_id, THEN THE system SHALL return HTTP 403.
4. THE GST_Module SHALL restrict GSTR-1 submission, GSTR-3B submission, and filing status updates to users with Accountant, Admin, or Owner roles.
5. THE WorkingCapital_Service SHALL restrict credit limit configuration to Admin and Owner roles.
6. THE Payment_Service SHALL restrict payment link creation to Accountant, Admin, and Owner roles.
7. WHILE a user has the Viewer role, THE system SHALL allow read-only access to all Phase 4 dashboards and reports without allowing any create, update, or delete operations.

---

### Requirement 21: Audit Trail for Phase 4 Operations

**User Story:** As an Owner, I want all compliance and payment actions to be recorded in the audit trail, so that I have a complete history for regulatory review.

#### Acceptance Criteria

1. THE GST_Module SHALL record an audit log entry for every Filing_Status transition, including the previous status, new status, user ID, and timestamp.
2. THE EInvoice_Service SHALL record an audit log entry for every IRN generation attempt and every cancellation attempt, including the IRP response code.
3. THE EWayBill_Service SHALL record an audit log entry for every e-way bill generation and cancellation.
4. THE Payment_Service SHALL record an audit log entry for every payment link creation, payment received event, and reconciliation action.
5. THE WorkingCapital_Service SHALL record an audit log entry for every credit limit creation or update.
6. THE system SHALL use the existing audit_log utility for all Phase 4 audit entries, following the existing AuditLog model schema.
