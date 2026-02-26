'use client'
import { useState } from 'react'
import { useSearchParams } from 'next/navigation'

export default function EvaluatePage() {
  const searchParams = useSearchParams()
  const clientId = searchParams.get('client')
  
  const [formData, setFormData] = useState({
    customer_name: '',
    product_name: '',
    selling_price: '',
    cost_price: '',
    quantity: '',
    proposed_credit_days: ''
  })
  
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)

  const handleEvaluate = async (e) => {
    e.preventDefault()
    setLoading(true)

    const token = localStorage.getItem('token')
    
    try {
      const response = await fetch('http://localhost:8000/api/evaluations/evaluate', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          client_id: clientId,
          customer_name: formData.customer_name,
          product_name: formData.product_name,
          selling_price: parseFloat(formData.selling_price),
          cost_price: parseFloat(formData.cost_price),
          quantity: parseFloat(formData.quantity),
          proposed_credit_days: parseInt(formData.proposed_credit_days)
        })
      })

      const data = await response.json()
      setResult(data)
    } catch (error) {
      console.error('Evaluation failed:', error)
    } finally {
      setLoading(false)
    }
  }

  const getDecisionColor = (decision) => {
    switch (decision) {
      case 'safe': return 'bg-green-100 border-green-500 text-green-800'
      case 'caution': return 'bg-yellow-100 border-yellow-500 text-yellow-800'
      case 'risky': return 'bg-red-100 border-red-500 text-red-800'
      default: return 'bg-gray-100 border-gray-500 text-gray-800'
    }
  }

  return (
    <div className="min-h-screen bg-gray-50 py-8 px-4">
      <div className="max-w-4xl mx-auto">
        <h1 className="text-3xl font-bold mb-8">Evaluate Order</h1>

        <div className="bg-white rounded-lg shadow p-6 mb-6">
          <form onSubmit={handleEvaluate} className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Customer Name
                </label>
                <input
                  type="text"
                  required
                  value={formData.customer_name}
                  onChange={(e) => setFormData({...formData, customer_name: e.target.value})}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Product Name
                </label>
                <input
                  type="text"
                  required
                  value={formData.product_name}
                  onChange={(e) => setFormData({...formData, product_name: e.target.value})}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Selling Price (₹)
                </label>
                <input
                  type="number"
                  step="0.01"
                  required
                  value={formData.selling_price}
                  onChange={(e) => setFormData({...formData, selling_price: e.target.value})}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Cost Price (₹)
                </label>
                <input
                  type="number"
                  step="0.01"
                  required
                  value={formData.cost_price}
                  onChange={(e) => setFormData({...formData, cost_price: e.target.value})}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Quantity
                </label>
                <input
                  type="number"
                  step="0.01"
                  required
                  value={formData.quantity}
                  onChange={(e) => setFormData({...formData, quantity: e.target.value})}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Proposed Credit Days
                </label>
                <input
                  type="number"
                  required
                  value={formData.proposed_credit_days}
                  onChange={(e) => setFormData({...formData, proposed_credit_days: e.target.value})}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md"
                />
              </div>
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full bg-blue-600 text-white py-3 rounded-md font-medium hover:bg-blue-700 disabled:opacity-50"
            >
              {loading ? 'Evaluating...' : 'Evaluate Order'}
            </button>
          </form>
        </div>

        {result && (
          <div className={`rounded-lg border-2 p-6 ${getDecisionColor(result.decision)}`}>
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-2xl font-bold uppercase">{result.decision}</h2>
              <span className="text-3xl font-bold">
                ₹{result.order_value.toLocaleString('en-IN')}
              </span>
            </div>

            <div className="grid grid-cols-3 gap-4 mb-6">
              <div>
                <p className="text-sm opacity-75">Contribution Margin</p>
                <p className="text-2xl font-bold">{result.margin.margin_percentage}%</p>
              </div>
              <div>
                <p className="text-sm opacity-75">Per Unit Contribution</p>
                <p className="text-2xl font-bold">₹{result.margin.contribution_per_unit}</p>
              </div>
              <div>
                <p className="text-sm opacity-75">WC Impact</p>
                <p className="text-2xl font-bold">₹{result.working_capital.wc_increase.toLocaleString('en-IN')}</p>
              </div>
            </div>

            <div className="mb-6">
              <h3 className="font-bold mb-2">Reasons:</h3>
              <ul className="list-disc pl-5 space-y-1">
                {result.reasons.map((reason, idx) => (
                  <li key={idx}>{reason}</li>
                ))}
              </ul>
            </div>

            <div className="bg-white bg-opacity-50 p-4 rounded">
              <h3 className="font-bold mb-2">📋 Recommendation:</h3>
              <p>{result.recommendation}</p>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
