import React from 'react'
import { AnalyticsData } from '../types'
import { BarChart, Bar, LineChart, Line, PieChart, Pie, Cell, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts'
import { TrendingUp, AlertTriangle, Zap, Clock } from 'lucide-react'

interface AnalyticsDashboardProps {
  analytics: AnalyticsData
}

export default function AnalyticsDashboard({ analytics }: AnalyticsDashboardProps) {
  const riskDistributionData = Object.entries(analytics.risk_distribution.buckets).map(
    ([range, count]) => ({ range, count })
  )

  const performanceMetrics = [
    {
      icon: Zap,
      label: 'Total Transactions',
      value: analytics.performance.total_transactions.toLocaleString(),
      color: 'text-blue-400'
    },
    {
      icon: AlertTriangle,
      label: 'Flagged Transactions',
      value: analytics.performance.flagged_count,
      color: 'text-red-400'
    },
    {
      icon: TrendingUp,
      label: 'Flag Rate',
      value: `${(analytics.performance.flag_rate * 100).toFixed(1)}%`,
      color: 'text-yellow-400'
    },
    {
      icon: Clock,
      label: 'Avg Latency',
      value: `${analytics.performance.avg_latency.toFixed(1)}ms`,
      color: 'text-green-400'
    }
  ]

  const riskLevelData = [
    { name: 'Low Risk', value: analytics.risk_distribution.buckets['0.0-0.2'], color: '#10b981' },
    { name: 'Medium Risk', value: (analytics.risk_distribution.buckets['0.2-0.4'] + analytics.risk_distribution.buckets['0.4-0.6']), color: '#f59e0b' },
    { name: 'High Risk', value: (analytics.risk_distribution.buckets['0.6-0.8'] + analytics.risk_distribution.buckets['0.8-1.0']), color: '#ef4444' }
  ]

  return (
    <div className="space-y-6">
      {/* Key Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {performanceMetrics.map((metric, idx) => {
          const Icon = metric.icon
          return (
            <div key={idx} className="bg-gray-900 rounded-lg border border-gray-800 p-6">
              <div className="flex items-center justify-between mb-3">
                <div className={`${metric.color}`}>
                  <Icon className="w-6 h-6" />
                </div>
                <div className="text-xs text-gray-500">24h</div>
              </div>
              <div className={`text-2xl font-bold ${metric.color} mb-1`}>
                {metric.value}
              </div>
              <div className="text-sm text-gray-400">{metric.label}</div>
            </div>
          )
        })}
      </div>

      {/* Charts Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Risk Distribution */}
        <div className="bg-gray-900 rounded-lg border border-gray-800 p-6">
          <h3 className="text-lg font-bold text-white mb-4">Risk Distribution</h3>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={riskDistributionData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
              <XAxis dataKey="range" tick={{ fill: '#9ca3af', fontSize: 12 }} />
              <YAxis tick={{ fill: '#9ca3af', fontSize: 12 }} />
              <Tooltip
                contentStyle={{ backgroundColor: '#1f2937', border: '1px solid #374151' }}
                labelStyle={{ color: '#f3f4f6' }}
              />
              <Bar dataKey="count" fill="#3b82f6" radius={[8, 8, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
          <div className="mt-4 p-3 bg-gray-800/50 rounded text-sm text-gray-300">
            <div className="grid grid-cols-3 gap-4">
              <div>
                <div className="text-xs text-gray-500">Mean</div>
                <div className="text-lg font-bold text-white">{(analytics.risk_distribution.mean * 100).toFixed(1)}%</div>
              </div>
              <div>
                <div className="text-xs text-gray-500">Median</div>
                <div className="text-lg font-bold text-white">{(analytics.risk_distribution.median * 100).toFixed(1)}%</div>
              </div>
              <div>
                <div className="text-xs text-gray-500">P99</div>
                <div className="text-lg font-bold text-white">{(analytics.risk_distribution.p99 * 100).toFixed(1)}%</div>
              </div>
            </div>
          </div>
        </div>

        {/* Risk Categories Pie Chart */}
        <div className="bg-gray-900 rounded-lg border border-gray-800 p-6">
          <h3 className="text-lg font-bold text-white mb-4">Risk Categories</h3>
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie
                data={riskLevelData}
                cx="50%"
                cy="50%"
                labelLine={false}
                label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                outerRadius={100}
                fill="#8884d8"
                dataKey="value"
              >
                {riskLevelData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={entry.color} />
                ))}
              </Pie>
              <Tooltip
                contentStyle={{ backgroundColor: '#1f2937', border: '1px solid #374151' }}
                labelStyle={{ color: '#f3f4f6' }}
              />
            </PieChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Propagation Stats */}
      <div className="bg-gray-900 rounded-lg border border-gray-800 p-6">
        <h3 className="text-lg font-bold text-white mb-4">Graph Propagation Analysis</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="p-4 bg-gray-800/50 rounded">
            <div className="text-sm text-gray-400 mb-2">Avg Propagation Depth</div>
            <div className="text-3xl font-bold text-blue-400">
              {analytics.performance.avg_propagation_depth.toFixed(2)}
            </div>
            <div className="text-xs text-gray-500 mt-1">Maximum depth limit: 2</div>
          </div>
          <div className="p-4 bg-gray-800/50 rounded">
            <div className="text-sm text-gray-400 mb-2">Cache Hit Rate</div>
            <div className="text-3xl font-bold text-green-400">
              70%
            </div>
            <div className="text-xs text-gray-500 mt-1">Estimated based on demo data</div>
          </div>
          <div className="p-4 bg-gray-800/50 rounded">
            <div className="text-sm text-gray-400 mb-2">Avg Propagation Speed</div>
            <div className="text-3xl font-bold text-purple-400">
              {(analytics.performance.avg_latency / Math.max(1, analytics.performance.avg_propagation_depth)).toFixed(1)}ms
            </div>
            <div className="text-xs text-gray-500 mt-1">Per hop latency</div>
          </div>
        </div>
      </div>
    </div>
  )
}
