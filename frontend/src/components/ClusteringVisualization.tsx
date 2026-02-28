import React, { useMemo } from 'react'
import { Transaction } from '../types'
import { AlertTriangle, Link2, Users } from 'lucide-react'

interface ClusteringVisualizationProps {
  transactions: Transaction[]
}

interface Cluster {
  id: string
  nodes: string[]
  avgRisk: number
  transactionCount: number
}

export default function ClusteringVisualization({ transactions }: ClusteringVisualizationProps) {
  const clusters = useMemo(() => {
    const clusterMap = new Map<string, Cluster>()

    // Find users with high risk and clustering info
    const highRiskUsers = new Set<string>()
    transactions.forEach(txn => {
      if (txn.clustering_info?.rings && txn.clustering_info.rings.length > 0) {
        txn.clustering_info.rings.forEach(ring => {
          ring.nodes.forEach(node => highRiskUsers.add(node))
        })
      }
    })

    // Build clusters
    if (highRiskUsers.size > 0) {
      const nodes = Array.from(highRiskUsers)
      const avgRisk = transactions
        .filter(t => highRiskUsers.has(t.user_id))
        .reduce((sum, t) => sum + t.risk_score, 0) / nodes.length

      clusterMap.set('ring_1', {
        id: 'ring_1',
        nodes,
        avgRisk,
        transactionCount: transactions.filter(t => highRiskUsers.has(t.user_id)).length
      })
    }

    return Array.from(clusterMap.values())
  }, [transactions])

  const fraudRingTransactions = useMemo(() => {
    const fraudUsers = new Set<string>()
    clusters.forEach(cluster => {
      cluster.nodes.forEach(node => fraudUsers.add(node))
    })
    return transactions.filter(t => fraudUsers.has(t.user_id))
  }, [clusters, transactions])

  return (
    <div className="space-y-6">
      {/* Overview */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="bg-gray-900 rounded-lg border border-gray-800 p-6">
          <div className="flex items-center gap-3 mb-2">
            <AlertTriangle className="w-5 h-5 text-red-400" />
            <span className="text-sm text-gray-400">Fraud Rings Detected</span>
          </div>
          <div className="text-3xl font-bold text-red-400">{clusters.length}</div>
        </div>

        <div className="bg-gray-900 rounded-lg border border-gray-800 p-6">
          <div className="flex items-center gap-3 mb-2">
            <Users className="w-5 h-5 text-yellow-400" />
            <span className="text-sm text-gray-400">Involved Users</span>
          </div>
          <div className="text-3xl font-bold text-yellow-400">
            {new Set(clusters.flatMap(c => c.nodes)).size}
          </div>
        </div>

        <div className="bg-gray-900 rounded-lg border border-gray-800 p-6">
          <div className="flex items-center gap-3 mb-2">
            <Link2 className="w-5 h-5 text-purple-400" />
            <span className="text-sm text-gray-400">Suspicious Transactions</span>
          </div>
          <div className="text-3xl font-bold text-purple-400">{fraudRingTransactions.length}</div>
        </div>
      </div>

      {/* Clusters Detail */}
      {clusters.length > 0 ? (
        <div className="space-y-4">
          {clusters.map((cluster, idx) => (
            <div key={cluster.id} className="bg-gray-900 rounded-lg border border-red-500/30 p-6">
              <div className="flex items-start justify-between mb-4">
                <div>
                  <h3 className="text-lg font-bold text-white mb-1">Fraud Ring #{idx + 1}</h3>
                  <p className="text-sm text-gray-400">{cluster.nodes.length} connected users</p>
                </div>
                <div className="text-right">
                  <div className="text-2xl font-bold text-red-400">{(cluster.avgRisk * 100).toFixed(0)}%</div>
                  <div className="text-xs text-gray-500">Average Risk</div>
                </div>
              </div>

              {/* Network Visualization (Simple ASCII representation) */}
              <div className="mb-4 p-4 bg-gray-800/50 rounded font-mono text-sm">
                <div className="text-gray-400 space-y-2">
                  {cluster.nodes.map((node, i) => (
                    <div key={node} className="flex items-center gap-2">
                      <span className="text-blue-400">○</span>
                      <span className="text-gray-300">{node}</span>
                      {i < cluster.nodes.length - 1 && (
                        <span className="text-gray-600 ml-auto text-xs">↓</span>
                      )}
                    </div>
                  ))}
                </div>
              </div>

              {/* Member Stats */}
              <div className="grid grid-cols-3 gap-3 mb-4">
                <div className="p-3 bg-gray-800/50 rounded">
                  <div className="text-xs text-gray-500">Members</div>
                  <div className="text-lg font-bold text-white">{cluster.nodes.length}</div>
                </div>
                <div className="p-3 bg-gray-800/50 rounded">
                  <div className="text-xs text-gray-500">Transactions</div>
                  <div className="text-lg font-bold text-white">{cluster.transactionCount}</div>
                </div>
                <div className="p-3 bg-gray-800/50 rounded">
                  <div className="text-xs text-gray-500">Risk Boost</div>
                  <div className="text-lg font-bold text-yellow-400">+15%</div>
                </div>
              </div>

              {/* Recent Transactions */}
              <div className="border-t border-gray-800 pt-4">
                <div className="text-sm font-medium text-gray-300 mb-2">Recent Transactions</div>
                <div className="space-y-2">
                  {fraudRingTransactions.slice(0, 3).map(txn => (
                    <div
                      key={txn.transaction_id}
                      className="flex items-center justify-between text-xs p-2 bg-gray-800/30 rounded"
                    >
                      <span className="text-gray-400">{txn.user_id}</span>
                      <span className="text-gray-400">${txn.transaction_amount.toFixed(2)}</span>
                      <span className="text-red-400 font-medium">
                        {(txn.risk_score * 100).toFixed(0)}%
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className="bg-gray-900 rounded-lg border border-gray-800 p-12 text-center">
          <div className="text-green-400 text-5xl mb-3">✓</div>
          <h3 className="text-lg font-bold text-white mb-1">No Fraud Rings Detected</h3>
          <p className="text-gray-400">All transactions appear normal. No coordinated fraud patterns detected.</p>
        </div>
      )}

      {/* Detection Algorithm Info */}
      <div className="bg-gray-900 rounded-lg border border-gray-800 p-6">
        <h3 className="text-lg font-bold text-white mb-3">Detection Algorithm</h3>
        <div className="space-y-2 text-sm text-gray-400">
          <p>
            <strong>Strongly Connected Components (SCC)</strong>: Detects cycles in entity relationships
          </p>
          <p>
            <strong>Dense Subgraphs</strong>: Identifies highly interconnected clusters
          </p>
          <p>
            <strong>Star Patterns</strong>: Finds central nodes with many connections (hub operators)
          </p>
          <p className="text-xs text-gray-500 mt-3">
            Risk boost applied: +15% for ring members, +10% for dense clusters
          </p>
        </div>
      </div>
    </div>
  )
}
