import React from 'react'
import { Transaction, RiskLevel } from '../types'
import { AlertCircle, CheckCircle, Clock } from 'lucide-react'

interface TransactionFeedProps {
  transactions: Transaction[]
  selectedTransaction: Transaction | null
  onSelectTransaction: (txn: Transaction | null) => void
}

function getRiskLevelColor(level: RiskLevel) {
  switch (level) {
    case 'low':
      return 'text-green-400'
    case 'medium':
      return 'text-yellow-400'
    case 'high':
      return 'text-red-400'
  }
}

function getRiskLevelBg(level: RiskLevel) {
  switch (level) {
    case 'low':
      return 'bg-green-500/10 border-green-500/30'
    case 'medium':
      return 'bg-yellow-500/10 border-yellow-500/30'
    case 'high':
      return 'bg-red-500/10 border-red-500/30'
  }
}

function getRiskLevel(score: number): RiskLevel {
  if (score < 0.3) return 'low'
  if (score < 0.6) return 'medium'
  return 'high'
}

export default function TransactionFeed({
  transactions,
  selectedTransaction,
  onSelectTransaction
}: TransactionFeedProps) {
  return (
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
      {/* Transaction List */}
      <div className="lg:col-span-2">
        <div className="bg-gray-900 rounded-lg border border-gray-800 overflow-hidden">
          <div className="p-4 border-b border-gray-800">
            <h2 className="text-xl font-bold text-white">Transaction Feed</h2>
            <p className="text-sm text-gray-400 mt-1">Latest 50 transactions</p>
          </div>

          <div className="divide-y divide-gray-800 max-h-[600px] overflow-y-auto">
            {transactions.map(txn => {
              const riskLevel = getRiskLevel(txn.risk_score)
              const isSelected = selectedTransaction?.transaction_id === txn.transaction_id

              return (
                <button
                  key={txn.transaction_id}
                  onClick={() => onSelectTransaction(isSelected ? null : txn)}
                  className={`w-full p-4 text-left transition-colors ${
                    isSelected
                      ? 'bg-gray-800 border-l-4 border-blue-500'
                      : 'hover:bg-gray-800/50'
                  }`}
                >
                  <div className="flex items-start justify-between gap-4">
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 mb-1">
                        <span className="text-sm font-mono text-gray-400">
                          {txn.user_id}
                        </span>
                        {txn.cached && (
                          <span className="text-xs bg-blue-500/20 text-blue-300 px-2 py-0.5 rounded">
                            📦 Cached
                          </span>
                        )}
                      </div>
                      <div className="text-sm text-gray-400 mb-2">
                        {txn.merchant_id} • ${txn.transaction_amount.toFixed(2)}
                      </div>
                      <div className="flex gap-2 text-xs text-gray-500">
                        <span>{txn.device_id}</span>
                        <span>•</span>
                        <span>{txn.ip_address}</span>
                      </div>
                    </div>

                    <div className="text-right flex-shrink-0">
                      <div
                        className={`text-xl font-bold mb-1 ${getRiskLevelColor(riskLevel)}`}
                      >
                        {(txn.risk_score * 100).toFixed(0)}%
                      </div>
                      <div className="text-xs text-gray-500">
                        {txn.total_latency_ms.toFixed(1)}ms
                      </div>
                    </div>
                  </div>
                </button>
              )
            })}
          </div>
        </div>
      </div>

      {/* Transaction Details */}
      <div>
        {selectedTransaction ? (
          <div className="bg-gray-900 rounded-lg border border-gray-800 p-6 sticky top-32">
            <h3 className="text-lg font-bold text-white mb-4">Transaction Details</h3>

            {/* Risk Score */}
            <div className={`p-4 rounded-lg border mb-4 ${getRiskLevelBg(
              getRiskLevel(selectedTransaction.risk_score)
            )}`}>
              <div className="text-sm text-gray-400 mb-1">Risk Score</div>
              <div className={`text-3xl font-bold ${getRiskLevelColor(
                getRiskLevel(selectedTransaction.risk_score)
              )}`}>
                {(selectedTransaction.risk_score * 100).toFixed(1)}%
              </div>
              <div className="text-xs text-gray-400 mt-1">
                Base: {(selectedTransaction.base_risk * 100).toFixed(1)}% • Boost: {(selectedTransaction.clustering_boost * 100).toFixed(1)}%
              </div>
            </div>

            {/* Explanation */}
            {selectedTransaction.explanation && (
              <div className="mb-4 p-3 bg-gray-800/50 rounded border border-gray-700">
                <div className="flex items-center gap-2 mb-1">
                  {selectedTransaction.explanation.recommendation === 'approve' && (
                    <CheckCircle className="w-4 h-4 text-green-400" />
                  )}
                  {selectedTransaction.explanation.recommendation === 'review' && (
                    <Clock className="w-4 h-4 text-yellow-400" />
                  )}
                  {selectedTransaction.explanation.recommendation === 'challenge' && (
                    <AlertCircle className="w-4 h-4 text-red-400" />
                  )}
                  <span className="text-sm font-medium capitalize">
                    {selectedTransaction.explanation.recommendation}
                  </span>
                </div>
                <p className="text-xs text-gray-300">
                  {selectedTransaction.explanation.reason}
                </p>
              </div>
            )}

            {/* Clustering Info */}
            {selectedTransaction.clustering_info?.rings && selectedTransaction.clustering_info.rings.length > 0 && (
              <div className="mb-4 p-3 bg-red-500/10 border border-red-500/30 rounded">
                <div className="text-sm font-medium text-red-300 mb-2">🔗 Fraud Ring Detected</div>
                <div className="text-xs text-gray-300">
                  {selectedTransaction.clustering_info.rings[0].nodes.length} nodes in ring
                </div>
              </div>
            )}

            {/* Debug Info */}
            <div className="text-xs text-gray-500 space-y-1">
              <div><strong>ID:</strong> {selectedTransaction.transaction_id.substring(0, 12)}...</div>
              <div><strong>Depth:</strong> {selectedTransaction.propagation_depth}</div>
              <div><strong>Latency:</strong> {selectedTransaction.total_latency_ms.toFixed(2)}ms</div>
              <div><strong>Time:</strong> {new Date(selectedTransaction.timestamp).toLocaleTimeString()}</div>
            </div>
          </div>
        ) : (
          <div className="bg-gray-900 rounded-lg border border-gray-800 p-6 sticky top-32 text-center">
            <p className="text-gray-400">Select a transaction to view details</p>
          </div>
        )}
      </div>
    </div>
  )
}
