// frontend/src/app/financial-data/page.js
// Financial Data Upload & Management

"use client";

import React, { useState, useEffect } from "react";
import AppLayout from "../../components/layout/AppLayout";
import PageHeader from "../../components/layout/PageHeader";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export default function FinancialDataPage() {
  const [statements, setStatements] = useState([]);
  const [loading, setLoading] = useState(true);
  const [uploadType, setUploadType] = useState(null);
  const [uploadFile, setUploadFile] = useState(null);
  const [uploadParams, setUploadParams] = useState({
    client_id: 1,
    period_start: "",
    period_end: "",
    as_of_date: ""
  });
  const [uploading, setUploading] = useState(false);

  useEffect(() => {
    fetchStatements();
  }, []);

  const fetchStatements = async () => {
    try {
      const token = localStorage.getItem("token");
      const clientId = localStorage.getItem("selectedClientId") || 1;
      
      const response = await fetch(
        `${API_BASE_URL}/api/financial-data/statements?client_id=${clientId}`,
        {
          headers: { Authorization: `Bearer ${token}` }
        }
      );

      if (!response.ok) throw new Error("Failed to fetch statements");
      const data = await response.json();
      setStatements(data);
    } catch (error) {
      console.error("Error fetching statements:", error);
    } finally {
      setLoading(false);
    }
  };

  const downloadTemplate = async (templateType) => {
    try {
      const response = await fetch(
        `${API_BASE_URL}/api/financial-data/templates/${templateType}.xlsx`
      );
      
      if (!response.ok) throw new Error("Failed to download template");
      
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `${templateType}_template.xlsx`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (error) {
      alert("Error downloading template: " + error.message);
    }
  };

  const handleUpload = async () => {
    if (!uploadFile || !uploadType) {
      alert("Please select a file and upload type");
      return;
    }

    setUploading(true);
    try {
      const token = localStorage.getItem("token");
      const formData = new FormData();
      formData.append("file", uploadFile);

      let url = `${API_BASE_URL}/api/financial-data/upload/${uploadType}`;
      const params = new URLSearchParams({
        client_id: uploadParams.client_id
      });

      if (uploadType === "inventory") {
        params.append("as_of_date", uploadParams.as_of_date);
      } else {
        params.append("period_start", uploadParams.period_start);
        params.append("period_end", uploadParams.period_end);
      }

      url += `?${params.toString()}`;

      const response = await fetch(url, {
        method: "POST",
        headers: { Authorization: `Bearer ${token}` },
        body: formData
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || "Upload failed");
      }

      const result = await response.json();
      alert(`Upload successful: ${result.message}`);
      
      // Reset form
      setUploadType(null);
      setUploadFile(null);
      setUploadParams({
        client_id: 1,
        period_start: "",
        period_end: "",
        as_of_date: ""
      });
      
      // Refresh statements
      await fetchStatements();
      
    } catch (error) {
      alert("Upload failed: " + error.message);
    } finally {
      setUploading(false);
    }
  };

  const formatStatementType = (type) => {
    const types = {
      balance_sheet: "Balance Sheet",
      profit_loss: "Profit & Loss",
      inventory: "Inventory"
    };
    return types[type] || type;
  };

  return (
    <AppLayout>
      <PageHeader
        title="Financial Data Management"
        description="Upload and manage your financial statements and inventory data"
        icon="📄"
        breadcrumbs={[
          { name: "Dashboard", href: "/dashboard" },
          { name: "Financial Data" }
        ]}
      />

      <div className="p-6">
        <div className="max-w-7xl mx-auto">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          
          {/* Upload Section */}
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-xl font-semibold mb-6">Upload Financial Data</h2>
            
            {/* Template Downloads */}
            <div className="mb-6">
              <h3 className="text-sm font-medium text-gray-700 mb-3">
                Download Templates
              </h3>
              <div className="grid grid-cols-1 gap-2">
                <button
                  onClick={() => downloadTemplate("balance-sheet")}
                  className="flex items-center justify-between p-3 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors"
                >
                  <div className="flex items-center">
                    <span className="text-2xl mr-3">📊</span>
                    <div className="text-left">
                      <div className="font-medium">Balance Sheet Template</div>
                      <div className="text-sm text-gray-500">Assets, Liabilities, Equity</div>
                    </div>
                  </div>
                  <svg className="w-5 h-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                  </svg>
                </button>
                
                <button
                  onClick={() => downloadTemplate("profit-loss")}
                  className="flex items-center justify-between p-3 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors"
                >
                  <div className="flex items-center">
                    <span className="text-2xl mr-3">💰</span>
                    <div className="text-left">
                      <div className="font-medium">Profit & Loss Template</div>
                      <div className="text-sm text-gray-500">Revenue, Expenses, Profit</div>
                    </div>
                  </div>
                  <svg className="w-5 h-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                  </svg>
                </button>
                
                <button
                  onClick={() => downloadTemplate("inventory")}
                  className="flex items-center justify-between p-3 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors"
                >
                  <div className="flex items-center">
                    <span className="text-2xl mr-3">📦</span>
                    <div className="text-left">
                      <div className="font-medium">Inventory Template</div>
                      <div className="text-sm text-gray-500">Stock Items, Quantities, Values</div>
                    </div>
                  </div>
                  <svg className="w-5 h-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                  </svg>
                </button>
              </div>
            </div>

            {/* Upload Form */}
            <div className="border-t pt-6">
              <h3 className="text-sm font-medium text-gray-700 mb-3">
                Upload Completed File
              </h3>
              
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Upload Type
                  </label>
                  <select
                    value={uploadType || ""}
                    onChange={(e) => setUploadType(e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="">Select type...</option>
                    <option value="balance-sheet">Balance Sheet</option>
                    <option value="profit-loss">Profit & Loss</option>
                    <option value="inventory">Inventory</option>
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    File
                  </label>
                  <input
                    type="file"
                    accept=".xlsx,.xls,.csv"
                    onChange={(e) => setUploadFile(e.target.files[0])}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>

                {uploadType && uploadType !== "inventory" && (
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        Period Start
                      </label>
                      <input
                        type="date"
                        value={uploadParams.period_start}
                        onChange={(e) => setUploadParams({
                          ...uploadParams,
                          period_start: e.target.value
                        })}
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        Period End
                      </label>
                      <input
                        type="date"
                        value={uploadParams.period_end}
                        onChange={(e) => setUploadParams({
                          ...uploadParams,
                          period_end: e.target.value
                        })}
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                      />
                    </div>
                  </div>
                )}

                {uploadType === "inventory" && (
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      As of Date
                    </label>
                    <input
                      type="date"
                      value={uploadParams.as_of_date}
                      onChange={(e) => setUploadParams({
                        ...uploadParams,
                        as_of_date: e.target.value
                      })}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                  </div>
                )}

                <button
                  onClick={handleUpload}
                  disabled={uploading || !uploadFile || !uploadType}
                  className="w-full px-4 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-blue-400 disabled:cursor-not-allowed transition-colors"
                >
                  {uploading ? "Uploading..." : "Upload File"}
                </button>
              </div>
            </div>
          </div>

          {/* Statements List */}
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-xl font-semibold mb-6">Uploaded Statements</h2>
            
            {loading ? (
              <div className="text-center py-8">
                <div className="w-8 h-8 border-4 border-blue-400 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
                <p className="text-gray-500">Loading statements...</p>
              </div>
            ) : statements.length === 0 ? (
              <div className="text-center py-8 text-gray-500">
                <div className="text-4xl mb-4">📄</div>
                <p>No financial statements uploaded yet</p>
                <p className="text-sm mt-1">Upload your first statement to get started</p>
              </div>
            ) : (
              <div className="space-y-3">
                {statements.map((statement) => (
                  <div
                    key={statement.id}
                    className="border border-gray-200 rounded-lg p-4 hover:bg-gray-50 transition-colors"
                  >
                    <div className="flex items-center justify-between">
                      <div>
                        <h3 className="font-medium">
                          {formatStatementType(statement.statement_type)}
                        </h3>
                        <p className="text-sm text-gray-500">
                          {new Date(statement.period_start).toLocaleDateString()} - {new Date(statement.period_end).toLocaleDateString()}
                        </p>
                      </div>
                      <div className="text-right">
                        <div className="text-sm text-gray-500">
                          Uploaded {new Date(statement.created_at).toLocaleDateString()}
                        </div>
                        {statement.current_ratio && (
                          <div className="text-xs text-blue-600">
                            Current Ratio: {statement.current_ratio.toFixed(2)}
                          </div>
                        )}
                        {statement.gross_margin && (
                          <div className="text-xs text-green-600">
                            Gross Margin: {statement.gross_margin.toFixed(1)}%
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
          </div>
        </div>
      </div>
    </AppLayout>
  );
}