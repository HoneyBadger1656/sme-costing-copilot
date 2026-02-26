// frontend/src/app/scenarios/page.js

"use client";

import { useState, useEffect } from "react";

export default function ScenarioManager() {
  const [scenarios, setScenarios] = useState([]);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [selectedScenarios, setSelectedScenarios] = useState([]);
  const [comparison, setComparison] = useState(null);

  const [formData, setFormData] = useState({
    name: "",
    description: "",
    rawMaterialChange: "0",
    creditDaysChange: "0",
    volumeChangePercent: "0",
    marginChangePercent: "0",
  });

  useEffect(() => {
    fetchScenarios();
  }, []);

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
        `http://localhost:8000/api/scenarios?client_id=${clientId}`,
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
        changes.raw_material_cost_change = parseFloat(
          formData.rawMaterialChange
        );
      }
      if (parseInt(formData.creditDaysChange || "0", 10) !== 0) {
        changes.credit_days_change = parseInt(
          formData.creditDaysChange,
          10
        );
      }
      if (parseFloat(formData.volumeChangePercent || "0") !== 0) {
        changes.volume_change_percent = parseFloat(
          formData.volumeChangePercent
        );
      }
      if (parseFloat(formData.marginChangePercent || "0") !== 0) {
        changes.margin_change_percent = parseFloat(
          formData.marginChangePercent
        );
      }

      const response = await fetch(
        `http://localhost:8000/api/scenarios?client_id=${clientId}`,
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
        "http://localhost:8000/api/scenarios/compare",
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
    <div className="min-h-screen bg-gray-50 p-8">
      <div className="max-w-7xl mx-auto">
        <div className="flex justify-between items-center mb-8">
          <div>
            <h1 className="text-3xl font-bold">Scenario Manager</h1>
            <p className="text-gray-600 mt-2">
              Run what-if analysis to see impact of business decisions
            </p>
          </div>
          <button
            onClick={() => setShowCreateModal(true)}
            className="bg-blue-600 text-white px-6 py-3 rounded-lg hover:bg-blue-700"
          >
            + Create Scenario
          </button>
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

                    {/* Changes */}
                    <div className="grid grid-cols-4 gap-4 mb-4">
                      {scenario.changes &&
                        scenario.changes.raw_material_cost_change != null && (
                          <div className="bg-blue-50 p-3 rounded">
                            <div className="text-xs text-gray-600">
                              RM Cost Change
                            </div>
                            <div className="font-semibold">
                              ₹
                              {scenario.changes.raw_material_cost_change > 0
                                ? "+"
                                : ""}
                              {scenario.changes.raw_material_cost_change}
                            </div>
                          </div>
                        )}

                      {scenario.changes &&
                        scenario.changes.credit_days_change != null && (
                          <div className="bg-purple-50 p-3 rounded">
                            <div className="text-xs text-gray-600">
                              Credit Days
                            </div>
                            <div className="font-semibold">
                              {scenario.changes.credit_days_change > 0
                                ? "+"
                                : ""}
                              {scenario.changes.credit_days_change} days
                            </div>
                          </div>
                        )}

                      {scenario.changes &&
                        scenario.changes.volume_change_percent != null && (
                          <div className="bg-green-50 p-3 rounded">
                            <div className="text-xs text-gray-600">
                              Volume
                            </div>
                            <div className="font-semibold">
                              {scenario.changes.volume_change_percent > 0
                                ? "+"
                                : ""}
                              {scenario.changes.volume_change_percent}%
                            </div>
                          </div>
                        )}

                      {scenario.changes &&
                        scenario.changes.margin_change_percent != null && (
                          <div className="bg-yellow-50 p-3 rounded">
                            <div className="text-xs text-gray-600">
                              Margin
                            </div>
                            <div className="font-semibold">
                              {scenario.changes.margin_change_percent > 0
                                ? "+"
                                : ""}
                              {scenario.changes.margin_change_percent}%
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
                              className={`font-semibold ${
                                scenario.impact_summary.revenue_change >= 0
                                  ? "text-green-600"
                                  : "text-red-600"
                              }`}
                            >
                              ₹
                              {scenario.impact_summary.revenue_change.toLocaleString()}
                              <span className="text-xs ml-1">
                                (
                                {scenario.impact_summary
                                  .revenue_change_percent > 0
                                  ? "+"
                                  : ""}
                                {
                                  scenario.impact_summary
                                    .revenue_change_percent
                                }
                                %)
                              </span>
                            </div>
                          </div>

                          <div>
                            <div className="text-xs text-gray-600">
                              Margin Impact
                            </div>
                            <div
                              className={`font-semibold ${
                                scenario.impact_summary.margin_change >= 0
                                  ? "text-green-600"
                                  : "text-red-600"
                              }`}
                            >
                              ₹
                              {scenario.impact_summary.margin_change.toLocaleString()}
                              <span className="text-xs ml-1">
                                (
                                {scenario.impact_summary
                                  .margin_change_percent > 0
                                  ? "+"
                                  : ""}
                                {scenario.impact_summary.margin_change_percent}
                                %)
                              </span>
                            </div>
                          </div>

                          <div>
                            <div className="text-xs text-gray-600">
                              WC Impact
                            </div>
                            <div
                              className={`font-semibold ${
                                scenario.impact_summary.wc_change <= 0
                                  ? "text-green-600"
                                  : "text-orange-600"
                              }`}
                            >
                              ₹
                              {Math.abs(
                                scenario.impact_summary.wc_change
                              ).toLocaleString()}
                              <span className="text-xs ml-1">
                                {scenario.impact_summary.wc_change > 0
                                  ? "more blocked"
                                  : "freed"}
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
                      className={`px-4 py-3 text-right ${
                        s.revenue_change >= 0
                          ? "text-green-600"
                          : "text-red-600"
                      }`}
                    >
                      ₹{s.revenue_change.toLocaleString()}
                    </td>
                    <td
                      className={`px-4 py-3 text-right ${
                        s.margin_change >= 0
                          ? "text-green-600"
                          : "text-red-600"
                      }`}
                    >
                      ₹{s.margin_change.toLocaleString()}
                    </td>
                    <td
                      className={`px-4 py-3 text-right ${
                        s.wc_change <= 0
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

        {/* Create Scenario Modal */}
        {showCreateModal && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
            <div className="bg-white rounded-lg p-8 max-w-2xl w-full">
              <h2 className="text-2xl font-bold mb-6">
                Create What-If Scenario
              </h2>

              <form onSubmit={handleCreateScenario}>
                <div className="space-y-4">
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
                    <textarea
                      value={formData.description}
                      onChange={(e) =>
                        setFormData({
                          ...formData,
                          description: e.target.value,
                        })
                      }
                      placeholder="Optional: Explain what you're testing"
                      rows={2}
                      className="w-full px-4 py-2 border rounded-lg"
                    />
                  </div>

                  <div className="border-t pt-4">
                    <h3 className="font-semibold mb-4">
                      What changes do you want to test?
                    </h3>

                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <label className="block text-sm font-medium mb-2">
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
                          className="w-full px-4 py-2 border rounded-lg"
                        />
                        <p className="text-xs text-gray-500 mt-1">
                          Use negative for reduction
                        </p>
                      </div>

                      <div>
                        <label className="block text-sm font-medium mb-2">
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
                          className="w-full px-4 py-2 border rounded-lg"
                        />
                        <p className="text-xs text-gray-500 mt-1">
                          Use + for increase, - for decrease
                        </p>
                      </div>

                      <div>
                        <label className="block text-sm font-medium mb-2">
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
                          className="w-full px-4 py-2 border rounded-lg"
                        />
                        <p className="text-xs text-gray-500 mt-1">
                          % increase/decrease in order volume
                        </p>
                      </div>

                      <div>
                        <label className="block text-sm font-medium mb-2">
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
                          className="w-full px-4 py-2 border rounded-lg"
                        />
                        <p className="text-xs text-gray-500 mt-1">
                          Change in profit margin %
                        </p>
                      </div>
                    </div>
                  </div>
                </div>

                <div className="flex gap-4 mt-6">
                  <button
                    type="submit"
                    className="flex-1 bg-blue-600 text-white py-3 rounded-lg hover:bg-blue-700"
                  >
                    Create Scenario
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
  );
}
