// API configuration and utility functions
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

export const api = {
  // Auth endpoints
  register: async (email, password, name, organizationName) => {
    const response = await fetch(`${API_BASE_URL}/api/auth/register`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        email,
        password,
        name,
        organization_name: organizationName
      })
    })
    const data = await response.json()
    if (!response.ok) {
      // Handle FastAPI validation errors
      if (Array.isArray(data.detail)) {
        const errorMessages = data.detail.map(err => err.msg).join(', ')
        throw new Error(errorMessages)
      }
      throw new Error(data.detail || data.message || 'Registration failed')
    }
    return data
  },

  login: async (email, password) => {
    const response = await fetch(`${API_BASE_URL}/api/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      body: new URLSearchParams({
        username: email,
        password
      })
    })
    const data = await response.json()
    if (!response.ok) {
      // Handle FastAPI validation errors
      if (Array.isArray(data.detail)) {
        const errorMessages = data.detail.map(err => err.msg).join(', ')
        throw new Error(errorMessages)
      }
      throw new Error(data.detail || data.message || 'Login failed')
    }
    return data
  },

  getCurrentUser: async (token) => {
    const response = await fetch(`${API_BASE_URL}/api/auth/me`, {
      headers: { 'Authorization': `Bearer ${token}` }
    })
    if (!response.ok) throw new Error('Failed to fetch user')
    return response.json()
  },

  // Clients endpoints
  getClients: async (token) => {
    const response = await fetch(`${API_BASE_URL}/api/clients`, {
      headers: { 'Authorization': `Bearer ${token}` }
    })
    if (!response.ok) throw new Error('Failed to fetch clients')
    return response.json()
  },

  createClient: async (token, clientData) => {
    const response = await fetch(`${API_BASE_URL}/api/clients/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      },
      body: JSON.stringify(clientData)
    })
    if (!response.ok) throw new Error('Failed to create client')
    return response.json()
  },

  // Evaluations endpoints
  evaluateOrder: async (token, evaluationData) => {
    const response = await fetch(`${API_BASE_URL}/api/evaluations/evaluate`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      },
      body: JSON.stringify(evaluationData)
    })
    if (!response.ok) throw new Error('Failed to evaluate order')
    return response.json()
  },

  // ── GST ──────────────────────────────────────────────────────────────────
  getGSTConfig: async (token, clientId) => {
    const r = await fetch(`${API_BASE_URL}/api/gst/config/${clientId}`, { headers: { Authorization: `Bearer ${token}` } })
    if (!r.ok) throw new Error('Failed to fetch GST config')
    return r.json()
  },
  saveGSTConfig: async (token, data) => {
    const r = await fetch(`${API_BASE_URL}/api/gst/config`, { method: 'POST', headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` }, body: JSON.stringify(data) })
    if (!r.ok) throw new Error('Failed to save GST config')
    return r.json()
  },
  getHSNCodes: async (token, q = '') => {
    const r = await fetch(`${API_BASE_URL}/api/gst/hsn?q=${encodeURIComponent(q)}`, { headers: { Authorization: `Bearer ${token}` } })
    if (!r.ok) throw new Error('Failed to fetch HSN codes')
    return r.json()
  },
  generateGSTR1: async (token, clientId, period) => {
    const r = await fetch(`${API_BASE_URL}/api/gst/gstr1/generate`, { method: 'POST', headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` }, body: JSON.stringify({ client_id: clientId, period }) })
    if (!r.ok) throw new Error('Failed to generate GSTR-1')
    return r.json()
  },
  getGSTR1: async (token, clientId, period) => {
    const r = await fetch(`${API_BASE_URL}/api/gst/gstr1/${clientId}/${period}`, { headers: { Authorization: `Bearer ${token}` } })
    if (!r.ok) throw new Error('Failed to fetch GSTR-1')
    return r.json()
  },
  submitGSTR1: async (token, returnId) => {
    const r = await fetch(`${API_BASE_URL}/api/gst/gstr1/${returnId}/submit`, { method: 'POST', headers: { Authorization: `Bearer ${token}` } })
    if (!r.ok) throw new Error('Failed to submit GSTR-1')
    return r.json()
  },
  generateGSTR3B: async (token, clientId, period) => {
    const r = await fetch(`${API_BASE_URL}/api/gst/gstr3b/generate`, { method: 'POST', headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` }, body: JSON.stringify({ client_id: clientId, period }) })
    if (!r.ok) throw new Error('Failed to generate GSTR-3B')
    return r.json()
  },
  uploadReconciliation: async (token, clientId, period, file) => {
    const fd = new FormData(); fd.append('file', file)
    const r = await fetch(`${API_BASE_URL}/api/gst/reconciliation/upload?client_id=${clientId}&period=${period}`, { method: 'POST', headers: { Authorization: `Bearer ${token}` }, body: fd })
    if (!r.ok) throw new Error('Failed to upload reconciliation')
    return r.json()
  },
  getReconciliation: async (token, clientId, period) => {
    const r = await fetch(`${API_BASE_URL}/api/gst/reconciliation/${clientId}/${period}`, { headers: { Authorization: `Bearer ${token}` } })
    if (!r.ok) throw new Error('Failed to fetch reconciliation')
    return r.json()
  },
  getComplianceCalendar: async (token, clientId) => {
    const r = await fetch(`${API_BASE_URL}/api/gst/compliance-calendar/${clientId}`, { headers: { Authorization: `Bearer ${token}` } })
    if (!r.ok) throw new Error('Failed to fetch compliance calendar')
    return r.json()
  },

  // ── E-Invoice ─────────────────────────────────────────────────────────────
  generateIRN: async (token, orderId) => {
    const r = await fetch(`${API_BASE_URL}/api/einvoice/generate/${orderId}`, { method: 'POST', headers: { Authorization: `Bearer ${token}` } })
    if (!r.ok) throw new Error('Failed to generate IRN')
    return r.json()
  },
  getEInvoice: async (token, orderId) => {
    const r = await fetch(`${API_BASE_URL}/api/einvoice/${orderId}`, { headers: { Authorization: `Bearer ${token}` } })
    if (!r.ok) throw new Error('Failed to fetch e-invoice')
    return r.json()
  },
  cancelIRN: async (token, orderId, reason) => {
    const r = await fetch(`${API_BASE_URL}/api/einvoice/cancel/${orderId}`, { method: 'POST', headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` }, body: JSON.stringify({ reason }) })
    if (!r.ok) throw new Error('Failed to cancel IRN')
    return r.json()
  },

  // ── E-Way Bill ────────────────────────────────────────────────────────────
  generateEWB: async (token, orderId, data) => {
    const r = await fetch(`${API_BASE_URL}/api/ewaybill/generate/${orderId}`, { method: 'POST', headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` }, body: JSON.stringify(data) })
    if (!r.ok) throw new Error('Failed to generate e-way bill')
    return r.json()
  },
  getEWB: async (token, orderId) => {
    const r = await fetch(`${API_BASE_URL}/api/ewaybill/${orderId}`, { headers: { Authorization: `Bearer ${token}` } })
    if (!r.ok) throw new Error('Failed to fetch e-way bill')
    return r.json()
  },
  cancelEWB: async (token, orderId, reason) => {
    const r = await fetch(`${API_BASE_URL}/api/ewaybill/cancel/${orderId}`, { method: 'POST', headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` }, body: JSON.stringify({ reason }) })
    if (!r.ok) throw new Error('Failed to cancel e-way bill')
    return r.json()
  },
  getTransporters: async (token) => {
    const r = await fetch(`${API_BASE_URL}/api/ewaybill/transporters`, { headers: { Authorization: `Bearer ${token}` } })
    if (!r.ok) throw new Error('Failed to fetch transporters')
    return r.json()
  },
  addTransporter: async (token, data) => {
    const r = await fetch(`${API_BASE_URL}/api/ewaybill/transporters`, { method: 'POST', headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` }, body: JSON.stringify(data) })
    if (!r.ok) throw new Error('Failed to add transporter')
    return r.json()
  },

  // ── Payments ──────────────────────────────────────────────────────────────
  createPaymentLink: async (token, orderId) => {
    const r = await fetch(`${API_BASE_URL}/api/payments/invoice-link/${orderId}`, { method: 'POST', headers: { Authorization: `Bearer ${token}` } })
    if (!r.ok) throw new Error('Failed to create payment link')
    return r.json()
  },
  getPaymentLink: async (token, orderId) => {
    const r = await fetch(`${API_BASE_URL}/api/payments/invoice-link/${orderId}`, { headers: { Authorization: `Bearer ${token}` } })
    if (!r.ok) throw new Error('Failed to fetch payment link')
    return r.json()
  },
  generateUPIQR: async (token, orderId) => {
    const r = await fetch(`${API_BASE_URL}/api/payments/upi-qr/${orderId}`, { method: 'POST', headers: { Authorization: `Bearer ${token}` } })
    if (!r.ok) throw new Error('Failed to generate UPI QR')
    return r.blob()
  },
  getPaymentAnalytics: async (token, startDate, endDate) => {
    const params = new URLSearchParams()
    if (startDate) params.set('start_date', startDate)
    if (endDate) params.set('end_date', endDate)
    const r = await fetch(`${API_BASE_URL}/api/payments/analytics?${params}`, { headers: { Authorization: `Bearer ${token}` } })
    if (!r.ok) throw new Error('Failed to fetch payment analytics')
    return r.json()
  },

  // ── Working Capital ───────────────────────────────────────────────────────
  getAgingReport: async (token, clientId) => {
    const r = await fetch(`${API_BASE_URL}/api/working-capital/aging/${clientId}`, { headers: { Authorization: `Bearer ${token}` } })
    if (!r.ok) throw new Error('Failed to fetch aging report')
    return r.json()
  },
  getCashFlowForecast: async (token, clientId, days = 30) => {
    const r = await fetch(`${API_BASE_URL}/api/working-capital/forecast/${clientId}?days=${days}`, { headers: { Authorization: `Bearer ${token}` } })
    if (!r.ok) throw new Error('Failed to fetch cash flow forecast')
    return r.json()
  },
  getWorkingCapitalCycle: async (token, clientId, days = 30) => {
    const r = await fetch(`${API_BASE_URL}/api/working-capital/cycle/${clientId}?days=${days}`, { headers: { Authorization: `Bearer ${token}` } })
    if (!r.ok) throw new Error('Failed to fetch working capital cycle')
    return r.json()
  },
  getCollectionEfficiency: async (token) => {
    const r = await fetch(`${API_BASE_URL}/api/working-capital/collection-efficiency`, { headers: { Authorization: `Bearer ${token}` } })
    if (!r.ok) throw new Error('Failed to fetch collection efficiency')
    return r.json()
  },
  getCreditLimit: async (token, clientId, orderAmount = 0) => {
    const r = await fetch(`${API_BASE_URL}/api/working-capital/credit-limit/${clientId}?order_amount=${orderAmount}`, { headers: { Authorization: `Bearer ${token}` } })
    if (!r.ok) throw new Error('Failed to fetch credit limit')
    return r.json()
  },
  setCreditLimit: async (token, clientId, amount) => {
    const r = await fetch(`${API_BASE_URL}/api/working-capital/credit-limit/${clientId}`, { method: 'POST', headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` }, body: JSON.stringify({ amount }) })
    if (!r.ok) throw new Error('Failed to set credit limit')
    return r.json()
  }
}
