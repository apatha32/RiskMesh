import React, { useState, useEffect } from 'react'
import { Transaction, AnalyticsData } from './types'
import { apiClient } from './api/client'
import Header from './components/Header'
import TransactionFeed from './components/TransactionFeed'
import AnalyticsDashboard from './components/AnalyticsDashboard'
import ClusteringVisualization from './components/ClusteringVisualization'
import UserProfiles from './components/UserProfiles'

type DashboardTab = 'transactions' | 'analytics' | 'clustering' | 'users'

function App() {
  const [activeTab, setActiveTab] = useState<DashboardTab>('transactions')
  const [transactions, setTransactions] = useState<Transaction[]>([])
  const [analytics, setAnalytics] = useState<AnalyticsData | null>(null)
  const [loading, setLoading] = useState(false)
  const [demoMode, setDemoMode] = useState(true)
  const [selectedTransaction, setSelectedTransaction] = useState<Transaction | null>(null)

  useEffect(() => {
    loadData()
    const interval = setInterval(loadData, 5000) // Refresh every 5 seconds
    return () => clearInterval(interval)
  }, [demoMode])

  const loadData = async () => {
    setLoading(true)
    try {
      const [txns, analyticsData] = await Promise.all([
        apiClient.getTransactions(50),
        apiClient.getAnalytics()
      ])
      setTransactions(txns)
      setAnalytics(analyticsData)
    } catch (error) {
      console.error('Failed to load data:', error)
    }
    setLoading(false)
  }

  const toggleDemoMode = () => {
    apiClient.setDemoMode(!demoMode)
    setDemoMode(!demoMode)
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-950 via-gray-900 to-gray-800">
      <Header demoMode={demoMode} onToggleDemoMode={toggleDemoMode} onRefresh={loadData} />

      {/* Tab Navigation */}
      <div className="sticky top-16 z-40 bg-gray-900/80 backdrop-blur border-b border-gray-800">
        <div className="max-w-7xl mx-auto px-4 py-4">
          <div className="flex gap-2">
            {[
              { id: 'transactions', label: '📊 Transactions', badge: transactions.length },
              { id: 'analytics', label: '📈 Analytics' },
              { id: 'clustering', label: '🔗 Fraud Rings' },
              { id: 'users', label: '👥 Users' }
            ].map(tab => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id as DashboardTab)}
                className={`px-4 py-2 rounded-lg font-medium transition-all ${
                  activeTab === tab.id
                    ? 'bg-blue-600 text-white'
                    : 'bg-gray-800 text-gray-300 hover:bg-gray-700'
                }`}
              >
                {tab.label}
                {tab.badge !== undefined && (
                  <span className="ml-2 bg-gray-900 px-2 py-0.5 rounded text-sm">
                    {tab.badge}
                  </span>
                )}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="max-w-7xl mx-auto px-4 py-8">
        {loading && (
          <div className="text-center py-12">
            <div className="inline-block">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"></div>
            </div>
            <p className="mt-4 text-gray-400">Loading data...</p>
          </div>
        )}

        {!loading && (
          <>
            {activeTab === 'transactions' && (
              <TransactionFeed
                transactions={transactions}
                selectedTransaction={selectedTransaction}
                onSelectTransaction={setSelectedTransaction}
              />
            )}

            {activeTab === 'analytics' && analytics && (
              <AnalyticsDashboard analytics={analytics} />
            )}

            {activeTab === 'clustering' && (
              <ClusteringVisualization transactions={transactions} />
            )}

            {activeTab === 'users' && (
              <UserProfiles
                transactions={transactions}
                analytics={analytics}
              />
            )}
          </>
        )}
      </div>
    </div>
  )
}

export default App
