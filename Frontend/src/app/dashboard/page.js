'use client'
import { useState, useEffect, useRef } from 'react'
import Link from 'next/link'
import AppLayout from '../../components/layout/AppLayout'
import PageHeader from '../../components/layout/PageHeader'
import Card, { CardHeader, CardTitle, CardContent } from '../../components/ui/Card'
import Button from '../../components/ui/Button'

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

export default function Dashboard() {
  const [user, setUser] = useState(null)
  const [clients, setClients] = useState([])
  const [stats, setStats] = useState({ 
    evaluations: 0, 
    margin: '--', 
    totalOrders: 0, 
    outstandingReceivables: 0, 
    cashFlowStatus: 'neutral',
    recentActivity: []
  })
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [showUploadModal, setShowUploadModal] = useState(false)
  const [uploadType, setUploadType] = useState("orders")
  const [uploadLoading, setUploadLoading] = useState(false)
  const fileInputRef = useRef(null)

  const handleFileUpload = async (file, type) => {
    if (!file) return;

    const formData = new FormData();
    formData.append("file", file);
    
    const token = localStorage.getItem("token");
    const clientId = clients.length > 0 ? clients[0].id : 1;
    
    setUploadLoading(true);
    
    try {
      const endpoint = type === "orders" ? "import/orders" : 
                     type === "products" ? "import/products" : 
                     "import/financial";
      
      const response = await fetch(`${API_BASE_URL}/api/integrations/${endpoint}?client_id=${clientId}`, {
        method: "POST",
        headers: {
          "Authorization": `Bearer ${token}`
        },
        body: formData
      });

      const result = await response.json();
      
      if (result.success) {
        alert(`✅ Upload successful! ${result.records_imported || 0} records imported.`);
        setShowUploadModal(false);
        // Refresh dashboard data
        window.location.reload();
      } else {
        alert(`❌ Upload failed: ${result.message || "Unknown error"}`);
      }
    } catch (error) {
      alert(`❌ Upload failed: ${error.message}`);
    } finally {
      setUploadLoading(false);
    }
  };

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

        // Fetch comprehensive stats from first client if available
        let statsData = { 
          evaluations: 0, 
          margin: '--', 
          totalOrders: 0, 
          outstandingReceivables: 0, 
          cashFlowStatus: 'neutral',
          recentActivity: []
        }
        
        if (clientsData.length > 0) {
          const firstClientId = clientsData[0]?.id
          
          try {
            // Fetch profitability data
            const profRes = await fetch(`${API_BASE_URL}/api/financials/profitability?client_id=${firstClientId}&days=30`, {
              headers: { 'Authorization': `Bearer ${token}` }
            })
            if (profRes.ok) {
              const profData = await profRes.json()
              statsData.evaluations = profData?.summary?.order_count || 0
              statsData.totalOrders = profData?.summary?.total_orders || 0
              const marginPct = profData?.summary?.margin_percentage
              statsData.margin = (marginPct != null && marginPct !== 0) ? `${marginPct.toFixed(1)}%` : '--'
            }
          } catch (e) {
            console.error('Profitability fetch error:', e)
          }

          try {
            // Fetch receivables data
            const recRes = await fetch(`${API_BASE_URL}/api/financials/receivables?client_id=${firstClientId}`, {
              headers: { 'Authorization': `Bearer ${token}` }
            })
            if (recRes.ok) {
              const recData = await recRes.json()
              statsData.outstandingReceivables = recData?.summary?.total_outstanding || 0
            }
          } catch (e) {
            console.error('Receivables fetch error:', e)
          }

          try {
            // Fetch cash flow forecast
            const cashRes = await fetch(`${API_BASE_URL}/api/financials/cash-flow-forecast?client_id=${firstClientId}&days=30`, {
              headers: { 'Authorization': `Bearer ${token}` }
            })
            if (cashRes.ok) {
              const cashData = await cashRes.json()
              const netCashFlow = cashData?.forecast?.net_cash_flow || 0
              statsData.cashFlowStatus = netCashFlow > 0 ? 'positive' : netCashFlow < 0 ? 'negative' : 'neutral'
            }
          } catch (e) {
            console.error('Cash flow fetch error:', e)
          }

          // Mock recent activity (in a real app, this would come from an API)
          statsData.recentActivity = [
            { id: 1, type: 'order_evaluation', description: 'Order evaluated for ABC Corp', time: '2 hours ago', status: 'success' },
            { id: 2, type: 'scenario_created', description: 'New scenario: "Increase raw material cost"', time: '4 hours ago', status: 'info' },
            { id: 3, type: 'data_import', description: 'Imported 25 products from Excel', time: '1 day ago', status: 'success' },
            { id: 4, type: 'client_added', description: 'New client: XYZ Manufacturing', time: '2 days ago', status: 'info' },
            { id: 5, type: 'tally_sync', description: 'Synced ledgers from Tally', time: '3 days ago', status: 'success' }
          ]
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
          <div className="flex space-x-3">
            <Button 
              variant="outline" 
              onClick={() => setShowUploadModal(true)}
            >
              📁 Import Data
            </Button>
            <Link href="/clients/new">
              <Button>Add Client</Button>
            </Link>
          </div>
        }
      />

      <div className="p-4 sm:p-6">
        {/* Stats Cards */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4 sm:gap-6 mb-6 sm:mb-8">
          <Card>
            <CardContent className="text-center p-4">
              <div className="text-2xl sm:text-3xl font-bold text-blue-600">{clients?.length || 0}</div>
              <div className="text-xs sm:text-sm text-gray-500 mt-1">Total Clients</div>
            </CardContent>
          </Card>
          
          <Card>
            <CardContent className="text-center p-4">
              <div className="text-2xl sm:text-3xl font-bold text-green-600">{stats.totalOrders}</div>
              <div className="text-xs sm:text-sm text-gray-500 mt-1">Total Orders</div>
            </CardContent>
          </Card>
          
          <Card>
            <CardContent className="text-center p-4">
              <div className="text-2xl sm:text-3xl font-bold text-purple-600">{stats.margin}</div>
              <div className="text-xs sm:text-sm text-gray-500 mt-1">Average Margin</div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="text-center p-4">
              <div className="text-xl sm:text-2xl lg:text-3xl font-bold text-orange-600">
                ₹{stats.outstandingReceivables.toLocaleString('en-IN')}
              </div>
              <div className="text-xs sm:text-sm text-gray-500 mt-1">Outstanding Receivables</div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="text-center p-4">
              <div className={`text-2xl sm:text-3xl font-bold ${
                stats.cashFlowStatus === 'positive' ? 'text-green-600' :
                stats.cashFlowStatus === 'negative' ? 'text-red-600' :
                'text-gray-600'
              }`}>
                {stats.cashFlowStatus === 'positive' ? '📈' :
                 stats.cashFlowStatus === 'negative' ? '📉' : '➖'}
              </div>
              <div className="text-xs sm:text-sm text-gray-500 mt-1">Cash Flow Status</div>
            </CardContent>
          </Card>
        </div>

        {/* Main Content Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-4 sm:gap-6">
          
          {/* Clients Section */}
          <div className="lg:col-span-2">
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
                    {clients.slice(0, 5).map((client, idx) => (
                      <div key={client?.id || idx} className="border rounded-lg p-3 sm:p-4 hover:bg-gray-50 transition-colors">
                        <div className="flex flex-col sm:flex-row sm:justify-between sm:items-start space-y-3 sm:space-y-0">
                          <div className="flex-1">
                            <h3 className="font-semibold text-gray-900">{client?.business_name || client?.name || 'Unnamed'}</h3>
                            <p className="text-sm text-gray-600">{client?.industry || 'No industry specified'}</p>
                            {client?.contact_email && (
                              <p className="text-xs text-gray-500 mt-1">{client?.contact_email}</p>
                            )}
                          </div>
                          <div className="flex space-x-2">
                            <Link href={`/evaluate?client=${client?.id}`}>
                              <Button variant="outline" size="sm" className="w-full sm:w-auto">Evaluate Order</Button>
                            </Link>
                          </div>
                        </div>
                      </div>
                    ))}
                    {clients.length > 5 && (
                      <div className="text-center pt-4">
                        <Link href="/clients">
                          <Button variant="outline" size="sm">
                            View All {clients.length} Clients
                          </Button>
                        </Link>
                      </div>
                    )}
                  </div>
                )}
              </CardContent>
            </Card>
          </div>

          {/* Recent Activity Section */}
          <div className="lg:col-span-1">
            <Card>
              <CardHeader>
                <CardTitle>Recent Activity</CardTitle>
              </CardHeader>
              <CardContent>
                {stats.recentActivity.length === 0 ? (
                  <div className="text-center py-8 text-gray-500">
                    <div className="text-4xl mb-4">📋</div>
                    <p>No recent activity</p>
                  </div>
                ) : (
                  <div className="space-y-4">
                    {stats.recentActivity.map((activity) => (
                      <div key={activity.id} className="flex items-start space-x-3">
                        <div className={`w-2 h-2 rounded-full mt-2 flex-shrink-0 ${
                          activity.status === 'success' ? 'bg-green-500' :
                          activity.status === 'info' ? 'bg-blue-500' :
                          'bg-gray-500'
                        }`}></div>
                        <div className="flex-1 min-w-0">
                          <p className="text-sm text-gray-900">{activity.description}</p>
                          <p className="text-xs text-gray-500">{activity.time}</p>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>

            {/* Quick Actions */}
            <Card className="mt-4 sm:mt-6">
              <CardHeader>
                <CardTitle>Quick Actions</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-2 sm:grid-cols-1 gap-2 sm:gap-3">
                  <Link href="/evaluate" className="block">
                    <Button variant="outline" className="w-full justify-start text-sm">
                      📈 Evaluate Order
                    </Button>
                  </Link>
                  <Link href="/scenarios" className="block">
                    <Button variant="outline" className="w-full justify-start text-sm">
                      🔄 Create Scenario
                    </Button>
                  </Link>
                  <Link href="/assistant" className="block">
                    <Button variant="outline" className="w-full justify-start text-sm">
                      🤖 Ask AI Assistant
                    </Button>
                  </Link>
                  <Button 
                    variant="outline" 
                    className="w-full justify-start text-sm"
                    onClick={() => setShowUploadModal(true)}
                  >
                    📁 Import Data
                  </Button>
                </div>
              </CardContent>
            </Card>
          </div>
        </div>
      </div>

      {/* Upload Modal */}
      {showUploadModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-md mx-4">
            <div className="flex justify-between items-center mb-4">
              <h3 className="text-lg font-semibold">Quick Data Import</h3>
              <button
                onClick={() => setShowUploadModal(false)}
                className="text-gray-400 hover:text-gray-600"
              >
                ✕
              </button>
            </div>
            
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Upload Type
                </label>
                <select
                  value={uploadType}
                  onChange={(e) => setUploadType(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                >
                  <option value="orders">Orders</option>
                  <option value="products">Products</option>
                  <option value="financial">Financial Data</option>
                </select>
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Select File
                </label>
                <input
                  ref={fileInputRef}
                  type="file"
                  accept=".xlsx,.xls,.csv"
                  onChange={(e) => e.target.files[0] && handleFileUpload(e.target.files[0], uploadType)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  disabled={uploadLoading}
                />
              </div>
              
              <div className="text-sm text-gray-500">
                Supports .xlsx, .xls, .csv files (max 10MB)
              </div>
              
              <div className="flex justify-between pt-4">
                <Button
                  variant="outline"
                  onClick={() => setShowUploadModal(false)}
                  disabled={uploadLoading}
                >
                  Cancel
                </Button>
                <Link href="/integrations">
                  <Button variant="outline">
                    Full Upload Options
                  </Button>
                </Link>
              </div>
            </div>
            
            {uploadLoading && (
              <div className="absolute inset-0 bg-white bg-opacity-75 flex items-center justify-center rounded-lg">
                <div className="text-center">
                  <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto mb-2"></div>
                  <div className="text-gray-600">Uploading...</div>
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </AppLayout>
  )
}
