'use client'
import { useState, useEffect } from 'react'
import AppLayout from '../../../components/layout/AppLayout'
import { api } from '../../../lib/api'

const TABS = ['B2B', 'B2CS', 'B2CL', 'Exports', 'Nil-Rated']

export default function GSTR1Page() {
  const [clients, setClients] = useState([])
  const [clientId, setClientId] = useState(null)
  const [period, setPeriod] = useState(() => {
    const d = new Date(); d.setMonth(d.getMonth() - 1)
    return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}`
  })
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(false)
  const [generating, setGenerating] = useState(false)
  const [submitting, setSubmitting] = useState(false)
  const [activeTab, setActiveTab] = useState('B2B')
  const [error, setError] = useState(null)
  const [msg, setMsg] = useState(null)

  const token = typeof window !== 'undefined' ? localStorage.getItem('token') : null

  useEffect(() => {
    if (!token) return
    api.getClients(token).then(d => { setClients(d); if (d.length) setClientId(d[0].id) }).catch(() => {})
  }, [])

  const fetchGSTR1 = async () => {
    if (!clientId) return
    setLoading(true); setError(null)
    try {
      const d = await api.getGSTR1(token, clientId, period)
      setData(d)
    } catch (e) {
      setData(null)
    } finally { setLoading(false) }
  }

  useEffect(() => { fetchGSTR1() }, [clientId, period])

  const handleGenerate = async () => {
    setGenerating(true); setError(null); setMsg(null)
    try {
      const d = await api.generateGSTR1(token, clientId, period)
      setData(d); setMsg('GSTR-1 generated successfully')
    } catch (e) { setError(e.message) }
    finally { setGenerating(false) }
  }

  const handleSubmit = async () => {
    if (!data) return
    setSubmitting(true); setError(null); setMsg(null)
    try {
      await api.submitGSTR1(token, data.id)
      setMsg('Submitted for review'); fetchGSTR1()
    } catch (e) { setError(e.message) }
    finally { setSubmitting(false) }
  }

  const handleExportJSON = () => {
    if (!data) return
    const blob = new Blob([JSON.stringify(data.return_data, null, 2)], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a'); a.href = url; a.download = `GSTR1_${period}.json`; a.click()
  }

  const returnData = data?.return_data || {}
  const tabData = {
    'B2B': returnData.b2b || [],
    'B2CS': returnData.b2cs || [],
    'B2CL': returnData.b2cl || [],
    'Exports': returnData.exports || [],
    'Nil-Rated': returnData.nil_rated || [],
  }
  const flagged = returnData.flagged_invoices || []

  return (
    <AppLayout>
      <div className="p-6 max-w-6xl mx-auto">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">GSTR-1</h1>
            <p className="text-gray-500 text-sm mt-1">Outward supplies return</p>
          </div>
          <div className="flex gap-3">
            <select className="border rounded-lg px-3 py-2 text-sm" value={clientId || ''} onChange={e => setClientId(Number(e.target.value))}>
              {clients.map(c => <option key={c.id} value={c.id}>{c.name}</option>)}
            </select>
            <input type="month" className="border rounded-lg px-3 py-2 text-sm" value={period} onChange={e => setPeriod(e.target.value)} />
          </div>
        </div>

        {error && <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">{error}</div>}
        {msg && <div className="mb-4 p-3 bg-green-50 border border-green-200 rounded-lg text-green-700 text-sm">{msg}</div>}

        {/* Actions */}
        <div className="flex gap-3 mb-6">
          <button onClick={handleGenerate} disabled={generating || !clientId} className="px-4 py-2 bg-blue-600 text-white rounded-lg text-sm font-medium hover:bg-blue-700 disabled:opacity-50">
            {generating ? 'Generating...' : 'Generate GSTR-1'}
          </button>
          {data && data.status === 'draft' && (
            <button onClick={handleSubmit} disabled={submitting} className="px-4 py-2 bg-green-600 text-white rounded-lg text-sm font-medium hover:bg-green-700 disabled:opacity-50">
              {submitting ? 'Submitting...' : 'Submit for Review'}
            </button>
          )}
          {data && (
            <button onClick={handleExportJSON} className="px-4 py-2 border border-gray-300 text-gray-700 rounded-lg text-sm font-medium hover:bg-gray-50">
              Export JSON
            </button>
          )}
          {data && (
            <span className={`px-3 py-2 rounded-lg text-sm font-medium ${
              data.status === 'filed' ? 'bg-green-100 text-green-800' :
              data.status === 'under_review' ? 'bg-blue-100 text-blue-800' :
              'bg-yellow-100 text-yellow-800'
            }`}>
              Status: {data.status}
            </span>
          )}
        </div>

        {/* Flagged invoices */}
        {flagged.length > 0 && (
          <div className="mb-6 bg-yellow-50 border border-yellow-200 rounded-xl p-4">
            <h3 className="font-semibold text-yellow-800 mb-2">⚠ {flagged.length} Flagged Invoice(s)</h3>
            <p className="text-sm text-yellow-700 mb-2">These invoices were excluded due to missing HSN codes or buyer GSTIN:</p>
            <ul className="text-sm text-yellow-700 space-y-1">
              {flagged.map((f, i) => <li key={i}>• Order #{f.order_number}: {f.reason}</li>)}
            </ul>
          </div>
        )}

        {/* Tax summary */}
        {data && (
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
            {[
              { label: 'Taxable Value', value: returnData.summary?.total_taxable_value },
              { label: 'CGST', value: returnData.summary?.total_cgst },
              { label: 'SGST', value: returnData.summary?.total_sgst },
              { label: 'IGST', value: returnData.summary?.total_igst },
            ].map(({ label, value }) => (
              <div key={label} className="bg-white border rounded-xl p-4">
                <div className="text-sm text-gray-500">{label}</div>
                <div className="text-xl font-bold text-gray-900 mt-1">₹{(value || 0).toLocaleString('en-IN', { maximumFractionDigits: 0 })}</div>
              </div>
            ))}
          </div>
        )}

        {/* Tabs */}
        {data && (
          <div className="bg-white border rounded-xl">
            <div className="flex border-b">
              {TABS.map(tab => (
                <button key={tab} onClick={() => setActiveTab(tab)}
                  className={`px-4 py-3 text-sm font-medium border-b-2 transition-colors ${activeTab === tab ? 'border-blue-600 text-blue-600' : 'border-transparent text-gray-500 hover:text-gray-700'}`}>
                  {tab} ({tabData[tab].length})
                </button>
              ))}
            </div>
            <div className="p-4">
              {tabData[activeTab].length === 0 ? (
                <div className="text-center text-gray-400 py-8">No {activeTab} invoices for this period</div>
              ) : (
                <table className="w-full text-sm">
                  <thead className="bg-gray-50">
                    <tr>
                      {['Invoice No', 'Date', 'Party', 'Taxable', 'GST', 'Total'].map(h => (
                        <th key={h} className="text-left px-3 py-2 text-gray-600 font-medium">{h}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {tabData[activeTab].map((inv, i) => (
                      <tr key={i} className="border-t hover:bg-gray-50">
                        <td className="px-3 py-2 font-mono text-xs">{inv.invoice_number || inv.order_number}</td>
                        <td className="px-3 py-2 text-gray-600">{inv.invoice_date || inv.order_date}</td>
                        <td className="px-3 py-2">{inv.buyer_name || inv.customer_name}</td>
                        <td className="px-3 py-2">₹{(inv.taxable_value || 0).toLocaleString('en-IN', { maximumFractionDigits: 0 })}</td>
                        <td className="px-3 py-2">₹{((inv.cgst || 0) + (inv.sgst || 0) + (inv.igst || 0)).toLocaleString('en-IN', { maximumFractionDigits: 0 })}</td>
                        <td className="px-3 py-2 font-medium">₹{(inv.total_value || 0).toLocaleString('en-IN', { maximumFractionDigits: 0 })}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}
            </div>
          </div>
        )}

        {!data && !loading && (
          <div className="bg-white border rounded-xl p-12 text-center text-gray-400">
            No GSTR-1 found for {period}. Click "Generate GSTR-1" to create one.
          </div>
        )}
      </div>
    </AppLayout>
  )
}
