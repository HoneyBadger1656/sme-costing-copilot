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
    if (!response.ok) throw new Error('Login failed')
    return response.json()
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
  }
}
