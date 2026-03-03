// frontend/src/app/integrations/page.js
// Data Integration Settings page

"use client";

import React, { useState } from "react";
import AppLayout from "../../components/layout/AppLayout";
import PageHeader from "../../components/layout/PageHeader";
import Card, { CardHeader, CardTitle, CardContent } from "../../components/ui/Card";
import Button from "../../components/ui/Button";

export default function IntegrationsPage() {
  const [activeTab, setActiveTab] = useState("tally");
  const [tallyConfig, setTallyConfig] = useState({
    url: "",
    port: "9000",
    company: ""
  });
  const [zohoStatus, setZohoStatus] = useState("disconnected");

  const tabs = [
    { id: "tally", name: "Tally Integration", icon: "🏢" },
    { id: "zoho", name: "Zoho Books", icon: "📚" },
    { id: "upload", name: "File Upload", icon: "📁" }
  ];

  const handleTallyTest = async () => {
    // Placeholder for Tally connection test
    alert("Tally connection test - Feature coming soon");
  };

  const handleZohoConnect = async () => {
    // Placeholder for Zoho OAuth flow
    alert("Zoho Books connection - Feature coming soon");
  };

  return (
    <AppLayout>
      <PageHeader
        title="Data Integrations"
        description="Connect your accounting software and manage data imports"
        icon="🔗"
        breadcrumbs={[
          { name: "Dashboard", href: "/dashboard" },
          { name: "Integrations" }
        ]}
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
        {activeTab === "tally" && (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <Card>
              <CardHeader>
                <CardTitle>Tally Prime Connection</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Tally Server URL
                    </label>
                    <input
                      type="text"
                      value={tallyConfig.url}
                      onChange={(e) => setTallyConfig({...tallyConfig, url: e.target.value})}
                      placeholder="http://localhost"
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    />
                  </div>
                  
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Port
                    </label>
                    <input
                      type="text"
                      value={tallyConfig.port}
                      onChange={(e) => setTallyConfig({...tallyConfig, port: e.target.value})}
                      placeholder="9000"
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    />
                  </div>
                  
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Company Name
                    </label>
                    <input
                      type="text"
                      value={tallyConfig.company}
                      onChange={(e) => setTallyConfig({...tallyConfig, company: e.target.value})}
                      placeholder="Your Company Name"
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    />
                  </div>
                  
                  <div className="flex space-x-3">
                    <Button onClick={handleTallyTest} variant="outline" className="flex-1">
                      Test Connection
                    </Button>
                    <Button disabled className="flex-1">
                      Sync Now
                    </Button>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Connection Status</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-center py-8">
                  <div className="w-16 h-16 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-4">
                    <span className="text-2xl">🔌</span>
                  </div>
                  <h3 className="text-lg font-medium text-gray-900 mb-2">Not Connected</h3>
                  <p className="text-gray-500 text-sm">
                    Configure your Tally connection settings and test the connection to get started.
                  </p>
                </div>
              </CardContent>
            </Card>
          </div>
        )}

        {activeTab === "zoho" && (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <Card>
              <CardHeader>
                <CardTitle>Zoho Books Integration</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                    <div className="flex items-center">
                      <svg className="w-5 h-5 text-blue-600 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                      </svg>
                      <span className="text-blue-800 font-medium">OAuth Integration</span>
                    </div>
                    <p className="text-blue-700 mt-2 text-sm">
                      Connect securely to your Zoho Books account using OAuth authentication.
                    </p>
                  </div>
                  
                  <Button onClick={handleZohoConnect} className="w-full">
                    Connect to Zoho Books
                  </Button>
                  
                  <div className="text-sm text-gray-500">
                    <p>After connecting, you'll be able to:</p>
                    <ul className="list-disc list-inside mt-2 space-y-1">
                      <li>Import invoices and bills</li>
                      <li>Sync customer and vendor data</li>
                      <li>Pull financial reports</li>
                      <li>Automatic data synchronization</li>
                    </ul>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Connection Status</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-center py-8">
                  <div className="w-16 h-16 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-4">
                    <span className="text-2xl">📚</span>
                  </div>
                  <h3 className="text-lg font-medium text-gray-900 mb-2">Not Connected</h3>
                  <p className="text-gray-500 text-sm">
                    Click "Connect to Zoho Books" to start the OAuth authentication process.
                  </p>
                </div>
              </CardContent>
            </Card>
          </div>
        )}

        {activeTab === "upload" && (
          <Card>
            <CardHeader>
              <CardTitle>File Upload Options</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <div className="text-center p-6 border border-gray-200 rounded-lg hover:border-blue-300 transition-colors">
                  <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center mx-auto mb-4">
                    <span className="text-2xl">📊</span>
                  </div>
                  <h3 className="font-medium mb-2">Financial Statements</h3>
                  <p className="text-sm text-gray-500 mb-4">
                    Upload balance sheets, P&L statements, and cash flow data
                  </p>
                  <Button variant="outline" size="sm" className="w-full">
                    Upload Financial Data
                  </Button>
                </div>

                <div className="text-center p-6 border border-gray-200 rounded-lg hover:border-blue-300 transition-colors">
                  <div className="w-12 h-12 bg-green-100 rounded-lg flex items-center justify-center mx-auto mb-4">
                    <span className="text-2xl">📦</span>
                  </div>
                  <h3 className="font-medium mb-2">Inventory Data</h3>
                  <p className="text-sm text-gray-500 mb-4">
                    Upload stock items, quantities, and valuation data
                  </p>
                  <Button variant="outline" size="sm" className="w-full">
                    Upload Inventory
                  </Button>
                </div>

                <div className="text-center p-6 border border-gray-200 rounded-lg hover:border-blue-300 transition-colors">
                  <div className="w-12 h-12 bg-purple-100 rounded-lg flex items-center justify-center mx-auto mb-4">
                    <span className="text-2xl">📋</span>
                  </div>
                  <h3 className="font-medium mb-2">Order Data</h3>
                  <p className="text-sm text-gray-500 mb-4">
                    Upload customer orders, products, and transaction data
                  </p>
                  <Button variant="outline" size="sm" className="w-full">
                    Upload Orders
                  </Button>
                </div>
              </div>

              <div className="mt-8 bg-yellow-50 border border-yellow-200 rounded-lg p-4">
                <div className="flex items-center">
                  <svg className="w-5 h-5 text-yellow-600 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                  <span className="text-yellow-800 font-medium">File Upload Tips</span>
                </div>
                <div className="text-yellow-700 mt-2 text-sm">
                  <ul className="list-disc list-inside space-y-1">
                    <li>Use our Excel templates for best results</li>
                    <li>Supported formats: .xlsx, .xls, .csv</li>
                    <li>Maximum file size: 10MB</li>
                    <li>Ensure data is properly formatted before upload</li>
                  </ul>
                </div>
              </div>
            </CardContent>
          </Card>
        )}
      </div>
    </AppLayout>
  );
}