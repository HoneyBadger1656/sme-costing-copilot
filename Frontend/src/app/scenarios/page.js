// frontend/src/app/scenarios/page.js

"use client";

import { useState, useEffect } from "react";
import AppLayout from "../../components/layout/AppLayout";
import PageHeader from "../../components/layout/PageHeader";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export default function ScenarioManager() {
  const [scenarios, setScenarios] = useState([]);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [selectedScenarios, setSelectedScenarios] = useState([]);
  const [comparison, setComparison] = useState(null);
  const [baselineData, setBaselineData] = useState(null);
  const [quickScenarioText, setQuickScenarioText] = useState("");

  const [formData, setFormData] = useState({
    name: "",
    description: "",
    rawMaterialChange: "0",
    labourCostChange: "0",
    overheadPercentChange: "0",
    sellingPriceChange: "0",
    gstRateChange: "0",
    interestRateChange: "0",
    inventoryHoldingPeriodChange: "0",
    creditDaysChange: "0",
    volumeChangePercent: "0",
    marginChangePercent: "0",
  });

  useEffect(() => {
    fetchScenarios();
    fetchBaselineData();
  }, []);

  const fetchBaselineData = async () => {
    try {
      const token = typeof window !== "undefined"
        ? localStorage.getItem("token")
        : null;
      const clientId =
        typeof window !== "undefined"
          ? localStorage.getItem("selectedClientId") || 1
          : 1;

      // We'll create a dummy scenario to get baseline data
      const response = await fetch(
        `${API_BASE_URL}/api/scenarios?client_id=${clientId}`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${token}`,
          },
          body: JSON.stringify({
            name: "Baseline",
            description: "Current state",
            changes: {},
          }),
        }
      );

      if (response.ok) {
        const data = await response.json();
        setBaselineData(data.impact_summary);
        // Delete the dummy scenario
        await fetch(`${API_BASE_URL}/api/scenarios/${data.id}`, {
          method: "DELETE",
          headers: { Authorization: `Bearer ${token}` },
        });
      }
    } catch (error) {
      console.error("Error fetching baseline data:", error);
    }
  };
  const fetchScenarios = async () => {
    try {
      const token = typeof window !== "undefined"
        ? localStorage.getItem("token")
        : null;
      const clientId =
        typeof window !== "undefined"
          ? localStorage.getItem("selectedClientId") || 1
          : 1;

      const response = await fetch(
        `${API_BASE_URL}/api/scenarios?client_id=${clientId}`,
        {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        }
      );

      if (!response.ok) {
        throw new Error("Failed to fetch scenarios");
      }

      const data = await response.json();
      setScenarios(Array.isArray(data) ? data : []);
    } catch (error) {
      console.error("Error fetching scenarios:", error);
    }
  };

  const handleQuickScenario = async () => {
    if (!quickScenarioText.trim()) return;

    try {
      const token = typeof window !== "undefined"
        ? localStorage.getItem("token")
        : null;

      const response = await fetch(
        `${API_BASE_URL}/api/scenarios/parse-quick-scenario`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${token}`,
          },
          body: JSON.stringify({ text: quickScenarioText }),
        }
      );

      if (!response.ok) {
        throw new Error("Failed to parse scenario");
      }

      const parsed = await response.json();
      
      // Pre-fill the form with parsed data
      setFormData({
        name: parsed.name,
        description: parsed.description,
        rawMaterialChange: parsed.changes.raw_material_cost_change?.toString() || "0",
        labourCostChange: parsed.changes.labour_cost_change?.toString() || "0",
        overheadPercentChange: parsed.changes.overhead_percent_change?.toString() || "0",
        sellingPriceChange: parsed.changes.selling_price_change?.toString() || "0",
        gstRateChange: parsed.changes.gst_rate_change?.toString() || "0",
        interestRateChange: parsed.changes.interest_rate_change?.toString() || "0",
        inventoryHoldingPeriodChange: parsed.changes.inventory_holding_period_change?.toString() || "0",
        creditDaysChange: parsed.changes.credit_days_change?.toString() || "0",
        volumeChangePercent: parsed.changes.volume_change_percent?.toString() || "0",
        marginChangePercent: parsed.changes.margin_change_percent?.toString() || "0",
      });

      setShowCreateModal(true);
      setQuickScenarioText("");
    } catch (error) {
      alert("Error parsing scenario: " + error.message);
    }
  };
  const handleCreateScenario = async (e) => {
    e.preventDefault();

    try {
      const token = typeof window !== "undefined"
        ? localStorage.getItem("token")
        : null;
      const clientId =
        typeof window !== "undefined"
          ? localStorage.getItem("selectedClientId") || 1
          : 1;

      const changes = {};
      if (parseFloat(formData.rawMaterialChange || "0") !== 0) {
        changes.raw_material_cost_change = parseFloat(formData.rawMaterialChange);
      }
      if (parseFloat(formData.labourCostChange || "0") !== 0) {
        changes.labour_cost_change = parseFloat(formData.labourCostChange);
      }
      if (parseFloat(formData.overheadPercentChange || "0") !== 0) {
        changes.overhead_percent_change = parseFloat(formData.overheadPercentChange);
      }
      if (parseFloat(formData.sellingPriceChange || "0") !== 0) {
        changes.selling_price_change = parseFloat(formData.sellingPriceChange);
      }
      if (parseFloat(formData.gstRateChange || "0") !== 0) {
        changes.gst_rate_change = parseFloat(formData.gstRateChange);
      }
      if (parseFloat(formData.interestRateChange || "0") !== 0) {
        changes.interest_rate_change = parseFloat(formData.interestRateChange);
      }
      if (parseFloat(formData.inventoryHoldingPeriodChange || "0") !== 0) {
        changes.inventory_holding_period_change = parseFloat(formData.inventoryHoldingPeriodChange);
      }
      if (parseInt(formData.creditDaysChange || "0", 10) !== 0) {
        changes.credit_days_change = parseInt(formData.creditDaysChange, 10);
      }
      if (parseFloat(formData.volumeChangePercent || "0") !== 0) {
        changes.volume_change_percent = parseFloat(formData.volumeChangePercent);
      }
      if (parseFloat(formData.marginChangePercent || "0") !== 0) {
        changes.margin_change_percent = parseFloat(formData.marginChangePercent);
      }

      const response = await fetch(
        `${API_BASE_URL}/api/scenarios?client_id=${clientId}`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${token}`,
          },
          body: JSON.stringify({
            name: formData.name,
            description: formData.description,
            changes,
          }),
        }
      );

      if (!response.ok) {
        const errText = await response.text();
        throw new Error(errText || "Failed to create scenario");
      }

      setShowCreateModal(false);
      await fetchScenarios();
      setFormData({
        name: "",
        description: "",
        rawMaterialChange: "0",
        labourCostChange: "0",
        overheadPercentChange: "0",
        sellingPriceChange: "0",
        gstRateChange: "0",
        interestRateChange: "0",
        inventoryHoldingPeriodChange: "0",
        creditDaysChange: "0",
        volumeChangePercent: "0",
        marginChangePercent: "0",
      });
    } catch (error) {
      alert("Error creating scenario: " + error.message);
    }
  };
  const handleCompare = async () => {
    if (selectedScenarios.length < 2) {
      alert("Select at least 2 scenarios to compare");
      return;
    }

    try {
      const token = typeof window !== "undefined"
        ? localStorage.getItem("token")
        : null;

      const response = await fetch(
        `${API_BASE_URL}/api/scenarios/compare`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${token}`,
          },
          body: JSON.stringify(selectedScenarios),
        }
      );

      if (!response.ok) {
        const errText = await response.text();
        throw new Error(errText || "Failed to compare scenarios");
      }

      const data = await response.json();
      setComparison(data);
    } catch (error) {
      alert("Error comparing scenarios: " + error.message);
    }
  };

  const toggleScenarioSelection = (id) => {
    setSelectedScenarios((prev) =>
      prev.includes(id) ? prev.filter((sid) => sid !== id) : [...prev, id]
    );
  };

  return (
    <AppLayout>
      <PageHeader
        title="Scenario Manager"
        description="Run what-if analysis to see impact of business decisions"
        icon="🔄"
        breadcrumbs={[
          { name: "Dashboard", href: "/dashboard" },
          { name: "Scenario Manager" }
        ]}
        actions={
          <button
            onClick={() => setShowCreateModal(true)}
            className="bg-blue-600 text-white px-6 py-3 rounded-lg hover:bg-blue-700"
          >
            + Create Scenario
          </button>
        }
      />

      <div className="p-6">
        <div className="max-w-7xl mx-auto">

        {/* Quick Scenario Input */}
        <div className="bg-white rounded-lg shadow mb-8 p-6">
          <h2 className="text-xl font-semibold mb-4">Quick Scenario</h2>
          <p className="text-gray-600 mb-4">
            Describe your scenario in plain language, and we'll set up the parameters for you.
          </p>
          <div className="flex gap-4">
            <input
              type="text"
              value={quickScenarioText}
              onChange={(e) => setQuickScenarioText(e.target.value)}
              placeholder="e.g., What if raw material costs go up by 15%?"
              className="flex-1 px-4 py-2 border rounded-lg"
              onKeyPress={(e) => e.key === 'Enter' && handleQuickScenario()}
            />
            <button
              onClick={handleQuickScenario}
              className="bg-green-600 text-white px-6 py-2 rounded-lg hover:bg-green-700"
            >
              Parse & Create
            </button>
          </div>
          <div className="mt-2 text-sm text-gray-500">
            Try: "raw material up 10%", "labour cost down ₹5", "credit days increase 15 days", "volume up 20%"
          </div>
        </div>
        {/* Scenario list */}
        <div className="bg-white rounded-lg shadow mb-8">
          <div className="p-6 border-b">
            <div className="flex justify-between items-center">
              <h2 className="text-xl font-semibold">Your Scenarios</h2>
              {selectedScenarios.length >= 2 && (
                <button
                  onClick={handleCompare}
                  className="bg-green-600 text-white px-4 py-2 rounded-lg hover:bg-green-700"
                >
                  Compare Selected ({selectedScenarios.length})
                </button>
              )}
            </div>
          </div>

          <div className="divide-y">
            {scenarios.map((scenario) => (
              <div key={scenario.id} className="p-6 hover:bg-gray-50">
                <div className="flex items-start gap-4">
                  <input
                    type="checkbox"
                    checked={selectedScenarios.includes(scenario.id)}
                    onChange={() => toggleScenarioSelection(scenario.id)}
                    className="mt-1"
                  />

                  <div className="flex-1">
                    <div className="flex justify-between items-start mb-3">
                      <div>
                        <h3 className="text-lg font-semibold">
                          {scenario.name}
                        </h3>
                        {scenario.description && (
                          <p className="text-sm text-gray-600 mt-1">
                            {scenario.description}
                          </p>
                        )}
                      </div>
                      <div className="text-sm text-gray-500">
                        {scenario.created_at
                          ? new Date(
                            scenario.created_at
                          ).toLocaleDateString()
                          : ""}
                      </div>
                    </div>

                    {/* Changes Grid - More Parameters */}
                    <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-3 mb-4">
                      {scenario.changes &&
                        scenario.changes.raw_material_cost_change != null && (
                          <div className="bg-blue-50 p-3 rounded">
                            <div className="text-xs text-gray-600">
                              RM Cost
                            </div>
                            <div className="font-semibold">
                              ₹{scenario.changes.raw_material_cost_change > 0 ? "+" : ""}
                              {scenario.changes.raw_material_cost_change}
                            </div>
                          </div>
                        )}

                      {scenario.changes &&
                        scenario.changes.labour_cost_change != null && (
                          <div className="bg-purple-50 p-3 rounded">
                            <div className="text-xs text-gray-600">
                              Labour Cost
                            </div>
                            <div className="font-semibold">
                              ₹{scenario.changes.labour_cost_change > 0 ? "+" : ""}
                              {scenario.changes.labour_cost_change}
                            </div>
                          </div>
                        )}

                      {scenario.changes &&
                        scenario.changes.overhead_percent_change != null && (
                          <div className="bg-orange-50 p-3 rounded">
                            <div className="text-xs text-gray-600">
                              Overhead %
                            </div>
                            <div className="font-semibold">
                              {scenario.changes.overhead_percent_change > 0 ? "+" : ""}
                              {scenario.changes.overhead_percent_change}%
                            </div>
                          </div>
                        )}

                      {scenario.changes &&
                        scenario.changes.selling_price_change != null && (
                          <div className="bg-green-50 p-3 rounded">
                            <div className="text-xs text-gray-600">
                              Selling Price
                            </div>
                            <div className="font-semibold">
                              ₹{scenario.changes.selling_price_change > 0 ? "+" : ""}
                              {scenario.changes.selling_price_change}
                            </div>
                          </div>
                        )}

                      {scenario.changes &&
                        scenario.changes.credit_days_change != null && (
                          <div className="bg-indigo-50 p-3 rounded">
                            <div className="text-xs text-gray-600">
                              Credit Days
                            </div>
                            <div className="font-semibold">
                              {scenario.changes.credit_days_change > 0 ? "+" : ""}
                              {scenario.changes.credit_days_change} days
                            </div>
                          </div>
                        )}

                      {scenario.changes &&
                        scenario.changes.volume_change_percent != null && (
                          <div className="bg-teal-50 p-3 rounded">
                            <div className="text-xs text-gray-600">
                              Volume
                            </div>
                            <div className="font-semibold">
                              {scenario.changes.volume_change_percent > 0 ? "+" : ""}
                              {scenario.changes.volume_change_percent}%
                            </div>
                          </div>
                        )}
                    </div>
                    {/* Impact summary */}
                    {scenario.impact_summary && (
                      <div className="bg-gray-50 p-4 rounded-lg">
                        <div className="grid grid-cols-3 gap-4 mb-3">
                          <div>
                            <div className="text-xs text-gray-600">
                              Revenue Impact
                            </div>
                            <div
                              className={`font-semibold ${scenario.impact_summary.revenue_change >= 0
                                  ? "text-green-600"
                                  : "text-red-600"
                                }`}
                            >
                              ₹{scenario.impact_summary.revenue_change.toLocaleString()}
                              <span className="text-xs ml-1">
                                ({scenario.impact_summary.revenue_change_percent > 0 ? "+" : ""}
                                {scenario.impact_summary.revenue_change_percent}%)
                              </span>
                            </div>
                          </div>

                          <div>
                            <div className="text-xs text-gray-600">
                              Margin Impact
                            </div>
                            <div
                              className={`font-semibold ${scenario.impact_summary.margin_change >= 0
                                  ? "text-green-600"
                                  : "text-red-600"
                                }`}
                            >
                              ₹{scenario.impact_summary.margin_change.toLocaleString()}
                              <span className="text-xs ml-1">
                                ({scenario.impact_summary.margin_change_percent > 0 ? "+" : ""}
                                {scenario.impact_summary.margin_change_percent}%)
                              </span>
                            </div>
                          </div>

                          <div>
                            <div className="text-xs text-gray-600">
                              WC Impact
                            </div>
                            <div
                              className={`font-semibold ${scenario.impact_summary.wc_change <= 0
                                  ? "text-green-600"
                                  : "text-orange-600"
                                }`}
                            >
                              ₹{Math.abs(scenario.impact_summary.wc_change).toLocaleString()}
                              <span className="text-xs ml-1">
                                {scenario.impact_summary.wc_change > 0 ? "more blocked" : "freed"}
                              </span>
                            </div>
                          </div>
                        </div>

                        <div className="border-t pt-3 mt-3">
                          <div className="text-xs text-gray-600 mb-1">
                            Cash Flow Impact
                          </div>
                          <div className="text-sm mb-2">
                            {scenario.impact_summary.cash_flow_impact}
                          </div>

                          <div className="text-xs text-gray-600 mb-1">
                            Profitability Impact
                          </div>
                          <div className="text-sm mb-2">
                            {scenario.impact_summary.profitability_impact}
                          </div>

                          <div className="bg-blue-100 border-l-4 border-blue-600 p-3 mt-3">
                            <div className="text-sm font-medium">
                              {scenario.impact_summary.recommendation}
                            </div>
                          </div>
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            ))}

            {scenarios.length === 0 && (
              <div className="p-12 text-center text-gray-500">
                <p>No scenarios yet. Create your first what-if analysis.</p>
              </div>
            )}
          </div>
        </div>
        {/* Comparison results */}
        {comparison && (
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-xl font-semibold mb-6">Scenario Comparison</h2>

            <div className="grid grid-cols-3 gap-6 mb-6">
              <div className="bg-green-50 p-4 rounded-lg border-2 border-green-500">
                <div className="text-sm text-gray-600 mb-1">
                  Best for Profit
                </div>
                <div className="text-lg font-bold text-green-700">
                  {comparison.best_for_profit}
                </div>
              </div>

              <div className="bg-blue-50 p-4 rounded-lg border-2 border-blue-500">
                <div className="text-sm text-gray-600 mb-1">
                  Best for Cash Flow
                </div>
                <div className="text-lg font-bold text-blue-700">
                  {comparison.best_for_cash}
                </div>
              </div>

              <div className="bg-purple-50 p-4 rounded-lg border-2 border-purple-500">
                <div className="text-sm text-gray-600 mb-1">
                  Balanced Choice
                </div>
                <div className="text-lg font-bold text-purple-700">
                  {comparison.balanced_choice || "No balanced option"}
                </div>
              </div>
            </div>

            <table className="w-full">
              <thead className="bg-gray-50 border-b-2">
                <tr>
                  <th className="px-4 py-3 text-left text-sm font-semibold">
                    Scenario
                  </th>
                  <th className="px-4 py-3 text-right text-sm font-semibold">
                    Revenue Change
                  </th>
                  <th className="px-4 py-3 text-right text-sm font-semibold">
                    Margin Change
                  </th>
                  <th className="px-4 py-3 text-right text-sm font-semibold">
                    WC Change
                  </th>
                </tr>
              </thead>
              <tbody>
                {comparison.scenarios.map((s) => (
                  <tr key={s.id} className="border-b">
                    <td className="px-4 py-3 font-medium">{s.name}</td>
                    <td
                      className={`px-4 py-3 text-right ${s.revenue_change >= 0
                          ? "text-green-600"
                          : "text-red-600"
                        }`}
                    >
                      ₹{s.revenue_change.toLocaleString()}
                    </td>
                    <td
                      className={`px-4 py-3 text-right ${s.margin_change >= 0
                          ? "text-green-600"
                          : "text-red-600"
                        }`}
                    >
                      ₹{s.margin_change.toLocaleString()}
                    </td>
                    <td
                      className={`px-4 py-3 text-right ${s.wc_change <= 0
                          ? "text-green-600"
                          : "text-orange-600"
                        }`}
                    >
                      ₹{Math.abs(s.wc_change).toLocaleString()}
                      <span className="text-xs ml-1">
                        {s.wc_change > 0 ? "↑" : "↓"}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
        {/* Create Scenario Modal - Side by Side View */}
        {showCreateModal && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
            <div className="bg-white rounded-lg p-8 max-w-6xl w-full max-h-[90vh] overflow-y-auto">
              <h2 className="text-2xl font-bold mb-6">
                Create What-If Scenario
              </h2>

              <form onSubmit={handleCreateScenario}>
                <div className="space-y-6">
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm font-medium mb-2">
                        Scenario Name *
                      </label>
                      <input
                        type="text"
                        value={formData.name}
                        onChange={(e) =>
                          setFormData({ ...formData, name: e.target.value })
                        }
                        required
                        placeholder="e.g., Lower RM cost by ₹10"
                        className="w-full px-4 py-2 border rounded-lg"
                      />
                    </div>

                    <div>
                      <label className="block text-sm font-medium mb-2">
                        Description
                      </label>
                      <input
                        type="text"
                        value={formData.description}
                        onChange={(e) =>
                          setFormData({
                            ...formData,
                            description: e.target.value,
                          })
                        }
                        placeholder="Optional: Explain what you're testing"
                        className="w-full px-4 py-2 border rounded-lg"
                      />
                    </div>
                  </div>

                  {/* Side-by-Side Parameter View */}
                  <div className="border-t pt-6">
                    <h3 className="font-semibold mb-4 text-center">
                      Actual Data vs Hypothetical Changes
                    </h3>

                    <div className="grid grid-cols-2 gap-8">
                      {/* Left Column - Actual Data */}
                      <div>
                        <h4 className="font-medium text-gray-700 mb-4 text-center bg-gray-100 py-2 rounded">
                          📊 Current Actual Data
                        </h4>
                        <div className="space-y-3">
                          <div className="bg-blue-50 p-3 rounded">
                            <div className="text-sm text-gray-600">Raw Material Cost</div>
                            <div className="font-semibold">₹{baselineData?.average_rm_cost || "Loading..."}</div>
                          </div>
                          <div className="bg-purple-50 p-3 rounded">
                            <div className="text-sm text-gray-600">Labour Cost</div>
                            <div className="font-semibold">₹{baselineData?.average_labour_cost || "Loading..."}</div>
                          </div>
                          <div className="bg-orange-50 p-3 rounded">
                            <div className="text-sm text-gray-600">Credit Days</div>
                            <div className="font-semibold">{baselineData?.average_credit_days || "Loading..."} days</div>
                          </div>
                          <div className="bg-green-50 p-3 rounded">
                            <div className="text-sm text-gray-600">Total Revenue</div>
                            <div className="font-semibold">₹{baselineData?.total_revenue?.toLocaleString() || "Loading..."}</div>
                          </div>
                          <div className="bg-indigo-50 p-3 rounded">
                            <div className="text-sm text-gray-600">Total Margin</div>
                            <div className="font-semibold">₹{baselineData?.total_margin?.toLocaleString() || "Loading..."}</div>
                          </div>
                          <div className="bg-teal-50 p-3 rounded">
                            <div className="text-sm text-gray-600">Working Capital Blocked</div>
                            <div className="font-semibold">₹{baselineData?.working_capital_blocked?.toLocaleString() || "Loading..."}</div>
                          </div>
                        </div>
                      </div>
                      {/* Right Column - Hypothetical Changes */}
                      <div>
                        <h4 className="font-medium text-gray-700 mb-4 text-center bg-yellow-100 py-2 rounded">
                          🔄 What-If Changes
                        </h4>
                        <div className="space-y-3">
                          <div>
                            <label className="block text-sm font-medium mb-1">
                              Raw Material Cost Change (₹)
                            </label>
                            <input
                              type="number"
                              step="0.01"
                              value={formData.rawMaterialChange}
                              onChange={(e) =>
                                setFormData({
                                  ...formData,
                                  rawMaterialChange: e.target.value,
                                })
                              }
                              placeholder="e.g., -10 for ₹10 reduction"
                              className="w-full px-3 py-2 border rounded"
                            />
                          </div>

                          <div>
                            <label className="block text-sm font-medium mb-1">
                              Labour Cost Change (₹)
                            </label>
                            <input
                              type="number"
                              step="0.01"
                              value={formData.labourCostChange}
                              onChange={(e) =>
                                setFormData({
                                  ...formData,
                                  labourCostChange: e.target.value,
                                })
                              }
                              placeholder="e.g., +5 for ₹5 increase"
                              className="w-full px-3 py-2 border rounded"
                            />
                          </div>

                          <div>
                            <label className="block text-sm font-medium mb-1">
                              Overhead Percentage Change (%)
                            </label>
                            <input
                              type="number"
                              step="0.1"
                              value={formData.overheadPercentChange}
                              onChange={(e) =>
                                setFormData({
                                  ...formData,
                                  overheadPercentChange: e.target.value,
                                })
                              }
                              placeholder="e.g., +2 for 2% increase"
                              className="w-full px-3 py-2 border rounded"
                            />
                          </div>

                          <div>
                            <label className="block text-sm font-medium mb-1">
                              Selling Price Change (₹)
                            </label>
                            <input
                              type="number"
                              step="0.01"
                              value={formData.sellingPriceChange}
                              onChange={(e) =>
                                setFormData({
                                  ...formData,
                                  sellingPriceChange: e.target.value,
                                })
                              }
                              placeholder="e.g., +20 for ₹20 increase"
                              className="w-full px-3 py-2 border rounded"
                            />
                          </div>

                          <div>
                            <label className="block text-sm font-medium mb-1">
                              GST Rate Change (%)
                            </label>
                            <input
                              type="number"
                              step="0.1"
                              value={formData.gstRateChange}
                              onChange={(e) =>
                                setFormData({
                                  ...formData,
                                  gstRateChange: e.target.value,
                                })
                              }
                              placeholder="e.g., +1 for 1% GST increase"
                              className="w-full px-3 py-2 border rounded"
                            />
                          </div>

                          <div>
                            <label className="block text-sm font-medium mb-1">
                              Interest Rate Change (%)
                            </label>
                            <input
                              type="number"
                              step="0.1"
                              value={formData.interestRateChange}
                              onChange={(e) =>
                                setFormData({
                                  ...formData,
                                  interestRateChange: e.target.value,
                                })
                              }
                              placeholder="e.g., +0.5 for 0.5% increase"
                              className="w-full px-3 py-2 border rounded"
                            />
                          </div>
                        </div>
                      </div>
                    </div>
                    {/* Additional Parameters Row */}
                    <div className="mt-6 pt-4 border-t">
                      <h4 className="font-medium text-gray-700 mb-4">Additional Parameters</h4>
                      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                        <div>
                          <label className="block text-sm font-medium mb-1">
                            Inventory Holding Period Change (days)
                          </label>
                          <input
                            type="number"
                            value={formData.inventoryHoldingPeriodChange}
                            onChange={(e) =>
                              setFormData({
                                ...formData,
                                inventoryHoldingPeriodChange: e.target.value,
                              })
                            }
                            placeholder="e.g., +10 for 10 more days"
                            className="w-full px-3 py-2 border rounded"
                          />
                        </div>

                        <div>
                          <label className="block text-sm font-medium mb-1">
                            Credit Days Change
                          </label>
                          <input
                            type="number"
                            value={formData.creditDaysChange}
                            onChange={(e) =>
                              setFormData({
                                ...formData,
                                creditDaysChange: e.target.value,
                              })
                            }
                            placeholder="e.g., +15 for 15 more days"
                            className="w-full px-3 py-2 border rounded"
                          />
                        </div>

                        <div>
                          <label className="block text-sm font-medium mb-1">
                            Volume Change (%)
                          </label>
                          <input
                            type="number"
                            step="0.1"
                            value={formData.volumeChangePercent}
                            onChange={(e) =>
                              setFormData({
                                ...formData,
                                volumeChangePercent: e.target.value,
                              })
                            }
                            placeholder="e.g., +20 for 20% growth"
                            className="w-full px-3 py-2 border rounded"
                          />
                        </div>

                        <div>
                          <label className="block text-sm font-medium mb-1">
                            Margin Change (%)
                          </label>
                          <input
                            type="number"
                            step="0.1"
                            value={formData.marginChangePercent}
                            onChange={(e) =>
                              setFormData({
                                ...formData,
                                marginChangePercent: e.target.value,
                              })
                            }
                            placeholder="e.g., -2 for 2% margin drop"
                            className="w-full px-3 py-2 border rounded"
                          />
                        </div>
                      </div>
                    </div>
                  </div>
                </div>

                <div className="flex gap-4 mt-8">
                  <button
                    type="submit"
                    className="flex-1 bg-blue-600 text-white py-3 rounded-lg hover:bg-blue-700"
                  >
                    Run Scenario Analysis
                  </button>
                  <button
                    type="button"
                    onClick={() => setShowCreateModal(false)}
                    className="flex-1 bg-gray-200 text-gray-700 py-3 rounded-lg hover:bg-gray-300"
                  >
                    Cancel
                  </button>
                </div>
              </form>
            </div>
          </div>
        )}
        </div>
      </div>
    </AppLayout>
  );
}