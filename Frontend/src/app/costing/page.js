// frontend/src/app/costing/page.js
// Automated Costing page with formula library

"use client";

import React, { useState } from "react";
import AppLayout from "../../components/layout/AppLayout";
import PageHeader from "../../components/layout/PageHeader";
import Card, { CardHeader, CardTitle, CardContent } from "../../components/ui/Card";
import Button from "../../components/ui/Button";

const costingFormulas = [
  {
    id: "unit_cost",
    name: "Unit Cost",
    description: "Calculate total cost per unit including raw materials, labor, and overhead",
    category: "Basic Costing"
  },
  {
    id: "contribution_margin",
    name: "Contribution Margin",
    description: "Selling price minus variable cost per unit",
    category: "Basic Costing"
  },
  {
    id: "contribution_margin_ratio",
    name: "Contribution Margin Ratio",
    description: "Contribution margin as a percentage of selling price",
    category: "Basic Costing"
  },
  {
    id: "break_even_units",
    name: "Break-Even Point (Units)",
    description: "Number of units needed to cover all fixed costs",
    category: "Break-Even Analysis"
  },
  {
    id: "break_even_revenue",
    name: "Break-Even Point (Revenue)",
    description: "Revenue needed to cover all fixed costs",
    category: "Break-Even Analysis"
  },
  {
    id: "minimum_order_qty",
    name: "Minimum Order Quantity",
    description: "Minimum units needed to make an order profitable",
    category: "Order Analysis"
  },
  {
    id: "target_selling_price",
    name: "Target Selling Price",
    description: "Price needed to achieve target profit margin",
    category: "Pricing"
  },
  {
    id: "markup_percentage",
    name: "Markup Percentage",
    description: "Markup as a percentage of cost",
    category: "Pricing"
  }
];

const categories = [...new Set(costingFormulas.map(f => f.category))];

export default function CostingPage() {
  const [selectedFormula, setSelectedFormula] = useState(null);
  const [selectedCategory, setSelectedCategory] = useState("All");

  const filteredFormulas = selectedCategory === "All" 
    ? costingFormulas 
    : costingFormulas.filter(f => f.category === selectedCategory);

  return (
    <AppLayout>
      <PageHeader
        title="Automated Costing"
        description="Calculate costing metrics using our formula library"
        icon="📊"
        breadcrumbs={[
          { name: "Dashboard", href: "/dashboard" },
          { name: "Automated Costing" }
        ]}
      />

      <div className="p-6">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          
          {/* Formula Library */}
          <div className="lg:col-span-1">
            <Card>
              <CardHeader>
                <CardTitle>Formula Library</CardTitle>
                <div className="mt-4">
                  <select 
                    value={selectedCategory}
                    onChange={(e) => setSelectedCategory(e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  >
                    <option value="All">All Categories</option>
                    {categories.map(category => (
                      <option key={category} value={category}>{category}</option>
                    ))}
                  </select>
                </div>
              </CardHeader>
              
              <CardContent className="space-y-2">
                {filteredFormulas.map((formula) => (
                  <button
                    key={formula.id}
                    onClick={() => setSelectedFormula(formula)}
                    className={`w-full text-left p-3 rounded-lg border transition-colors ${
                      selectedFormula?.id === formula.id
                        ? "border-blue-500 bg-blue-50"
                        : "border-gray-200 hover:border-gray-300 hover:bg-gray-50"
                    }`}
                  >
                    <div className="font-medium text-sm">{formula.name}</div>
                    <div className="text-xs text-gray-500 mt-1">{formula.category}</div>
                  </button>
                ))}
              </CardContent>
            </Card>
          </div>

          {/* Formula Details & Calculator */}
          <div className="lg:col-span-2">
            {selectedFormula ? (
              <Card>
                <CardHeader>
                  <CardTitle>{selectedFormula.name}</CardTitle>
                  <p className="text-gray-600 mt-2">{selectedFormula.description}</p>
                </CardHeader>
                
                <CardContent>
                  <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4 mb-6">
                    <div className="flex items-center">
                      <svg className="w-5 h-5 text-yellow-600 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                      </svg>
                      <span className="text-yellow-800 font-medium">Coming Soon</span>
                    </div>
                    <p className="text-yellow-700 mt-2 text-sm">
                      Formula calculations will be available in the next update. The backend API endpoints are being developed.
                    </p>
                  </div>

                  <div className="space-y-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        Input Parameters
                      </label>
                      <div className="space-y-3">
                        <input
                          type="number"
                          placeholder="Raw Material Cost (₹)"
                          className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                          disabled
                        />
                        <input
                          type="number"
                          placeholder="Labor Cost (₹)"
                          className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                          disabled
                        />
                        <input
                          type="number"
                          placeholder="Overhead Cost (₹)"
                          className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                          disabled
                        />
                      </div>
                    </div>

                    <Button disabled className="w-full">
                      Calculate {selectedFormula.name}
                    </Button>

                    <div className="bg-gray-50 rounded-lg p-4">
                      <h4 className="font-medium text-gray-900 mb-2">Result</h4>
                      <div className="text-2xl font-bold text-gray-400">--</div>
                      <div className="text-sm text-gray-500 mt-1">Select inputs and calculate to see result</div>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ) : (
              <Card>
                <CardContent className="text-center py-12">
                  <div className="text-6xl mb-4">📊</div>
                  <h3 className="text-lg font-medium text-gray-900 mb-2">Select a Formula</h3>
                  <p className="text-gray-500">
                    Choose a costing formula from the library to get started with calculations.
                  </p>
                </CardContent>
              </Card>
            )}
          </div>
        </div>
      </div>
    </AppLayout>
  );
}