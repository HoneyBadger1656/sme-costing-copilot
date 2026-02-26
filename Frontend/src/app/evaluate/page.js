// frontend/src/app/evaluate/page.js
// UPDATED to call real API

"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";

export default function EvaluateOrder() {
  const router = useRouter();
  const [formData, setFormData] = useState({
    customerName: "",
    productName: "",
    sellingPrice: "",
    costPrice: "",
    quantity: "",
    creditDays: 30,
  });
  
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);

  const handleChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  const handleEvaluate = async (e) => {
    e.preventDefault();
    setLoading(true);

    try {
      const token = localStorage.getItem("token");
      
      const response = await fetch("http://localhost:8000/api/costing/evaluate-order", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Authorization": `Bearer ${token}`
        },
        body: JSON.stringify({
          customer_name: formData.customerName,
          product_id: 1, // Placeholder - will be replaced with actual product selection
          selling_price: parseFloat(formData.sellingPrice),
          cost_price: parseFloat(formData.costPrice),
          quantity: parseFloat(formData.quantity),
          credit_days: parseInt(formData.creditDays)
        })
      });

      if (!response.ok) {
        throw new Error("Evaluation failed");
      }

      const data = await response.json();
      setResult(data);
    } catch (error) {
      alert("Error evaluating order: " + error.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 p-8">
      <div className="max-w-4xl mx-auto">
        <h1 className="text-3xl font-bold mb-8">Evaluate Order</h1>

        <form onSubmit={handleEvaluate} className="bg-white p-8 rounded-lg shadow">
          <div className="grid grid-cols-2 gap-6">
            <div>
              <label className="block text-sm font-medium mb-2">Customer Name</label>
              <input
                type="text"
                name="customerName"
                value={formData.customerName}
                onChange={handleChange}
                required
                className="w-full px-4 py-2 border rounded-lg"
              />
            </div>

            <div>
              <label className="block text-sm font-medium mb-2">Product Name</label>
              <input
                type="text"
                name="productName"
                value={formData.productName}
                onChange={handleChange}
                required
                className="w-full px-4 py-2 border rounded-lg"
              />
            </div>

            <div>
              <label className="block text-sm font-medium mb-2">Selling Price (₹)</label>
              <input
                type="number"
                name="sellingPrice"
                value={formData.sellingPrice}
                onChange={handleChange}
                required
                step="0.01"
                className="w-full px-4 py-2 border rounded-lg"
              />
            </div>

            <div>
              <label className="block text-sm font-medium mb-2">Cost Price (₹)</label>
              <input
                type="number"
                name="costPrice"
                value={formData.costPrice}
                onChange={handleChange}
                required
                step="0.01"
                className="w-full px-4 py-2 border rounded-lg"
              />
            </div>

            <div>
              <label className="block text-sm font-medium mb-2">Quantity</label>
              <input
                type="number"
                name="quantity"
                value={formData.quantity}
                onChange={handleChange}
                required
                className="w-full px-4 py-2 border rounded-lg"
              />
            </div>

            <div>
              <label className="block text-sm font-medium mb-2">Proposed Credit Days</label>
              <input
                type="number"
                name="creditDays"
                value={formData.creditDays}
                onChange={handleChange}
                required
                className="w-full px-4 py-2 border rounded-lg"
              />
            </div>
          </div>

          <button
            type="submit"
            disabled={loading}
            className="mt-6 w-full bg-blue-600 text-white py-3 rounded-lg hover:bg-blue-700 disabled:bg-gray-400"
          >
            {loading ? "Evaluating..." : "Evaluate Order"}
          </button>
        </form>

        {/* NEW: Results display */}
        {result && (
          <div className="mt-8 bg-white p-8 rounded-lg shadow">
            <h2 className="text-2xl font-bold mb-6">Evaluation Results</h2>
            
            <div className="grid grid-cols-2 gap-6 mb-6">
              <div className="p-4 bg-gray-50 rounded">
                <div className="text-sm text-gray-600">Total Cost</div>
                <div className="text-2xl font-bold">₹{result.total_cost.toLocaleString()}</div>
              </div>
              
              <div className="p-4 bg-gray-50 rounded">
                <div className="text-sm text-gray-600">Total Revenue</div>
                <div className="text-2xl font-bold">₹{result.total_revenue.toLocaleString()}</div>
              </div>
              
              <div className="p-4 bg-gray-50 rounded">
                <div className="text-sm text-gray-600">Gross Margin</div>
                <div className="text-2xl font-bold">₹{result.gross_margin.toLocaleString()}</div>
              </div>
              
              <div className={`p-4 rounded ${
                result.margin_percentage >= 15 ? 'bg-green-50' : 
                result.margin_percentage >= 10 ? 'bg-yellow-50' : 'bg-red-50'
              }`}>
                <div className="text-sm text-gray-600">Margin %</div>
                <div className="text-2xl font-bold">{result.margin_percentage}%</div>
              </div>
            </div>

            <div className="p-4 bg-blue-50 rounded mb-4">
              <div className="text-sm text-gray-600 mb-1">Working Capital Impact</div>
              <div className="font-semibold">₹{result.working_capital_blocked.toLocaleString()} blocked for {formData.creditDays} days</div>
            </div>

            <div className={`p-6 rounded-lg ${
              result.risk_level === 'low' ? 'bg-green-100 border-2 border-green-500' :
              result.risk_level === 'medium' ? 'bg-yellow-100 border-2 border-yellow-500' :
              'bg-red-100 border-2 border-red-500'
            }`}>
              <div className="flex justify-between items-start mb-3">
                <div>
                  <div className="text-sm font-medium mb-1">Profitability Score</div>
                  <div className="text-3xl font-bold">{result.profitability_score}/100</div>
                </div>
                <div className={`px-4 py-2 rounded-full text-sm font-bold ${
                  result.risk_level === 'low' ? 'bg-green-200' :
                  result.risk_level === 'medium' ? 'bg-yellow-200' :
                  'bg-red-200'
                }`}>
                  {result.risk_level.toUpperCase()} RISK
                </div>
              </div>
              
              <div className="text-sm mb-3">
                <strong>Recommendation:</strong> {result.recommendations}
              </div>
              
              <div className={`text-center py-3 rounded font-bold text-lg ${
                result.should_accept ? 'bg-green-500 text-white' : 'bg-red-500 text-white'
              }`}>
                {result.should_accept ? '✓ ACCEPT THIS ORDER' : '⚠ REVIEW BEFORE ACCEPTING'}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
