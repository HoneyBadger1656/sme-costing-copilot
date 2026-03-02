# SME Costing Copilot — Full Project Analysis & Completion Plan

**Date:** 2 March 2026  
**Purpose:** This document lists every requirement, maps what has been built so far, identifies what is missing, and lays out a concrete step-by-step plan to finish the platform.

---

## Table of Contents

1. [Platform Overview](#1-platform-overview)  
2. [What the Platform Must Do (Requirements)](#2-what-the-platform-must-do-requirements)  
3. [Current File-by-File Inventory](#3-current-file-by-file-inventory)  
4. [Progress Assessment — Module by Module](#4-progress-assessment--module-by-module)  
5. [Bugs and Issues in Existing Code](#5-bugs-and-issues-in-existing-code)  
6. [Detailed Completion Plan](#6-detailed-completion-plan)  
7. [Suggested Order of Work](#7-suggested-order-of-work)  

---

## 1. Platform Overview

The platform is an **AI-powered financial management tool for Indian SMEs** (small and medium enterprises). It helps business owners and chartered accountants to:

- Pull data from **Tally**, **Zoho Books**, or **Excel/CSV files**
- Automatically compute costing and financial metrics
- Run what-if scenarios to see the effect of business decisions
- Chat with an AI assistant that has access to all uploaded financial data

**Technology stack:**

| Layer    | Technology         |
|----------|--------------------|
| Backend  | Python, FastAPI, SQLAlchemy, SQLite/PostgreSQL |
| Frontend | Next.js (React), Tailwind CSS |
| AI       | Groq (Llama 3.1) or OpenAI (GPT-4o-mini) |
| Deploy   | Docker, Railway (backend), Vercel (frontend) |

---

## 2. What the Platform Must Do (Requirements)

### 2.1 Data Integration Layer (Foundation)

| # | Requirement | Description |
|---|-------------|-------------|
| D1 | Tally integration | Connect to Tally Prime, pull ledgers (receivables, payables), invoices, and stock data |
| D2 | Zoho Books integration | OAuth-based connection, pull invoices, bills, and customer/vendor data |
| D3 | Excel/CSV upload | User uploads Excel or CSV files containing orders, products, or financial data |
| D4 | Data normalisation | All imported data (from any source) must be stored in the same format so the rest of the platform can use it without caring about the source |

### 2.2 Module 1 — Automated Costing

| # | Requirement | Description |
|---|-------------|-------------|
| C1 | Formula library | A list of all costing formulas the user can click on. Examples: Unit Cost, Contribution Margin, Break-Even Point, Minimum Order Quantity, Cost per Unit with Overheads, etc. |
| C2 | One-click result | When the user clicks a formula, the system reads their data and instantly shows the answer (for example, "Minimum Order Quantity = 500 units") |
| C3 | Product-level costing | For each product: raw material cost + labour cost + overhead = total cost; then apply margin → selling price; then apply GST → final price |
| C4 | Order evaluation | Enter an order (customer, product, quantity, price, credit days) and get a score (0–100), risk level (low/medium/high), and a recommendation (accept/reject/review) |
| C5 | Bill of Materials | Store component-level cost breakdown for each product |

### 2.3 Module 2 — Automated Financial Management

| # | Requirement | Description |
|---|-------------|-------------|
| F1 | Financial formula library | A list of financial formulas the user can click on. Examples: Weighted Average Cost of Capital (WACC), Cost of Equity, Working Capital Ratio, Current Ratio, Quick Ratio, Debt-to-Equity Ratio, Return on Capital Employed, etc. |
| F2 | One-click result | Same as costing — click a formula, get the result from actual data |
| F3 | Profitability summary | Revenue, cost, gross profit, margin percentage for any time period |
| F4 | Receivables analysis | Outstanding amounts, age buckets (0–30, 31–60, 61–90, 90+ days), overdue items |
| F5 | Payables analysis | Same age-bucket analysis for amounts the business owes |
| F6 | Cash flow forecast | Predict net cash flow for the next N days based on receivables due and payables due |
| F7 | Working capital management | Show how much cash is locked in operations (debtor days, creditor days, inventory days, cash conversion cycle) |

### 2.4 Module 3 — Scenario Manager

| # | Requirement | Description |
|---|-------------|-------------|
| S1 | Side-by-side view | One half shows actual (current) data; the other half has input fields for the user to enter hypothetical values |
| S2 | Editable parameters | The user can change: raw material cost, selling price, credit days, order volume, labour cost, overhead, interest rate, or any other cost item |
| S3 | Run simulation | When the user clicks "Run", the system computes the effect on all financials: revenue, cost, margin, working capital, cash flow |
| S4 | Show changes | Every affected number must show: the original value, the new value, the absolute change (₹), and the percentage change (%) |
| S5 | Multiple scenarios | The user can save and compare multiple scenarios side by side |
| S6 | Recommendations | The system suggests which scenario is best for profit, best for cash flow, and the most balanced option |

### 2.5 Module 4 — AI Financial Assistant

| # | Requirement | Description |
|---|-------------|-------------|
| A1 | Access to all data | The assistant must be able to read all uploaded financial data (orders, products, ledgers, receivables, payables) |
| A2 | Natural language queries | The user types a question in plain language; the assistant answers using actual data |
| A3 | Query types | Must handle: profitability questions, cash flow questions, costing questions, customer analysis, order analysis, and general financial queries |
| A4 | Conversation history | Past messages are saved and displayed |
| A5 | Suggested questions | Show a list of sample questions the user can click |

---

## 3. Current File-by-File Inventory

### 3.1 Backend Files

| File | Purpose | Lines | Status |
|------|---------|-------|--------|
| `Backend/app/main.py` | FastAPI app setup, CORS, router registration, static file serving | 114 | Working |
| `Backend/app/core/database.py` | SQLAlchemy engine + session setup (SQLite or PostgreSQL) | 34 | Working |
| `Backend/app/models/models.py` | 10 database tables: User, Organization, Client, Product, BOMItem, Order, OrderItem, OrderEvaluation, Scenario, Ledger, IntegrationSync, ChatMessage | 256 | Working |
| `Backend/app/api/auth.py` | Register, login, JWT token, get-current-user | 137 | Working, but has a bug (see Section 5) |
| `Backend/app/api/clients.py` | CRUD for clients | 137 | Working |
| `Backend/app/api/costing.py` | Calculate product cost, evaluate order, recalculate order | 169 | Working |
| `Backend/app/api/financials.py` | Profitability, receivables, payables, cash flow forecast | 61 | Working |
| `Backend/app/api/scenarios.py` | Create, list, compare, delete scenarios | 102 | Working |
| `Backend/app/api/assistant.py` | Chat endpoint, conversation history | 50 | Working |
| `Backend/app/api/integrations.py` | Tally test/sync, Zoho auth/token/sync, Excel/CSV import for orders and products | 164 | Working, but has a bug (see Section 5) |
| `Backend/app/api/data_upload.py` | CSV and Excel upload for clients | 161 | Working, but has a bug (see Section 5) |
| `Backend/app/api/evaluations.py` | Order evaluations | 5446 bytes | Exists |
| `Backend/app/api/payments.py` | Subscription payments | 4853 bytes | Exists |
| `Backend/app/services/costing_engine.py` | Contribution margin, working capital impact, order evaluation, scenario comparison | 217 | Working |
| `Backend/app/services/costing_service.py` | Product unit cost calculation, order evaluation with recommendations | 178 | Working |
| `Backend/app/services/financial_service.py` | Profitability summary, receivables summary, payables summary, cash flow forecast | 249 | Working |
| `Backend/app/services/scenario_service.py` | Scenario creation, impact calculation, comparison, recommendations | 262 | Working |
| `Backend/app/services/ai_assistant_service.py` | Query classification, data retrieval (RAG pattern), LLM call, conversation storage | 311 | Working |
| `Backend/app/services/integration_service.py` | TallyIntegration (XML), ZohoIntegration (REST), ExcelCSVImport (pandas) | 494 | Working |
| `Backend/app/middleware/security.py` | Security middleware | — | Exists |
| `Backend/requirements.txt` | Python dependencies | — | Present |
| `Backend/init_db.py` | Database initialisation script | 525 bytes | Present |

### 3.2 Frontend Files

| File | Purpose | Lines | Status |
|------|---------|-------|--------|
| `frontend/src/app/page.js` | Login page | 92 | Working |
| `frontend/src/app/register/page.js` | Registration page | — | Exists |
| `frontend/src/app/dashboard/page.js` | Dashboard with client list, basic stats (Total Clients, Evaluations, Margin) | 168 | Partially working — stats are hardcoded |
| `frontend/src/app/evaluate/page.js` | Order evaluation form + results display | 224 | Working — calls real API |
| `frontend/src/app/products/page.js` | Product list + add product form with costing rules | 374 | Working — calls real API |
| `frontend/src/app/scenarios/page.js` | Scenario creation, list, comparison | 670 | Working — calls real API |
| `frontend/src/app/assistant/page.js` | Chat interface with sidebar suggestions | 206 | Working — calls real API |
| `frontend/src/app/clients/` | Client management pages | — | Exists (folder with subpage) |
| `frontend/src/app/subscribe/page.js` | Subscription page | — | Exists |
| `frontend/src/app/layout.js` | Root layout (Geist font, Tailwind) | 30 | Working but metadata is still default ("Create Next App") |
| `frontend/src/app/globals.css` | Global styles | 488 bytes | Present |
| `frontend/src/lib/api.js` | API helper (register, login, getClients, createClient, evaluateOrder) | 81 | Partially complete — many endpoints not included |

### 3.3 Configuration & Deployment Files

| File | Purpose |
|------|---------|
| `.env` / `.env.example` | Environment variables (API keys, database URL) |
| `Dockerfile`, `Dockerfile.backend`, `Dockerfile.full` | Docker configs |
| `railway.toml`, `render.yaml` | Deployment configs |
| `DEPLOYMENT_GUIDE.md` | Deployment instructions |
| `DEBUGGING_GUIDE.md` | Debugging tips |

---

## 4. Progress Assessment — Module by Module

### 4.1 Data Integration Layer

| Requirement | Backend | Frontend | % Done |
|-------------|---------|----------|--------|
| D1 — Tally integration | Connection test + ledger sync implemented | No UI for configuring Tally | 50% |
| D2 — Zoho integration | OAuth URL, token exchange, invoice sync implemented | No UI for connecting Zoho | 50% |
| D3 — Excel/CSV upload | Order import and product import working; client CSV/Excel upload working | No UI for file upload (no visible upload button or page) | 50% |
| D4 — Data normalisation | Partially done — Tally, Zoho, and CSV data are stored in the Ledger/Order tables | No visual indicator of data source | 70% |

**Overall Data Integration: ~55% complete**

### 4.2 Module 1 — Automated Costing

| Requirement | Backend | Frontend | % Done |
|-------------|---------|----------|--------|
| C1 — Formula library | Only basic cost formulas exist (unit cost, contribution margin); missing: Break-Even Point, Minimum Order Quantity, Batch Costing, etc. | No formula library page | 30% |
| C2 — One-click result | Product cost calculation API exists | No clickable formula UI | 20% |
| C3 — Product-level costing | Fully implemented (RM + labour + overhead + margin + GST) | Product page exists and calculates costs | 85% |
| C4 — Order evaluation | Fully implemented with score, risk level, recommendations | Evaluate page exists and shows results | 85% |
| C5 — Bill of Materials | Database model exists (BOMItem) | No API routes or UI for BOM | 15% |

**Overall Automated Costing: ~45% complete**

### 4.3 Module 2 — Automated Financial Management

| Requirement | Backend | Frontend | % Done |
|-------------|---------|----------|--------|
| F1 — Financial formula library | Missing entirely — no WACC, no Cost of Equity, no ratios (Current Ratio, Quick Ratio, Debt-to-Equity, ROE, ROCE, etc.) | No formula library page | 5% |
| F2 — One-click result | Not implemented | No UI | 0% |
| F3 — Profitability summary | API exists (`/api/financials/profitability`) | No frontend page for financials | 50% |
| F4 — Receivables analysis | API exists (`/api/financials/receivables`) | No frontend page | 50% |
| F5 — Payables analysis | API exists (`/api/financials/payables`) | No frontend page | 50% |
| F6 — Cash flow forecast | API exists (`/api/financials/cash-flow-forecast`) | No frontend page | 50% |
| F7 — Working capital management | Partially — working capital blocked per order is computed, but full working capital cycle (debtor days, creditor days, inventory days, cash conversion cycle) is missing | No frontend page | 25% |

**Overall Automated Financial Management: ~30% complete**

### 4.4 Module 3 — Scenario Manager

| Requirement | Backend | Frontend | % Done |
|-------------|---------|----------|--------|
| S1 — Side-by-side view | Impact data is computed but not structured for side-by-side display | Frontend shows impact in a single block, not split into "Actual vs Hypothetical" columns | 40% |
| S2 — Editable parameters | 4 parameters supported: raw material cost change, credit days change, volume change %, margin change % | Form exists with all 4 fields | 60% |
| S3 — Run simulation | Impact is calculated on creation | Works via "Create Scenario" | 70% |
| S4 — Show changes | Shows revenue change, margin change, WC change with amounts and percentages | Missing: original values next to new values; only shows the change, not both numbers | 60% |
| S5 — Multiple scenarios | Scenario comparison API works; frontend has checkboxes and comparison table | Working | 80% |
| S6 — Recommendations | Backend generates recommendations (best for profit, best for cash, balanced) | Frontend displays them | 80% |

**Overall Scenario Manager: ~65% complete**

### 4.5 Module 4 — AI Financial Assistant

| Requirement | Backend | Frontend | % Done |
|-------------|---------|----------|--------|
| A1 — Access to all data | Retrieves orders, products, ledgers based on query type | Already connected to database | 70% |
| A2 — Natural language queries | LLM call with RAG pattern works | Chat interface exists | 80% |
| A3 — Query types | 6 types handled: profitability, cash flow, costing, customer analysis, orders, general | Automatic classification works | 75% |
| A4 — Conversation history | Saved and retrievable via API | Displayed in chat | 85% |
| A5 — Suggested questions | Not in backend (frontend-only) | 6 suggested questions shown in sidebar | 90% |

**Overall AI Assistant: ~80% complete**

### 4.6 Common / Cross-Cutting

| Area | Status |
|------|--------|
| User authentication | Working (register + login + JWT) |
| Navigation | No shared navigation bar — every page is standalone; no sidebar or menu |
| Dashboard | Very basic — only shows client count; no financial summary, no charts |
| Responsive design | Basic — Tailwind classes used but no mobile-specific design |
| Error handling | Minimal — most errors just print to console |
| Loading states | Basic loading indicators exist |
| Layout metadata | Still shows "Create Next App" — not updated to "SME Costing Copilot" |

---

## 5. Bugs and Issues in Existing Code

| # | File | Issue |
|---|------|-------|
| 1 | `Backend/app/api/auth.py` line 119 | Login checks `user.password_hash` but the model field is called `user.hashed_password`. This will crash on login. |
| 2 | `Backend/app/api/integrations.py` line 102 | Uses `datetime.utcnow()` but `datetime` is never imported in that scope. Will crash when exchanging Zoho tokens. |
| 3 | `Backend/app/api/data_upload.py` lines 72, 141 | Uses `uuid.uuid4()` but `uuid` is never imported. Will crash on CSV/Excel client upload. |
| 4 | `Backend/app/api/costing.py` line 13 | Router uses `prefix="/api/costing"` but `main.py` also adds prefix `/api/costing`, resulting in the actual path being `/api/costing/api/costing/...`. Double prefix. |
| 5 | `Backend/app/api/scenarios.py` line 13 | Same double-prefix issue: router prefix is `/api/scenarios` and main.py also adds `/api/scenarios`. |
| 6 | `frontend/src/app/layout.js` | Page title is "Create Next App" instead of "SME Costing Copilot". |
| 7 | Frontend — several pages | API URLs are hardcoded to `http://localhost:8000` instead of using the `NEXT_PUBLIC_API_URL` environment variable from `api.js`. |
| 8 | `frontend/src/app/dashboard/page.js` | Evaluations count is hardcoded to `0` and Margin is hardcoded to `--`. Not fetched from backend. |

---

## 6. Detailed Completion Plan

### Phase 1 — Fix Bugs (Estimated: 1–2 hours)

1. **Fix login bug** (`auth.py` line 119): Change `user.password_hash` to `user.hashed_password`.
2. **Fix double API prefixes** in `costing.py` and `scenarios.py`: Remove the `prefix=` from the router definition since `main.py` already provides the prefix.
3. **Fix missing imports** in `data_upload.py` (add `import uuid`) and `integrations.py` (add `from datetime import datetime` where missing).
4. **Standardise frontend API URLs**: Replace all hardcoded `http://localhost:8000` with the `API_BASE_URL` variable from `lib/api.js`.
5. **Update layout metadata**: Change page title from "Create Next App" to "SME Costing Copilot".

---

### Phase 2 — Complete the Automated Costing Module (Estimated: 3–5 days)

#### 2A. Build the Costing Formula Library (Backend)

Add the following formulas to a new file `Backend/app/services/costing_formulas.py`:

| Formula | What it computes |
|---------|------------------|
| Unit Cost | Raw material + labour + overhead per unit |
| Contribution Margin | Selling price − variable cost per unit |
| Contribution Margin Ratio | (Selling price − variable cost) / selling price × 100 |
| Break-Even Point (units) | Fixed costs / contribution margin per unit |
| Break-Even Point (₹) | Fixed costs / contribution margin ratio |
| Minimum Order Quantity | Fixed costs for the order / contribution margin per unit |
| Cost per Batch | (Fixed setup cost + variable cost × batch size) |
| Target Selling Price | Total cost / (1 − target margin %) |
| Markup Percentage | (Selling price − cost) / cost × 100 |

Each formula should:
- Accept the required inputs (some from the database, some entered by the user)
- Return: the formula name, the result value, the unit (₹ or units or %), and a short plain-language explanation

#### 2B. Create API endpoint for formula library

New endpoint: `GET /api/costing/formulas` → returns the list of all available formulas with their names, required inputs, and descriptions.

New endpoint: `POST /api/costing/formulas/{formula_id}/calculate` → accepts input values, runs the formula, returns the result.

#### 2C. Build the Formula Library frontend page

New page: `frontend/src/app/costing/page.js`

- Left panel: list of all formulas (clickable cards)
- Right panel: shows the selected formula's name, a brief description of what it computes, the input fields (pre-filled from data where possible), a "Calculate" button, and the result displayed prominently

#### 2D. Complete Bill of Materials

- Add API routes for BOM: create BOM item, list BOM items for a product, update, delete
- Add UI for BOM within the Products page — expandable section showing component-level cost breakdown

---

### Phase 3 — Build the Financial Management Module (Estimated: 4–6 days)

#### 3A. Build the Financial Formula Library (Backend)

Add a new file `Backend/app/services/financial_formulas.py` with:

| Formula | What it computes |
|---------|------------------|
| Current Ratio | Current assets / current liabilities |
| Quick Ratio | (Current assets − inventory) / current liabilities |
| Debt-to-Equity Ratio | Total debt / total equity |
| Working Capital | Current assets − current liabilities |
| Working Capital Ratio | Current assets / current liabilities |
| Debtor Days | (Receivables / annual revenue) × 365 |
| Creditor Days | (Payables / annual purchases) × 365 |
| Cash Conversion Cycle | Debtor days + inventory days − creditor days |
| Cost of Equity | Risk-free rate + beta × market risk premium |
| WACC | (E/V × cost of equity) + (D/V × cost of debt × (1 − tax rate)) |
| Return on Equity (ROE) | Net income / shareholders' equity × 100 |
| Return on Capital Employed (ROCE) | Operating profit / capital employed × 100 |
| Gross Profit Margin | (Revenue − COGS) / revenue × 100 |
| Net Profit Margin | Net income / revenue × 100 |
| Operating Profit Margin | Operating profit / revenue × 100 |

Same pattern as costing formulas: each takes inputs, returns result with explanation.

#### 3B. Create API endpoints

- `GET /api/financials/formulas` → list all available financial formulas
- `POST /api/financials/formulas/{formula_id}/calculate` → run a formula
- Enhance existing endpoints to pull more data for the formulas

#### 3C. Build the Financial Management frontend page

New page: `frontend/src/app/financials/page.js`

- Tab or sidebar layout with sections: Formulas, Profitability, Receivables, Payables, Cash Flow, Working Capital
- Formula library layout identical to costing module
- Dashboard-style cards for profitability, receivables, payables, and cash flow (using existing backend APIs)

#### 3D. Add data model support for financial statements

The current data model tracks orders and ledgers but does not store:
- Balance sheet items (assets, liabilities, equity)
- Income statement items (revenue, expenses)
- Inventory data

Two options:
1. **Option A**: Expect users to upload these via Excel/CSV with specific templates
2. **Option B**: Pull them automatically from Tally or Zoho

Recommendation: Start with Option A (upload templates). Provide downloadable Excel templates with the required column names.

---

### Phase 4 — Improve the Scenario Manager (Estimated: 2–3 days)

#### 4A. Redesign the frontend for side-by-side view

- Left column: "Actual Data" — shows current values pulled from the database (raw material cost, selling price, credit days, volume, margin, total revenue, total cost, working capital blocked, etc.)
- Right column: "Hypothetical" — input fields pre-filled with actual values; user changes any value
- "Run Scenario" button computes the impact
- Results section: a table where every row shows: Parameter Name | Actual Value | New Value | Change (₹) | Change (%)

#### 4B. Add more editable parameters

Currently only 4 parameters can be changed. Add:
- Labour cost change (₹)
- Overhead percentage change
- Selling price change (₹ or %)
- GST/tax rate change
- Interest rate change
- Inventory holding period change

Update `ScenarioService._calculate_impact()` to handle the new parameters.

#### 4C. Add "quick scenario" feature

Allow the user to type a natural-language scenario (for example, "What if raw material costs go up by 15%?") and the system automatically fills in the fields.

---

### Phase 5 — Enhance the AI Assistant (Estimated: 2–3 days)

#### 5A. Expand data access

Currently the assistant only looks at orders, products, and ledgers. Add retrieval for:
- Scenario results (so the user can ask "Which scenario is best?")
- Financial formula results (so the user can ask "What is my current ratio?")
- Integration status (so the user can ask "Is my Tally connection active?")

#### 5B. Improve query classification

The current keyword-based classifier misses many valid questions. Consider using the LLM itself to classify the query (send a short classification prompt before the main prompt).

#### 5C. Add file upload to assistant

Allow the user to upload a document (PDF, Excel, CSV) directly in the chat. The assistant reads it and answers questions about it.

#### 5D. Add conversation memory

Currently each message is independent. Send the last 5–10 messages as context to the LLM so the assistant remembers the conversation.

---

### Phase 6 — Build Data Integration UI (Estimated: 2–3 days)

#### 6A. Create Integration Settings page

New page: `frontend/src/app/integrations/page.js`

Three tabs:
1. **Tally** — fields for Tally URL, port, company name; "Test Connection" button; "Sync Now" button
2. **Zoho** — "Connect to Zoho" button (opens OAuth flow); sync status
3. **Upload** — drag-and-drop file upload for CSV/Excel; template downloads; upload history

#### 6B. Add upload UI to the Dashboard

Add an "Import Data" button to the dashboard that opens a quick upload dialog.

---

### Phase 7 — Build Shared Navigation and Polish the UI (Estimated: 2–3 days)

#### 7A. Add global navigation

Create a reusable sidebar or top navigation bar component that appears on every page, with links to:
- Dashboard
- Automated Costing
- Financial Management
- Scenario Manager
- AI Assistant
- Integrations / Data Upload
- Settings / Account

#### 7B. Fix the Dashboard

Replace hardcoded values with real API calls:
- Total Clients (already done)
- Total Orders
- Average Margin
- Outstanding Receivables
- Cash Flow Status
- Recent activity feed

#### 7C. Mobile responsiveness

Ensure all pages work on mobile screens (at minimum: dashboard, assistant, evaluate).

#### 7D. Update metadata and branding

- Change page title to "SME Costing Copilot"
- Add a proper favicon
- Add meta descriptions for each page

---

## 7. Suggested Order of Work

| Order | Phase | What to do | Why this order |
|-------|-------|------------|----------------|
| 1 | Phase 1 | Fix all bugs | Cannot test anything properly until bugs are fixed |
| 2 | Phase 7A | Build navigation bar | Every subsequent page needs the nav bar, so build it first |
| 3 | Phase 2 | Complete Automated Costing | This is the core feature and has the most backend progress already |
| 4 | Phase 3 | Build Financial Management | Depends on some costing structures; second most important module |
| 5 | Phase 4 | Improve Scenario Manager | Already 65% done; mostly frontend improvements |
| 6 | Phase 5 | Enhance AI Assistant | Already 80% done; mostly quality-of-life improvements |
| 7 | Phase 6 | Build Integration UI | Backend already works; just needs frontend pages |
| 8 | Phase 7B–D | Dashboard and polish | Final touches after all features work |

---

## Summary Table

| Module | Backend Progress | Frontend Progress | Overall | Key Gap |
|--------|-----------------|-------------------|---------|---------|
| Data Integration | 55% | 10% | ~35% | No frontend UI for Tally/Zoho/Upload |
| Automated Costing | 50% | 40% | ~45% | No formula library; no BOM UI |
| Financial Management | 35% | 0% | ~20% | No financial formulas; no frontend page |
| Scenario Manager | 75% | 60% | ~65% | No side-by-side view; limited parameters |
| AI Assistant | 80% | 80% | ~80% | Limited data access; no conversation memory |
| Navigation / UX | — | 10% | ~10% | No shared nav; dashboard is a shell |

**Estimated total work remaining: 15–22 days of development time.**

---

*This document covers all requirements, all existing files, all known bugs, and all remaining work. No assumptions have been made beyond what the code and requirements explicitly state.*
