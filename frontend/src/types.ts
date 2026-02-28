export interface Transaction {
  transaction_id: string
  user_id: string
  device_id: string
  ip_address: string
  merchant_id: string
  transaction_amount: number
  risk_score: number
  base_risk: number
  clustering_boost: number
  propagation_depth: number
  total_latency_ms: number
  timestamp: string
  cached: boolean
  explanation?: {
    recommendation: string
    reason: string
    calculation_breakdown?: Record<string, any>
  }
  clustering_info?: {
    rings?: Array<{ nodes: string[]; avg_risk: number }>
    dense_subgraphs?: Array<any>
    star_patterns?: Array<any>
  }
}

export interface User {
  id: string
  email: string
  name: string
  avg_risk: number
  transaction_count: number
  flagged_count: number
  devices: string[]
  ips: string[]
}

export interface AnalyticsData {
  risk_distribution: {
    mean: number
    median: number
    p95: number
    p99: number
    buckets: Record<string, number>
  }
  performance: {
    total_transactions: number
    flagged_count: number
    flag_rate: number
    avg_latency: number
    avg_propagation_depth: number
  }
  top_risky_users: User[]
}

export type RiskLevel = 'low' | 'medium' | 'high'
