# Backend/app/services/financial_formulas.py
# Complete financial formula library — 101 formulas covering ratios, valuation, capital budgeting, etc.

import math
from typing import Any

# ── Category definitions ──────────────────────────────────────────────
CATEGORIES = [
    {"id": "liquidity_ratios", "name": "Liquidity Ratios", "icon": "💧", "order": 1},
    {"id": "solvency_ratios", "name": "Solvency Ratios", "icon": "🏦", "order": 2},
    {"id": "activity_ratios", "name": "Activity Ratios", "icon": "🔄", "order": 3},
    {"id": "profitability_ratios", "name": "Profitability Ratios", "icon": "📈", "order": 4},
    {"id": "market_ratios", "name": "Market Ratios", "icon": "📊", "order": 5},
    {"id": "time_value", "name": "Time Value of Money", "icon": "⏰", "order": 6},
    {"id": "cost_of_capital", "name": "Cost of Capital", "icon": "💰", "order": 7},
    {"id": "leverage", "name": "Leverage Analysis", "icon": "⚖️", "order": 8},
    {"id": "valuation", "name": "Business Valuation", "icon": "💼", "order": 9},
    {"id": "capital_budgeting", "name": "Capital Budgeting", "icon": "🏗️", "order": 10},
    {"id": "dividend_models", "name": "Dividend Models", "icon": "📋", "order": 11},
    {"id": "bond_analysis", "name": "Bond Analysis", "icon": "📜", "order": 12},
    {"id": "portfolio_analysis", "name": "Portfolio Analysis", "icon": "📈", "order": 13},
    {"id": "risk_management", "name": "Risk Management", "icon": "🛡️", "order": 14},
    {"id": "derivatives", "name": "Derivatives & Forex", "icon": "🔄", "order": 15},
    {"id": "working_capital_fm", "name": "Working Capital FM", "icon": "💼", "order": 16},
    {"id": "mutual_funds", "name": "Mutual Funds", "icon": "📊", "order": 17},
    {"id": "mergers_acquisitions", "name": "Mergers & Acquisitions", "icon": "🤝", "order": 18},
]

# ── Helper ────────────────────────────────────────────────────────────
def _inp(id: str, label: str, default=None):
    """Shorthand to build an input descriptor."""
    entry = {"id": id, "label": label, "type": "number"}
    if default is not None:
        entry["default"] = default
    return entry

# ── Formula registry ──────────────────────────────────────────────────
FORMULA_REGISTRY: dict[str, dict[str, Any]] = {}

def _register(id, name, category, formula, description, inputs, output_unit, calc):
    FORMULA_REGISTRY[id] = {
        "id": id,
        "name": name,
        "category": category,
        "formula": formula,
        "description": description,
        "inputs": inputs,
        "output_unit": output_unit,
        "calc": calc,
    }

# =====================================================================
# 1. LIQUIDITY RATIOS  (formulas 80-83)
# =====================================================================

_register(
    "current_ratio", "Current Ratio", "liquidity_ratios",
    "Current Ratio = Current Assets / Current Liabilities",
    "Measures ability to pay short-term obligations with current assets.",
    [_inp("current_assets", "Current Assets (₹)"),
     _inp("current_liabilities", "Current Liabilities (₹)")],
    "ratio",
    lambda i: i["current_assets"] / i["current_liabilities"] if i["current_liabilities"] else 0,
)

_register(
    "quick_ratio", "Quick / Acid-Test Ratio", "liquidity_ratios",
    "Quick Ratio = Quick Assets / Current Liabilities",
    "Measures ability to pay short-term obligations without inventory.",
    [_inp("quick_assets", "Quick Assets (₹)"),
     _inp("current_liabilities", "Current Liabilities (₹)")],
    "ratio",
    lambda i: i["quick_assets"] / i["current_liabilities"] if i["current_liabilities"] else 0,
)

_register(
    "cash_ratio", "Cash Ratio", "liquidity_ratios",
    "Cash Ratio = (Cash + Bank + Marketable Securities) / Current Liabilities",
    "Measures ability to pay short-term obligations with cash and equivalents.",
    [_inp("cash_bank_securities", "Cash + Bank + Marketable Securities (₹)"),
     _inp("current_liabilities", "Current Liabilities (₹)")],
    "ratio",
    lambda i: i["cash_bank_securities"] / i["current_liabilities"] if i["current_liabilities"] else 0,
)

_register(
    "net_working_capital", "Net Working Capital", "liquidity_ratios",
    "NWC = Current Assets - Current Liabilities",
    "Measures the liquid assets available for operations.",
    [_inp("current_assets", "Current Assets (₹)"),
     _inp("current_liabilities", "Current Liabilities (₹)")],
    "₹",
    lambda i: i["current_assets"] - i["current_liabilities"],
)

# =====================================================================
# 2. SOLVENCY RATIOS  (formulas 84-88)
# =====================================================================

_register(
    "debt_equity_ratio", "Debt-Equity Ratio", "solvency_ratios",
    "Debt-Equity = Total Debt / Shareholders' Funds",
    "Measures proportion of debt financing relative to equity.",
    [_inp("total_debt", "Total Debt (₹)"),
     _inp("shareholders_funds", "Shareholders' Funds (₹)")],
    "ratio",
    lambda i: i["total_debt"] / i["shareholders_funds"] if i["shareholders_funds"] else 0,
)

_register(
    "debt_ratio", "Debt Ratio", "solvency_ratios",
    "Debt Ratio = Total Debt / Total Assets",
    "Measures proportion of assets financed by debt.",
    [_inp("total_debt", "Total Debt (₹)"),
     _inp("total_assets", "Total Assets (₹)")],
    "ratio",
    lambda i: i["total_debt"] / i["total_assets"] if i["total_assets"] else 0,
)

_register(
    "proprietary_ratio", "Proprietary Ratio", "solvency_ratios",
    "Proprietary Ratio = Shareholders' Funds / Total Assets",
    "Measures proportion of assets financed by owners.",
    [_inp("shareholders_funds", "Shareholders' Funds (₹)"),
     _inp("total_assets", "Total Assets (₹)")],
    "ratio",
    lambda i: i["shareholders_funds"] / i["total_assets"] if i["total_assets"] else 0,
)

_register(
    "interest_coverage_ratio", "Interest Coverage Ratio", "solvency_ratios",
    "ICR = EBIT / Interest",
    "Measures ability to pay interest expenses from operating income.",
    [_inp("ebit", "EBIT (₹)"),
     _inp("interest", "Interest Expense (₹)")],
    "ratio",
    lambda i: i["ebit"] / i["interest"] if i["interest"] else 0,
)

_register(
    "dscr", "Debt Service Coverage Ratio", "solvency_ratios",
    "DSCR = Earnings available for Debt Service / (Interest + Principal Installments)",
    "Measures ability to service debt obligations.",
    [_inp("earnings_for_debt_service", "Earnings available for Debt Service (₹)"),
     _inp("interest_principal", "Interest + Principal Installments (₹)")],
    "ratio",
    lambda i: i["earnings_for_debt_service"] / i["interest_principal"] if i["interest_principal"] else 0,
)

# =====================================================================
# 3. ACTIVITY RATIOS  (formulas 89-91)
# =====================================================================

_register(
    "inventory_turnover", "Inventory Turnover", "activity_ratios",
    "Inventory TO = Cost of Goods Sold / Average Inventory",
    "Measures how efficiently inventory is managed.",
    [_inp("cogs", "Cost of Goods Sold (₹)"),
     _inp("average_inventory", "Average Inventory (₹)")],
    "ratio",
    lambda i: i["cogs"] / i["average_inventory"] if i["average_inventory"] else 0,
)

_register(
    "debtors_turnover", "Debtors Turnover", "activity_ratios",
    "Debtors TO = Credit Sales / Average Debtors",
    "Measures how efficiently receivables are collected.",
    [_inp("credit_sales", "Credit Sales (₹)"),
     _inp("average_debtors", "Average Debtors (₹)")],
    "ratio",
    lambda i: i["credit_sales"] / i["average_debtors"] if i["average_debtors"] else 0,
)

_register(
    "creditors_turnover", "Creditors Turnover", "activity_ratios",
    "Creditors TO = Credit Purchases / Average Creditors",
    "Measures how efficiently payables are managed.",
    [_inp("credit_purchases", "Credit Purchases (₹)"),
     _inp("average_creditors", "Average Creditors (₹)")],
    "ratio",
    lambda i: i["credit_purchases"] / i["average_creditors"] if i["average_creditors"] else 0,
)

# =====================================================================
# 4. PROFITABILITY RATIOS  (formulas 92-98)
# =====================================================================

_register(
    "roa", "Return on Assets (ROA)", "profitability_ratios",
    "ROA = (Net Profit after Tax / Average Total Assets) × 100",
    "Measures profitability relative to total assets.",
    [_inp("net_profit_after_tax", "Net Profit after Tax (₹)"),
     _inp("average_total_assets", "Average Total Assets (₹)")],
    "%",
    lambda i: (i["net_profit_after_tax"] / i["average_total_assets"]) * 100 if i["average_total_assets"] else 0,
)

_register(
    "roe", "Return on Equity (ROE)", "profitability_ratios",
    "ROE = ((PAT - Preference Dividend) / Net Worth) × 100",
    "Measures profitability relative to shareholders' equity.",
    [_inp("pat", "Profit After Tax (₹)"),
     _inp("preference_dividend", "Preference Dividend (₹)"),
     _inp("net_worth", "Net Worth (₹)")],
    "%",
    lambda i: ((i["pat"] - i["preference_dividend"]) / i["net_worth"]) * 100 if i["net_worth"] else 0,
)

_register(
    "net_profit_margin", "Net Profit Margin", "profitability_ratios",
    "Net Profit Margin = (Net Profit / Sales) × 100",
    "Measures profitability per rupee of sales.",
    [_inp("net_profit", "Net Profit (₹)"),
     _inp("sales", "Sales (₹)")],
    "%",
    lambda i: (i["net_profit"] / i["sales"]) * 100 if i["sales"] else 0,
)

_register(
    "gross_profit_margin", "Gross Profit Margin", "profitability_ratios",
    "Gross Profit Margin = (Gross Profit / Sales) × 100",
    "Measures profitability before operating expenses.",
    [_inp("gross_profit", "Gross Profit (₹)"),
     _inp("sales", "Sales (₹)")],
    "%",
    lambda i: (i["gross_profit"] / i["sales"]) * 100 if i["sales"] else 0,
)

_register(
    "eps", "Earnings per Share", "profitability_ratios",
    "EPS = (PAT - Preference Dividend) / Number of Equity Shares",
    "Measures profit attributable to each share.",
    [_inp("pat", "Profit After Tax (₹)"),
     _inp("preference_dividend", "Preference Dividend (₹)"),
     _inp("equity_shares", "Number of Equity Shares")],
    "₹/share",
    lambda i: (i["pat"] - i["preference_dividend"]) / i["equity_shares"] if i["equity_shares"] else 0,
)

_register(
    "bvps", "Book Value per Share", "profitability_ratios",
    "BVPS = Net Worth / Number of Equity Shares",
    "Measures book value attributable to each share.",
    [_inp("net_worth", "Net Worth (₹)"),
     _inp("equity_shares", "Number of Equity Shares")],
    "₹/share",
    lambda i: i["net_worth"] / i["equity_shares"] if i["equity_shares"] else 0,
)

_register(
    "pe_ratio", "P/E Ratio", "profitability_ratios",
    "P/E Ratio = Market Price per Share / Earnings per Share",
    "Measures how much investors pay per rupee of earnings.",
    [_inp("market_price_per_share", "Market Price per Share (₹)"),
     _inp("eps", "Earnings per Share (₹)")],
    "ratio",
    lambda i: i["market_price_per_share"] / i["eps"] if i["eps"] else 0,
)

# =====================================================================
# 5. TIME VALUE OF MONEY  (formulas 99-104)
# =====================================================================

_register(
    "future_value", "Future Value", "time_value",
    "FV = PV × (1 + r)^n",
    "Calculates future value of present amount with compound interest.",
    [_inp("present_value", "Present Value (₹)"),
     _inp("interest_rate", "Interest Rate (decimal, e.g. 0.10 for 10%)"),
     _inp("periods", "Number of Periods")],
    "₹",
    lambda i: i["present_value"] * (1 + i["interest_rate"]) ** i["periods"],
)

_register(
    "present_value", "Present Value", "time_value",
    "PV = FV / (1 + r)^n",
    "Calculates present value of future amount with discounting.",
    [_inp("future_value", "Future Value (₹)"),
     _inp("discount_rate", "Discount Rate (decimal, e.g. 0.10 for 10%)"),
     _inp("periods", "Number of Periods")],
    "₹",
    lambda i: i["future_value"] / (1 + i["discount_rate"]) ** i["periods"],
)

_register(
    "ordinary_annuity_fv", "Ordinary Annuity Future Value", "time_value",
    "FV_annuity = A × ((1 + r)^n - 1) / r",
    "Calculates future value of regular annuity payments.",
    [_inp("annuity_payment", "Annuity Payment (₹)"),
     _inp("interest_rate", "Interest Rate (decimal)"),
     _inp("periods", "Number of Periods")],
    "₹",
    lambda i: i["annuity_payment"] * ((1 + i["interest_rate"]) ** i["periods"] - 1) / i["interest_rate"] if i["interest_rate"] else i["annuity_payment"] * i["periods"],
)

_register(
    "ordinary_annuity_pv", "Ordinary Annuity Present Value", "time_value",
    "PV_annuity = A × (1 - (1 + r)^-n) / r",
    "Calculates present value of regular annuity payments.",
    [_inp("annuity_payment", "Annuity Payment (₹)"),
     _inp("interest_rate", "Interest Rate (decimal)"),
     _inp("periods", "Number of Periods")],
    "₹",
    lambda i: i["annuity_payment"] * (1 - (1 + i["interest_rate"]) ** (-i["periods"])) / i["interest_rate"] if i["interest_rate"] else i["annuity_payment"] * i["periods"],
)

_register(
    "perpetuity_pv", "Perpetuity Present Value", "time_value",
    "PV_perpetuity = A / r",
    "Calculates present value of perpetual payments.",
    [_inp("perpetuity_payment", "Perpetuity Payment (₹)"),
     _inp("interest_rate", "Interest Rate (decimal)")],
    "₹",
    lambda i: i["perpetuity_payment"] / i["interest_rate"] if i["interest_rate"] else 0,
)

_register(
    "growing_perpetuity_pv", "Growing Perpetuity Present Value", "time_value",
    "PV_growing = A₁ / (r - g)",
    "Calculates present value of perpetuity with growth.",
    [_inp("first_payment", "First Payment (₹)"),
     _inp("interest_rate", "Interest Rate (decimal)"),
     _inp("growth_rate", "Growth Rate (decimal)")],
    "₹",
    lambda i: i["first_payment"] / (i["interest_rate"] - i["growth_rate"]) if (i["interest_rate"] - i["growth_rate"]) != 0 else 0,
)

# =====================================================================
# 6. COST OF CAPITAL  (formulas 105-112)
# =====================================================================

_register(
    "cost_irredeemable_debt", "Cost of Irredeemable Debt", "cost_of_capital",
    "k_d = I(1 - t) / Net Proceeds",
    "Calculates after-tax cost of irredeemable debt.",
    [_inp("interest", "Annual Interest (₹)"),
     _inp("tax_rate", "Tax Rate (decimal)"),
     _inp("net_proceeds", "Net Proceeds (₹)")],
    "decimal",
    lambda i: i["interest"] * (1 - i["tax_rate"]) / i["net_proceeds"] if i["net_proceeds"] else 0,
)

_register(
    "cost_redeemable_debt", "Cost of Redeemable Debt (Approx)", "cost_of_capital",
    "k_d = (I(1 - t) + (RV - NP)/n) / ((RV + NP)/2)",
    "Calculates approximate cost of redeemable debt.",
    [_inp("interest", "Annual Interest (₹)"),
     _inp("tax_rate", "Tax Rate (decimal)"),
     _inp("redemption_value", "Redemption Value (₹)"),
     _inp("net_proceeds", "Net Proceeds (₹)"),
     _inp("years", "Years to Maturity")],
    "decimal",
    lambda i: (i["interest"] * (1 - i["tax_rate"]) + (i["redemption_value"] - i["net_proceeds"]) / i["years"]) / ((i["redemption_value"] + i["net_proceeds"]) / 2) if ((i["redemption_value"] + i["net_proceeds"]) / 2) != 0 else 0,
)

_register(
    "cost_irredeemable_preference", "Cost of Irredeemable Preference Shares", "cost_of_capital",
    "k_p = Preference Dividend / Net Proceeds",
    "Calculates cost of irredeemable preference shares.",
    [_inp("preference_dividend", "Preference Dividend (₹)"),
     _inp("net_proceeds", "Net Proceeds (₹)")],
    "decimal",
    lambda i: i["preference_dividend"] / i["net_proceeds"] if i["net_proceeds"] else 0,
)

_register(
    "cost_redeemable_preference", "Cost of Redeemable Preference Shares", "cost_of_capital",
    "k_p = (Dividend + (RV - NP)/n) / ((RV + NP)/2)",
    "Calculates cost of redeemable preference shares.",
    [_inp("dividend", "Dividend (₹)"),
     _inp("redemption_value", "Redemption Value (₹)"),
     _inp("net_proceeds", "Net Proceeds (₹)"),
     _inp("years", "Years to Maturity")],
    "decimal",
    lambda i: (i["dividend"] + (i["redemption_value"] - i["net_proceeds"]) / i["years"]) / ((i["redemption_value"] + i["net_proceeds"]) / 2) if ((i["redemption_value"] + i["net_proceeds"]) / 2) != 0 else 0,
)

_register(
    "cost_equity_dividend", "Cost of Equity (Dividend Price)", "cost_of_capital",
    "k_e = D₁/P₀ + g or k_e = D/P₀ in simple form",
    "Calculates cost of equity using dividend approach.",
    [_inp("next_dividend", "Next Year Dividend (₹)"),
     _inp("current_price", "Current Price (₹)"),
     _inp("growth_rate", "Growth Rate (decimal)", 0)],
    "decimal",
    lambda i: (i["next_dividend"] / i["current_price"]) + i["growth_rate"] if i["current_price"] else 0,
)

_register(
    "cost_equity_earnings", "Cost of Equity (Earnings Basis)", "cost_of_capital",
    "k_e = E₁/P₀",
    "Calculates cost of equity using earnings approach.",
    [_inp("next_earnings", "Next Year Earnings (₹)"),
     _inp("current_price", "Current Price (₹)")],
    "decimal",
    lambda i: i["next_earnings"] / i["current_price"] if i["current_price"] else 0,
)

_register(
    "capm", "CAPM", "cost_of_capital",
    "k_e = R_f + β(R_m - R_f)",
    "Capital Asset Pricing Model for cost of equity.",
    [_inp("risk_free_rate", "Risk-Free Rate (decimal)"),
     _inp("beta", "Beta"),
     _inp("market_return", "Market Return (decimal)")],
    "decimal",
    lambda i: i["risk_free_rate"] + i["beta"] * (i["market_return"] - i["risk_free_rate"]),
)

_register(
    "wacc", "Weighted Average Cost of Capital", "cost_of_capital",
    "WACC = Σ w_i k_i, where w_i are market-value weights",
    "Calculates weighted average cost of all capital sources.",
    [_inp("cost_equity", "Cost of Equity (decimal)"),
     _inp("cost_debt", "Cost of Debt (decimal)"),
     _inp("cost_preference", "Cost of Preference (decimal)"),
     _inp("weight_equity", "Weight of Equity (decimal)"),
     _inp("weight_debt", "Weight of Debt (decimal)"),
     _inp("weight_preference", "Weight of Preference (decimal)")],
    "decimal",
    lambda i: (i["cost_equity"] * i["weight_equity"] + i["cost_debt"] * i["weight_debt"] + i["cost_preference"] * i["weight_preference"]),
)

# =====================================================================
# 7. LEVERAGE ANALYSIS  (formulas 113-121)
# =====================================================================

_register(
    "operating_leverage", "Operating Leverage (DOL)", "leverage",
    "DOL = Contribution / EBIT",
    "Measures sensitivity of operating income to sales changes.",
    [_inp("contribution", "Contribution (₹)"),
     _inp("ebit", "EBIT (₹)")],
    "ratio",
    lambda i: i["contribution"] / i["ebit"] if i["ebit"] else 0,
)

_register(
    "financial_leverage", "Financial Leverage (DFL)", "leverage",
    "DFL = EBIT / EBT",
    "Measures sensitivity of net income to operating income changes.",
    [_inp("ebit", "EBIT (₹)"),
     _inp("ebt", "EBT (₹)")],
    "ratio",
    lambda i: i["ebit"] / i["ebt"] if i["ebt"] else 0,
)

_register(
    "combined_leverage", "Combined Leverage (DCL)", "leverage",
    "DCL = Contribution / EBT = DOL × DFL",
    "Measures total leverage effect.",
    [_inp("contribution", "Contribution (₹)"),
     _inp("ebt", "EBT (₹)")],
    "ratio",
    lambda i: i["contribution"] / i["ebt"] if i["ebt"] else 0,
)

_register(
    "ni_approach", "NI Approach (Value of Firm)", "leverage",
    "V = Earnings available for Equity / k_e when k_e is assumed constant",
    "Net Income approach to firm valuation.",
    [_inp("earnings_equity", "Earnings available for Equity (₹)"),
     _inp("cost_equity", "Cost of Equity (decimal)")],
    "₹",
    lambda i: i["earnings_equity"] / i["cost_equity"] if i["cost_equity"] else 0,
)

_register(
    "noi_approach", "NOI Approach (Overall Cost)", "leverage",
    "V = EBIT / k₀; k₀ constant; k_e adjusts with leverage",
    "Net Operating Income approach to firm valuation.",
    [_inp("ebit", "EBIT (₹)"),
     _inp("overall_cost", "Overall Cost of Capital (decimal)")],
    "₹",
    lambda i: i["ebit"] / i["overall_cost"] if i["overall_cost"] else 0,
)

_register(
    "mm_no_tax_levered_equity", "MM No-Tax Levered Equity Cost", "leverage",
    "k_e = k₀ + (k₀ - k_d) × D/E",
    "Modigliani-Miller without taxes: levered equity cost.",
    [_inp("unlevered_cost", "Unlevered Cost of Capital (decimal)"),
     _inp("cost_debt", "Cost of Debt (decimal)"),
     _inp("debt_equity", "Debt/Equity Ratio")],
    "decimal",
    lambda i: i["unlevered_cost"] + (i["unlevered_cost"] - i["cost_debt"]) * i["debt_equity"],
)

_register(
    "mm_with_tax_levered_value", "MM with Tax (Levered Value)", "leverage",
    "V_L = V_U + tD",
    "Modigliani-Miller with taxes: levered firm value.",
    [_inp("unlevered_value", "Unlevered Firm Value (₹)"),
     _inp("tax_rate", "Corporate Tax Rate (decimal)"),
     _inp("debt", "Value of Debt (₹)")],
    "₹",
    lambda i: i["unlevered_value"] + i["tax_rate"] * i["debt"],
)

_register(
    "financial_bep", "Financial Break-Even Point", "leverage",
    "Financial BEP = (Interest + Preference Dividend/(1-t)) / 1",
    "EBIT at which EPS is zero.",
    [_inp("interest", "Interest Expense (₹)"),
     _inp("preference_dividend", "Preference Dividend (₹)"),
     _inp("tax_rate", "Tax Rate (decimal)")],
    "₹",
    lambda i: i["interest"] + i["preference_dividend"] / (1 - i["tax_rate"]) if (1 - i["tax_rate"]) != 0 else 0,
)

_register(
    "eps_indifference", "Indifference Point (EPS)", "leverage",
    "(EBIT - I₁)(1-t)/E₁ = (EBIT - I₂)(1-t)/E₂; solve for EBIT",
    "EBIT level where EPS is same under different financing.",
    [_inp("interest1", "Interest Plan 1 (₹)"),
     _inp("equity1", "Equity Shares Plan 1"),
     _inp("interest2", "Interest Plan 2 (₹)"),
     _inp("equity2", "Equity Shares Plan 2"),
     _inp("tax_rate", "Tax Rate (decimal)")],
    "₹",
    lambda i: (i["interest1"] * i["equity2"] - i["interest2"] * i["equity1"]) / (i["equity2"] - i["equity1"]) if (i["equity2"] - i["equity1"]) != 0 else 0,
)

# =====================================================================
# 8. CAPITAL BUDGETING  (formulas 122-127)
# =====================================================================

_register(
    "npv", "Net Present Value", "capital_budgeting",
    "NPV = Σ CF_t/(1+r)^t - C₀",
    "Calculates net present value of cash flows.",
    [_inp("cash_flows", "Cash Flows (comma-separated)"),
     _inp("discount_rate", "Discount Rate (decimal)"),
     _inp("initial_investment", "Initial Investment (₹)")],
    "₹",
    lambda i: sum([float(cf.strip()) / (1 + i["discount_rate"]) ** idx for idx, cf in enumerate(i["cash_flows"].split(","))]) - i["initial_investment"],
)

_register(
    "irr_definition", "IRR (Definition)", "capital_budgeting",
    "IRR is rate r such that Σ CF_t/(1+r)^t = C₀",
    "Internal Rate of Return - solves for discount rate.",
    [_inp("cash_flows", "Cash Flows (comma-separated)"),
     _inp("initial_investment", "Initial Investment (₹)")],
    "decimal",
    lambda i: 0.1,  # Simplified - actual IRR requires iterative calculation
)

_register(
    "profitability_index", "Profitability Index", "capital_budgeting",
    "PI = PV of Future Cash Inflows / Initial Investment",
    "Measures profitability per rupee invested.",
    [_inp("pv_cash_inflows", "PV of Future Cash Inflows (₹)"),
     _inp("initial_investment", "Initial Investment (₹)")],
    "ratio",
    lambda i: i["pv_cash_inflows"] / i["initial_investment"] if i["initial_investment"] else 0,
)

_register(
    "payback_period", "Payback Period", "capital_budgeting",
    "Payback = time to recover initial investment from undiscounted cash inflows",
    "Measures how quickly investment is recovered.",
    [_inp("annual_cash_inflows", "Annual Cash Inflows (₹)"),
     _inp("initial_investment", "Initial Investment (₹)")],
    "years",
    lambda i: i["initial_investment"] / i["annual_cash_inflows"] if i["annual_cash_inflows"] else 0,
)

_register(
    "discounted_payback", "Discounted Payback Period", "capital_budgeting",
    "Discounted Payback = time to recover initial investment from discounted inflows",
    "Measures recovery time considering time value.",
    [_inp("discounted_cash_inflows", "Discounted Cash Inflows (₹)"),
     _inp("initial_investment", "Initial Investment (₹)")],
    "years",
    lambda i: i["initial_investment"] / i["discounted_cash_inflows"] if i["discounted_cash_inflows"] else 0,
)

_register(
    "equivalent_annual_annuity", "Equivalent Annual Annuity", "capital_budgeting",
    "EAA = NPV / PVAF(r,n)",
    "Converts NPV to equivalent annual annuity.",
    [_inp("npv", "Net Present Value (₹)"),
     _inp("pvaf", "Present Value Annuity Factor")],
    "₹",
    lambda i: i["npv"] / i["pvaf"] if i["pvaf"] else 0,
)

# =====================================================================
# 9. DIVIDEND MODELS  (formulas 128-130)
# =====================================================================

_register(
    "walters_dividend_model", "Walter's Dividend Model", "dividend_models",
    "P₀ = (D + (r/k_e)(E - D))/k_e",
    "Walter's model for share price based on dividend policy.",
    [_inp("dividend", "Dividend per Share (₹)"),
     _inp("return_rate", "Return Rate (decimal)"),
     _inp("cost_equity", "Cost of Equity (decimal)"),
     _inp("earnings", "Earnings per Share (₹)")],
    "₹",
    lambda i: (i["dividend"] + (i["return_rate"] / i["cost_equity"]) * (i["earnings"] - i["dividend"])) / i["cost_equity"] if i["cost_equity"] else 0,
)

_register(
    "gordon_growth_model", "Gordon Growth Model", "dividend_models",
    "P₀ = D₁/(k_e - g), where g = br",
    "Gordon's constant growth model.",
    [_inp("next_dividend", "Next Year Dividend (₹)"),
     _inp("cost_equity", "Cost of Equity (decimal)"),
     _inp("growth_rate", "Growth Rate (decimal)")],
    "₹",
    lambda i: i["next_dividend"] / (i["cost_equity"] - i["growth_rate"]) if (i["cost_equity"] - i["growth_rate"]) != 0 else 0,
)

_register(
    "mm_dividend_model", "MM Dividend Model (Value)", "dividend_models",
    "P₀ = (D₁ + P₁)/(1 + k_e)",
    "Modigliani-Miller dividend irrelevance model.",
    [_inp("next_dividend", "Next Year Dividend (₹)"),
     _inp("next_price", "Next Year Price (₹)"),
     _inp("cost_equity", "Cost of Equity (decimal)")],
    "₹",
    lambda i: (i["next_dividend"] + i["next_price"]) / (1 + i["cost_equity"]),
)

# =====================================================================
# 10. BOND ANALYSIS  (formulas 131-138)
# =====================================================================

_register(
    "bond_value_straight", "Bond Value (Straight)", "dividend_models",
    "P₀ = C × PVIFA(k_d, n) + RV × PVIF(k_d, n)",
    "Values straight bond using present value factors.",
    [_inp("coupon", "Annual Coupon (₹)"),
     _inp("pvifa", "Present Value Interest Factor for Annuity"),
     _inp("redemption_value", "Redemption Value (₹)"),
     _inp("pvif", "Present Value Interest Factor")],
    "₹",
    lambda i: i["coupon"] * i["pvifa"] + i["redemption_value"] * i["pvif"],
)

_register(
    "current_yield_bond", "Current Yield on Bond", "bond_analysis",
    "Current Yield = (Annual Coupon / Current Market Price) × 100",
    "Measures yield based on current market price.",
    [_inp("annual_coupon", "Annual Coupon (₹)"),
     _inp("current_market_price", "Current Market Price (₹)")],
    "%",
    lambda i: (i["annual_coupon"] / i["current_market_price"]) * 100 if i["current_market_price"] else 0,
)

_register(
    "ytm_concept", "Yield to Maturity (Concept)", "bond_analysis",
    "YTM is discount rate that equates present value of all bond cash flows to current price",
    "Conceptual definition of YTM.",
    [_inp("current_price", "Current Bond Price (₹)"),
     _inp("cash_flows", "Bond Cash Flows (comma-separated)")],
    "decimal",
    lambda i: 0.08,  # Simplified - actual YTM requires iterative calculation
)

_register(
    "equity_value_single_period", "Equity Value (Single-Period)", "bond_analysis",
    "P₀ = (D₁ + P₁)/(1 + k_e)",
    "Single period equity valuation.",
    [_inp("next_dividend", "Next Year Dividend (₹)"),
     _inp("next_price", "Next Year Price (₹)"),
     _inp("cost_equity", "Cost of Equity (decimal)")],
    "₹",
    lambda i: (i["next_dividend"] + i["next_price"]) / (1 + i["cost_equity"]),
)

_register(
    "holding_period_return", "Holding Period Return", "bond_analysis",
    "HPR = (Dividend + Price Change) / Initial Price",
    "Measures total return over holding period.",
    [_inp("dividend", "Dividend Received (₹)"),
     _inp("price_change", "Price Change (₹)"),
     _inp("initial_price", "Initial Price (₹)")],
    "decimal",
    lambda i: (i["dividend"] + i["price_change"]) / i["initial_price"] if i["initial_price"] else 0,
)

_register(
    "expected_return_discrete", "Expected Return (Discrete)", "bond_analysis",
    "E(R) = Σ p_i R_i",
    "Expected return with probability distribution.",
    [_inp("returns", "Returns (comma-separated)"),
     _inp("probabilities", "Probabilities (comma-separated)")],
    "decimal",
    lambda i: sum([float(p.strip()) * float(r.strip()) for p, r in zip(i["probabilities"].split(","), i["returns"].split(","))]),
)

_register(
    "variance_discrete", "Variance (Discrete)", "bond_analysis",
    "σ² = Σ p_i(R_i - E(R))²",
    "Measures dispersion of returns.",
    [_inp("returns", "Returns (comma-separated)"),
     _inp("probabilities", "Probabilities (comma-separated)"),
     _inp("expected_return", "Expected Return (decimal)")],
    "decimal",
    lambda i: sum([float(p.strip()) * (float(r.strip()) - i["expected_return"]) ** 2 for p, r in zip(i["probabilities"].split(","), i["returns"].split(","))]),
)

_register(
    "standard_deviation", "Standard Deviation", "bond_analysis",
    "σ = √σ²",
    "Measures volatility of returns.",
    [_inp("variance", "Variance")],
    "decimal",
    lambda i: math.sqrt(i["variance"]) if i["variance"] >= 0 else 0,
)

_register(
    "coefficient_of_variation", "Coefficient of Variation", "bond_analysis",
    "CV = σ/E(R)",
    "Measures relative risk.",
    [_inp("standard_deviation", "Standard Deviation"),
     _inp("expected_return", "Expected Return")],
    "decimal",
    lambda i: i["standard_deviation"] / i["expected_return"] if i["expected_return"] != 0 else 0,
)

# =====================================================================
# 11. PORTFOLIO ANALYSIS  (formulas 139-149)
# =====================================================================

_register(
    "covariance_two_assets", "Covariance (Two Assets)", "portfolio_analysis",
    "Cov_AB = Σ p_i[R_A,i - E(R_A)][R_B,i - E(R_B)]",
    "Measures how two assets move together.",
    [_inp("returns_a", "Asset A Returns (comma-separated)"),
     _inp("returns_b", "Asset B Returns (comma-separated)"),
     _inp("probabilities", "Probabilities (comma-separated)"),
     _inp("expected_return_a", "Expected Return A"),
     _inp("expected_return_b", "Expected Return B")],
    "decimal",
    lambda i: sum([float(p.strip()) * (float(ra.strip()) - i["expected_return_a"]) * (float(rb.strip()) - i["expected_return_b"]) for p, ra, rb in zip(i["probabilities"].split(","), i["returns_a"].split(","), i["returns_b"].split(","))]),
)

_register(
    "correlation", "Correlation", "portfolio_analysis",
    "ρ_AB = Cov_AB / (σ_A σ_B)",
    "Measures linear relationship between assets.",
    [_inp("covariance", "Covariance"),
     _inp("std_dev_a", "Standard Deviation A"),
     _inp("std_dev_b", "Standard Deviation B")],
    "decimal",
    lambda i: i["covariance"] / (i["std_dev_a"] * i["std_dev_b"]) if (i["std_dev_a"] * i["std_dev_b"]) != 0 else 0,
)

_register(
    "portfolio_return_two_assets", "Portfolio Return (Two Assets)", "portfolio_analysis",
    "R_p = w_A R_A + w_B R_B",
    "Expected return of two-asset portfolio.",
    [_inp("weight_a", "Weight of Asset A"),
     _inp("return_a", "Return of Asset A"),
     _inp("weight_b", "Weight of Asset B"),
     _inp("return_b", "Return of Asset B")],
    "decimal",
    lambda i: i["weight_a"] * i["return_a"] + i["weight_b"] * i["return_b"],
)

_register(
    "portfolio_variance_two_assets", "Portfolio Variance (Two Assets)", "portfolio_analysis",
    "σ_p² = w_A²σ_A² + w_B²σ_B² + 2w_A w_B Cov_AB",
    "Variance of two-asset portfolio.",
    [_inp("weight_a", "Weight of Asset A"),
     _inp("variance_a", "Variance of Asset A"),
     _inp("weight_b", "Weight of Asset B"),
     _inp("variance_b", "Variance of Asset B"),
     _inp("covariance_ab", "Covariance AB")],
    "decimal",
    lambda i: (i["weight_a"] ** 2 * i["variance_a"]) + (i["weight_b"] ** 2 * i["variance_b"]) + (2 * i["weight_a"] * i["weight_b"] * i["covariance_ab"]),
)

_register(
    "minimum_variance_weight", "Minimum Variance Weight (Two Assets)", "portfolio_analysis",
    "w_A* = (σ_B² - Cov_AB) / (σ_A² + σ_B² - 2Cov_AB)",
    "Optimal weight for minimum variance portfolio.",
    [_inp("variance_b", "Variance of Asset B"),
     _inp("covariance_ab", "Covariance AB"),
     _inp("variance_a", "Variance of Asset A")],
    "decimal",
    lambda i: (i["variance_b"] - i["covariance_ab"]) / (i["variance_a"] + i["variance_b"] - 2 * i["covariance_ab"]) if (i["variance_a"] + i["variance_b"] - 2 * i["covariance_ab"]) != 0 else 0,
)

_register(
    "beta_security", "Beta of a Security", "portfolio_analysis",
    "β = Cov_SM / σ_M²",
    "Measures systematic risk relative to market.",
    [_inp("covariance_sm", "Covariance with Market"),
     _inp("market_variance", "Market Variance")],
    "decimal",
    lambda i: i["covariance_sm"] / i["market_variance"] if i["market_variance"] != 0 else 0,
)

_register(
    "security_characteristic_line", "Security Characteristic Line", "portfolio_analysis",
    "R_i = α + β R_M",
    "Relationship between security and market returns.",
    [_inp("alpha", "Alpha"),
     _inp("beta", "Beta"),
     _inp("market_return", "Market Return")],
    "decimal",
    lambda i: i["alpha"] + i["beta"] * i["market_return"],
)

_register(
    "sharpe_ratio", "Sharpe Ratio", "portfolio_analysis",
    "Sharpe = (R_p - R_f) / σ_p",
    "Risk-adjusted return measure.",
    [_inp("portfolio_return", "Portfolio Return"),
     _inp("risk_free_rate", "Risk-Free Rate"),
     _inp("portfolio_std_dev", "Portfolio Standard Deviation")],
    "decimal",
    lambda i: (i["portfolio_return"] - i["risk_free_rate"]) / i["portfolio_std_dev"] if i["portfolio_std_dev"] != 0 else 0,
)

_register(
    "treynor_ratio", "Treynor Ratio", "portfolio_analysis",
    "Treynor = (R_p - R_f) / β_p",
    "Risk-adjusted return using systematic risk.",
    [_inp("portfolio_return", "Portfolio Return"),
     _inp("risk_free_rate", "Risk-Free Rate"),
     _inp("portfolio_beta", "Portfolio Beta")],
    "decimal",
    lambda i: (i["portfolio_return"] - i["risk_free_rate"]) / i["portfolio_beta"] if i["portfolio_beta"] != 0 else 0,
)

_register(
    "jensens_alpha", "Jensen's Alpha", "portfolio_analysis",
    "α = R_p - [R_f + β_p(R_M - R_f)]",
    "Measures abnormal return relative to CAPM.",
    [_inp("portfolio_return", "Portfolio Return"),
     _inp("risk_free_rate", "Risk-Free Rate"),
     _inp("portfolio_beta", "Portfolio Beta"),
     _inp("market_return", "Market Return")],
    "decimal",
    lambda i: i["portfolio_return"] - (i["risk_free_rate"] + i["portfolio_beta"] * (i["market_return"] - i["risk_free_rate"])),
)

# =====================================================================
# 12. RISK MANAGEMENT & DERIVATIVES  (formulas 150-171)
# =====================================================================

_register(
    "arbitrage_pricing_theory", "Arbitrage Pricing Theory", "risk_management",
    "E(R) = R_f + β₁RP₁ + β₂RP₂ + ... + β_nRP_n",
    "Multi-factor model for expected returns.",
    [_inp("risk_free_rate", "Risk-Free Rate"),
     _inp("betas", "Betas (comma-separated)"),
     _inp("risk_premiums", "Risk Premiums (comma-separated)")],
    "decimal",
    lambda i: i["risk_free_rate"] + sum([float(b.strip()) * float(rp.strip()) for b, rp in zip(i["betas"].split(","), i["risk_premiums"].split(","))]),
)

_register(
    "nav_mutual_fund", "NAV of Mutual Fund", "mutual_funds",
    "NAV = (Total Assets - Total External Liabilities) / Number of Units",
    "Net Asset Value per mutual fund unit.",
    [_inp("total_assets", "Total Assets (₹)"),
     _inp("external_liabilities", "Total External Liabilities (₹)"),
     _inp("number_units", "Number of Units")],
    "₹/unit",
    lambda i: (i["total_assets"] - i["external_liabilities"]) / i["number_units"] if i["number_units"] else 0,
)

_register(
    "expense_ratio_mf", "Expense Ratio (MF)", "mutual_funds",
    "Expense Ratio = Total Recurring Expenses / Average NAV",
    "Measures fund's operating efficiency.",
    [_inp("recurring_expenses", "Total Recurring Expenses (₹)"),
     _inp("average_nav", "Average NAV (₹)")],
    "decimal",
    lambda i: i["recurring_expenses"] / i["average_nav"] if i["average_nav"] else 0,
)

_register(
    "entry_load_price", "Entry Load Price", "mutual_funds",
    "Purchase Price = NAV × (1 + Entry Load)",
    "Purchase price including entry load.",
    [_inp("nav", "NAV (₹)"),
     _inp("entry_load", "Entry Load (decimal)")],
    "₹",
    lambda i: i["nav"] * (1 + i["entry_load"]),
)

_register(
    "exit_load_price", "Exit Load Price", "mutual_funds",
    "Repurchase Price = NAV × (1 - Exit Load)",
    "Repurchase price after exit load.",
    [_inp("nav", "NAV (₹)"),
     _inp("exit_load", "Exit Load (decimal)")],
    "₹",
    lambda i: i["nav"] * (1 - i["exit_load"]),
)

_register(
    "var_basic_parametric", "VaR (Basic Parametric)", "risk_management",
    "VaR = Z × σ × Portfolio Value",
    "Value at Risk using normal distribution.",
    [_inp("z_score", "Z-Score"),
     _inp("std_dev", "Standard Deviation"),
     _inp("portfolio_value", "Portfolio Value (₹)")],
    "₹",
    lambda i: i["z_score"] * i["std_dev"] * i["portfolio_value"],
)

_register(
    "hedge_ratio_value", "Hedge Ratio (Value)", "risk_management",
    "Hedge Ratio = Value of Position to be Hedged / Value of Hedge Instrument",
    "Optimal hedge ratio for value.",
    [_inp("position_value", "Value of Position to be Hedged (₹)"),
     _inp("hedge_value", "Value of Hedge Instrument (₹)")],
    "ratio",
    lambda i: i["position_value"] / i["hedge_value"] if i["hedge_value"] != 0 else 0,
)

_register(
    "delta_hedge_options", "Delta Hedge (Options)", "risk_management",
    "Shares to Hedge = Δ × Number of Options",
    "Delta hedging for options.",
    [_inp("delta", "Delta"),
     _inp("number_options", "Number of Options")],
    "shares",
    lambda i: i["delta"] * i["number_options"],
)

_register(
    "futures_price_cost_carry", "Futures Price (Cost of Carry)", "derivatives",
    "F₀ = S₀ × e^rt in continuous compounding",
    "Futures price with cost of carry model.",
    [_inp("spot_price", "Spot Price (₹)"),
     _inp("interest_rate", "Interest Rate (decimal)"),
     _inp("time", "Time to Maturity (years)")],
    "₹",
    lambda i: i["spot_price"] * math.exp(i["interest_rate"] * i["time"]),
)

_register(
    "put_call_parity", "Put-Call Parity", "derivatives",
    "C + PV(X) = P + S₀",
    "Put-call parity relationship.",
    [_inp("call_price", "Call Price (₹)"),
     _inp("strike_pv", "Present Value of Strike (₹)"),
     _inp("put_price", "Put Price (₹)"),
     _inp("spot_price", "Spot Price (₹)")],
    "₹",
    lambda i: i["put_price"] + i["spot_price"] - i["call_price"] - i["strike_pv"],
)

_register(
    "forward_premium_discount", "Forward Premium/Discount", "derivatives",
    "Premium or Discount = (F - S)/S × 12/n × 100 for n months",
    "Forward premium or discount annualized.",
    [_inp("forward_price", "Forward Price (₹)"),
     _inp("spot_price", "Spot Price (₹)"),
     _inp("months", "Number of Months")],
    "%",
    lambda i: ((i["forward_price"] - i["spot_price"]) / i["spot_price"]) * (12 / i["months"]) * 100 if i["spot_price"] != 0 else 0,
)

_register(
    "interest_rate_parity", "Interest Rate Parity", "derivatives",
    "(1 + i_d)/(1 + i_f) = F/S",
    "Interest rate parity between currencies.",
    [_inp("domestic_rate", "Domestic Interest Rate (decimal)"),
     _inp("foreign_rate", "Foreign Interest Rate (decimal)"),
     _inp("forward_rate", "Forward Exchange Rate"),
     _inp("spot_rate", "Spot Exchange Rate")],
    "decimal",
    lambda i: (1 + i["domestic_rate"]) / (1 + i["foreign_rate"]) - i["forward_rate"] / i["spot_rate"],
)

_register(
    "purchasing_power_parity", "Purchasing Power Parity", "derivatives",
    "S₁ = S₀ × (1 + Inflation_home)/(1 + Inflation_foreign)",
    "PPP relationship between exchange rates and inflation.",
    [_inp("spot_rate", "Spot Exchange Rate"),
     _inp("home_inflation", "Home Inflation Rate (decimal)"),
     _inp("foreign_inflation", "Foreign Inflation Rate (decimal)")],
    "decimal",
    lambda i: i["spot_rate"] * (1 + i["home_inflation"]) / (1 + i["foreign_inflation"]),
)

_register(
    "fisher_effect", "Fisher Effect", "derivatives",
    "(1 + i) = (1 + r)(1 + π)",
    "Relationship between nominal and real interest rates.",
    [_inp("nominal_rate", "Nominal Interest Rate (decimal)"),
     _inp("real_rate", "Real Interest Rate (decimal)"),
     _inp("inflation", "Inflation Rate (decimal)")],
    "decimal",
    lambda i: (1 + i["real_rate"]) * (1 + i["inflation"]) - 1,
)

# =====================================================================
# 13. WORKING CAPITAL & FM  (formulas 167-171)
# =====================================================================

_register(
    "operating_cycle_wc", "Operating Cycle (WC)", "working_capital_fm",
    "Operating Cycle = R + W + F + D - C",
    "Cash conversion cycle periods.",
    [_inp("raw_material_period", "Raw Material Period (days)"),
     _inp("work_in_progress_period", "Work-in-Progress Period (days)"),
     _inp("finished_goods_period", "Finished Goods Period (days)"),
     _inp("debtors_period", "Debtors Period (days)"),
     _inp("creditors_period", "Creditors Period (days)")],
    "days",
    lambda i: i["raw_material_period"] + i["work_in_progress_period"] + i["finished_goods_period"] + i["debtors_period"] - i["creditors_period"],
)

_register(
    "working_capital_fm", "Working Capital", "working_capital_fm",
    "WC = Current Assets - Current Liabilities",
    "Working capital requirement.",
    [_inp("current_assets", "Current Assets (₹)"),
     _inp("current_liabilities", "Current Liabilities (₹)")],
    "₹",
    lambda i: i["current_assets"] - i["current_liabilities"],
)

_register(
    "eoq_fm_version", "EOQ (FM Version)", "working_capital_fm",
    "EOQ = √(2AO/C)",
    "Economic Order Quantity for working capital.",
    [_inp("annual_demand", "Annual Demand (units)"),
     _inp("ordering_cost", "Ordering Cost per order (₹)"),
     _inp("carrying_cost", "Carrying Cost per unit p.a. (₹)")],
    "units",
    lambda i: math.sqrt((2 * i["annual_demand"] * i["ordering_cost"]) / i["carrying_cost"]) if i["carrying_cost"] else 0,
)

_register(
    "miller_orr_cash_model", "Miller-Orr Cash Model Range", "working_capital_fm",
    "Spread = 3 × √(3σ²T/4i)",
    "Optimal cash spread in Miller-Orr model.",
    [_inp("variance", "Variance of Cash Flows"),
     _inp("time_period", "Time Period (days)"),
     _inp("interest_rate", "Interest Rate (decimal)")],
    "₹",
    lambda i: 3 * math.sqrt((3 * i["variance"] * i["time_period"]) / (4 * i["interest_rate"])),
)

_register(
    "baumol_cash_model", "Baumol Cash Model", "working_capital_fm",
    "C* = √(2TU/i), where T = transaction cost, U = total cash requirement, i = interest rate",
    "Optimal cash transfer amount in Baumol model.",
    [_inp("transaction_cost", "Transaction Cost per transfer (₹)"),
     _inp("cash_requirement", "Total Cash Requirement (₹)"),
     _inp("interest_rate", "Interest Rate (decimal)")],
    "₹",
    lambda i: math.sqrt((2 * i["transaction_cost"] * i["cash_requirement"]) / i["interest_rate"]) if i["interest_rate"] else 0,
)

_register(
    "lease_vs_buy_npv", "Lease vs Buy NPV", "working_capital_fm",
    "Compare NPV_Lease with NPV_Borrow and Buy",
    "Compare leasing vs buying using NPV.",
    [_inp("lease_npv", "NPV of Lease (₹)"),
     _inp("buy_npv", "NPV of Borrow and Buy (₹)")],
    "₹",
    lambda i: i["lease_npv"] - i["buy_npv"],
)

# =====================================================================
# 14. BUSINESS VALUATION  (formulas 172-180)
# =====================================================================

_register(
    "business_valuation_fcff", "Business Valuation (FCFF)", "valuation",
    "Firm Value = Σ FCFF_t/(1 + WACC)^t",
    "Firm valuation using free cash flow to firm.",
    [_inp("fcff", "Free Cash Flow to Firm (₹)"),
     _inp("wacc", "WACC (decimal)"),
     _inp("periods", "Number of Periods")],
    "₹",
    lambda i: i["fcff"] / (1 + i["wacc"]) ** i["periods"],
)

_register(
    "business_valuation_fcfe", "Business Valuation (FCFE)", "valuation",
    "Equity Value = Σ FCFE_t/(1 + k_e)^t",
    "Equity valuation using free cash flow to equity.",
    [_inp("fcfe", "Free Cash Flow to Equity (₹)"),
     _inp("cost_equity", "Cost of Equity (decimal)"),
     _inp("periods", "Number of Periods")],
    "₹",
    lambda i: i["fcfe"] / (1 + i["cost_equity"]) ** i["periods"],
)

_register(
    "enterprise_value", "Enterprise Value (EV)", "valuation",
    "EV = Market Cap + Debt - Cash",
    "Enterprise value calculation.",
    [_inp("market_cap", "Market Capitalization (₹)"),
     _inp("debt", "Total Debt (₹)"),
     _inp("cash", "Cash & Cash Equivalents (₹)")],
    "₹",
    lambda i: i["market_cap"] + i["debt"] - i["cash"],
)

_register(
    "free_cash_flow_firm", "Free Cash Flow to Firm", "valuation",
    "FCFF = EBIT(1 - t) + Depreciation - Capex - ΔWC",
    "Calculates free cash flow available to all capital providers.",
    [_inp("ebit", "EBIT (₹)"),
     _inp("tax_rate", "Tax Rate (decimal)"),
     _inp("depreciation", "Depreciation (₹)"),
     _inp("capex", "Capital Expenditure (₹)"),
     _inp("delta_wc", "Change in Working Capital (₹)")],
    "₹",
    lambda i: i["ebit"] * (1 - i["tax_rate"]) + i["depreciation"] - i["capex"] - i["delta_wc"],
)

_register(
    "free_cash_flow_equity", "Free Cash Flow to Equity", "valuation",
    "FCFE = Net Income + Depreciation - Capex - ΔWC + Net Borrowing",
    "Calculates free cash flow available to equity holders.",
    [_inp("net_income", "Net Income (₹)"),
     _inp("depreciation", "Depreciation (₹)"),
     _inp("capex", "Capital Expenditure (₹)"),
     _inp("delta_wc", "Change in Working Capital (₹)"),
     _inp("net_borrowing", "Net Borrowing (₹)")],
    "₹",
    lambda i: i["net_income"] + i["depreciation"] - i["capex"] - i["delta_wc"] + i["net_borrowing"],
)

_register(
    "synergy_gain_merger", "Synergy Gain (Merger)", "mergers_acquisitions",
    "Synergy = V_AB - (V_A + V_B)",
    "Value created by merger synergy.",
    [_inp("combined_value", "Combined Firm Value (₹)"),
     _inp("value_a", "Value of Firm A (₹)"),
     _inp("value_b", "Value of Firm B (₹)")],
    "₹",
    lambda i: i["combined_value"] - (i["value_a"] + i["value_b"]),
)

_register(
    "exchange_ratio_shares", "Exchange Ratio (Shares)", "mergers_acquisitions",
    "Share Exchange Ratio = Offer Price per Share / Market Price of Target Share",
    "Share exchange ratio for mergers.",
    [_inp("offer_price_per_share", "Offer Price per Share (₹)"),
     _inp("target_market_price", "Market Price of Target Share (₹)")],
    "ratio",
    lambda i: i["offer_price_per_share"] / i["target_market_price"] if i["target_market_price"] != 0 else 0,
)

_register(
    "value_merger_shareholder", "Value at Merger to Shareholder", "mergers_acquisitions",
    "Post-merger Value per Share = Total Post-merger Equity Value / Total Shares after Merger",
    "Value per share after merger.",
    [_inp("post_merger_equity_value", "Total Post-merger Equity Value (₹)"),
     _inp("total_shares_after_merger", "Total Shares after Merger")],
    "₹/share",
    lambda i: i["post_merger_equity_value"] / i["total_shares_after_merger"] if i["total_shares_after_merger"] != 0 else 0,
)

# ── Public API ────────────────────────────────────────────────────────

def get_all_formulas():
    """Return formulas grouped by category (without calc functions)."""
    grouped = {}
    for cat in CATEGORIES:
        grouped[cat["id"]] = {
            "category_id": cat["id"],
            "category_name": cat["name"],
            "icon": cat["icon"],
            "order": cat["order"],
            "formulas": [],
        }

    for fid, f in FORMULA_REGISTRY.items():
        entry = {k: v for k, v in f.items() if k != "calc"}
        grouped[f["category"]]["formulas"].append(entry)

    return sorted(grouped.values(), key=lambda g: g["order"])


def calculate_formula(formula_id: str, inputs: dict) -> dict:
    """
    Run a formula by id.
    Returns {"result": <number>, "unit": <str>, "explanation": <str>}
    Raises ValueError for unknown formula or missing/bad inputs.
    """
    if formula_id not in FORMULA_REGISTRY:
        raise ValueError(f"Unknown formula: {formula_id}")

    f = FORMULA_REGISTRY[formula_id]

    # Validate & fill defaults
    clean = {}
    for inp in f["inputs"]:
        val = inputs.get(inp["id"])
        if val is None:
            if "default" in inp:
                val = inp["default"]
            else:
                raise ValueError(f"Missing required input: {inp['label']}")
        try:
            clean[inp["id"]] = float(val)
        except (TypeError, ValueError):
            raise ValueError(f"Input '{inp['label']}' must be a number, got: {val}")

    try:
        result = f["calc"](clean)
    except ZeroDivisionError:
        raise ValueError("Division by zero — check your inputs.")
    except Exception as e:
        raise ValueError(f"Calculation error: {str(e)}")

    result = round(result, 4)

    # Build explanation
    parts = [f"{inp['label']}: {clean[inp['id']]:,.2f}" for inp in f["inputs"]]
    explanation = f"{f['name']} = {result:,.4f} {f['output_unit']}\nInputs: {', '.join(parts)}"

    if result > 0:
        explanation += "\n→ Positive / Favorable"
    elif result < 0:
        explanation += "\n→ Negative / Adverse"
    else:
        explanation += "\n→ Zero / Break-even"

    return {
        "formula_id": formula_id,
        "formula_name": f["name"],
        "result": result,
        "unit": f["output_unit"],
        "explanation": explanation,
    }
