// frontend/src/app/products/page.js
// Product management with costing rules

"use client";

import React, { useState, useEffect } from "react";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export default function Products() {
  const [products, setProducts] = useState([]);
  const [showForm, setShowForm] = useState(false);
  const [expandedProducts, setExpandedProducts] = useState(new Set());
  const [bomData, setBomData] = useState({});
  const [showBomForm, setShowBomForm] = useState(false);
  const [selectedProductId, setSelectedProductId] = useState(null);
  const [bomFormData, setBomFormData] = useState({
    component_name: "",
    quantity: "",
    unit: "pcs",
    unit_cost: "",
    notes: "",
  });
  const [formData, setFormData] = useState({
    name: "",
    category: "",
    unit: "pcs",
    rawMaterialCost: "",
    labourCost: "",
    overheadPercentage: "10",
    targetMargin: "20",
    taxRate: "18",
  });

  const fetchProducts = async () => {
    try {
      const token =
        typeof window !== "undefined" ? localStorage.getItem("token") : null;

      const response = await fetch(`${API_BASE_URL}/api/products`, {
        headers: { Authorization: `Bearer ${token}` },
      });

      if (!response.ok) {
        throw new Error("Failed to fetch products");
      }

      const data = await response.json();
      setProducts(Array.isArray(data) ? data : []);
    } catch (error) {
      console.error("Error fetching products:", error);
    }
  };

  const fetchBomItems = async (productId) => {
    try {
      const token = typeof window !== "undefined" ? localStorage.getItem("token") : null;
      const response = await fetch(`${API_BASE_URL}/api/costing/products/${productId}/bom`, {
        headers: { Authorization: `Bearer ${token}` },
      });

      if (!response.ok) {
        throw new Error("Failed to fetch BOM items");
      }

      const data = await response.json();
      setBomData(prev => ({ ...prev, [productId]: data }));
    } catch (error) {
      console.error("Error fetching BOM items:", error);
    }
  };

  const toggleProductExpansion = (productId) => {
    const newExpanded = new Set(expandedProducts);
    if (newExpanded.has(productId)) {
      newExpanded.delete(productId);
    } else {
      newExpanded.add(productId);
      if (!bomData[productId]) {
        fetchBomItems(productId);
      }
    }
    setExpandedProducts(newExpanded);
  };

  const handleAddBomItem = (productId) => {
    setSelectedProductId(productId);
    setShowBomForm(true);
    setBomFormData({
      component_name: "",
      quantity: "",
      unit: "pcs",
      unit_cost: "",
      notes: "",
    });
  };

  const handleBomSubmit = async (e) => {
    e.preventDefault();
    try {
      const token = typeof window !== "undefined" ? localStorage.getItem("token") : null;
      const response = await fetch(`${API_BASE_URL}/api/costing/products/${selectedProductId}/bom`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          component_name: bomFormData.component_name,
          quantity: parseFloat(bomFormData.quantity),
          unit: bomFormData.unit,
          unit_cost: parseFloat(bomFormData.unit_cost),
          notes: bomFormData.notes,
        }),
      });

      if (!response.ok) {
        throw new Error("Failed to add BOM item");
      }

      setShowBomForm(false);
      await fetchBomItems(selectedProductId);
    } catch (error) {
      alert("Error adding BOM item: " + error.message);
    }
  };

  const handleDeleteBomItem = async (bomId, productId) => {
    try {
      const token = typeof window !== "undefined" ? localStorage.getItem("token") : null;
      const response = await fetch(`${API_BASE_URL}/api/costing/bom/${bomId}`, {
        method: "DELETE",
        headers: { Authorization: `Bearer ${token}` },
      });

      if (!response.ok) {
        throw new Error("Failed to delete BOM item");
      }

      await fetchBomItems(productId);
    } catch (error) {
      alert("Error deleting BOM item: " + error.message);
    }
  };

  useEffect(() => {
    fetchProducts();
  }, []);

  const handleSubmit = async (e) => {
    e.preventDefault();

    try {
      const token =
        typeof window !== "undefined" ? localStorage.getItem("token") : null;
      const clientId =
        typeof window !== "undefined"
          ? localStorage.getItem("selectedClientId") || 1
          : 1;

      const response = await fetch(`${API_BASE_URL}/api/products`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          client_id: clientId,
          name: formData.name,
          category: formData.category,
          unit: formData.unit,
          raw_material_cost: parseFloat(formData.rawMaterialCost || "0"),
          labour_cost_per_unit: parseFloat(formData.labourCost || "0"),
          overhead_percentage: parseFloat(formData.overheadPercentage || "0"),
          target_margin_percentage: parseFloat(formData.targetMargin || "0"),
          tax_rate: parseFloat(formData.taxRate || "0"),
        }),
      });

      if (!response.ok) {
        const errText = await response.text();
        throw new Error(errText || "Failed to create product");
      }

      setShowForm(false);
      await fetchProducts();

      setFormData({
        name: "",
        category: "",
        unit: "pcs",
        rawMaterialCost: "",
        labourCost: "",
        overheadPercentage: "10",
        targetMargin: "20",
        taxRate: "18",
      });
    } catch (error) {
      alert("Error creating product: " + error.message);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 p-8">
      <div className="max-w-6xl mx-auto">
        <div className="flex justify-between items-center mb-8">
          <h1 className="text-3xl font-bold">Products &amp; Costing Rules</h1>
          <button
            onClick={() => setShowForm(true)}
            className="bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700"
          >
            + Add Product
          </button>
        </div>

        {/* Product list */}
        <div className="bg-white rounded-lg shadow overflow-hidden">
          <table className="w-full">
            <thead className="bg-gray-50 border-b">
              <tr>
                <th className="px-6 py-3 text-left text-sm font-semibold w-8">
                  
                </th>
                <th className="px-6 py-3 text-left text-sm font-semibold">
                  Product
                </th>
                <th className="px-6 py-3 text-left text-sm font-semibold">
                  Category
                </th>
                <th className="px-6 py-3 text-right text-sm font-semibold">
                  RM Cost
                </th>
                <th className="px-6 py-3 text-right text-sm font-semibold">
                  Labour
                </th>
                <th className="px-6 py-3 text-right text-sm font-semibold">
                  Total Cost
                </th>
                <th className="px-6 py-3 text-right text-sm font-semibold">
                  Selling Price
                </th>
                <th className="px-6 py-3 text-right text-sm font-semibold">
                  Margin %
                </th>
              </tr>
            </thead>
            <tbody>
              {products.map((product) => {
                const directCost =
                  (product.raw_material_cost || 0) +
                  (product.labour_cost_per_unit || 0);
                const overhead =
                  directCost * ((product.overhead_percentage || 0) / 100);
                const totalCost = directCost + overhead;
                const marginFraction =
                  1 - (product.target_margin_percentage || 0) / 100;
                const sellingPrice =
                  marginFraction !== 0 ? totalCost / marginFraction : totalCost;
                const bomItems = bomData[product.id] || [];
                const bomTotalCost = bomItems.reduce((sum, item) => sum + item.total_cost, 0);

                return (
                  <React.Fragment key={product.id}>
                    <tr
                      className="border-b hover:bg-gray-50 cursor-pointer"
                      onClick={() => toggleProductExpansion(product.id)}
                    >
                      <td className="px-6 py-4">
                        <div className="flex items-center justify-center">
                          <svg
                            className={`w-4 h-4 text-gray-400 transition-transform ${
                              expandedProducts.has(product.id) ? "rotate-90" : ""
                            }`}
                            fill="none"
                            stroke="currentColor"
                            viewBox="0 0 24 24"
                          >
                            <path
                              strokeLinecap="round"
                              strokeLinejoin="round"
                              strokeWidth={2}
                              d="M9 5l7 7-7 7"
                            />
                          </svg>
                        </div>
                      </td>
                      <td className="px-6 py-4">
                        <div className="font-medium">{product.name}</div>
                        <div className="text-sm text-gray-500">
                          {product.unit}
                        </div>
                      </td>
                      <td className="px-6 py-4 text-sm">{product.category}</td>
                      <td className="px-6 py-4 text-right">
                        ₹
                        {(product.raw_material_cost || 0).toFixed(2)}
                      </td>
                      <td className="px-6 py-4 text-right">
                        ₹
                        {(product.labour_cost_per_unit || 0).toFixed(2)}
                      </td>
                      <td className="px-6 py-4 text-right font-semibold">
                        ₹{totalCost.toFixed(2)}
                      </td>
                      <td className="px-6 py-4 text-right font-semibold">
                        ₹{sellingPrice.toFixed(2)}
                      </td>
                      <td className="px-6 py-4 text-right">
                        <span
                          className={`font-semibold ${(product.target_margin_percentage || 0) >= 15
                              ? "text-green-600"
                              : "text-yellow-600"
                            }`}
                        >
                          {product.target_margin_percentage}%
                        </span>
                      </td>
                    </tr>
                    
                    {/* BOM Details Row */}
                    {expandedProducts.has(product.id) && (
                      <tr>
                        <td colSpan="8" className="px-0 py-0 bg-gray-50">
                          <div className="px-6 py-4">
                            <div className="flex items-center justify-between mb-4">
                              <h3 className="text-sm font-semibold text-gray-700">
                                Bill of Materials (BOM)
                              </h3>
                              <button
                                onClick={(e) => {
                                  e.stopPropagation();
                                  handleAddBomItem(product.id);
                                }}
                                className="bg-blue-600 text-white px-3 py-1 rounded text-sm hover:bg-blue-700"
                              >
                                + Add Component
                              </button>
                            </div>
                            
                            {bomItems.length === 0 ? (
                              <div className="text-center py-8 text-gray-500">
                                <p className="text-sm">No BOM components added yet</p>
                                <p className="text-xs mt-1">Click &quot;Add Component&quot; to start building the bill of materials</p>
                              </div>
                            ) : (
                              <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
                                <table className="w-full text-sm">
                                  <thead className="bg-gray-100 border-b">
                                    <tr>
                                      <th className="px-4 py-2 text-left font-medium">Component</th>
                                      <th className="px-4 py-2 text-right font-medium">Quantity</th>
                                      <th className="px-4 py-2 text-right font-medium">Unit Cost</th>
                                      <th className="px-4 py-2 text-right font-medium">Total Cost</th>
                                      <th className="px-4 py-2 text-left font-medium">Notes</th>
                                      <th className="px-4 py-2 text-center font-medium">Actions</th>
                                    </tr>
                                  </thead>
                                  <tbody>
                                    {bomItems.map((item) => (
                                      <tr key={item.id} className="border-b border-gray-100">
                                        <td className="px-4 py-2">{item.component_name}</td>
                                        <td className="px-4 py-2 text-right">
                                          {item.quantity} {item.unit}
                                        </td>
                                        <td className="px-4 py-2 text-right">₹{item.unit_cost.toFixed(2)}</td>
                                        <td className="px-4 py-2 text-right font-medium">₹{item.total_cost.toFixed(2)}</td>
                                        <td className="px-4 py-2 text-sm text-gray-600">{item.notes || "-"}</td>
                                        <td className="px-4 py-2 text-center">
                                          <button
                                            onClick={(e) => {
                                              e.stopPropagation();
                                              handleDeleteBomItem(item.id, product.id);
                                            }}
                                            className="text-red-600 hover:text-red-800 text-sm"
                                          >
                                            Delete
                                          </button>
                                        </td>
                                      </tr>
                                    ))}
                                    <tr className="bg-gray-50 font-semibold">
                                      <td className="px-4 py-2" colSpan="3">BOM Total</td>
                                      <td className="px-4 py-2 text-right">₹{bomTotalCost.toFixed(2)}</td>
                                      <td colSpan="2"></td>
                                    </tr>
                                  </tbody>
                                </table>
                              </div>
                            )}
                          </div>
                        </td>
                      </tr>
                    )}
                  </React.Fragment>
                );
              })}
            </tbody>
          </table>
        </div>

        {/* Add Product Modal */}
        {showForm && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4">
            <div className="bg-white rounded-lg p-8 max-w-2xl w-full max-h-[90vh] overflow-y-auto">
              <h2 className="text-2xl font-bold mb-6">Add New Product</h2>

              <form onSubmit={handleSubmit}>
                <div className="grid grid-cols-2 gap-4">
                  <div className="col-span-2">
                    <label className="block text-sm font-medium mb-2">
                      Product Name *
                    </label>
                    <input
                      type="text"
                      value={formData.name}
                      onChange={(e) =>
                        setFormData({ ...formData, name: e.target.value })
                      }
                      required
                      className="w-full px-4 py-2 border rounded-lg"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium mb-2">
                      Category
                    </label>
                    <input
                      type="text"
                      value={formData.category}
                      onChange={(e) =>
                        setFormData({
                          ...formData,
                          category: e.target.value,
                        })
                      }
                      className="w-full px-4 py-2 border rounded-lg"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium mb-2">
                      Unit
                    </label>
                    <select
                      value={formData.unit}
                      onChange={(e) =>
                        setFormData({ ...formData, unit: e.target.value })
                      }
                      className="w-full px-4 py-2 border rounded-lg"
                    >
                      <option value="pcs">Pieces</option>
                      <option value="kg">Kilograms</option>
                      <option value="litre">Litres</option>
                      <option value="metre">Metres</option>
                    </select>
                  </div>

                  <div>
                    <label className="block text-sm font-medium mb-2">
                      Raw Material Cost (₹) *
                    </label>
                    <input
                      type="number"
                      step="0.01"
                      value={formData.rawMaterialCost}
                      onChange={(e) =>
                        setFormData({
                          ...formData,
                          rawMaterialCost: e.target.value,
                        })
                      }
                      required
                      className="w-full px-4 py-2 border rounded-lg"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium mb-2">
                      Labour Cost/Unit (₹) *
                    </label>
                    <input
                      type="number"
                      step="0.01"
                      value={formData.labourCost}
                      onChange={(e) =>
                        setFormData({
                          ...formData,
                          labourCost: e.target.value,
                        })
                      }
                      required
                      className="w-full px-4 py-2 border rounded-lg"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium mb-2">
                      Overhead % *
                    </label>
                    <input
                      type="number"
                      step="0.1"
                      value={formData.overheadPercentage}
                      onChange={(e) =>
                        setFormData({
                          ...formData,
                          overheadPercentage: e.target.value,
                        })
                      }
                      required
                      className="w-full px-4 py-2 border rounded-lg"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium mb-2">
                      Target Margin % *
                    </label>
                    <input
                      type="number"
                      step="0.1"
                      value={formData.targetMargin}
                      onChange={(e) =>
                        setFormData({
                          ...formData,
                          targetMargin: e.target.value,
                        })
                      }
                      required
                      className="w-full px-4 py-2 border rounded-lg"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium mb-2">
                      GST/Tax Rate % *
                    </label>
                    <input
                      type="number"
                      step="0.1"
                      value={formData.taxRate}
                      onChange={(e) =>
                        setFormData({
                          ...formData,
                          taxRate: e.target.value,
                        })
                      }
                      required
                      className="w-full px-4 py-2 border rounded-lg"
                    />
                  </div>
                </div>

                <div className="flex gap-4 mt-6">
                  <button
                    type="submit"
                    className="flex-1 bg-blue-600 text-white py-3 rounded-lg hover:bg-blue-700"
                  >
                    Create Product
                  </button>
                  <button
                    type="button"
                    onClick={() => setShowForm(false)}
                    className="flex-1 bg-gray-200 text-gray-700 py-3 rounded-lg hover:bg-gray-300"
                  >
                    Cancel
                  </button>
                </div>
              </form>
            </div>
          </div>
        )}

        {/* Add BOM Item Modal */}
        {showBomForm && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4">
            <div className="bg-white rounded-lg p-6 max-w-md w-full">
              <h2 className="text-xl font-bold mb-4">Add BOM Component</h2>

              <form onSubmit={handleBomSubmit}>
                <div className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium mb-2">
                      Component Name *
                    </label>
                    <input
                      type="text"
                      value={bomFormData.component_name}
                      onChange={(e) =>
                        setBomFormData({ ...bomFormData, component_name: e.target.value })
                      }
                      required
                      className="w-full px-4 py-2 border rounded-lg"
                    />
                  </div>

                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm font-medium mb-2">
                        Quantity *
                      </label>
                      <input
                        type="number"
                        step="any"
                        value={bomFormData.quantity}
                        onChange={(e) =>
                          setBomFormData({ ...bomFormData, quantity: e.target.value })
                        }
                        required
                        className="w-full px-4 py-2 border rounded-lg"
                      />
                    </div>

                    <div>
                      <label className="block text-sm font-medium mb-2">
                        Unit
                      </label>
                      <select
                        value={bomFormData.unit}
                        onChange={(e) =>
                          setBomFormData({ ...bomFormData, unit: e.target.value })
                        }
                        className="w-full px-4 py-2 border rounded-lg"
                      >
                        <option value="pcs">Pieces</option>
                        <option value="kg">Kilograms</option>
                        <option value="litre">Litres</option>
                        <option value="metre">Metres</option>
                        <option value="set">Sets</option>
                      </select>
                    </div>
                  </div>

                  <div>
                    <label className="block text-sm font-medium mb-2">
                      Unit Cost (₹) *
                    </label>
                    <input
                      type="number"
                      step="0.01"
                      value={bomFormData.unit_cost}
                      onChange={(e) =>
                        setBomFormData({ ...bomFormData, unit_cost: e.target.value })
                      }
                      required
                      className="w-full px-4 py-2 border rounded-lg"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium mb-2">
                      Notes
                    </label>
                    <textarea
                      value={bomFormData.notes}
                      onChange={(e) =>
                        setBomFormData({ ...bomFormData, notes: e.target.value })
                      }
                      rows={3}
                      className="w-full px-4 py-2 border rounded-lg"
                      placeholder="Optional notes about this component"
                    />
                  </div>
                </div>

                <div className="flex gap-4 mt-6">
                  <button
                    type="submit"
                    className="flex-1 bg-blue-600 text-white py-2 rounded-lg hover:bg-blue-700"
                  >
                    Add Component
                  </button>
                  <button
                    type="button"
                    onClick={() => setShowBomForm(false)}
                    className="flex-1 bg-gray-200 text-gray-700 py-2 rounded-lg hover:bg-gray-300"
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
