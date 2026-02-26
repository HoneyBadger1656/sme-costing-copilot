// frontend/src/app/products/page.js
// Product management with costing rules

"use client";

import { useState, useEffect } from "react";

export default function Products() {
  const [products, setProducts] = useState([]);
  const [showForm, setShowForm] = useState(false);
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

      const response = await fetch("http://localhost:8000/api/products", {
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

      const response = await fetch("http://localhost:8000/api/products", {
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

                return (
                  <tr
                    key={product.id}
                    className="border-b hover:bg-gray-50"
                  >
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
                        className={`font-semibold ${
                          (product.target_margin_percentage || 0) >= 15
                            ? "text-green-600"
                            : "text-yellow-600"
                        }`}
                      >
                        {product.target_margin_percentage}%
                      </span>
                    </td>
                  </tr>
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
      </div>
    </div>
  );
}
