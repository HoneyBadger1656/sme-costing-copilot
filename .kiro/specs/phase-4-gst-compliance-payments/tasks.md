# Implementation Tasks: Phase 4 — GST Compliance, E-Invoicing, E-Way Bills & Payments

## Overview

Tasks are ordered by dependency. Each task builds on the previous. Execute sequentially.

---

## Task 1: Database Models and Alembic Migration

- [x] 1.1 Add 10 new SQLAlchemy models to `Backend/app/models/models.py`: `GSTConfiguration`, `HSNSACMaster`, `GSTReturn`, `GSTReconciliation`, `EInvoice`, `EWayBill`, `Transporter`, `InvoicePaymentLink`, `PaymentReminder`, `CreditLimit`
- [x] 1.2 Add `hsn_sac_id` FK column to `Product` model and `organization_id` FK column to `Order` model (if not already present)
- [x] 1.3 Create Alembic migration `Backend/alembic/versions/xxxx_phase4_gst_payments.py` that creates all 10 new tables with correct indexes, FK constraints, and `organization_id` columns for multi-tenancy
- [x] 1.4 Run migration locally and verify all tables are created without errors

---

## Task 2: GST Service Layer

- [x] 2.1 Create `Backend/app/services/gst_service.py` with `GSTService` class containing:
  - `validate_gstin(gstin)` — validates 15-char format, returns `(is_valid, error_segment)`
  - `generate_gstr1(client_id, period, db)` — compiles invoiced/completed Orders, classifies into B2B/B2CS/B2CL/exports/nil-rated, computes CGST/SGST/IGST per line, stores in `gst_returns` with `status='draft'`
  - `generate_gstr3b(client_id, period, db)` — requires GSTR-1 to exist first, aggregates output tax and ITC, stores in `gst_returns`
  - `reconcile_itc(client_id, period, gstr2_data, db)` — matches supplier invoices against Ledger entries by `(supplier_gstin, invoice_number)`, classifies as matched/mismatched/missing
  - `get_compliance_calendar(client_id, db)` — returns due dates for next 12 months based on filing frequency
- [x] 2.2 Pre-seed `hsn_sac_master` table with at least 20 common HSN/SAC codes for manufacturing and services (via a seed script or migration data)

---

## Task 3: E-Invoice Service Layer

- [x] 3.1 Create `Backend/app/services/einvoice_service.py` with `EInvoiceService` class containing:
  - `generate_irn(order_id, db)` — idempotency guard, turnover threshold check, builds IRP payload, calls IRP API or mock, stores IRN/ack/QR code, logs audit entry
  - `cancel_irn(order_id, reason, db)` — validates 24-hour window, calls IRP cancellation, updates status, resets Order status, logs audit entry
  - `_build_irp_payload(order_id, db)` — constructs IRP schema v1.1 JSON from Order + OrderItem + GSTConfiguration
  - Mock IRP client returning realistic fake IRN when `MOCK_GOVERNMENT_APIS=true`

---

## Task 4: E-Way Bill Service Layer

- [x] 4.1 Create `Backend/app/services/ewaybill_service.py` with `EWayBillService` class containing:
  - `generate_ewb(order_id, transporter_data, db)` — validates goods value > ₹50,000, computes `valid_until = max(1, ceil(distance/200))` days, calls NIC API or mock, stores EWB details, logs audit entry
  - `cancel_ewb(order_id, reason, db)` — validates 24-hour window, calls NIC cancellation or mock, updates status, logs audit entry
  - `check_expiring_ewbs(db)` — finds EWayBills expiring within 6 hours, sends email alerts
  - `_compute_validity_days(distance_km, transport_mode)` — pure function for validity calculation
  - Mock NIC client returning realistic fake EWB numbers when `MOCK_GOVERNMENT_APIS=true`

---

## Task 5: Invoice Payment Service Layer

- [x] 5.1 Create `Backend/app/services/invoice_payment_service.py` with `InvoicePaymentService` class containing:
  - `create_payment_link(order_id, db)` — guards against paid orders (HTTP 409), computes outstanding amount, creates Razorpay payment link with 24h expiry, stores in `invoice_payment_links`, sends email to client, logs audit entry
  - `generate_upi_qr(order_id, db)` — builds UPI deep link `upi://pay?pa=...&pn=...&am=...&tn=...&cu=INR`, encodes as PNG QR code using `qrcode` library, returns bytes
  - `reconcile_payment(razorpay_payment_id, order_id, amount, db)` — idempotency check by payment ID, updates `Order.amount_paid`, sets `payment_status` to `paid`/`partial`, creates Ledger entry, cancels pending PaymentReminders, logs audit entry
  - `get_payment_analytics(org_id, start_date, end_date, db)` — returns total invoiced/collected/outstanding, aging breakdown, daily collections time-series, top 10 customers by outstanding

---

## Task 6: Working Capital Service Extensions

- [x] 6.1 Add the following methods to `FinancialService` in `Backend/app/services/financial_service.py`:
  - `get_aging_report(client_id, db)` — wraps existing `get_receivables_summary` with per-bucket drill-down to individual Ledger entries and percentage of total
  - `get_working_capital_cycle(client_id, period_days, db)` — computes DSO, DPO, DIO, CCC with current and prior period values
  - `get_collection_efficiency(org_id, db)` — per-client score = `(collected_on_or_before_due / total_invoiced) * 100`, classifies as Excellent/Good/Fair/Poor, returns ranked list
  - `set_credit_limit(client_id, amount, user_id, db)` — upserts `CreditLimit` record, logs audit entry
  - `check_credit_limit(client_id, order_amount, db)` — returns `{limit, utilization, available, would_exceed, warning_80pct}`
- [x] 6.2 Add daily cash flow time-series to existing `get_cash_flow_forecast` — return daily data points `{date, projected_inflow, projected_outflow, net_cash_flow, cumulative_balance}` and flag dates where cumulative balance < 0

---

## Task 7: GST API Router

- [x] 7.1 Create `Backend/app/api/gst.py` with the following endpoints:
  - `POST /gst/config` — create/update GSTIN config (Accountant+), validates GSTIN format
  - `GET /gst/config/{client_id}` — get GSTIN config (Viewer+)
  - `GET /gst/hsn` — list HSN/SAC codes with `?q=` search (Viewer+)
  - `POST /gst/hsn` — create HSN/SAC entry (Admin+)
  - `POST /gst/gstr1/generate` — generate GSTR-1 (Accountant+)
  - `GET /gst/gstr1/{client_id}/{period}` — get GSTR-1 data (Viewer+)
  - `POST /gst/gstr1/{id}/submit` — advance status to `under_review` (Accountant+)
  - `POST /gst/gstr3b/generate` — generate GSTR-3B (Accountant+)
  - `POST /gst/reconciliation/upload` — upload GSTR-2A/2B JSON (Accountant+)
  - `GET /gst/reconciliation/{client_id}/{period}` — get reconciliation result (Viewer+)
  - `GET /gst/compliance-calendar/{client_id}` — get filing due dates (Viewer+)
- [x] 7.2 Register `gst` router in `Backend/app/main.py` with prefix `/api/gst`

---

## Task 8: E-Invoice API Router

- [x] 8.1 Create `Backend/app/api/einvoice.py` with:
  - `POST /einvoice/generate/{order_id}` — generate IRN (Accountant+)
  - `GET /einvoice/{order_id}` — get e-invoice status (Viewer+)
  - `POST /einvoice/cancel/{order_id}` — cancel IRN with reason (Accountant+)
- [x] 8.2 Register `einvoice` router in `Backend/app/main.py` with prefix `/api/einvoice`

---

## Task 9: E-Way Bill API Router

- [x] 9.1 Create `Backend/app/api/ewaybill.py` with:
  - `POST /ewaybill/generate/{order_id}` — generate e-way bill (Accountant+)
  - `GET /ewaybill/{order_id}` — get e-way bill (Viewer+)
  - `POST /ewaybill/cancel/{order_id}` — cancel e-way bill (Accountant+)
  - `GET /ewaybill/transporters` — list saved transporters (Viewer+)
  - `POST /ewaybill/transporters` — add transporter to master (Accountant+)
- [x] 9.2 Register `ewaybill` router in `Backend/app/main.py` with prefix `/api/ewaybill`

---

## Task 10: Invoice Payment API Endpoints

- [x] 10.1 Extend `Backend/app/api/payments.py` with:
  - `POST /payments/invoice-link/{order_id}` — create Razorpay payment link (Accountant+)
  - `GET /payments/invoice-link/{order_id}` — get payment link status (Viewer+)
  - `POST /payments/upi-qr/{order_id}` — generate UPI QR code PNG (Accountant+)
  - `GET /payments/analytics` — payment analytics dashboard (Accountant+)
  - `POST /payments/invoice-webhook` — Razorpay webhook for `payment.captured` events (public, HMAC-verified)

---

## Task 11: Working Capital API Router

- [x] 11.1 Create `Backend/app/api/working_capital.py` with:
  - `GET /working-capital/aging/{client_id}` — receivables aging report (Accountant+)
  - `GET /working-capital/forecast/{client_id}` — cash flow forecast with `?days=30|60|90` (Accountant+)
  - `GET /working-capital/cycle/{client_id}` — DIO/DSO/DPO/CCC (Accountant+)
  - `GET /working-capital/collection-efficiency` — collection scores for all clients (Accountant+)
  - `POST /working-capital/credit-limit/{client_id}` — set credit limit (Admin+)
  - `GET /working-capital/credit-limit/{client_id}` — get credit limit + utilization (Viewer+)
- [x] 11.2 Register `working_capital` router in `Backend/app/main.py` with prefix `/api/working-capital`

---

## Task 12: Celery Tasks

- [x] 12.1 Add the following periodic tasks to `Backend/app/tasks.py`:
  - `send_payment_reminders()` — daily task, finds pending `PaymentReminder` records where `scheduled_at <= now`, sends emails with invoice number, amount, due date, and payment link URL
  - `check_expiring_ewaybills()` — hourly task, finds `EWayBill` records where `valid_until` is within 6 hours, sends email alerts to Accountant and Owner
  - `check_gst_filing_deadlines()` — daily task, finds `GSTReturn` records due in 7 days with `status='draft'`, sends email to Accountant/Admin/Owner
  - `check_credit_utilization()` — daily task, finds clients where utilization > 80% of credit limit, sends email to Owner
- [x] 12.2 Schedule `send_payment_reminders` and `check_gst_filing_deadlines` as daily beat tasks; schedule `check_expiring_ewaybills` as hourly beat task in `Backend/app/celery_app.py`

---

## Task 13: Frontend — GST Compliance Pages

- [x] 13.1 Create `frontend/src/app/gst/page.js` — GST Dashboard with compliance calendar table (upcoming due dates + status badges), filing status summary cards, and returns list with status filter
- [x] 13.2 Create `frontend/src/app/gst/gstr1/page.js` — GSTR-1 page with period selector, generate button, validation report for flagged invoices, tabbed sections (B2B/B2CS/B2CL/Exports/Nil-rated), tax summary table, JSON/Excel export buttons, and submit-for-review button
- [ ] 13.3 Create `frontend/src/app/gst/reconciliation/page.js` — ITC reconciliation page with drag-drop file upload, summary cards (matched/mismatched/missing ITC), mismatch table with accept/dispute actions, and Excel export
- [x] 13.4 Add GST API functions to `frontend/src/lib/api.js`: `generateGSTR1`, `submitGSTR1`, `generateGSTR3B`, `uploadReconciliation`, `getComplianceCalendar`, `getGSTConfig`, `saveGSTConfig`

---

## Task 14: Frontend — E-Invoice and E-Way Bill Pages

- [ ] 14.1 Create `frontend/src/app/einvoice/page.js` — E-Invoice management page with table showing order number, IRN, status, ack date; generate and cancel buttons; status badges (pending/generated/cancelled/failed/not_applicable)
- [ ] 14.2 Create `frontend/src/app/ewaybill/page.js` — E-Way Bill page with EWB table, generate modal (transporter GSTIN, vehicle, mode, distance), cancel button, expiry alert banner, and transporter master CRUD table
- [x] 14.3 Add e-invoice and e-way bill API functions to `frontend/src/lib/api.js`: `generateIRN`, `cancelIRN`, `getEInvoice`, `generateEWB`, `cancelEWB`, `getTransporters`, `addTransporter`

---

## Task 15: Frontend — Working Capital Dashboard

- [ ] 15.1 Create `frontend/src/app/working-capital/page.js` with:
  - Receivables aging stacked bar chart (Recharts `BarChart`) with 0–30/31–60/61–90/90+ buckets
  - Client-level aging drill-down table with expandable ledger entries
  - Cash flow forecast line chart (Recharts `LineChart`) with 30/60/90-day horizon selector; highlight negative cumulative balance dates in red
  - CCC panel showing DIO, DSO, DPO, CCC with prior period comparison arrows
  - Collection efficiency table ranked from lowest to highest score with classification badges
  - Credit limits table with utilization progress bars and set-limit modal (Admin/Owner only)
- [x] 15.2 Add working capital API functions to `frontend/src/lib/api.js`: `getAgingReport`, `getCashFlowForecast`, `getWorkingCapitalCycle`, `getCollectionEfficiency`, `getCreditLimit`, `setCreditLimit`

---

## Task 16: Frontend — Payment Features

- [ ] 16.1 Add payment link and UPI QR functionality to the existing orders/invoices UI:
  - "Send Payment Link" button on order detail page — calls `POST /payments/invoice-link/{order_id}`, shows success toast with short URL
  - "Generate UPI QR" button — fetches QR code PNG and displays in modal with download option
  - Payment analytics dashboard at `frontend/src/app/payments/page.js` — total invoiced/collected/outstanding cards, aging breakdown bar chart, daily collections line chart, top 10 customers table
- [x] 16.2 Add payment API functions to `frontend/src/lib/api.js`: `createPaymentLink`, `getPaymentLink`, `generateUPIQR`, `getPaymentAnalytics`

---

## Task 17: Navigation and Integration

- [x] 17.1 Add navigation links to the sidebar/nav component for all new pages: GST, E-Invoice, E-Way Bill, Working Capital, Payments
- [ ] 17.2 Add credit limit warning banner to the order creation/confirmation flow — call `GET /working-capital/credit-limit/{client_id}` when an order is confirmed; show warning modal if `would_exceed=true` requiring explicit acknowledgement

---

## Task 18: Unit Tests

- [ ] 18.1 Create `Backend/tests/test_phase4_gst.py` with unit tests:
  - `test_gstin_validation_valid_examples` — known-good GSTINs pass
  - `test_gstin_validation_invalid_examples` — wrong length, wrong state code fail with correct error segment
  - `test_gstr3b_requires_gstr1` — returns HTTP 400 when GSTR-1 missing
  - `test_gstr1_flags_incomplete_invoices` — invoices missing HSN or buyer GSTIN are excluded and listed
- [ ] 18.2 Create `Backend/tests/test_phase4_payments.py` with unit tests:
  - `test_webhook_invalid_signature` — invalid HMAC returns HTTP 400
  - `test_payment_link_paid_order` — creating link for paid order returns HTTP 409
  - `test_payment_reconciliation_partial` — partial payment sets status to `partial`
  - `test_payment_reconciliation_full` — full payment sets status to `paid` and creates Ledger entry
- [ ] 18.3 Create `Backend/tests/test_phase4_einvoice_ewb.py` with unit tests:
  - `test_irn_generation_below_threshold` — orders below turnover threshold get `not_applicable`
  - `test_irn_idempotency` — calling generate twice returns same IRN without duplicate DB record
  - `test_cancellation_outside_window` — cancellation after 24 hours returns HTTP 400
  - `test_ewb_not_required_below_50k` — orders ≤ ₹50,000 get `not_required` status
  - `test_ewb_validity_road_transport` — validity = `max(1, ceil(distance/200))` days

---

## Task 19: Property-Based Tests

- [ ] 19.1 Create `Backend/tests/test_phase4_properties.py` with Hypothesis property tests (minimum 100 examples each):
  - Property 1: GSTIN format validation — `@given(st.text())` — valid GSTINs accepted, invalid rejected with error
  - Property 2: GST amount invariant — `@given(taxable_value, cgst_rate)` — CGST=SGST for intra-state, IGST=CGST+SGST
  - Property 6: ITC reconciliation round-trip — stored `raw_data` equals input
  - Property 8: E-invoice idempotency — second `generate_irn` call returns same IRN, no new DB record
  - Property 9: Cancellation time window — succeeds within 24h, fails after
  - Property 10: E-way bill validity — `max(1, ceil(distance/200))` for road transport
  - Property 11: Payment webhook idempotency — second webhook call is a no-op
  - Property 12: Payment status transition — `amount_paid` increases by exactly `p`, status set correctly
  - Property 13: Aging bucket completeness — sum of buckets equals total outstanding
  - Property 14: CCC formula — `CCC = DIO + DSO - DPO` always holds
  - Property 15: Credit utilization consistency — equals sum of outstanding receivable Ledger entries
  - Property 16: Collection efficiency score and classification thresholds

---

## Task 20: Environment Configuration and Deployment

- [ ] 20.1 Add the following environment variables to `Backend/.env.example`:
  - `MOCK_GOVERNMENT_APIS=true` — controls IRP/NIC mock mode
  - `IRP_API_URL` — IRP endpoint (production)
  - `NIC_API_URL` — NIC e-way bill endpoint (production)
  - `IRP_CLIENT_ID` / `IRP_CLIENT_SECRET` — IRP credentials
  - `ORGANIZATION_UPI_VPA` — default UPI VPA for QR code generation
- [ ] 20.2 Add `qrcode[pil]` and `hypothesis` to `Backend/requirements.txt`
- [ ] 20.3 Update Railway environment variables (document which new vars need to be set in production)
- [ ] 20.4 Verify all new API endpoints are accessible after deployment by running smoke tests against the Railway URL
