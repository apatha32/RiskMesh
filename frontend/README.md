# RiskMesh Dashboard

Real-time fraud detection dashboard for RiskMesh fraud intelligence engine.

## Features

- 📊 **Transaction Feed**: Live transaction stream with risk scores
- 📈 **Real-Time Analytics**: Risk distribution, performance metrics, trends
- 🔗 **Fraud Ring Detection**: Visualize detected fraud clusters and relationships
- 👥 **User Profiles**: Historical behavior, risk patterns, device/IP analysis
- 🎬 **Demo Mode**: Built-in demo data for testing without backend
- ⚡ **Live API Integration**: Switch between demo and real RiskMesh backend

## Quick Start

### Install Dependencies

```bash
cd frontend
npm install
```

### Run Development Server

```bash
npm run dev
```

Dashboard opens at `http://localhost:3000` automatically.

### Build for Production

```bash
npm run build
npm run preview
```

## Demo Mode

The dashboard starts in **Demo Mode** with simulated fraud scenarios:

- **50 transactions** with realistic risk distributions
- **Fraud ring scenario** with 3 coordinated users
- **Mock analytics** showing distribution and performance metrics
- **Simulated network delays** for authentic UX

Toggle between Demo and Live Mode using the header button.

## Real API Integration

To connect to real RiskMesh backend:

1. Ensure backend is running on `http://localhost:8000`
2. Set up valid API key in `src/api/client.ts`
3. Click "Use Real API" button in dashboard header

```typescript
// src/api/client.ts
export const apiClient = new RiskMeshAPI(
  'http://localhost:8000',
  'your-api-key-here',
  false  // Set to false for real API, true for demo
)
```

## Dashboard Tabs

### Transactions
- Live transaction stream with real-time risk scores
- Click to view detailed breakdown
- Explanations showing why each score was calculated
- Cache status indicators

### Analytics
- **Risk Distribution**: Histogram of risk scores across transactions
- **Performance Metrics**: Latency, throughput, flag rates
- **Graphs Stats**: Propagation depth, cache performance
- **Percentiles**: Mean, median, p95, p99 risk scores

### Fraud Rings
- **SCC Detection**: Strongly connected components (cycles)
- **Dense Subgraphs**: Highly interconnected clusters
- **Star Patterns**: Hub operators with many connections
- **Ring Members**: Detailed user connections and transaction history

### Users
- **Top Risky Users**: Ranked by average risk score
- **User Activity**: Transaction counts, flagged transactions
- **Device Diversity**: Number of unique devices per user
- **Geographic Diversity**: Unique IP addresses used
- **Transaction Velocity**: Total volume and patterns

## Data Structures

### Transaction
```typescript
{
  transaction_id: string
  user_id: string
  device_id: string
  ip_address: string
  merchant_id: string
  transaction_amount: number
  risk_score: number          // 0-1
  base_risk: number           // Before propagation
  clustering_boost: number    // Fraud ring boost
  explanation: {
    recommendation: 'approve' | 'review' | 'challenge'
    reason: string
  }
  clustering_info: {
    rings: Array<{
      nodes: string[]
      avg_risk: number
    }>
  }
}
```

### Analytics
```typescript
{
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
    flag_rate: number          // 0-1
    avg_latency: number        // ms
    avg_propagation_depth: number
  }
}
```

## Customization

### Colors & Styling

Risk levels (Tailwind):
- **Low**: `text-risk-low` (#10b981)
- **Medium**: `text-risk-medium` (#f59e0b)
- **High**: `text-risk-high` (#ef4444)

### Demo Data

Modify demo scenarios in `src/api/demoData.ts`:

```typescript
export function generateDemoTransactions(count: number = 50): Transaction[] {
  // Customize fraud patterns, amounts, merchants, etc.
}

export function generateDemoAnalytics(): AnalyticsData {
  // Adjust risk distributions, performance metrics
}
```

## Components

- **Header**: Navigation, mode toggle, refresh button
- **TransactionFeed**: List view + detail panel
- **AnalyticsDashboard**: Charts and metrics
- **ClusteringVisualization**: Fraud ring detection display
- **UserProfiles**: User activity analysis

## Performance

- Smooth rendering of 50+ transactions
- Automatic refresh every 5 seconds
- Responsive design (mobile, tablet, desktop)
- Efficient React component rendering

## Troubleshooting

### Dashboard won't load
- Check if Vite dev server is running
- Verify `npm install` completed successfully
- Check browser console for errors

### Real API not connecting
- Ensure RiskMesh backend running on port 8000
- Verify API key is valid
- Check CORS settings if running on different domain

### Demo data not updating
- Click refresh button to manually reload
- Check browser developer tools for errors
- Verify `apiClient.setDemoMode(true)` in Dev Tools console

## Development

```bash
# Start dev server with hot reload
npm run dev

# Type checking
npx tsc --noEmit

# Build for production
npm run build

# Preview production build
npm run preview
```

## Tech Stack

- **React 18**: UI framework
- **TypeScript**: Type safety
- **Vite**: Build tool & dev server
- **Tailwind CSS**: Styling
- **Recharts**: Data visualization
- **Lucide Icons**: Icon library
- **Axios**: HTTP client

## License

MIT
