import axios, { AxiosInstance } from 'axios'
import { Transaction, AnalyticsData } from '../types'
import { generateDemoTransactions, generateDemoAnalytics } from './demoData'

export class RiskMeshAPI {
  private client: AxiosInstance
  private useDemo: boolean

  constructor(apiUrl: string = 'http://localhost:8000', apiKey: string = '', demoMode: boolean = true) {
    this.useDemo = demoMode
    this.client = axios.create({
      baseURL: apiUrl,
      headers: {
        'X-API-Key': apiKey || 'riskmesh-key-demo-001',
        'Content-Type': 'application/json'
      }
    })
  }

  async getTransactions(count: number = 50): Promise<Transaction[]> {
    if (this.useDemo) {
      // Simulate network delay
      await new Promise(resolve => setTimeout(resolve, 300))
      return generateDemoTransactions(count)
    }

    try {
      const response = await this.client.get('/api/stats')
      return [response.data]
    } catch (error) {
      console.error('Failed to fetch transactions:', error)
      return generateDemoTransactions(count)
    }
  }

  async getAnalytics(): Promise<AnalyticsData> {
    if (this.useDemo) {
      await new Promise(resolve => setTimeout(resolve, 200))
      return generateDemoAnalytics()
    }

    try {
      const response = await this.client.get('/api/analytics/performance?hours=24')
      return response.data
    } catch (error) {
      console.error('Failed to fetch analytics:', error)
      return generateDemoAnalytics()
    }
  }

  async processTransaction(event: {
    user_id: string
    device_id: string
    ip_address: string
    merchant_id: string
    transaction_amount: number
  }): Promise<Transaction> {
    if (this.useDemo) {
      await new Promise(resolve => setTimeout(resolve, 100))
      const [txn] = generateDemoTransactions(1)
      return {
        ...txn,
        ...event
      }
    }

    try {
      const response = await this.client.post('/api/event', event)
      return response.data
    } catch (error) {
      console.error('Failed to process transaction:', error)
      const [txn] = generateDemoTransactions(1)
      return {
        ...txn,
        ...event
      }
    }
  }

  setDemoMode(enabled: boolean) {
    this.useDemo = enabled
  }
}

export const apiClient = new RiskMeshAPI('http://localhost:8000', '', true)
