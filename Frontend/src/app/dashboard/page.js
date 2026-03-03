'use client'
import { useState, useEffect } from 'react'
import Link from 'next/link'
import AppLayout from '../components/layout/AppLayout'
import PageHeader from '../components/layout/PageHeader'
import Card, { CardHeader, CardTitle, CardContent } from '../components/ui/Card'
import Button from '../components/ui/Button'

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

export default function Dashboard() {
  const [user, setUser] = useState(null)
  const [clients, setClients] = useState([])
  const [stats, setStats] = useState({ evaluations: 0, margin: '--' })
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    let isMounted = true

    const fetchData = async () => {
      try {
        if (typeof window === 'undefined') {
          setLoading(false)
          return
        }

        let token = null
        try {
          token = localStorage.getItem('token')
        } catch (e) {
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
        let userData = null
        try {
          const res = await fetch(`${API_BASE_URL}/api/auth/me`, {
            headers: { 'Authorization': `Bearer ${token}` }
          })
          if (res.ok) userData = await res.json()
        } catch (e) {
          console.error('User fetch error:', e)
        }

        // Fetch clients
        let clientsData = []
        try {
          const res = await fetch(`${API_BASE_URL}/api/clients`, {
            headers: { 'Authorization': `Bearer ${token}` }
          })
          if (res.ok) {
            const data = await res.json()
            clientsData = Array.isArray(data) ? data : []
          }
        } catch (e) {
          console.error('Clients fetch error:', e)
        }

        // Fetch stats from first client if available
        let statsData = { evaluations: 0, margin: '--' }
        if (clientsData.length > 0) {
          try {
            const firstClientId = clientsData[0]?.id
            const res = await fetch(`${API_BASE_URL}/api/financials/profitability?client_id=${firstClientId}&days=30`, {
              headers: { 'Authorization': `Bearer ${token}` }
            })
            if (res.ok) {
              const profData = await res.json()
              statsData.evaluations = profData?.summary?.order_count || 0
              const marginPct = profData?.summary?.margin_percentage
              statsData.margin = (marginPct != null && marginPct !== 0) ? `${marginPct}%` : '--'
            }
          } catch (e) {
            console.error('Stats fetch error:', e)
          }
        }

        if (isMounted) {
          setUser(userData)
          setClients(clientsData)
          setStats(statsData)
          setLoading(false)
        }
      } catch (e) {
        setError('System error: ' + e.message)
        setLoading(false)
      }
    }

    fetchData()
    return () => { isMounted = false }
  }, [])

  if (loading) {
    return (
      <AppLayout>
        <div className="flex items-center justify-center h-64">
          <div className="text-center">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto mb-4"></div>
            <div className="text-gray-600">Loading dashboard...</div>
          </div>
        </div>
      </AppLayout>
    )
  }

  if (error) {
    return (
      <AppLayout>
        <div className="flex items-center justify-center h-64">
          <div className="text-center">
            <div className="text-red-600 mb-4">{error}</div>
            <Link href="/">
              <Button>Go to Login</Button>
            </Link>
          </div>
        </div>
      </AppLayout>
    )
  }

  return (
    <AppLayout>
      <PageHeader
        title="Dashboard"
        description={`Welcome back, ${user?.name || user?.full_name || 'User'}`}
        icon="🏠"
        actions={
          <Link href="/clients/new">
            <Button>Add Client</Button>
          </Link>
        }
      />

      <div className="p-6">
        {/* Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
          <Card>
            <CardContent className="text-center">
              <div className="text-3xl font-bold text-blue-600">{clients?.length || 0}</div>
              <div className="text-sm text-gray-500 mt-1">Total Clients</div>
            </CardContent>
          </Card>
          
          <Card>
            <CardContent className="text-center">
              <div className="text-3xl font-bold text-green-600">{stats.evaluations}</div>
              <div className="text-sm text-gray-500 mt-1">Evaluations</div>
            </CardContent>
          </Card>
          
          <Card>
            <CardContent className="text-center">
              <div className="text-3xl font-bold text-purple-600">{stats.margin}</div>
              <div className="text-sm text-gray-500 mt-1">Average Margin</div>
            </CardContent>
          </Card>
        </div>

        {/* Clients Section */}
        <Card>
          <CardHeader>
            <div className="flex justify-between items-center">
              <CardTitle>Your Clients</CardTitle>
              <Link href="/clients/new">
                <Button size="sm">Add Client</Button>
              </Link>
            </div>
          </CardHeader>
          
          <CardContent>
            {(!clients || clients.length === 0) ? (
              <div className="text-center py-8">
                <div className="text-6xl mb-4">👥</div>
                <h3 className="text-lg font-medium text-gray-900 mb-2">No clients yet</h3>
                <p className="text-gray-500 mb-4">Add your first client to get started with costing and analysis.</p>
                <Link href="/clients/new">
                  <Button>Add Your First Client</Button>
                </Link>
              </div>
            ) : (
              <div className="space-y-4">
                {clients.map((client, idx) => (
                  <div key={client?.id || idx} className="border rounded-lg p-4 hover:bg-gray-50 transition-colors">
                    <div className="flex justify-between items-start">
                      <div>
                        <h3 className="font-semibold text-gray-900">{client?.business_name || client?.name || 'Unnamed'}</h3>
                        <p className="text-sm text-gray-600">{client?.industry || 'No industry specified'}</p>
                        {client?.contact_email && (
                          <p className="text-xs text-gray-500 mt-1">{client?.contact_email}</p>
                        )}
                      </div>
                      <div className="flex space-x-2">
                        <Link href={`/evaluate?client=${client?.id}`}>
                          <Button variant="outline" size="sm">Evaluate Order</Button>
                        </Link>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </AppLayout>
  )
}
