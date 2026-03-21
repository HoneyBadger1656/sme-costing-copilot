'use client'
import { useState, useEffect } from 'react'
import AppLayout from '../../components/layout/AppLayout'
import { api } from '../../lib/api'

const STATUS_COLORS = {
  draft: 'bg-yellow-100 text-yellow-800',
  under_review: 'bg-blue-100 text-blue-800',
  filed: 'bg-green-100 text-green-800',
  overdue: 'bg-red-100 text-red-800',
}

export default function GSTPage() {
  const [clients, setClients] = useState([])
  const [selectedClient, setSelectedClient] = useState(null)
  const [calendar, setCalendar] = useState([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [statusFilter, setStatusFilter] = useState('all')

  const token = typeof window !== 'undefined' ? localStorage.getItem('token') : null

  useEffect(() => {
    if (!token) return
    api.getClients(token).then(data => {
      setClients(data)
      if (data.length > 0) setSelectedClient(data[0].id)
    }).catch(() => {})
  }, [])

  useEffect(() => {
    if (!selectedClient || !token) return
    setLoading(true)
    api.getComplianceCalendar(token, selectedClient)
      .then(data => setCalendar(data.calendar || []))
      .catch(e => setError(e.message))
      .finally(() => setLoading(false))
  }, [selectedClient])

  const filtered = statusFilter === 'all' ? calendar : calendar.filter(c => c.status === statusFilter)

  const counts = calendar.reduce((acc, c) => {
    acc[c.status] = (acc[c.status] || 0) + 1
    return acc
  }, {})

  return (
    <AppLayout>
      <div className="p-6 max-w-6xl mx-auto">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">GST Compliance</h1>
            <p className="text-gray-500 text-sm mt-1">Manage GSTR-1, GSTR-3B, and ITC reconciliation</p>
          </div>
          <select
            className="border rounded-lg px-3 py-2 text-sm"
            value={selectedClient || ''}
            onChange={e => setSelectedClient(Number(e.target.value))}
          >
            {clients.map(c => <option key={c.id} value={c.id}>{c.name}</option>)}
          </select>
        </div>

        {/* Summary cards */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
          {[
            { label: 'Draft', key: 'draft', color: 'yellow' },
            { label: 'Under Review', key: 'under_review', color: 'blue' },
            { label: 'Filed', key: 'filed', color: 'green' },
            { label: 'Overdue', key: 'overdue', color: 'red' },
          ].map(({ label, key, color }) => (
            <div key={key} className={`bg-${color}-50 border border-${color}-200 rounded-xl p-4`}>
              <div className={`text-2xl font-bold text-${color}-700`}>{counts[key] || 0}</div>
              <div className={`text-sm text-${color}-600`}>{label}</div>
            </div>
          ))}
        </div>

        {/* Quick links */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
          <a href="/gst/gstr1" className="block bg-white border rounded-xl p-4 hover:shadow-md transition-shadow">
            <div className="text-lg font-semibold text-gray-800">GSTR-1</div>
            <div className="text-sm text-gray-500 mt-1">Outward supplies return</div>
            <div className="mt-3 text-blue-600 text-sm font-medium">Generate →</div>
          </a>
          <a href="/gst/reconciliation" className="block bg-white border rounded-xl p-4 hover:shadow-md transition-shadow">
            <div className="text-lg font-semibold text-gray-800">ITC Reconciliation</div>
            <div className="text-sm text-gray-500 mt-1">Match GSTR-2A/2B with books</div>
            <div className="mt-3 text-blue-600 text-sm font-medium">Reconcile →</div>
          </a>
          <div className="bg-white border rounded-xl p-4">
            <div className="text-lg font-semibold text-gray-800">GSTR-3B</div>
            <div className="text-sm text-gray-500 mt-1">Summary return</div>
            <div className="mt-3 text-gray-400 text-sm">Requires GSTR-1 first</div>
          </div>
        </div>

        {/* Compliance calendar */}
        <div className="bg-white border rounded-xl">
          <div className="flex items-center justify-between p-4 border-b">
            <h2 className="font-semibold text-gray-800">Compliance Calendar</h2>
            <select
              className="border rounded px-2 py-1 text-sm"
              value={statusFilter}
              onChange={e => setStatusFilter(e.target.value)}
            >
              <option value="all">All</option>
              <option value="draft">Draft</option>
              <option value="under_review">Under Review</option>
              <option value="filed">Filed</option>
              <option value="overdue">Overdue</option>
            </select>
          </div>
          {loading ? (
            <div className="p-8 text-center text-gray-400">Loading...</div>
          ) : error ? (
            <div className="p-8 text-center text-red-500">{error}</div>
          ) : filtered.length === 0 ? (
            <div className="p-8 text-center text-gray-400">No filings found. Select a client with GST configuration.</div>
          ) : (
            <table className="w-full text-sm">
              <thead className="bg-gray-50">
                <tr>
                  {['Return Type', 'Period', 'Due Date', 'Status'].map(h => (
                    <th key={h} className="text-left px-4 py-3 text-gray-600 font-medium">{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {filtered.map((item, i) => (
                  <tr key={i} className="border-t hover:bg-gray-50">
                    <td className="px-4 py-3 font-medium">{item.return_type}</td>
                    <td className="px-4 py-3 text-gray-600">{item.period}</td>
                    <td className="px-4 py-3 text-gray-600">{item.due_date}</td>
                    <td className="px-4 py-3">
                      <span className={`px-2 py-1 rounded-full text-xs font-medium ${STATUS_COLORS[item.status] || 'bg-gray-100 text-gray-700'}`}>
                        {item.status}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      </div>
    </AppLayout>
  )
}
