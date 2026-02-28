import { Transaction, User, AnalyticsData, RiskLevel } from '../types'

const first_names = ['Alice', 'Bob', 'Charlie', 'Diana', 'Eve', 'Frank', 'Grace', 'Henry', 'Iris', 'Jack']
const last_names = ['Smith', 'Johnson', 'Williams', 'Brown', 'Jones', 'Garcia', 'Miller', 'Davis', 'Rodriguez', 'Taylor']
const merchants = ['Amazon', 'eBay', 'Walmart', 'Target', 'Best Buy', 'Starbucks', 'Uber', 'DoorDash', 'Netflix', 'Steam']
const ips = ['192.168.1.1', '10.0.0.5', '172.16.0.1', '203.0.113.45', '198.51.100.89', '192.0.2.102', '198.18.0.5', '169.254.1.1']

function randomFrom<T>(arr: T[]): T {
  return arr[Math.floor(Math.random() * arr.length)]
}

function randomInt(min: number, max: number): number {
  return Math.floor(Math.random() * (max - min + 1)) + min
}

function randomFloat(min: number, max: number): number {
  return Math.random() * (max - min) + min
}

export function generateDemoTransactions(count: number = 50): Transaction[] {
  const transactions: Transaction[] = []
  const now = new Date()

  // Create fraud ring scenario
  const fraudUsers = ['user_fraud_ring_1', 'user_fraud_ring_2', 'user_fraud_ring_3']
  
  for (let i = 0; i < count; i++) {
    const isFraudRing = i < 15
    const user_id = isFraudRing ? randomFrom(fraudUsers) : `user_${randomInt(100, 999)}`
    const isHighRiskTxn = randomInt(1, 100) <= 20 // 20% high risk
    
    const baseRisk = isHighRiskTxn ? randomFloat(0.3, 0.7) : randomFloat(0.01, 0.3)
    const clusterBoost = isFraudRing ? randomFloat(0.1, 0.2) : 0
    const propagationDepth = isHighRiskTxn ? randomInt(1, 3) : 0
    const riskScore = Math.min(1, baseRisk + clusterBoost)
    
    const timestamp = new Date(now.getTime() - i * 60000) // Each txn 1 min apart
    
    transactions.push({
      transaction_id: `txn_${Date.now()}_${i}`,
      user_id,
      device_id: `device_${randomInt(1, 50)}`,
      ip_address: randomFrom(ips),
      merchant_id: randomFrom(merchants),
      transaction_amount: isHighRiskTxn ? randomInt(500, 5000) : randomInt(10, 500),
      risk_score: riskScore,
      base_risk: baseRisk,
      clustering_boost: clusterBoost,
      propagation_depth: propagationDepth,
      total_latency_ms: randomFloat(5, 100),
      timestamp: timestamp.toISOString(),
      cached: Math.random() > 0.3,
      explanation: {
        recommendation: riskScore < 0.3 ? 'approve' : riskScore < 0.6 ? 'review' : 'challenge',
        reason: isHighRiskTxn 
          ? 'High transaction amount + new device detected'
          : 'Normal transaction pattern',
        calculation_breakdown: {
          base_risk: baseRisk,
          after_propagation: baseRisk + (propagationDepth > 0 ? randomFloat(0.05, 0.15) : 0),
          after_time_decay: riskScore * 0.99,
          cluster_boost: clusterBoost
        }
      },
      clustering_info: isFraudRing ? {
        rings: [{
          nodes: fraudUsers,
          avg_risk: 0.65
        }]
      } : undefined
    })
  }
  
  return transactions
}

export function generateDemoUser(user_id: string): User {
  return {
    id: user_id,
    email: `${user_id}@example.com`,
    name: `${randomFrom(first_names)} ${randomFrom(last_names)}`,
    avg_risk: randomFloat(0.1, 0.5),
    transaction_count: randomInt(5, 100),
    flagged_count: randomInt(0, 10),
    devices: [`device_${randomInt(1, 50)}`, `device_${randomInt(50, 100)}`],
    ips: [randomFrom(ips), randomFrom(ips)]
  }
}

export function generateDemoAnalytics(): AnalyticsData {
  return {
    risk_distribution: {
      mean: 0.35,
      median: 0.28,
      p95: 0.72,
      p99: 0.89,
      buckets: {
        '0.0-0.2': 450,
        '0.2-0.4': 280,
        '0.4-0.6': 150,
        '0.6-0.8': 80,
        '0.8-1.0': 40
      }
    },
    performance: {
      total_transactions: 1000,
      flagged_count: 150,
      flag_rate: 0.15,
      avg_latency: 32.5,
      avg_propagation_depth: 1.2
    },
    top_risky_users: [
      {
        id: 'user_fraud_ring_1',
        email: 'user_fraud_ring_1@example.com',
        name: 'Suspicious User 1',
        avg_risk: 0.78,
        transaction_count: 45,
        flagged_count: 28,
        devices: ['device_1', 'device_2', 'device_15'],
        ips: ['192.168.1.1', '203.0.113.45']
      },
      {
        id: 'user_fraud_ring_2',
        email: 'user_fraud_ring_2@example.com',
        name: 'Suspicious User 2',
        avg_risk: 0.72,
        transaction_count: 38,
        flagged_count: 22,
        devices: ['device_3', 'device_5'],
        ips: ['10.0.0.5', '198.51.100.89']
      },
      {
        id: 'user_123',
        email: 'user_123@example.com',
        name: 'Normal User',
        avg_risk: 0.15,
        transaction_count: 125,
        flagged_count: 2,
        devices: ['device_8'],
        ips: ['192.0.2.102']
      }
    ]
  }
}
