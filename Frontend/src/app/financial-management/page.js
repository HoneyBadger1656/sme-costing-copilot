// frontend/src/app/financial-management/page.js
// Financial Management page with formulas and analysis

"use client";

import React, { useState } from "react";
import Link from "next/link";
import AppLayout from "../../components/layout/AppLayout";
import PageHeader from "../../components/layout/PageHeader";
import Card, { CardHeader, CardTitle, CardContent } from "../../components/ui/Card";
import Button from "../../components/ui/Button";

const financialFormulas = [
  {
    id: "current_ratio",
    name: "Current Ratio",
    description: "Current assets divided by current liabilities",
    category: "Liquidity Ratios"
  },
  {
    id: "quick_ratio",
    name: "Quick Ratio",
    description: "Quick assets divided by current liabilities",
    category: "Liquidity Ratios"
  },
  {
    id: "debt_to_equity",
    name: "Debt-to-Equity Ratio",
    description: "Total debt divided by total equity",
    category: "Leverage Ratios"
  },
  {
    id: "working_capital",
    name: "Working Capital",
    description: "Current assets minus current liabilities",
    category: "Working Capital"
  },
  {
    id: "debtor_days",
    name: "Debtor Days",
    description: "Average collection period for receivables",
    category: "Working Capital"
  },
  {
    id: "creditor_days",
    name: "Creditor Days",
    description: "Average payment period for payables",
    category: "Working Capital"
  },
  {
    id: "cash_conversion_cycle",
    name: "Cash Conversion Cycle",
    description: "Time to convert investments into cash",
    category: "Working Capital"
  },
  {
    id: "roe",
    name: "Return on Equity (ROE)",
    description: "Net income as percentage of shareholders' equity",
    category: "Profitability Ratios"
  },
  {
    id: "roce",
    name: "Return on Capital Employed (ROCE)",
    description: "Operating profit as percentage of capital employed",
    category: "Profitability Ratios"
  },
  {
    id: "gross_profit_margin",
    name: "Gross Profit Margin",
    description: "Gross profit as percentage of revenue",
    category: "Profitability Ratios"
  }
];

const categories = [...new Set(financialFormulas.map(f => f.category))];

export default function FinancialManagementPage() {
  const [activeTab, setActiveTab] = useState("formulas");
  const [selectedFormula, setSelectedFormula] = useState(null);
  const [selectedCategory, setSelectedCategory] = useState("All");

  const filteredFormulas = selectedCategory === "All" 
    ? financialFormulas 
    : financialFormulas.filter(f => f.category === selectedCategory);

  const tabs = [
    { id: "formulas", name: "Financial Formulas", icon: "📊" },
    { id: "profitability", name: "Profitability", icon: "💹" },
    { id: "receivables", name: "Receivables", icon: "📥" },
    { id: "payables", name: "Payables", icon: "📤" },
    { id: "cashflow", name: "Cash Flow", icon: "💰" }
  ];

  return (
    <AppLayout>
      <PageHeader
        title="Financial Management"
        description="Comprehensive financial analysis and ratio calculations"
        icon="💰"
        breadcrumbs={[
          { name: "Dashboard", href: "/dashboard" },
          { name: "Financial Management" }
        ]}
        actions={
          <Link href="/financial-data">
            <Button variant="outline">
              📄 Upload Data
            </Button>
          </Link>
        }
      />

      <div className="p-6">
        {/* Tab Navigation */}
        <div className="mb-6">
          <div className="border-b border-gray-200">
            <nav className="-mb-px flex space-x-8">
              {tabs.map((tab) => (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`py-2 px-1 border-b-2 font-medium text-sm whitespace-nowrap ${
                    activeTab === tab.id
                      ? "border-blue-500 text-blue-600"
                      : "border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300"
                  }`}
                >
                  <span className="mr-2">{tab.icon}</span>
                  {tab.name}
                </button>
              ))}
            </nav>
          </div>
        </div>

        {/* Tab Content */}
        {activeTab === "formulas" && (
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

            {/* Formula Calculator */}
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
                        Financial formula calculations will be available in the next update. Please upload your financial data first.
                      </p>
                    </div>

                    <Button disabled className="w-full mb-4">
                      Calculate {selectedFormula.name}
                    </Button>

                    <div className="bg-gray-50 rounded-lg p-4">
                      <h4 className="font-medium text-gray-900 mb-2">Result</h4>
                      <div className="text-2xl font-bold text-gray-400">--</div>
                      <div className="text-sm text-gray-500 mt-1">Upload financial data to enable calculations</div>
                    </div>
                  </CardContent>
                </Card>
              ) : (
                <Card>
                  <CardContent className="text-center py-12">
                    <div className="text-6xl mb-4">💰</div>
                    <h3 className="text-lg font-medium text-gray-900 mb-2">Select a Financial Formula</h3>
                    <p className="text-gray-500">
                      Choose a financial ratio or formula from the library to get started.
                    </p>
                  </CardContent>
                </Card>
              )}
            </div>
          </div>
        )}

        {/* Other tabs - placeholder content */}
        {activeTab !== "formulas" && (
          <Card>
            <CardContent className="text-center py-12">
              <div className="text-6xl mb-4">
                {tabs.find(t => t.id === activeTab)?.icon}
              </div>
              <h3 className="text-lg font-medium text-gray-900 mb-2">
                {tabs.find(t => t.id === activeTab)?.name} Analysis
              </h3>
              <p className="text-gray-500 mb-4">
                This section will show detailed {activeTab} analysis and reports.
              </p>
              <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4 max-w-md mx-auto">
                <p className="text-yellow-800 text-sm">
                  Feature coming soon. Backend APIs are being developed for comprehensive financial analysis.
                </p>
              </div>
            </CardContent>
          </Card>
        )}
      </div>
    </AppLayout>
  );
}