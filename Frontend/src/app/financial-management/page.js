// frontend/src/app/financial-management/page.js
// Financial Management — Formula Library & Analysis

"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export default function FinancialManagementPage() {
  const [categories, setCategories] = useState([]);
  const [selectedCategory, setSelectedCategory] = useState(null);
  const [selectedFormula, setSelectedFormula] = useState(null);
  const [inputs, setInputs] = useState({});
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(true);
  const [calculating, setCalculating] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");
  const [sidebarOpen, setSidebarOpen] = useState(true);

  // Fetch all formulas on mount
  useEffect(() => {
    fetchFormulas();
  }, []);

  const fetchFormulas = async () => {
    try {
      const token =
        typeof window !== "undefined" ? localStorage.getItem("token") : null;
      const response = await fetch(`${API_BASE_URL}/api/financials/formulas`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (!response.ok) throw new Error("Failed to fetch formulas");
      const data = await response.json();
      setCategories(data);
      if (data.length > 0) setSelectedCategory(data[0].category_id);
    } catch (error) {
      console.error("Error fetching formulas:", error);
    } finally {
      setLoading(false);
    }
  };

  const handleCalculate = async () => {
    if (!selectedFormula) return;

    setCalculating(true);
    try {
      const token =
        typeof window !== "undefined" ? localStorage.getItem("token") : null;
      const response = await fetch(
        `${API_BASE_URL}/api/financials/formulas/${selectedFormula.id}/calculate`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${token}`,
          },
          body: JSON.stringify({ inputs }),
        }
      );

      if (!response.ok) throw new Error("Calculation failed");
      const data = await response.json();
      setResult(data);
    } catch (error) {
      console.error("Error calculating formula:", error);
      alert("Error calculating formula: " + error.message);
    } finally {
      setCalculating(false);
    }
  };

  const handleInputChange = (inputId, value) => {
    setInputs((prev) => ({ ...prev, [inputId]: value }));
  };

  const resetForm = () => {
    setInputs({});
    setResult(null);
  };

  const filteredCategories = categories.map((category) => ({
    ...category,
    formulas: category.formulas.filter(
      (formula) =>
        formula.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
        formula.description.toLowerCase().includes(searchQuery.toLowerCase())
    ),
  }));

  const currentCategory = filteredCategories.find(
    (cat) => cat.category_id === selectedCategory
  );

  return (
    <div className="min-h-screen bg-gray-50 flex">
      {/* Sidebar */}
      <div
        className={`${sidebarOpen ? "w-80" : "w-20"} bg-white border-r border-gray-200 transition-all duration-300 flex flex-col`}
      >
        <div className="p-4 border-b border-gray-200">
          <div className="flex items-center justify-between">
            <h2
              className={`font-bold text-xl text-gray-800 ${
                !sidebarOpen && "hidden"
              }`}
            >
              Financial Formulas
            </h2>
            <button
              onClick={() => setSidebarOpen(!sidebarOpen)}
              className="p-2 hover:bg-gray-100 rounded-lg"
            >
              <svg
                className="w-5 h-5"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M4 6h16M4 12h16M4 18h16"
                />
              </svg>
            </button>
          </div>
          {sidebarOpen && (
            <div className="mt-4">
              <input
                type="text"
                placeholder="Search formulas..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
          )}
        </div>

        <div className="flex-1 overflow-y-auto">
          {sidebarOpen && (
            <div className="p-4 space-y-2">
              {filteredCategories.map((category) => (
                <div key={category.category_id}>
                  <button
                    onClick={() => setSelectedCategory(category.category_id)}
                    className={`w-full text-left px-3 py-2 rounded-lg transition-colors ${
                      selectedCategory === category.category_id
                        ? "bg-blue-50 text-blue-700 border border-blue-200"
                        : "hover:bg-gray-100"
                    }`}
                  >
                    <div className="flex items-center space-x-2">
                      <span className="text-xl">{category.icon}</span>
                      <div>
                        <div className="font-medium">{category.category_name}</div>
                        <div className="text-xs text-gray-500">
                          {category.formulas.length} formulas
                        </div>
                      </div>
                    </div>
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Main Content */}
      <div className="flex-1 flex flex-col">
        {/* Header */}
        <div className="bg-white border-b border-gray-200 px-8 py-4">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold text-gray-800">
                Financial Management
              </h1>
              <p className="text-gray-600">
                Professional financial formulas and analysis tools
              </p>
            </div>
            <Link
              href="/dashboard"
              className="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors"
            >
              Back to Dashboard
            </Link>
          </div>
        </div>

        <div className="flex-1 flex">
          {/* Formula List */}
          <div className="w-96 bg-white border-r border-gray-200 overflow-y-auto">
            {currentCategory && (
              <div className="p-4">
                <h3 className="font-semibold text-lg mb-4 flex items-center">
                  <span className="mr-2">{currentCategory.icon}</span>
                  {currentCategory.category_name}
                </h3>
                <div className="space-y-2">
                  {currentCategory.formulas.map((formula) => (
                    <button
                      key={formula.id}
                      onClick={() => {
                        setSelectedFormula(formula);
                        resetForm();
                      }}
                      className={`w-full text-left p-3 rounded-lg border transition-all ${
                        selectedFormula?.id === formula.id
                          ? "border-blue-500 bg-blue-50"
                          : "border-gray-200 hover:border-gray-300 hover:bg-gray-50"
                      }`}
                    >
                      <div className="font-medium text-sm">{formula.name}</div>
                      <div className="text-xs text-gray-600 mt-1">
                        {formula.formula}
                      </div>
                    </button>
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* Formula Calculator */}
          <div className="flex-1 overflow-y-auto">
            {selectedFormula ? (
              <div className="p-8">
                <div className="max-w-3xl mx-auto">
                  <div className="bg-white rounded-lg border border-gray-200 p-6">
                    <h2 className="text-xl font-bold mb-2">
                      {selectedFormula.name}
                    </h2>
                    <div className="bg-gray-50 p-4 rounded-lg mb-6">
                      <p className="text-sm text-gray-700 mb-2">
                        {selectedFormula.description}
                      </p>
                      <div className="font-mono text-sm bg-white p-2 rounded border">
                        {selectedFormula.formula}
                      </div>
                    </div>

                    {/* Input Fields */}
                    <div className="space-y-4 mb-6">
                      <h3 className="font-semibold text-lg">Input Values</h3>
                      {selectedFormula.inputs.map((input) => (
                        <div key={input.id}>
                          <label className="block text-sm font-medium text-gray-700 mb-1">
                            {input.label}
                            {input.default && (
                              <span className="text-gray-500 text-xs ml-1">
                                (default: {input.default})
                              </span>
                            )}
                          </label>
                          <input
                            type="number"
                            step="any"
                            placeholder={input.default?.toString() || ""}
                            value={inputs[input.id] || ""}
                            onChange={(e) =>
                              handleInputChange(input.id, e.target.value)
                            }
                            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                          />
                        </div>
                      ))}
                    </div>

                    {/* Calculate Button */}
                    <div className="flex space-x-4 mb-6">
                      <button
                        onClick={handleCalculate}
                        disabled={calculating}
                        className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-blue-400 transition-colors"
                      >
                        {calculating ? "Calculating..." : "Calculate"}
                      </button>
                      <button
                        onClick={resetForm}
                        className="px-6 py-3 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300 transition-colors"
                      >
                        Reset
                      </button>
                    </div>

                    {/* Result */}
                    {result && (
                      <div className="bg-green-50 border border-green-200 rounded-lg p-6">
                        <h3 className="font-semibold text-lg mb-3 text-green-800">
                          Calculation Result
                        </h3>
                        <div className="text-2xl font-bold text-green-700 mb-3">
                          {result.result.toFixed(4)} {result.unit}
                        </div>
                        <div className="text-sm text-gray-700 whitespace-pre-line">
                          {result.explanation}
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            ) : (
              <div className="flex items-center justify-center h-full">
                <div className="text-center">
                  <div className="text-6xl mb-4">📊</div>
                  <h3 className="text-xl font-semibold text-gray-700 mb-2">
                    Select a Formula
                  </h3>
                  <p className="text-gray-500">
                    Choose a formula from the list to start your financial analysis
                  </p>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
