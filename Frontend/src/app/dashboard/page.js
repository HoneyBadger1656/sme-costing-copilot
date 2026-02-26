'use client'
import { useState, useEffect } from 'react'
import Link from 'next/link'
import { api } from '@/lib/api'

export default function Dashboard() {
  const [user, setUser] = useState(null)
  const [clients, setClients] = useState([])

  useEffect(() => {
    const fetchData = async () => {
      const token = localStorage.getItem('token')
      
      try {
        const userData = await api.getCurrentUser(token)
        setUser(userData)
      } catch (error) {
        console.error('Failed to fetch user data:', error)
      }

      try {
        const clientsData = await api.getClients(token)
        setClients(clientsData)
      } catch (error) {
        console.error('Failed to fetch clients:', error)
      }
    }

    fetchData()
  }, [])

  return (
    <div className="min-h-screen bg-gray-50">
      <nav className="bg-white shadow">
        <div className="max-w-7xl mx-auto px-4 py-4">
          <div className="flex justify-between">
            <h1 className="text-xl font-bold">SME Costing Copilot</h1>
            <span className="text-gray-600">Welcome, {user?.name}</span>
          </div>
        </div>
      </nav>

      <main className="max-w-7xl mx-auto py-6 px-4">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
          <div className="bg-white p-6 rounded-lg shadow">
            <h3 className="text-gray-500 text-sm">Total Clients</h3>
            <p className="text-3xl font-bold mt-2">{clients.length}</p>
          </div>
          <div className="bg-white p-6 rounded-lg shadow">
            <h3 className="text-gray-500 text-sm">Evaluations This Month</h3>
            <p className="text-3xl font-bold mt-2">12</p>
          </div>
          <div className="bg-white p-6 rounded-lg shadow">
            <h3 className="text-gray-500 text-sm">Average Margin</h3>
            <p className="text-3xl font-bold mt-2">22.5%</p>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow">
          <div className="px-6 py-4 border-b flex justify-between items-center">
            <h2 className="text-xl font-semibold">Your Clients</h2>
            <Link 
              href="/clients/new"
              className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700"
            >
              Add Client
            </Link>
          </div>
          <div className="p-6">
            {clients.length === 0 ? (
              <p className="text-gray-500">No clients yet. Add your first client to get started.</p>
            ) : (
              <div className="space-y-4">
                {clients.map(client => (
                  <div key={client.id} className="border rounded-lg p-4">
                    <div className="flex justify-between items-start">
                      <div>
                        <h3 className="font-semibold">{client.business_name}</h3>
                        <p className="text-sm text-gray-600">{client.industry}</p>
                      </div>
                      <Link
                        href={`/evaluate?client=${client.id}`}
                        className="text-blue-600 hover:text-blue-800"
                      >
                        Evaluate Order →
                      </Link>
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
