'use client'
import { useState, useEffect } from 'react'
import Link from 'next/link'

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

export default function Dashboard() {
  const [user, setUser] = useState(null)
  const [clients, setClients] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [debugInfo, setDebugInfo] = useState('')

  useEffect(() => {
    let isMounted = true
    
    const fetchData = async () => {
      try {
        setDebugInfo('Starting fetch...')
        
        if (typeof window === 'undefined') {
          setDebugInfo('Not browser')
          setLoading(false)
          return
        }

        let token = null
        try {
          token = localStorage.getItem('token')
          setDebugInfo('Token: ' + (token ? 'yes' : 'no'))
        } catch (e) {
          setDebugInfo('Storage error: ' + e.message)
          setError('Storage access failed')
          setLoading(false)
          return
        }
        
        if (!token) {
          setError('Please login first')
          setLoading(false)
          return
        }

        // Fetch user
        setDebugInfo(prev => prev + '\nFetching user...')
        let userData = null
        try {
          const res = await fetch(`${API_BASE_URL}/api/auth/me`, {
            headers: { 'Authorization': `Bearer ${token}` }
          })
          setDebugInfo(prev => prev + `\nUser status: ${res.status}`)
          if (res.ok) userData = await res.json()
        } catch (e) {
          setDebugInfo(prev => prev + '\nUser error: ' + e.message)
        }

        // Fetch clients
        setDebugInfo(prev => prev + '\nFetching clients...')
        let clientsData = []
        try {
          const res = await fetch(`${API_BASE_URL}/api/clients`, {
            headers: { 'Authorization': `Bearer ${token}` }
          })
          setDebugInfo(prev => prev + `\nClients status: ${res.status}`)
          if (res.ok) {
            const data = await res.json()
            clientsData = Array.isArray(data) ? data : []
          }
        } catch (e) {
          setDebugInfo(prev => prev + '\nClients error: ' + e.message)
        }

        if (isMounted) {
          setUser(userData)
          setClients(clientsData)
          setLoading(false)
        }
      } catch (e) {
        setDebugInfo('Critical: ' + e.message)
        setError('System error: ' + e.message)
        setLoading(false)
      }
    }

    fetchData()
    return () => { isMounted = false }
  }, [])

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div>
          <div className="text-lg mb-4">Loading...</div>
          <pre className="text-xs bg-gray-100 p-2 rounded max-w-md">{debugInfo}</pre>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="text-red-600 mb-4">{error}</div>
          <Link href="/login" className="text-blue-600 hover:underline">Go to Login</Link>
          <pre className="text-xs bg-gray-100 p-2 rounded mt-4 max-w-md">{debugInfo}</pre>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <nav className="bg-white shadow">
        <div className="max-w-7xl mx-auto px-4 py-4">
          <div className="flex justify-between">
            <h1 className="text-xl font-bold">SME Costing Copilot</h1>
            <span className="text-gray-600">Welcome, {user?.name || user?.full_name || 'User'}</span>
          </div>
        </div>
      </nav>

      <main className="max-w-7xl mx-auto py-6 px-4">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
          <div className="bg-white p-6 rounded-lg shadow">
            <h3 className="text-gray-500 text-sm">Total Clients</h3>
            <p className="text-3xl font-bold mt-2">{clients?.length || 0}</p>
          </div>
          <div className="bg-white p-6 rounded-lg shadow">
            <h3 className="text-gray-500 text-sm">Evaluations</h3>
            <p className="text-3xl font-bold mt-2">0</p>
          </div>
          <div className="bg-white p-6 rounded-lg shadow">
            <h3 className="text-gray-500 text-sm">Margin</h3>
            <p className="text-3xl font-bold mt-2">--</p>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow">
          <div className="px-6 py-4 border-b flex justify-between items-center">
            <h2 className="text-xl font-semibold">Your Clients</h2>
            <Link href="/clients/new" className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700">Add Client</Link>
          </div>
          <div className="p-6">
            {(!clients || clients.length === 0) ? (
              <p className="text-gray-500">No clients yet. <Link href="/clients/new" className="text-blue-600 hover:underline">Add your first client →</Link></p>
            ) : (
              <div className="space-y-4">
                {clients.map((client, idx) => (
                  <div key={client?.id || idx} className="border rounded-lg p-4">
                    <div className="flex justify-between items-start">
                      <div>
                        <h3 className="font-semibold">{client?.business_name || client?.name || 'Unnamed'}</h3>
                        <p className="text-sm text-gray-600">{client?.industry || 'No industry'}</p>
                      </div>
                      <Link href={`/evaluate?client=${client?.id}`} className="text-blue-600 hover:text-blue-800 text-sm">Evaluate →</Link>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </main>
    </div>
  )
}
