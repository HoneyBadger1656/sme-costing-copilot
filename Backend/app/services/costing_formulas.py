# Backend/app/services/costing_formulas.py
# Complete costing formula library — 82 formulas in 13 categories

import math
from typing import Any

# ── Category definitions ──────────────────────────────────────────────
CATEGORIES = [
    {"id": "cost_structure",       "name": "Cost Structure / Cost Sheet",       "icon": "📋", "order": 1},
    {"id": "conversion_overhead",  "name": "Conversion & Overhead Rates",       "icon": "⚙️", "order": 2},
    {"id": "marginal_cvp",         "name": "Marginal Costing & CVP Analysis",   "icon": "📊", "order": 3},
    {"id": "inventory",            "name": "Inventory Management",              "icon": "📦", "order": 4},
    {"id": "material_variance",    "name": "Standard Costing — Material",       "icon": "🧱", "order": 5},
    {"id": "labour_variance",      "name": "Standard Costing — Labour",         "icon": "👷", "order": 6},
    {"id": "overhead_variance",    "name": "Standard Costing — Overheads",      "icon": "🏭", "order": 7},
    {"id": "sales_variance",       "name": "Standard Costing — Sales",          "icon": "💰", "order": 8},
    {"id": "process_contract",     "name": "Process & Contract Costing",        "icon": "🔄", "order": 9},
    {"id": "joint_service",        "name": "Joint & Service Costing",           "icon": "🔗", "order": 10},
    {"id": "abc",                  "name": "Activity Based Costing",            "icon": "🎯", "order": 11},
    {"id": "strategic",            "name": "Strategic / Modern Costing",        "icon": "🚀", "order": 12},
    {"id": "performance",          "name": "Performance Measurement",           "icon": "📈", "order": 13},
]

# ── Helper ────────────────────────────────────────────────────────────
def _inp(id: str, label: str, default=None):
    """Shorthand to build an input descriptor."""
    entry = {"id": id, "label": label, "type": "number"}
    if default is not None:
        entry["default"] = default
    return entry

# ── Formula registry ──────────────────────────────────────────────────
# Each formula is a dict with: id, name, category, formula, description,
# inputs (list of input descriptors), output_unit, calc (callable).
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
# 1. COST STRUCTURE / COST SHEET  (formulas 1–6)
# =====================================================================

_register(
    "prime_cost", "Prime Cost", "cost_structure",
    "Prime Cost = Direct Materials + Direct Labour + Direct Expenses",
    "Total of all direct costs incurred in production.",
    [_inp("direct_materials", "Direct Materials (₹)"),
     _inp("direct_labour", "Direct Labour (₹)"),
     _inp("direct_expenses", "Direct Expenses (₹)", 0)],
    "₹",
    lambda i: i["direct_materials"] + i["direct_labour"] + i["direct_expenses"],
)

_register(
    "factory_cost", "Factory / Works Cost", "cost_structure",
    "Factory Cost = Prime Cost + Factory Overheads + Opening WIP − Closing WIP",
    "Cost incurred up to the factory stage including overheads and WIP adjustments.",
    [_inp("prime_cost", "Prime Cost (₹)"),
     _inp("factory_overheads", "Factory Overheads (₹)"),
     _inp("opening_wip", "Opening WIP (₹)", 0),
     _inp("closing_wip", "Closing WIP (₹)", 0)],
    "₹",
    lambda i: i["prime_cost"] + i["factory_overheads"] + i["opening_wip"] - i["closing_wip"],
)

_register(
    "cost_of_production", "Cost of Production", "cost_structure",
    "Cost of Production = Factory Cost + Administration Overheads",
    "Total cost of manufacturing goods including administration overheads related to production.",
    [_inp("factory_cost", "Factory Cost (₹)"),
     _inp("admin_overheads", "Administration Overheads (₹)", 0)],
    "₹",
    lambda i: i["factory_cost"] + i["admin_overheads"],
)

_register(
    "cogs", "Cost of Goods Sold (COGS)", "cost_structure",
    "COGS = Cost of Production + Opening FG − Closing FG",
    "Cost of goods actually sold after adjusting for finished goods inventory changes.",
    [_inp("cost_of_production", "Cost of Production (₹)"),
     _inp("opening_fg", "Opening Finished Goods (₹)", 0),
     _inp("closing_fg", "Closing Finished Goods (₹)", 0)],
    "₹",
    lambda i: i["cost_of_production"] + i["opening_fg"] - i["closing_fg"],
)

_register(
    "cost_of_sales", "Cost of Sales", "cost_structure",
    "Cost of Sales = COGS + Selling & Distribution Overheads",
    "Full cost of sales including selling and distribution overheads.",
    [_inp("cogs", "COGS (₹)"),
     _inp("selling_overheads", "Selling & Distribution Overheads (₹)", 0)],
    "₹",
    lambda i: i["cogs"] + i["selling_overheads"],
)

_register(
    "total_cost", "Total Cost", "cost_structure",
    "Total Cost = Fixed Cost + Variable Cost",
    "Sum of all fixed and variable costs.",
    [_inp("fixed_cost", "Fixed Cost (₹)"),
     _inp("variable_cost", "Variable Cost (₹)")],
    "₹",
    lambda i: i["fixed_cost"] + i["variable_cost"],
)


# =====================================================================
# 2. CONVERSION & OVERHEAD RATES  (formulas 7–10)
# =====================================================================

_register(
    "conversion_cost", "Conversion Cost", "conversion_overhead",
    "Conversion Cost = Direct Labour + Factory Overheads",
    "Cost of converting raw materials into finished goods.",
    [_inp("direct_labour", "Direct Labour (₹)"),
     _inp("factory_overheads", "Factory Overheads (₹)")],
    "₹",
    lambda i: i["direct_labour"] + i["factory_overheads"],
)

_register(
    "oar", "Overhead Absorption Rate", "conversion_overhead",
    "OAR = Budgeted Overheads / Budgeted Base Units",
    "Rate at which overheads are absorbed into cost units. Base can be units, labour hours, machine hours, or prime cost.",
    [_inp("budgeted_overheads", "Budgeted Overheads (₹)"),
     _inp("budgeted_base_units", "Budgeted Base Units")],
    "₹ per unit",
    lambda i: i["budgeted_overheads"] / i["budgeted_base_units"] if i["budgeted_base_units"] else 0,
)

_register(
    "machine_hour_rate", "Machine Hour Rate", "conversion_overhead",
    "Machine Hour Rate = Budgeted Machine Overheads / Budgeted Machine Hours",
    "Overhead cost per machine hour.",
    [_inp("budgeted_machine_overheads", "Budgeted Machine Overheads (₹)"),
     _inp("budgeted_machine_hours", "Budgeted Machine Hours")],
    "₹/hr",
    lambda i: i["budgeted_machine_overheads"] / i["budgeted_machine_hours"] if i["budgeted_machine_hours"] else 0,
)

_register(
    "labour_hour_rate", "Labour Hour Rate", "conversion_overhead",
    "Labour Hour Rate = Budgeted Labour Overheads / Budgeted Labour Hours",
    "Overhead cost per labour hour.",
    [_inp("budgeted_labour_overheads", "Budgeted Labour Overheads (₹)"),
     _inp("budgeted_labour_hours", "Budgeted Labour Hours")],
    "₹/hr",
    lambda i: i["budgeted_labour_overheads"] / i["budgeted_labour_hours"] if i["budgeted_labour_hours"] else 0,
)


# =====================================================================
# 3. MARGINAL COSTING & CVP ANALYSIS  (formulas 11–28)
# =====================================================================

_register(
    "vc_per_unit_totals", "Variable Cost per Unit (from totals)", "marginal_cvp",
    "VC per unit = Total Variable Cost / Total Units Produced",
    "Average variable cost per unit computed from aggregate data.",
    [_inp("total_variable_cost", "Total Variable Cost (₹)"),
     _inp("total_units", "Total Units Produced")],
    "₹/unit",
    lambda i: i["total_variable_cost"] / i["total_units"] if i["total_units"] else 0,
)

_register(
    "vc_per_unit_change", "Variable Cost per Unit (from change)", "marginal_cvp",
    "VC per unit = ΔTotal Cost / ΔUnits",
    "Variable cost derived from the change in total cost when output changes.",
    [_inp("delta_total_cost", "Change in Total Cost (₹)"),
     _inp("delta_units", "Change in Units")],
    "₹/unit",
    lambda i: i["delta_total_cost"] / i["delta_units"] if i["delta_units"] else 0,
)

_register(
    "contribution", "Contribution", "marginal_cvp",
    "Contribution = Sales − Variable Cost",
    "Amount remaining after covering variable costs; available to cover fixed costs and earn profit.",
    [_inp("sales", "Sales (₹)"),
     _inp("variable_cost", "Variable Cost (₹)")],
    "₹",
    lambda i: i["sales"] - i["variable_cost"],
)

_register(
    "marginal_equation", "Marginal Costing Equation", "marginal_cvp",
    "Sales − Variable Cost = Fixed Cost + Profit",
    "Fundamental marginal costing identity. Enter Sales, VC, and FC to find Profit.",
    [_inp("sales", "Sales (₹)"),
     _inp("variable_cost", "Variable Cost (₹)"),
     _inp("fixed_cost", "Fixed Cost (₹)")],
    "₹",
    lambda i: (i["sales"] - i["variable_cost"]) - i["fixed_cost"],
)

_register(
    "profit_from_contribution", "Profit / Loss from Contribution", "marginal_cvp",
    "Profit = Contribution − Fixed Cost",
    "If contribution > fixed cost, there is profit; otherwise, loss.",
    [_inp("contribution", "Contribution (₹)"),
     _inp("fixed_cost", "Fixed Cost (₹)")],
    "₹",
    lambda i: i["contribution"] - i["fixed_cost"],
)

_register(
    "pv_ratio", "P/V Ratio (Contribution / Sales)", "marginal_cvp",
    "P/V Ratio = (Contribution / Sales) × 100",
    "Profit-volume ratio indicates the proportion of contribution in sales.",
    [_inp("contribution", "Contribution (₹)"),
     _inp("sales", "Sales (₹)")],
    "%",
    lambda i: (i["contribution"] / i["sales"]) * 100 if i["sales"] else 0,
)

_register(
    "pv_ratio_per_unit", "P/V Ratio (per unit)", "marginal_cvp",
    "P/V Ratio = (Contribution per unit / Selling Price per unit) × 100",
    "P/V ratio computed from per-unit figures.",
    [_inp("contribution_per_unit", "Contribution per unit (₹)"),
     _inp("selling_price_per_unit", "Selling Price per unit (₹)")],
    "%",
    lambda i: (i["contribution_per_unit"] / i["selling_price_per_unit"]) * 100 if i["selling_price_per_unit"] else 0,
)

_register(
    "pv_ratio_change", "P/V Ratio (change basis)", "marginal_cvp",
    "P/V Ratio = (ΔContribution / ΔSales) × 100",
    "P/V ratio derived from changes in contribution and sales.",
    [_inp("delta_contribution", "Change in Contribution (₹)"),
     _inp("delta_sales", "Change in Sales (₹)")],
    "%",
    lambda i: (i["delta_contribution"] / i["delta_sales"]) * 100 if i["delta_sales"] else 0,
)

_register(
    "bep_units", "Break-Even Point (units)", "marginal_cvp",
    "BEP (units) = Fixed Cost / Contribution per unit",
    "Number of units that must be sold to cover all fixed costs.",
    [_inp("fixed_cost", "Fixed Cost (₹)"),
     _inp("contribution_per_unit", "Contribution per unit (₹)")],
    "units",
    lambda i: i["fixed_cost"] / i["contribution_per_unit"] if i["contribution_per_unit"] else 0,
)

_register(
    "bep_sales", "Break-Even Point (sales value)", "marginal_cvp",
    "BEP (sales) = Fixed Cost / (P/V Ratio / 100)",
    "Sales value required to break even.",
    [_inp("fixed_cost", "Fixed Cost (₹)"),
     _inp("pv_ratio", "P/V Ratio (%)")],
    "₹",
    lambda i: i["fixed_cost"] / (i["pv_ratio"] / 100) if i["pv_ratio"] else 0,
)

_register(
    "mos_value", "Margin of Safety (value)", "marginal_cvp",
    "MOS = Actual Sales − BEP Sales",
    "Excess of actual sales over break-even sales; cushion before losses begin.",
    [_inp("actual_sales", "Actual Sales (₹)"),
     _inp("bep_sales", "BEP Sales (₹)")],
    "₹",
    lambda i: i["actual_sales"] - i["bep_sales"],
)

_register(
    "mos_units", "Margin of Safety (units)", "marginal_cvp",
    "MOS (units) = Profit / Contribution per unit",
    "Number of units above break-even.",
    [_inp("profit", "Profit (₹)"),
     _inp("contribution_per_unit", "Contribution per unit (₹)")],
    "units",
    lambda i: i["profit"] / i["contribution_per_unit"] if i["contribution_per_unit"] else 0,
)

_register(
    "mos_ratio", "MOS Ratio", "marginal_cvp",
    "MOS Ratio = (MOS Sales / Total Sales) × 100",
    "Margin of safety expressed as a percentage of total sales.",
    [_inp("mos_sales", "MOS Sales (₹)"),
     _inp("total_sales", "Total Sales (₹)")],
    "%",
    lambda i: (i["mos_sales"] / i["total_sales"]) * 100 if i["total_sales"] else 0,
)

_register(
    "sales_for_profit_units", "Sales for Desired Profit (units)", "marginal_cvp",
    "Required Units = (Fixed Cost + Desired Profit) / Contribution per unit",
    "Units required to achieve a target profit.",
    [_inp("fixed_cost", "Fixed Cost (₹)"),
     _inp("desired_profit", "Desired Profit (₹)"),
     _inp("contribution_per_unit", "Contribution per unit (₹)")],
    "units",
    lambda i: (i["fixed_cost"] + i["desired_profit"]) / i["contribution_per_unit"] if i["contribution_per_unit"] else 0,
)

_register(
    "sales_for_profit_value", "Sales for Desired Profit (value)", "marginal_cvp",
    "Required Sales = (Fixed Cost + Desired Profit) / (P/V Ratio / 100)",
    "Sales revenue required to achieve a target profit.",
    [_inp("fixed_cost", "Fixed Cost (₹)"),
     _inp("desired_profit", "Desired Profit (₹)"),
     _inp("pv_ratio", "P/V Ratio (%)")],
    "₹",
    lambda i: (i["fixed_cost"] + i["desired_profit"]) / (i["pv_ratio"] / 100) if i["pv_ratio"] else 0,
)

_register(
    "indifference_point", "Indifference Point", "marginal_cvp",
    "Indifference Point (units) = ΔFixed Cost / ΔContribution per unit",
    "Output level where two cost structures yield the same total cost.",
    [_inp("delta_fixed_cost", "Difference in Fixed Costs (₹)"),
     _inp("delta_contribution_per_unit", "Difference in Contribution per unit (₹)")],
    "units",
    lambda i: i["delta_fixed_cost"] / i["delta_contribution_per_unit"] if i["delta_contribution_per_unit"] else 0,
)

_register(
    "composite_bep", "Composite BEP (sales mix)", "marginal_cvp",
    "Composite BEP Sales = Total Fixed Cost / (Overall P/V Ratio / 100)",
    "Break-even sales for a multi-product firm using the overall P/V ratio.",
    [_inp("total_fixed_cost", "Total Fixed Cost (₹)"),
     _inp("overall_pv_ratio", "Overall P/V Ratio (%)")],
    "₹",
    lambda i: i["total_fixed_cost"] / (i["overall_pv_ratio"] / 100) if i["overall_pv_ratio"] else 0,
)

_register(
    "overall_pv_ratio", "Overall P/V Ratio (multi-product)", "marginal_cvp",
    "Overall P/V Ratio = (Σ Product Contributions / Σ Product Sales) × 100",
    "Weighted average P/V ratio across all products.",
    [_inp("total_contribution", "Total Contribution (all products, ₹)"),
     _inp("total_sales", "Total Sales (all products, ₹)")],
    "%",
    lambda i: (i["total_contribution"] / i["total_sales"]) * 100 if i["total_sales"] else 0,
)


# =====================================================================
# 4. INVENTORY MANAGEMENT  (formulas 29–33)
# =====================================================================

_register(
    "eoq", "Economic Order Quantity (EOQ)", "inventory",
    "EOQ = √(2AO / C)",
    "Optimal order quantity that minimises total ordering and carrying costs. A = annual demand, O = ordering cost per order, C = carrying cost per unit per annum.",
    [_inp("annual_demand", "Annual Demand (units)"),
     _inp("ordering_cost", "Ordering Cost per order (₹)"),
     _inp("carrying_cost", "Carrying Cost per unit p.a. (₹)")],
    "units",
    lambda i: math.sqrt((2 * i["annual_demand"] * i["ordering_cost"]) / i["carrying_cost"]) if i["carrying_cost"] else 0,
)

_register(
    "reorder_level", "Reorder Level", "inventory",
    "Reorder Level = Maximum Usage × Maximum Lead Time",
    "Stock level at which a new order must be placed.",
    [_inp("max_usage", "Maximum Usage (units/day)"),
     _inp("max_lead_time", "Maximum Lead Time (days)")],
    "units",
    lambda i: i["max_usage"] * i["max_lead_time"],
)

_register(
    "max_stock_level", "Maximum Stock Level", "inventory",
    "Max Level = Reorder Level + EOQ − (Min Usage × Min Lead Time)",
    "Upper limit of stock to be held.",
    [_inp("reorder_level", "Reorder Level (units)"),
     _inp("eoq", "EOQ (units)"),
     _inp("min_usage", "Minimum Usage (units/day)"),
     _inp("min_lead_time", "Minimum Lead Time (days)")],
    "units",
    lambda i: i["reorder_level"] + i["eoq"] - (i["min_usage"] * i["min_lead_time"]),
)

_register(
    "min_stock_level", "Minimum Stock Level", "inventory",
    "Min Level = Reorder Level − (Normal Usage × Normal Lead Time)",
    "Safety stock — lowest stock level before risk of stockout.",
    [_inp("reorder_level", "Reorder Level (units)"),
     _inp("normal_usage", "Normal Usage (units/day)"),
     _inp("normal_lead_time", "Normal Lead Time (days)")],
    "units",
    lambda i: i["reorder_level"] - (i["normal_usage"] * i["normal_lead_time"]),
)

_register(
    "avg_stock_level", "Average Stock Level", "inventory",
    "Average Stock = (Min Level + Max Level) / 2",
    "Average inventory held over a period.",
    [_inp("min_level", "Minimum Level (units)"),
     _inp("max_level", "Maximum Level (units)")],
    "units",
    lambda i: (i["min_level"] + i["max_level"]) / 2,
)


# =====================================================================
# 5. STANDARD COSTING — MATERIAL VARIANCES  (formulas 34–38)
# =====================================================================

_register(
    "mcv", "Material Cost Variance", "material_variance",
    "MCV = (SP × SQ) − (AP × AQ)",
    "Total material cost variance — difference between standard and actual material cost.",
    [_inp("sp", "Standard Price (₹)"), _inp("sq", "Standard Quantity"),
     _inp("ap", "Actual Price (₹)"), _inp("aq", "Actual Quantity")],
    "₹",
    lambda i: (i["sp"] * i["sq"]) - (i["ap"] * i["aq"]),
)

_register(
    "mpv", "Material Price Variance", "material_variance",
    "MPV = (SP − AP) × AQ",
    "Variance due to the difference between standard and actual material price.",
    [_inp("sp", "Standard Price (₹)"), _inp("ap", "Actual Price (₹)"),
     _inp("aq", "Actual Quantity")],
    "₹",
    lambda i: (i["sp"] - i["ap"]) * i["aq"],
)

_register(
    "muv", "Material Usage Variance", "material_variance",
    "MUV = SP × (SQ − AQ)",
    "Variance due to the difference between standard and actual material quantity used.",
    [_inp("sp", "Standard Price (₹)"), _inp("sq", "Standard Quantity"),
     _inp("aq", "Actual Quantity")],
    "₹",
    lambda i: i["sp"] * (i["sq"] - i["aq"]),
)

_register(
    "mmv", "Material Mix Variance", "material_variance",
    "MMV = SP × (RSQ − AQ)",
    "Variance due to the difference between revised standard quantity and actual quantity. RSQ = Revised Standard Quantity.",
    [_inp("sp", "Standard Price (₹)"), _inp("rsq", "Revised Standard Quantity"),
     _inp("aq", "Actual Quantity")],
    "₹",
    lambda i: i["sp"] * (i["rsq"] - i["aq"]),
)

_register(
    "myv", "Material Yield Variance", "material_variance",
    "MYV = SP per unit of output × (AY − SY)",
    "Variance arising from the difference between actual yield and standard yield.",
    [_inp("sp_per_output", "Standard Price per unit of output (₹)"),
     _inp("ay", "Actual Yield (units)"), _inp("sy", "Standard Yield (units)")],
    "₹",
    lambda i: i["sp_per_output"] * (i["ay"] - i["sy"]),
)


# =====================================================================
# 6. STANDARD COSTING — LABOUR VARIANCES  (formulas 39–43)
# =====================================================================

_register(
    "lcv", "Labour Cost Variance", "labour_variance",
    "LCV = (SR × ST) − (AR × AT)",
    "Total labour cost variance.",
    [_inp("sr", "Standard Rate (₹/hr)"), _inp("st", "Standard Time (hrs)"),
     _inp("ar", "Actual Rate (₹/hr)"), _inp("at", "Actual Time (hrs)")],
    "₹",
    lambda i: (i["sr"] * i["st"]) - (i["ar"] * i["at"]),
)

_register(
    "lrv", "Labour Rate Variance", "labour_variance",
    "LRV = (SR − AR) × AT",
    "Variance due to the difference between standard and actual wage rate.",
    [_inp("sr", "Standard Rate (₹/hr)"), _inp("ar", "Actual Rate (₹/hr)"),
     _inp("at", "Actual Time (hrs)")],
    "₹",
    lambda i: (i["sr"] - i["ar"]) * i["at"],
)

_register(
    "lev", "Labour Efficiency Variance", "labour_variance",
    "LEV = SR × (ST − AT)",
    "Variance due to the difference between standard and actual labour time.",
    [_inp("sr", "Standard Rate (₹/hr)"),
     _inp("st", "Standard Time (hrs)"), _inp("at", "Actual Time (hrs)")],
    "₹",
    lambda i: i["sr"] * (i["st"] - i["at"]),
)

_register(
    "idle_time_variance", "Labour Idle Time Variance", "labour_variance",
    "Idle Time Variance = Idle Hours × SR",
    "Cost of abnormal idle time at standard rate.",
    [_inp("idle_hours", "Idle Hours"),
     _inp("sr", "Standard Rate (₹/hr)")],
    "₹",
    lambda i: i["idle_hours"] * i["sr"],
)

_register(
    "lmv", "Labour Mix Variance", "labour_variance",
    "LMV = SR × (RST − AT)",
    "Variance due to the difference between revised standard time and actual time. RST = Revised Standard Time.",
    [_inp("sr", "Standard Rate (₹/hr)"),
     _inp("rst", "Revised Standard Time (hrs)"), _inp("at", "Actual Time (hrs)")],
    "₹",
    lambda i: i["sr"] * (i["rst"] - i["at"]),
)


# =====================================================================
# 7. STANDARD COSTING — OVERHEAD VARIANCES  (formulas 44–48)
# =====================================================================

_register(
    "voh_expenditure", "Variable OH Expenditure Variance", "overhead_variance",
    "VOH Exp. Var. = (SR × ST) − (AR × AT)",
    "Difference between absorbed and actual variable overheads.",
    [_inp("sr", "Standard Rate (₹/hr)"), _inp("st", "Standard Time (hrs)"),
     _inp("ar", "Actual Rate (₹/hr)"), _inp("at", "Actual Time (hrs)")],
    "₹",
    lambda i: (i["sr"] * i["st"]) - (i["ar"] * i["at"]),
)

_register(
    "foh_cost", "Fixed OH Cost Variance", "overhead_variance",
    "FOH Cost Var. = (SR × ST) − Actual Fixed OH",
    "Total fixed overhead variance.",
    [_inp("sr", "Standard Rate (₹/hr)"), _inp("st", "Standard Time (hrs)"),
     _inp("actual_foh", "Actual Fixed Overheads (₹)")],
    "₹",
    lambda i: (i["sr"] * i["st"]) - i["actual_foh"],
)

_register(
    "foh_volume", "Fixed OH Volume Variance", "overhead_variance",
    "FOH Volume Var. = SR × (ST − BT)",
    "Variance due to actual production differing from budgeted production (in hours).",
    [_inp("sr", "Standard Rate (₹/hr)"),
     _inp("st", "Standard Time (hrs)"), _inp("bt", "Budgeted Time (hrs)")],
    "₹",
    lambda i: i["sr"] * (i["st"] - i["bt"]),
)

_register(
    "foh_capacity", "Fixed OH Capacity Variance", "overhead_variance",
    "FOH Capacity Var. = SR × (AT − RBT)",
    "Variance due to actual hours worked differing from revised budgeted hours.",
    [_inp("sr", "Standard Rate (₹/hr)"),
     _inp("at", "Actual Time (hrs)"), _inp("rbt", "Revised Budgeted Time (hrs)")],
    "₹",
    lambda i: i["sr"] * (i["at"] - i["rbt"]),
)

_register(
    "foh_calendar", "Fixed OH Calendar Variance", "overhead_variance",
    "FOH Calendar Var. = SR × (RBT − BT)",
    "Variance due to the difference between revised and original budgeted hours (caused by different number of working days).",
    [_inp("sr", "Standard Rate (₹/hr)"),
     _inp("rbt", "Revised Budgeted Time (hrs)"), _inp("bt", "Budgeted Time (hrs)")],
    "₹",
    lambda i: i["sr"] * (i["rbt"] - i["bt"]),
)


# =====================================================================
# 8. STANDARD COSTING — SALES VARIANCES  (formulas 49–53)
# =====================================================================

_register(
    "sales_value_var", "Sales Value Variance", "sales_variance",
    "Sales Value Var. = (AP × AQ) − (BP × BQ)",
    "Total variance between actual and budgeted sales value.",
    [_inp("ap", "Actual Price (₹)"), _inp("aq", "Actual Quantity"),
     _inp("bp", "Budgeted Price (₹)"), _inp("bq", "Budgeted Quantity")],
    "₹",
    lambda i: (i["ap"] * i["aq"]) - (i["bp"] * i["bq"]),
)

_register(
    "sales_price_var", "Sales Price Variance", "sales_variance",
    "Sales Price Var. = (AP − BP) × AQ",
    "Variance due to the difference between actual and budgeted selling price.",
    [_inp("ap", "Actual Price (₹)"), _inp("bp", "Budgeted Price (₹)"),
     _inp("aq", "Actual Quantity")],
    "₹",
    lambda i: (i["ap"] - i["bp"]) * i["aq"],
)

_register(
    "sales_volume_var", "Sales Volume Variance", "sales_variance",
    "Sales Volume Var. = BP × (AQ − BQ)",
    "Variance due to the difference between actual and budgeted sales volume.",
    [_inp("bp", "Budgeted Price (₹)"),
     _inp("aq", "Actual Quantity"), _inp("bq", "Budgeted Quantity")],
    "₹",
    lambda i: i["bp"] * (i["aq"] - i["bq"]),
)

_register(
    "sales_mix_var", "Sales Mix Variance", "sales_variance",
    "Sales Mix Var. = BP × (Actual Mix − Budgeted Mix)",
    "Variance from changing the proportion of products sold.",
    [_inp("bp", "Budgeted Price (₹)"),
     _inp("actual_mix_qty", "Actual Mix Quantity"), _inp("budgeted_mix_qty", "Budgeted Mix Quantity")],
    "₹",
    lambda i: i["bp"] * (i["actual_mix_qty"] - i["budgeted_mix_qty"]),
)

_register(
    "sales_qty_var", "Sales Quantity Variance", "sales_variance",
    "Sales Qty Var. = BP × (Budgeted Mix − BQ)",
    "Variance due to total sales volume being different from budget.",
    [_inp("bp", "Budgeted Price (₹)"),
     _inp("budgeted_mix_qty", "Budgeted Mix Quantity"), _inp("bq", "Budgeted Quantity")],
    "₹",
    lambda i: i["bp"] * (i["budgeted_mix_qty"] - i["bq"]),
)


# =====================================================================
# 9. PROCESS & CONTRACT COSTING  (formulas 54–58)
# =====================================================================

_register(
    "learning_curve", "Learning Curve (cumulative average)", "process_contract",
    "Y = a × X^b, b = ln(learning rate) / ln(2)",
    "Average time per unit when production doubles. a = time for first unit, X = cumulative units.",
    [_inp("first_unit_time", "Time for first unit (hrs)"),
     _inp("cumulative_units", "Cumulative Units"),
     _inp("learning_rate", "Learning Rate (e.g. 0.80 for 80%)")],
    "hrs/unit",
    lambda i: i["first_unit_time"] * (i["cumulative_units"] ** (math.log(i["learning_rate"]) / math.log(2))) if i["cumulative_units"] > 0 and i["learning_rate"] > 0 else 0,
)

_register(
    "equivalent_units", "Equivalent Production (WIP)", "process_contract",
    "Equivalent Units = Units × % Completion",
    "Converts partially complete units into fully equivalent units for cost allocation.",
    [_inp("units", "Units"),
     _inp("completion_pct", "% Completion (e.g. 60 for 60%)")],
    "equivalent units",
    lambda i: i["units"] * (i["completion_pct"] / 100),
)

_register(
    "cost_per_eu", "Cost per Equivalent Unit", "process_contract",
    "Cost per EU = Total Cost / Total Equivalent Units",
    "Unit cost based on equivalent production.",
    [_inp("total_cost", "Total Cost (₹)"),
     _inp("total_eu", "Total Equivalent Units")],
    "₹/unit",
    lambda i: i["total_cost"] / i["total_eu"] if i["total_eu"] else 0,
)

_register(
    "abnormal_loss", "Abnormal Loss Units", "process_contract",
    "Abnormal Loss = Actual Loss − Normal Loss",
    "Loss exceeding the expected normal process loss.",
    [_inp("actual_loss", "Actual Loss (units)"),
     _inp("normal_loss", "Normal Loss (units)")],
    "units",
    lambda i: i["actual_loss"] - i["normal_loss"],
)

_register(
    "contract_profit", "Contract Profit (notional)", "process_contract",
    "Profit transferred = Notional Profit × (Cash Received / Work Certified) × completion fraction",
    "Estimated profit to be recognised on an incomplete contract.",
    [_inp("notional_profit", "Notional Profit (₹)"),
     _inp("cash_received", "Cash Received (₹)"),
     _inp("work_certified", "Work Certified (₹)"),
     _inp("completion_fraction", "Completion Fraction (e.g. 0.67 for 2/3)", 0.67)],
    "₹",
    lambda i: i["notional_profit"] * (i["cash_received"] / i["work_certified"]) * i["completion_fraction"] if i["work_certified"] else 0,
)


# =====================================================================
# 10. JOINT & SERVICE COSTING  (formulas 59–61)
# =====================================================================

_register(
    "joint_cost_physical", "Joint Cost Apportionment (physical)", "joint_service",
    "Share = Total Joint Cost × (Physical Output of Product / Total Physical Output)",
    "Allocates joint cost based on physical output proportion.",
    [_inp("total_joint_cost", "Total Joint Cost (₹)"),
     _inp("product_output", "Physical Output of Product"),
     _inp("total_output", "Total Physical Output")],
    "₹",
    lambda i: i["total_joint_cost"] * (i["product_output"] / i["total_output"]) if i["total_output"] else 0,
)

_register(
    "joint_cost_sales_value", "Joint Cost Apportionment (sales value)", "joint_service",
    "Share = Total Joint Cost × (Sales Value of Product / Total Sales Value)",
    "Allocates joint cost based on sales value proportion.",
    [_inp("total_joint_cost", "Total Joint Cost (₹)"),
     _inp("product_sales_value", "Sales Value of Product (₹)"),
     _inp("total_sales_value", "Total Sales Value (₹)")],
    "₹",
    lambda i: i["total_joint_cost"] * (i["product_sales_value"] / i["total_sales_value"]) if i["total_sales_value"] else 0,
)

_register(
    "operating_cost_per_unit", "Operating Cost per Composite Unit", "joint_service",
    "Cost per Unit = Total Operating Cost / Total Composite Units",
    "Cost per composite unit of service (e.g. passenger-km, tonne-km).",
    [_inp("total_operating_cost", "Total Operating Cost (₹)"),
     _inp("total_composite_units", "Total Composite Units")],
    "₹/unit",
    lambda i: i["total_operating_cost"] / i["total_composite_units"] if i["total_composite_units"] else 0,
)


# =====================================================================
# 11. ACTIVITY BASED COSTING  (formulas 62–63)
# =====================================================================

_register(
    "activity_rate", "Activity Cost Driver Rate (ABC)", "abc",
    "Activity Rate = Budgeted Cost of Activity / Total Quantity of Cost Driver",
    "Cost per unit of the cost driver for an activity.",
    [_inp("budgeted_activity_cost", "Budgeted Cost of Activity (₹)"),
     _inp("total_driver_qty", "Total Cost Driver Quantity")],
    "₹/driver unit",
    lambda i: i["budgeted_activity_cost"] / i["total_driver_qty"] if i["total_driver_qty"] else 0,
)

_register(
    "abc_overhead_applied", "Overhead Applied to Product (ABC)", "abc",
    "Overhead = Activity Rate × Product's Driver Usage",
    "Overhead assigned to a product based on its consumption of the activity.",
    [_inp("activity_rate", "Activity Rate (₹)"),
     _inp("driver_usage", "Product's Driver Usage")],
    "₹",
    lambda i: i["activity_rate"] * i["driver_usage"],
)


# =====================================================================
# 12. STRATEGIC / MODERN COSTING  (formulas 64–68 + extras)
# =====================================================================

_register(
    "target_cost", "Target Cost", "strategic",
    "Target Cost = Target Selling Price − Target Profit",
    "Maximum allowable cost to achieve the desired profit at a given selling price.",
    [_inp("target_selling_price", "Target Selling Price (₹)"),
     _inp("target_profit", "Target Profit (₹)")],
    "₹",
    lambda i: i["target_selling_price"] - i["target_profit"],
)

_register(
    "lifecycle_cost_per_unit", "Life-Cycle Cost per Unit", "strategic",
    "Life-Cycle Cost per Unit = Total Life-Cycle Cost / Total Units over Life",
    "Average cost per unit across the product's entire life.",
    [_inp("total_lifecycle_cost", "Total Life-Cycle Cost (₹)"),
     _inp("total_units", "Total Units over Life")],
    "₹/unit",
    lambda i: i["total_lifecycle_cost"] / i["total_units"] if i["total_units"] else 0,
)

_register(
    "throughput_contribution", "Throughput Contribution", "strategic",
    "Throughput Contribution = Sales − Direct Material Cost",
    "Revenue remaining after deducting only direct material cost (Theory of Constraints).",
    [_inp("sales", "Sales (₹)"),
     _inp("direct_material_cost", "Direct Material Cost (₹)")],
    "₹",
    lambda i: i["sales"] - i["direct_material_cost"],
)

_register(
    "bottleneck_ranking", "Bottleneck-Based Ranking", "strategic",
    "Throughput per Bottleneck Hour = Throughput Contribution / Bottleneck Hours per Unit",
    "Ranks products by throughput per unit of the bottleneck resource.",
    [_inp("throughput_contribution", "Throughput Contribution (₹)"),
     _inp("bottleneck_hours", "Bottleneck Hours per Unit")],
    "₹/hr",
    lambda i: i["throughput_contribution"] / i["bottleneck_hours"] if i["bottleneck_hours"] else 0,
)

_register(
    "ebq", "Economic Batch Quantity (EBQ)", "strategic",
    "EBQ = √(2AS / [C × (1 − A/P)])",
    "Optimal batch size when production and consumption happen simultaneously. A = demand, S = setup cost, C = carrying cost, P = production rate.",
    [_inp("demand", "Annual Demand (A)"),
     _inp("setup_cost", "Setup Cost per batch (S, ₹)"),
     _inp("carrying_cost", "Carrying Cost per unit p.a. (C, ₹)"),
     _inp("production_rate", "Production Rate (P, units p.a.)")],
    "units",
    lambda i: math.sqrt((2 * i["demand"] * i["setup_cost"]) / (i["carrying_cost"] * (1 - i["demand"] / i["production_rate"]))) if (i["carrying_cost"] and i["production_rate"] and i["demand"] < i["production_rate"]) else 0,
)

_register(
    "markup_pct", "Markup Percentage", "strategic",
    "Markup % = ((Selling Price − Cost) / Cost) × 100",
    "Percentage added on top of cost to arrive at selling price.",
    [_inp("selling_price", "Selling Price (₹)"),
     _inp("cost", "Cost (₹)")],
    "%",
    lambda i: ((i["selling_price"] - i["cost"]) / i["cost"]) * 100 if i["cost"] else 0,
)

_register(
    "target_selling_price", "Target Selling Price", "strategic",
    "Target Selling Price = Total Cost / (1 − Target Margin %/100)",
    "Selling price needed to achieve a target margin on cost.",
    [_inp("total_cost", "Total Cost (₹)"),
     _inp("target_margin_pct", "Target Margin (%)")],
    "₹",
    lambda i: i["total_cost"] / (1 - i["target_margin_pct"] / 100) if i["target_margin_pct"] < 100 else 0,
)

_register(
    "cost_per_batch", "Cost per Batch", "strategic",
    "Cost per Batch = Fixed Setup Cost + (Variable Cost × Batch Size)",
    "Total cost for producing one batch.",
    [_inp("fixed_setup_cost", "Fixed Setup Cost (₹)"),
     _inp("variable_cost_per_unit", "Variable Cost per unit (₹)"),
     _inp("batch_size", "Batch Size (units)")],
    "₹",
    lambda i: i["fixed_setup_cost"] + (i["variable_cost_per_unit"] * i["batch_size"]),
)


# =====================================================================
# 13. PERFORMANCE MEASUREMENT  (formulas 69–79)
# =====================================================================

_register(
    "oee", "Overall Equipment Effectiveness (OEE)", "performance",
    "OEE = Availability × Performance × Quality",
    "Comprehensive measure of manufacturing productivity.",
    [_inp("availability", "Availability (decimal, e.g. 0.90)"),
     _inp("performance", "Performance (decimal, e.g. 0.85)"),
     _inp("quality", "Quality (decimal, e.g. 0.98)")],
    "%",
    lambda i: i["availability"] * i["performance"] * i["quality"] * 100,
)

_register(
    "oee_availability", "Availability (OEE component)", "performance",
    "Availability = Operating Time / Planned Production Time",
    "Proportion of planned time that the equipment is actually running.",
    [_inp("operating_time", "Operating Time (hrs)"),
     _inp("planned_time", "Planned Production Time (hrs)")],
    "decimal",
    lambda i: i["operating_time"] / i["planned_time"] if i["planned_time"] else 0,
)

_register(
    "oee_performance", "Performance (OEE component)", "performance",
    "Performance = Actual Output / Theoretical Output at Ideal Speed",
    "Ratio of actual production speed to ideal speed.",
    [_inp("actual_output", "Actual Output (units)"),
     _inp("theoretical_output", "Theoretical Output at Ideal Speed (units)")],
    "decimal",
    lambda i: i["actual_output"] / i["theoretical_output"] if i["theoretical_output"] else 0,
)

_register(
    "oee_quality", "Quality (OEE component)", "performance",
    "Quality = Good Units / Total Units Produced",
    "Proportion of output that meets quality standards.",
    [_inp("good_units", "Good Units"),
     _inp("total_units", "Total Units Produced")],
    "decimal",
    lambda i: i["good_units"] / i["total_units"] if i["total_units"] else 0,
)

_register(
    "eva", "Economic Value Added (EVA)", "performance",
    "EVA = NOPAT − (Capital Employed × WACC)",
    "Measures value creation above the cost of capital. Positive EVA means value creation.",
    [_inp("nopat", "NOPAT (₹)"),
     _inp("capital_employed", "Capital Employed (₹)"),
     _inp("wacc", "WACC (decimal, e.g. 0.10 for 10%)")],
    "₹",
    lambda i: i["nopat"] - (i["capital_employed"] * i["wacc"]),
)

_register(
    "residual_income", "Residual Income", "performance",
    "Residual Income = Operating Profit − (Capital Employed × Imputed Cost of Capital)",
    "Profit remaining after charging costs of capital on investment.",
    [_inp("operating_profit", "Operating Profit (₹)"),
     _inp("capital_employed", "Capital Employed (₹)"),
     _inp("cost_of_capital", "Imputed Cost of Capital (decimal, e.g. 0.12)")],
    "₹",
    lambda i: i["operating_profit"] - (i["capital_employed"] * i["cost_of_capital"]),
)

_register(
    "roi", "Return on Investment (ROI)", "performance",
    "ROI = (Operating Profit / Capital Employed) × 100",
    "Percentage return on capital employed.",
    [_inp("operating_profit", "Operating Profit (₹)"),
     _inp("capital_employed", "Capital Employed (₹)")],
    "%",
    lambda i: (i["operating_profit"] / i["capital_employed"]) * 100 if i["capital_employed"] else 0,
)

_register(
    "dupont_roi", "DuPont ROI Decomposition", "performance",
    "ROI = Profit Margin × Asset Turnover = (Profit/Sales) × (Sales/Assets)",
    "Breaks ROI into profit margin and asset efficiency components.",
    [_inp("profit", "Profit (₹)"),
     _inp("sales", "Sales (₹)"),
     _inp("assets", "Total Assets (₹)")],
    "%",
    lambda i: ((i["profit"] / i["sales"]) * (i["sales"] / i["assets"])) * 100 if i["sales"] and i["assets"] else 0,
)

_register(
    "transfer_price", "Transfer Price (cost-based)", "performance",
    "Transfer Price = Variable Cost per unit + Mark-up",
    "Internal selling price between divisions.",
    [_inp("variable_cost_per_unit", "Variable Cost per unit (₹)"),
     _inp("markup", "Mark-up (₹ per unit)")],
    "₹",
    lambda i: i["variable_cost_per_unit"] + i["markup"],
)

_register(
    "sales_growth_pct", "Sales Growth %", "performance",
    "Sales Growth = ((Current Sales − Base Sales) / Base Sales) × 100",
    "Percentage growth in sales over a base period.",
    [_inp("current_sales", "Current Sales (₹)"),
     _inp("base_sales", "Base Sales (₹)")],
    "%",
    lambda i: ((i["current_sales"] - i["base_sales"]) / i["base_sales"]) * 100 if i["base_sales"] else 0,
)

_register(
    "altman_z_score", "Altman Z-Score", "performance",
    "Z = 1.2X₁ + 1.4X₂ + 3.3X₃ + 0.6X₄ + 1.0X₅",
    "Predicts probability of bankruptcy. Z > 2.99 = safe, 1.81–2.99 = grey zone, < 1.81 = distress. X₁=Working Capital/Total Assets, X₂=Retained Earnings/Total Assets, X₃=EBIT/Total Assets, X₄=Market Value of Equity/Total Liabilities, X₅=Sales/Total Assets.",
    [_inp("x1", "X₁ (Working Capital / Total Assets)"),
     _inp("x2", "X₂ (Retained Earnings / Total Assets)"),
     _inp("x3", "X₃ (EBIT / Total Assets)"),
     _inp("x4", "X₄ (Market Equity / Total Liabilities)"),
     _inp("x5", "X₅ (Sales / Total Assets)")],
    "score",
    lambda i: 1.2 * i["x1"] + 1.4 * i["x2"] + 3.3 * i["x3"] + 0.6 * i["x4"] + 1.0 * i["x5"],
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
        explanation += "\n→ Favourable / Positive"
    elif result < 0:
        explanation += "\n→ Adverse / Negative"
    else:
        explanation += "\n→ Zero / Break-even"

    return {
        "formula_id": formula_id,
        "formula_name": f["name"],
        "result": result,
        "unit": f["output_unit"],
        "explanation": explanation,
    }
