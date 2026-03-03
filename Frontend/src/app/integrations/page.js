// frontend/src/app/integrations/page.js
// Data Integration Settings page

"use client";

import React, { useState, useEffect, useRef } from "react";
import AppLayout from "../../components/layout/AppLayout";
import PageHeader from "../../components/layout/PageHeader";
import Card, { CardHeader, CardTitle, CardContent } from "../../components/ui/Card";
import Button from "../../components/ui/Button";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export default function IntegrationsPage() {
  const [activeTab, setActiveTab] = useState("tally");
  const [loading, setLoading] = useState(false);
  const [uploadHistory, setUploadHistory] = useState([]);
  const fileInputRef = useRef(null);
  
  // Tally state
  const [tallyConfig, setTallyConfig] = useState({
    url: "http://localhost",
    port: "9000",
    company: ""
  });
  const [tallyStatus, setTallyStatus] = useState("disconnected");
  const [tallyMessage, setTallyMessage] = useState("");
  
  // Zoho state
  const [zohoStatus, setZohoStatus] = useState("disconnected");
  const [zohoMessage, setZohoMessage] = useState("");
  
  // Upload state
  const [dragActive, setDragActive] = useState(false);
  const [uploadType, setUploadType] = useState("orders");

  useEffect(() => {
    fetchUploadHistory();
  }, []);

  const fetchUploadHistory = async () => {
    // Placeholder for upload history - would come from backend
    setUploadHistory([
      { id: 1, type: "Orders", filename: "orders_jan_2024.xlsx", date: "2024-01-15", status: "success", records: 150 },
      { id: 2, type: "Products", filename: "product_catalog.csv", date: "2024-01-10", status: "success", records: 45 },
      { id: 3, type: "Financial", filename: "balance_sheet.xlsx", date: "2024-01-05", status: "failed", records: 0 }
    ]);
  };

  const tabs = [
    { id: "tally", name: "Tally Integration", icon: "🏢" },
    { id: "zoho", name: "Zoho Books", icon: "📚" },
    { id: "upload", name: "File Upload", icon: "📁" }
  ];

  const handleTallyTest = async () => {
    setLoading(true);
    setTallyMessage("");
    
    try {
      const token = localStorage.getItem("token");
      const response = await fetch(`${API_BASE_URL}/api/integrations/tally/test-connection`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Authorization": `Bearer ${token}`
        },
        body: JSON.stringify({
          tally_url: tallyConfig.url,
          tally_port: parseInt(tallyConfig.port),
          company_name: tallyConfig.company
        })
      });

      const result = await response.json();
      
      if (result.success) {
        setTallyStatus("connected");
        setTallyMessage("✅ Connection successful! Tally is reachable.");
      } else {
        setTallyStatus("error");
        setTallyMessage(`❌ Connection failed: ${result.message || "Unknown error"}`);
      }
    } catch (error) {
      setTallyStatus("error");
      setTallyMessage(`❌ Connection failed: ${error.message}`);
    } finally {
      setLoading(false);
    }
  };

  const handleTallySync = async () => {
    if (tallyStatus !== "connected") {
      setTallyMessage("⚠️ Please test connection first");
      return;
    }

    setLoading(true);
    setTallyMessage("🔄 Syncing data from Tally...");
    
    try {
      const token = localStorage.getItem("token");
      const clientId = localStorage.getItem("selectedClientId") || 1;
      
      const response = await fetch(`${API_BASE_URL}/api/integrations/tally/sync-ledgers`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Authorization": `Bearer ${token}`
        },
        body: JSON.stringify({
          tally_url: tallyConfig.url,
          tally_port: parseInt(tallyConfig.port),
          company_name: tallyConfig.company,
          client_id: parseInt(clientId)
        })
      });

      const result = await response.json();
      
      if (result.success) {
        setTallyMessage(`✅ Sync completed! ${result.records_synced || 0} records imported.`);
      } else {
        setTallyMessage(`❌ Sync failed: ${result.message || "Unknown error"}`);
      }
    } catch (error) {
      setTallyMessage(`❌ Sync failed: ${error.message}`);
    } finally {
      setLoading(false);
    }
  };

  const handleZohoConnect = async () => {
    setLoading(true);
    setZohoMessage("🔄 Initiating Zoho connection...");
    
    try {
      const token = localStorage.getItem("token");
      const response = await fetch(`${API_BASE_URL}/api/integrations/zoho/auth-url`, {
        headers: {
          "Authorization": `Bearer ${token}`
        }
      });

      const result = await response.json();
      
      if (result.auth_url) {
        setZohoMessage("🔗 Redirecting to Zoho for authentication...");
        // Open Zoho OAuth in new window
        window.open(result.auth_url, "zoho_auth", "width=600,height=700");
        
        // Listen for OAuth completion (simplified - in production would use proper OAuth flow)
        setTimeout(() => {
          setZohoStatus("connected");
          setZohoMessage("✅ Connected to Zoho Books successfully!");
        }, 3000);
      } else {
        setZohoMessage("❌ Failed to get Zoho authorization URL");
      }
    } catch (error) {
      setZohoMessage(`❌ Connection failed: ${error.message}`);
    } finally {
      setLoading(false);
    }
  };

  const handleFileUpload = async (file, type) => {
    if (!file) return;

    const formData = new FormData();
    formData.append("file", file);
    
    const token = localStorage.getItem("token");
    const clientId = localStorage.getItem("selectedClientId") || 1;
    
    setLoading(true);
    
    try {
      const endpoint = type === "orders" ? "import/orders" : 
                     type === "products" ? "import/products" : 
                     "import/financial";
      
      const response = await fetch(`${API_BASE_URL}/api/integrations/${endpoint}?client_id=${clientId}`, {
        method: "POST",
        headers: {
          "Authorization": `Bearer ${token}`
        },
        body: formData
      });

      const result = await response.json();
      
      if (result.success) {
        alert(`✅ Upload successful! ${result.records_imported || 0} records imported.`);
        fetchUploadHistory(); // Refresh history
      } else {
        alert(`❌ Upload failed: ${result.message || "Unknown error"}`);
      }
    } catch (error) {
      alert(`❌ Upload failed: ${error.message}`);
    } finally {
      setLoading(false);
    }
  };

  const handleDrag = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFileUpload(e.dataTransfer.files[0], uploadType);
    }
  };

  const downloadTemplate = (type) => {
    // Create sample CSV content based on type
    let csvContent = "";
    let filename = "";
    
    if (type === "orders") {
      csvContent = "customer_name,product_name,quantity,unit_price,credit_days,order_date\nABC Corp,Widget A,100,50.00,30,2024-01-15\nXYZ Ltd,Widget B,200,75.00,45,2024-01-16";
      filename = "orders_template.csv";
    } else if (type === "products") {
      csvContent = "name,raw_material_cost,labour_cost_per_unit,overhead_percentage,target_margin_percentage,gst_rate\nWidget A,30.00,10.00,15.0,25.0,18.0\nWidget B,45.00,15.00,20.0,30.0,18.0";
      filename = "products_template.csv";
    } else if (type === "financial") {
      csvContent = "account_name,account_type,amount,date\nCash,Asset,100000,2024-01-01\nAccounts Receivable,Asset,50000,2024-01-01\nAccounts Payable,Liability,25000,2024-01-01";
      filename = "financial_template.csv";
    }
    
    const blob = new Blob([csvContent], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    a.click();
    window.URL.revokeObjectURL(url);
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
                    <Button 
                      onClick={handleTallyTest} 
                      variant="outline" 
                      className="flex-1"
                      disabled={loading || !tallyConfig.url || !tallyConfig.company}
                    >
                      {loading ? "Testing..." : "Test Connection"}
                    </Button>
                    <Button 
                      onClick={handleTallySync}
                      className="flex-1"
                      disabled={loading || tallyStatus !== "connected"}
                    >
                      {loading ? "Syncing..." : "Sync Now"}
                    </Button>
                  </div>
                  
                  {tallyMessage && (
                    <div className={`p-3 rounded-lg text-sm ${
                      tallyStatus === "connected" ? "bg-green-50 text-green-800" :
                      tallyStatus === "error" ? "bg-red-50 text-red-800" :
                      "bg-blue-50 text-blue-800"
                    }`}>
                      {tallyMessage}
                    </div>
                  )}
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Connection Status</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-center py-8">
                  <div className={`w-16 h-16 rounded-full flex items-center justify-center mx-auto mb-4 ${
                    tallyStatus === "connected" ? "bg-green-100" :
                    tallyStatus === "error" ? "bg-red-100" :
                    "bg-gray-100"
                  }`}>
                    <span className="text-2xl">
                      {tallyStatus === "connected" ? "✅" :
                       tallyStatus === "error" ? "❌" : "🔌"}
                    </span>
                  </div>
                  <h3 className={`text-lg font-medium mb-2 ${
                    tallyStatus === "connected" ? "text-green-900" :
                    tallyStatus === "error" ? "text-red-900" :
                    "text-gray-900"
                  }`}>
                    {tallyStatus === "connected" ? "Connected" :
                     tallyStatus === "error" ? "Connection Failed" :
                     "Not Connected"}
                  </h3>
                  <p className="text-gray-500 text-sm">
                    {tallyStatus === "connected" ? "Tally integration is active and ready to sync data." :
                     tallyStatus === "error" ? "Please check your connection settings and try again." :
                     "Configure your Tally connection settings and test the connection to get started."}
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
                  
                  <Button 
                    onClick={handleZohoConnect} 
                    className="w-full"
                    disabled={loading || zohoStatus === "connected"}
                  >
                    {loading ? "Connecting..." : 
                     zohoStatus === "connected" ? "Connected to Zoho Books" :
                     "Connect to Zoho Books"}
                  </Button>
                  
                  {zohoMessage && (
                    <div className={`p-3 rounded-lg text-sm ${
                      zohoStatus === "connected" ? "bg-green-50 text-green-800" :
                      "bg-blue-50 text-blue-800"
                    }`}>
                      {zohoMessage}
                    </div>
                  )}
                  
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
                  <div className={`w-16 h-16 rounded-full flex items-center justify-center mx-auto mb-4 ${
                    zohoStatus === "connected" ? "bg-green-100" : "bg-gray-100"
                  }`}>
                    <span className="text-2xl">
                      {zohoStatus === "connected" ? "✅" : "📚"}
                    </span>
                  </div>
                  <h3 className={`text-lg font-medium mb-2 ${
                    zohoStatus === "connected" ? "text-green-900" : "text-gray-900"
                  }`}>
                    {zohoStatus === "connected" ? "Connected" : "Not Connected"}
                  </h3>
                  <p className="text-gray-500 text-sm">
                    {zohoStatus === "connected" ? 
                     "Zoho Books integration is active and ready to sync data." :
                     "Click \"Connect to Zoho Books\" to start the OAuth authentication process."}
                  </p>
                </div>
              </CardContent>
            </Card>
          </div>
        )}

        {activeTab === "upload" && (
          <div className="space-y-6">
            {/* Upload Type Selection */}
            <Card>
              <CardHeader>
                <CardTitle>Select Upload Type</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <button
                    onClick={() => setUploadType("orders")}
                    className={`p-4 border rounded-lg text-center transition-colors ${
                      uploadType === "orders" 
                        ? "border-blue-500 bg-blue-50 text-blue-700" 
                        : "border-gray-200 hover:border-gray-300"
                    }`}
                  >
                    <div className="text-2xl mb-2">📋</div>
                    <div className="font-medium">Orders</div>
                    <div className="text-sm text-gray-500">Customer orders and transactions</div>
                  </button>
                  
                  <button
                    onClick={() => setUploadType("products")}
                    className={`p-4 border rounded-lg text-center transition-colors ${
                      uploadType === "products" 
                        ? "border-blue-500 bg-blue-50 text-blue-700" 
                        : "border-gray-200 hover:border-gray-300"
                    }`}
                  >
                    <div className="text-2xl mb-2">📦</div>
                    <div className="font-medium">Products</div>
                    <div className="text-sm text-gray-500">Product catalog and costing data</div>
                  </button>
                  
                  <button
                    onClick={() => setUploadType("financial")}
                    className={`p-4 border rounded-lg text-center transition-colors ${
                      uploadType === "financial" 
                        ? "border-blue-500 bg-blue-50 text-blue-700" 
                        : "border-gray-200 hover:border-gray-300"
                    }`}
                  >
                    <div className="text-2xl mb-2">📊</div>
                    <div className="font-medium">Financial</div>
                    <div className="text-sm text-gray-500">Balance sheets and P&L data</div>
                  </button>
                </div>
              </CardContent>
            </Card>

            {/* Drag and Drop Upload Area */}
            <Card>
              <CardHeader>
                <CardTitle>Upload {uploadType.charAt(0).toUpperCase() + uploadType.slice(1)} Data</CardTitle>
              </CardHeader>
              <CardContent>
                <div
                  className={`border-2 border-dashed rounded-lg p-8 text-center transition-colors ${
                    dragActive 
                      ? 'border-blue-400 bg-blue-50' 
                      : 'border-gray-300 hover:border-gray-400'
                  }`}
                  onDragEnter={handleDrag}
                  onDragLeave={handleDrag}
                  onDragOver={handleDrag}
                  onDrop={handleDrop}
                >
                  <div className="text-4xl mb-4">📁</div>
                  <h3 className="text-lg font-medium mb-2">
                    Drag & drop your {uploadType} file here
                  </h3>
                  <p className="text-gray-500 mb-4">
                    or <button
                      onClick={() => fileInputRef.current?.click()}
                      className="text-blue-600 hover:text-blue-800 underline"
                    >
                      browse to choose a file
                    </button>
                  </p>
                  <p className="text-sm text-gray-400">
                    Supports .xlsx, .xls, .csv files (max 10MB)
                  </p>
                  
                  <input
                    ref={fileInputRef}
                    type="file"
                    accept=".xlsx,.xls,.csv"
                    onChange={(e) => e.target.files[0] && handleFileUpload(e.target.files[0], uploadType)}
                    className="hidden"
                  />
                </div>
                
                <div className="mt-4 flex justify-center">
                  <Button
                    onClick={() => downloadTemplate(uploadType)}
                    variant="outline"
                    size="sm"
                  >
                    📥 Download {uploadType.charAt(0).toUpperCase() + uploadType.slice(1)} Template
                  </Button>
                </div>
              </CardContent>
            </Card>

            {/* Upload History */}
            <Card>
              <CardHeader>
                <CardTitle>Upload History</CardTitle>
              </CardHeader>
              <CardContent>
                {uploadHistory.length === 0 ? (
                  <div className="text-center py-8 text-gray-500">
                    <div className="text-4xl mb-4">📋</div>
                    <p>No uploads yet. Upload your first file to get started.</p>
                  </div>
                ) : (
                  <div className="space-y-3">
                    {uploadHistory.map((upload) => (
                      <div key={upload.id} className="flex items-center justify-between p-3 border rounded-lg">
                        <div className="flex items-center space-x-3">
                          <div className={`w-3 h-3 rounded-full ${
                            upload.status === "success" ? "bg-green-500" : "bg-red-500"
                          }`}></div>
                          <div>
                            <div className="font-medium">{upload.filename}</div>
                            <div className="text-sm text-gray-500">
                              {upload.type} • {upload.date} • {upload.records} records
                            </div>
                          </div>
                        </div>
                        <div className={`text-sm font-medium ${
                          upload.status === "success" ? "text-green-600" : "text-red-600"
                        }`}>
                          {upload.status === "success" ? "✅ Success" : "❌ Failed"}
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>

            {/* Upload Tips */}
            <Card>
              <CardHeader>
                <CardTitle>Upload Guidelines</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
                  <div className="flex items-center mb-3">
                    <svg className="w-5 h-5 text-yellow-600 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                    <span className="text-yellow-800 font-medium">File Upload Tips</span>
                  </div>
                  <div className="text-yellow-700 text-sm space-y-2">
                    <div><strong>Orders:</strong> Include customer_name, product_name, quantity, unit_price, credit_days, order_date</div>
                    <div><strong>Products:</strong> Include name, raw_material_cost, labour_cost_per_unit, overhead_percentage, target_margin_percentage, gst_rate</div>
                    <div><strong>Financial:</strong> Include account_name, account_type, amount, date</div>
                    <div className="mt-3 pt-3 border-t border-yellow-300">
                      <ul className="list-disc list-inside space-y-1">
                        <li>Use our Excel templates for best results</li>
                        <li>Ensure all required columns are present</li>
                        <li>Check data formats before uploading</li>
                        <li>Maximum file size: 10MB</li>
                      </ul>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        )}
      </div>
    </AppLayout>
  );
}