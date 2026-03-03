// frontend/src/app/financial-management/page.js
// Financial Management - Ratios and Analysis

"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import AppLayout from "../../components/layout/AppLayout";
import PageHeader from "../../components/layout/PageHeader";
import Card, { CardHeader, CardTitle, CardContent } from "../../components/ui/Card";
import Button from "../../components/ui/Button";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export default function FinancialManagementPage() {
  const [categories, setCategories] = useState([]);
  const [selectedCategory, setSelectedCategory] = useState(null);
  const [selectedFormula, setSelectedFormula] = useState(null);
  const [inputs, setInputs] = useState({});
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(true);
  const [calculating, setCalculating] = useState(false);

  useEffect(() => {
    fetchFormulas();
  }, []);

  const fetchFormulas = async () => {
    try {
      const token = localStorage.getItem("token");
      const response = await fetch(`${API_BASE_URL}/api/financials/formulas`, {
        headers: { Authorization: `Bearer ${token}` }
      });

      if (!response.ok) throw new Error("Failed to fetch formulas");
      const data = await response.json();
      setCategories(data);
      
      // Auto-select first category
      if (data.length > 0) {
        setSelectedCategory(data[0]);
      }
    } catch (error) {
      console.error("Error fetching formulas:", error);
    } finally {
      setLoading(false);
    }
  };

  const handleFormulaSelect = (formula) => {
    setSelectedFormula(formula);
    setResult(null);
    
    // Initialize inputs with defaults
    const initialInputs = {};
    formula.inputs.forEach(input => {
      initialInputs[input.id] = input.default || "";
    });
    setInputs(initialInputs);
  };

  const handleInputChange = (inputId, value) => {
    setInputs(prev => ({
      ...prev,
      [inputId]: value
    }));
  };

  const calculateFormula = async () => {
    if (!selectedFormula) return;

    setCalculating(true);
    try {
      const token = localStorage.getItem("token");
      const response = await fetch(
        `${API_BASE_URL}/api/financials/formulas/${selectedFormula.id}/calculate`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${token}`
          },
          body: JSON.stringify({ inputs })
        }
      );

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || "Calculation failed");
      }

      const data = await response.json();
      setResult(data);
    } catch (error) {
      alert("Calculation error: " + error.message);
    } finally {
      setCalculating(false);
    }
  };

  if (loading) {
    return (
      <AppLayout>
        <div className="flex items-center justify-center h-64">
          <div className="text-center">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto mb-4"></div>
            <div className="text-gray-600">Loading formulas...</div>
          </div>
        </div>
      </AppLayout>
    );
  }

  return (
    <AppLayout>
      <PageHeader
        title="Financial Management"
        description="Financial ratios and analysis"
        icon="💰"
        breadcrumbs={[
          { name: "Dashboard", href: "/dashboard" },
          { name: "Financial Management" }
        ]}
        actions={
          <Link href="/financial-data">
            <Button>Upload Data</Button>
          </Link>
        }
      />

      <div className="p-6">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          
          {/* Formula Library */}
          <div className="lg:col-span-1">
            <Card>
              <CardHeader>
                <CardTitle>Formula Library</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {/* Category Selector */}
                  <div>
                    <label className="block text-sm font-medium mb-2">Category</label>
                    <select
                      value={selectedCategory?.category_id || ""}
                      onChange={(e) => {
                        const category = categories.find(c => c.category_id === e.target.value);
                        setSelectedCategory(category);
                        setSelectedFormula(null);
                        setResult(null);
                      }}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                    >
                      {categories.map(category => (
                        <option key={category.category_id} value={category.category_id}>
                          {category.icon} {category.category_name}
                        </option>
                      ))}
                    </select>
                  </div>

                  {/* Formula List */}
                  {selectedCategory && (
                    <div>
                      <label className="block text-sm font-medium mb-2">
                        Formulas ({selectedCategory.formulas.length})
                      </label>
                      <div className="space-y-2 max-h-96 overflow-y-auto">
                        {selectedCategory.formulas.map(formula => (
                          <button
                            key={formula.id}
                            onClick={() => handleFormulaSelect(formula)}
                            className={`w-full text-left p-3 rounded-lg border transition-colors ${
                              selectedFormula?.id === formula.id
                                ? "border-blue-500 bg-blue-50"
                                : "border-gray-200 hover:bg-gray-50"
                            }`}
                          >
                            <div className="font-medium text-sm">{formula.name}</div>
                            <div className="text-xs text-gray-500 mt-1">{formula.formula}</div>
                          </button>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Calculator */}
          <div className="lg:col-span-2">
            {selectedFormula ? (
              <Card>
                <CardHeader>
                  <CardTitle>{selectedFormula.name}</CardTitle>
                  <div className="text-sm text-gray-600">
                    <div className="font-mono bg-gray-100 p-2 rounded mt-2">
                      {selectedFormula.formula}
                    </div>
                    <p className="mt-2">{selectedFormula.description}</p>
                  </div>
                </CardHeader>
                <CardContent>
                  <div className="space-y-6">
                    
                    {/* Input Parameters */}
                    <div>
                      <h3 className="text-lg font-medium mb-4">Input Parameters</h3>
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        {selectedFormula.inputs.map(input => (
                          <div key={input.id}>
                            <label className="block text-sm font-medium mb-2">
                              {input.label}
                            </label>
                            <input
                              type="number"
                              step="any"
                              value={inputs[input.id] || ""}
                              onChange={(e) => handleInputChange(input.id, e.target.value)}
                              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                              placeholder={input.default ? `Default: ${input.default}` : "Enter value"}
                            />
                          </div>
                        ))}
                      </div>
                    </div>

                    {/* Calculate Button */}
                    <div>
                      <Button
                        onClick={calculateFormula}
                        disabled={calculating}
                        className="w-full md:w-auto"
                      >
                        {calculating ? "Calculating..." : "Calculate Result"}
                      </Button>
                    </div>

                    {/* Result */}
                    {result && (
                      <div className="bg-green-50 border border-green-200 rounded-lg p-4">
                        <h3 className="text-lg font-medium text-green-800 mb-2">Result</h3>
                        <div className="text-2xl font-bold text-green-900 mb-2">
                          {result.result.toLocaleString()} {result.unit}
                        </div>
                        <div className="text-sm text-green-700 whitespace-pre-line">
                          {result.explanation}
                        </div>
                      </div>
                    )}
                  </div>
                </CardContent>
              </Card>
            ) : (
              <Card>
                <CardContent className="text-center py-12">
                  <div className="text-4xl mb-4">💰</div>
                  <h3 className="text-lg font-medium text-gray-900 mb-2">Select a Formula</h3>
                  <p className="text-gray-500">
                    Choose a category and formula from the library to start calculating financial ratios.
                  </p>
                  <div className="mt-4">
                    <Link href="/financial-data">
                      <Button>Upload Financial Data First</Button>
                    </Link>
                  </div>
                </CardContent>
              </Card>
            )}
          </div>
        </div>
      </div>
    </AppLayout>
  );
}