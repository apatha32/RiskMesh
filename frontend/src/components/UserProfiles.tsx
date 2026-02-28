import React, { useMemo } from 'react'
import { Transaction, AnalyticsData, RiskLevel } from '../types'
import { User as UserIcon, Shield, AlertCircle } from 'lucide-react'

interface UserProfilesProps {
  transactions: Transaction[]
  analytics: AnalyticsData | null
}

interface UserSummary {
  userId: string
  transactionCount: number
  flaggedCount: number
  avgRisk: number
  totalAmount: number
  devices: Set<string>
  ips: Set<string>
  lastSeen: string
  isFraudRing: boolean
}

function getRiskLevel(score: number): RiskLevel {
  if (score < 0.3) return 'low'
  if (score < 0.6) return 'medium'
  return 'high'
}

function getRiskColor(level: RiskLevel) {
  switch (level) {
    case 'low':
      return 'text-green-400 bg-green-500/10'
    case 'medium':
      return 'text-yellow-400 bg-yellow-500/10'
    case 'high':
      return 'text-red-400 bg-red-500/10'
  }
}

export default function UserProfiles({ transactions, analytics }: UserProfilesProps) {
  const userProfiles = useMemo(() => {
    const users = new Map<string, UserSummary>()

    transactions.forEach(txn => {
      if (!users.has(txn.user_id)) {
        users.set(txn.user_id, {
          userId: txn.user_id,
          transactionCount: 0,
          flaggedCount: 0,
          avgRisk: 0,
          totalAmount: 0,
          devices: new Set(),
          ips: new Set(),
          lastSeen: txn.timestamp,
          isFraudRing: false
        })
      }

      const user = users.get(txn.user_id)!
      user.transactionCount += 1
      if (txn.risk_score > 0.6) user.flaggedCount += 1
      user.avgRisk = (user.avgRisk * (user.transactionCount - 1) + txn.risk_score) / user.transactionCount
      user.totalAmount += txn.transaction_amount
      user.devices.add(txn.device_id)
      user.ips.add(txn.ip_address)
      if (new Date(txn.timestamp) > new Date(user.lastSeen)) {
        user.lastSeen = txn.timestamp
      }
      if (txn.clustering_info?.rings && txn.clustering_info.rings.length > 0) {
        user.isFraudRing = true
      }
    })

    return Array.from(users.values())
      .sort((a, b) => b.avgRisk - a.avgRisk)
      .slice(0, 20)
  }, [transactions])

  const topRiskyUsers = analytics?.top_risky_users || []

  return (
    <div className="space-y-6">
      {/* User Summary Stats */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="bg-gray-900 rounded-lg border border-gray-800 p-6">
          <div className="flex items-center gap-3 mb-2">
            <UserIcon className="w-5 h-5 text-blue-400" />
            <span className="text-sm text-gray-400">Unique Users</span>
          </div>
          <div className="text-3xl font-bold text-blue-400">{userProfiles.length}</div>
        </div>

        <div className="bg-gray-900 rounded-lg border border-gray-800 p-6">
          <div className="flex items-center gap-3 mb-2">
            <AlertCircle className="w-5 h-5 text-red-400" />
            <span className="text-sm text-gray-400">High Risk Users</span>
          </div>
          <div className="text-3xl font-bold text-red-400">
            {userProfiles.filter(u => u.avgRisk > 0.6).length}
          </div>
        </div>

        <div className="bg-gray-900 rounded-lg border border-gray-800 p-6">
          <div className="flex items-center gap-3 mb-2">
            <Shield className="w-5 h-5 text-green-400" />
            <span className="text-sm text-gray-400">Low Risk Users</span>
          </div>
          <div className="text-3xl font-bold text-green-400">
            {userProfiles.filter(u => u.avgRisk < 0.3).length}
          </div>
        </div>
      </div>

      {/* Top Risky Users from Analytics */}
      {topRiskyUsers.length > 0 && (
        <div className="bg-gray-900 rounded-lg border border-gray-800 p-6">
          <h3 className="text-lg font-bold text-white mb-4">Top Risky Users</h3>
          <div className="space-y-2">
            {topRiskyUsers.map((user, idx) => (
              <div
                key={user.id}
                className="p-4 bg-gray-800/50 rounded hover:bg-gray-800 transition-colors cursor-pointer"
              >
                <div className="flex items-center justify-between">
                  <div>
                    <div className="font-medium text-white">#{idx + 1} {user.name}</div>
                    <div className="text-xs text-gray-400 mt-1">
                      {user.transaction_count} transactions • {user.flagged_count} flagged
                    </div>
                  </div>
                  <div className={`px-3 py-1 rounded font-bold ${getRiskColor(getRiskLevel(user.avg_risk))}`}>
                    {(user.avg_risk * 100).toFixed(0)}%
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* User Profiles Table */}
      <div className="bg-gray-900 rounded-lg border border-gray-800 overflow-hidden">
        <div className="p-6 border-b border-gray-800">
          <h3 className="text-lg font-bold text-white">User Profiles (Top 20)</h3>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-gray-800 bg-gray-800/50">
                <th className="px-6 py-3 text-left text-gray-400 font-medium">User ID</th>
                <th className="px-6 py-3 text-center text-gray-400 font-medium">Avg Risk</th>
                <th className="px-6 py-3 text-center text-gray-400 font-medium">Txns</th>
                <th className="px-6 py-3 text-center text-gray-400 font-medium">Flagged</th>
                <th className="px-6 py-3 text-center text-gray-400 font-medium">Devices</th>
                <th className="px-6 py-3 text-center text-gray-400 font-medium">IPs</th>
                <th className="px-6 py-3 text-center text-gray-400 font-medium">Total Vol</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-800">
              {userProfiles.map(user => {
                const riskLevel = getRiskLevel(user.avgRisk)
                return (
                  <tr
                    key={user.userId}
                    className={`hover:bg-gray-800/50 transition-colors ${
                      user.isFraudRing ? 'bg-red-500/5' : ''
                    }`}
                  >
                    <td className="px-6 py-4 text-gray-300">
                      <div className="flex items-center gap-2">
                        {user.isFraudRing && (
                          <span className="text-red-400">🔗</span>
                        )}
                        {user.userId}
                      </div>
                    </td>
                    <td className="px-6 py-4 text-center">
                      <span className={`px-2 py-1 rounded text-sm font-bold ${getRiskColor(riskLevel)}`}>
                        {(user.avgRisk * 100).toFixed(0)}%
                      </span>
                    </td>
                    <td className="px-6 py-4 text-center text-gray-300">
                      {user.transactionCount}
                    </td>
                    <td className="px-6 py-4 text-center text-yellow-400 font-medium">
                      {user.flaggedCount}
                    </td>
                    <td className="px-6 py-4 text-center text-gray-400">
                      {user.devices.size}
                    </td>
                    <td className="px-6 py-4 text-center text-gray-400">
                      {user.ips.size}
                    </td>
                    <td className="px-6 py-4 text-center text-gray-300">
                      ${user.totalAmount.toFixed(0)}
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>
      </div>

      {/* User Insights */}
      <div className="bg-gray-900 rounded-lg border border-gray-800 p-6">
        <h3 className="text-lg font-bold text-white mb-4">Insights</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm text-gray-400">
          <div className="p-4 bg-gray-800/50 rounded">
            <div className="font-medium text-white mb-1">High Activity Users</div>
            <p>
              {userProfiles.filter(u => u.transactionCount > 20).length} users with 20+ transactions
            </p>
          </div>
          <div className="p-4 bg-gray-800/50 rounded">
            <div className="font-medium text-white mb-1">Device Diversity</div>
            <p>
              Average {(Array.from(userProfiles.map(u => u.devices.size)).reduce((a, b) => a + b, 0) / userProfiles.length).toFixed(1)} devices per user
            </p>
          </div>
          <div className="p-4 bg-gray-800/50 rounded">
            <div className="font-medium text-white mb-1">Geographic Diversity</div>
            <p>
              Average {(Array.from(userProfiles.map(u => u.ips.size)).reduce((a, b) => a + b, 0) / userProfiles.length).toFixed(1)} unique IPs per user
            </p>
          </div>
          <div className="p-4 bg-gray-800/50 rounded">
            <div className="font-medium text-white mb-1">Transaction Velocity</div>
            <p>
              Average ${(userProfiles.reduce((sum, u) => sum + u.totalAmount, 0) / userProfiles.length).toFixed(2)} per user
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}
