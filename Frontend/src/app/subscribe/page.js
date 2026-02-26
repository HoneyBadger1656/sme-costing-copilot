'use client'
import { useState, useEffect } from 'react'

export default function SubscribePage() {
  const [selectedPlan, setSelectedPlan] = useState('growth')
  const [loading, setLoading] = useState(false)
  const [subscriptionStatus, setSubscriptionStatus] = useState(null)

  const plans = [
    {
      id: 'starter',
      name: 'Starter',
      price: '₹999',
      features: [
        'Up to 5 SME clients',
        'Core evaluation engine',
        'CSV data upload',
        'Basic reports',
        'Email support'
      ]
    },
    {
      id: 'growth',
      name: 'Growth',
      price: '₹2,499',
      popular: true,
      features: [
        'Up to 20 SME clients',
        'All Starter features',
        'Zoho Books sync',
        'Tally import',
        'Scenario comparison',
        'Priority support'
      ]
    },
    {
      id: 'pro',
      name: 'Pro',
      price: '₹4,999',
      features: [
        'Up to 50 SME clients',
        'All Growth features',
        'API access',
        'Custom rules',
        'White-label reports',
        'Dedicated success manager'
      ]
    }
  ]

  useEffect(() => {
    checkSubscriptionStatus()
  }, [])

  const checkSubscriptionStatus = async () => {
    const token = localStorage.getItem('token')
    const response = await fetch('http://localhost:8000/api/payments/subscription-status', {
      headers: { 'Authorization': `Bearer ${token}` }
    })
    const data = await response.json()
    setSubscriptionStatus(data)
  }

  const handleSubscribe = async () => {
    setLoading(true)
    const token = localStorage.getItem('token')

    try {
      const response = await fetch('http://localhost:8000/api/payments/create-subscription', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({ plan: selectedPlan })
      })

      const data = await response.json()
      
      // Redirect to Razorpay payment page
      window.location.href = data.short_url
    } catch (error) {
      console.error('Subscription failed:', error)
      alert('Failed to create subscription. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-gray-50 py-12 px-4">
      <div className="max-w-7xl mx-auto">
        <div className="text-center mb-12">
          <h1 className="text-4xl font-bold mb-4">Choose Your Plan</h1>
          <p className="text-xl text-gray-600">
            Start with 14-day free trial. Cancel anytime.
          </p>
          {subscriptionStatus?.trial_active && (
            <div className="mt-4 inline-block bg-green-100 text-green-800 px-4 py-2 rounded-full">
              ✓ Trial Active
            </div>
          )}
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          {plans.map(plan => (
            <div
              key={plan.id}
              className={`bg-white rounded-lg shadow-lg p-8 ${
                plan.popular ? 'ring-2 ring-blue-500' : ''
              } ${selectedPlan === plan.id ? 'border-2 border-blue-500' : ''}`}
              onClick={() => setSelectedPlan(plan.id)}
            >
              {plan.popular && (
                <div className="bg-blue-500 text-white text-sm font-bold py-1 px-4 rounded-full inline-block mb-4">
                  Most Popular
                </div>
              )}
              <h3 className="text-2xl font-bold mb-2">{plan.name}</h3>
              <div className="mb-6">
                <span className="text-4xl font-bold">{plan.price}</span>
                <span className="text-gray-600">/month</span>
              </div>
              <ul className="space-y-3 mb-8">
                {plan.features.map((feature, idx) => (
                  <li key={idx} className="flex items-start">
                    <svg className="w-5 h-5 text-green-500 mr-2 mt-0.5" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                    </svg>
                    {feature}
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>

        <div className="text-center mt-12">
          <button
            onClick={handleSubscribe}
            disabled={loading}
            className="bg-blue-600 text-white px-8 py-4 rounded-lg text-lg font-semibold hover:bg-blue-700 disabled:opacity-50"
          >
            {loading ? 'Processing...' : `Subscribe to ${plans.find(p => p.id === selectedPlan)?.name}`}
          </button>
        </div>
      </div>
    </div>
  )
}
