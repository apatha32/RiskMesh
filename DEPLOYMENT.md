# RiskMesh Deployment & Operations Guide

## Overview

This guide covers deploying, testing, and operating RiskMesh in local and production-like environments.

## Prerequisites

- Docker & Docker Compose (recommended for MVP)
- Python 3.11+ (for local development)
- PostgreSQL 15+ (for database)
- Redis 7+ (for caching/future use)

## Local Deployment with Docker

### Quick Start

```bash
cd riskmesh
docker-compose up -d
```

This starts:
- **FastAPI App**: http://localhost:8000
- **PostgreSQL**: localhost:5432
- **Redis**: localhost:6379  
- **Prometheus**: http://localhost:9090

### Verify Services

```bash
# Check health
curl http://localhost:8000/health

# Check stats
curl http://localhost:8000/api/stats

# View Prometheus metrics
curl http://localhost:8000/metrics
```

### Stop Services

```bash
docker-compose down
```

### Clean Up Data

```bash
docker-compose down -v  # Removes volumes too
```

---

## Environment Configuration

### Environment Variables

Create `.env` file in project root:

```env
# Database
DATABASE_URL=postgresql://riskmesh:riskmesh123@postgres:5432/riskmesh
REDIS_URL=redis://redis:6379/0

# App Settings
LOG_LEVEL=INFO
PORT=8000

# Performance Tuning
GRAPH_MAX_NODE_LIMIT=100000
PROPAGATION_MAX_DEPTH=2
PROPAGATION_ALPHA=0.5
RISK_THRESHOLD=0.1
```

### Docker Compose Override

Create `docker-compose.override.yml` for local customization:

```yaml
version: '3.8'

services:
  app:
    environment:
      - LOG_LEVEL=DEBUG
    ports:
      - "8000:8000"
  
  prometheus:
    ports:
      - "9090:9090"
```

---

## Testing

### Unit Tests

Test individual modules:

```bash
# Test GraphStore
pytest tests/test_graph_store.py -v

# Test Risk Propagation
pytest tests/test_propagation.py -v

# Test Base Risk Calculation
pytest tests/test_base_risk.py -v

# All tests
pytest tests/ -v
```

### Integration Tests

Test end-to-end flow:

```bash
pytest tests/test_integration.py -v
```

### Coverage Report

```bash
pytest --cov=app tests/
```

---

## Load Testing

### Using Locust

Load test against running instance:

```bash
# Start app first
docker-compose up -d

# Run load test
locust -f load_test.py --host http://localhost:8000

# Open http://localhost:8089
# Configure users and spawn rate
```

### Load Test Scenarios

**Light Load (MVP baseline)**:
- Users: 10
- Spawn rate: 1/sec
- Duration: 60s

**Medium Load**:
- Users: 100
- Spawn rate: 10/sec
- Duration: 300s

**High Load (Stress test)**:
- Users: 1000
- Spawn rate: 100/sec
- Duration: 600s

### Performance Goals

Target metrics:
- **Throughput**: 1000+ events/sec
- **Avg Latency**: <50ms
- **P95 Latency**: <100ms
- **P99 Latency**: <200ms
- **Memory**: Stable growth

---

## Monitoring with Prometheus

### Query Metrics

Prometheus endpoint: http://localhost:9090

Common queries:

```promql
# Request rate
rate(riskmesh_requests_total[1m])

# Average latency
avg(riskmesh_request_latency_ms)

# P95 latency
histogram_quantile(0.95, riskmesh_request_latency_ms)

# Graph node count
riskmesh_graph_nodes

# Graph edge count
riskmesh_graph_edges

# Error rate
rate(riskmesh_errors_total[1m])
```

### Alerting Rules

Create `alerts.yml`:

```yaml
groups:
  - name: riskmesh_alerts
    interval: 30s
    rules:
      - alert: HighLatency
        expr: avg(riskmesh_request_latency_ms) > 50
        for: 2m
        annotations:
          summary: "High request latency detected"
      
      - alert: HighErrorRate
        expr: rate(riskmesh_errors_total[5m]) > 0.01
        for: 2m
        annotations:
          summary: "Error rate above 1%"
```

---

## API Endpoints

### Process Event

```bash
curl -X POST http://localhost:8000/api/event \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user_123",
    "device_id": "device_456",
    "ip_address": "192.168.1.1",
    "merchant_id": "merchant_789",
    "transaction_amount": 250.00
  }'
```

Response:
```json
{
  "transaction_id": "abc-123-def",
  "risk_score": 0.35,
  "propagation_depth": 2,
  "timestamp": "2026-02-28T10:30:00"
}
```

### Get Statistics

```bash
curl http://localhost:8000/api/stats
```

Response:
```json
{
  "graph_nodes": 1250,
  "graph_edges": 3840,
  "timestamp": "2026-02-28T10:30:00"
}
```

### Health Check

```bash
curl http://localhost:8000/health
```

Response:
```json
{
  "status": "healthy",
  "service": "riskmesh",
  "version": "0.1.0"
}
```

---

## Database Operations

### Connect to PostgreSQL

```bash
# From Docker
docker-compose exec postgres psql -U riskmesh -d riskmesh

# From Host (if exposed)
psql -h localhost -U riskmesh -d riskmesh
```

### Common Queries

```sql
-- Count transactions
SELECT COUNT(*) FROM transactions;

-- Average risk by user
SELECT user_id, AVG(risk_score) as avg_risk 
FROM transactions 
GROUP BY user_id 
ORDER BY avg_risk DESC;

-- Recent transactions
SELECT * FROM transactions 
ORDER BY timestamp DESC 
LIMIT 100;

-- Risk distribution
SELECT 
  CASE 
    WHEN risk_score < 0.3 THEN 'low'
    WHEN risk_score < 0.6 THEN 'medium'
    ELSE 'high'
  END as risk_level,
  COUNT(*) as count
FROM transactions
GROUP BY risk_level;
```

### Backup Database

```bash
# Backup
docker-compose exec postgres pg_dump -U riskmesh riskmesh > backup.sql

# Restore
docker-compose exec -T postgres psql -U riskmesh riskmesh < backup.sql
```

---

## Troubleshooting

### App won't start

```bash
# Check logs
docker-compose logs app

# Common issues:
# 1. Database not ready - wait for healthcheck
# 2. Port 8000 already in use - change docker-compose.yml
# 3. Missing dependencies - rebuild image
```

### Database connection fails

```bash
# Check PostgreSQL is running
docker-compose ps postgres

# Check connection string
docker-compose exec app env | grep DATABASE_URL

# Test connection
docker-compose exec postgres pg_isready
```

### High latency

```bash
# Check graph size
curl http://localhost:8000/api/stats

# Monitor resources
docker-compose stats

# Check Prometheus metrics
# - Request latency trend
# - Graph growth rate
# - Propagation depth
```

### Memory leak

```bash
# Monitor memory usage
docker-compose exec app ps aux | grep uvicorn

# Check graph node count increases unbounded
curl http://localhost:8000/api/stats

# Consider adding TTL/pruning for old nodes
```

---

## Performance Tuning

### Propagation Configuration

In `app/graph/propagation.py`:

```python
# More aggressive propagation (use with caution)
propagator = RiskPropagator(
    alpha=0.7,           # Higher = more propagation
    max_depth=3,         # Deeper propagation
    risk_threshold=0.05  # Lower = more events trigger propagation
)

# Conservative propagation
propagator = RiskPropagator(
    alpha=0.3,
    max_depth=1,
    risk_threshold=0.3
)
```

### Database Tuning

```sql
-- Index frequently queried columns
CREATE INDEX idx_transactions_user_id ON transactions(user_id);
CREATE INDEX idx_transactions_timestamp ON transactions(timestamp DESC);
CREATE INDEX idx_transactions_risk_score ON transactions(risk_score);

-- Vacuum to maintain performance
VACUUM ANALYZE transactions;
```

### Caching Strategy

Future improvement: Add Redis caching for hot nodes

```python
# Cache frequently accessed users
cache_key = f"risk:{user_id}"
cached_risk = redis_client.get(cache_key)
if cached_risk:
    return float(cached_risk)
```

---

## Production Considerations

### Before Production Deployment

- [ ] Load test with expected traffic volume
- [ ] Set up monitoring and alerting
- [ ] Configure backups (daily minimum)
- [ ] Set up log aggregation
- [ ] Create runbooks for common issues
- [ ] Test disaster recovery
- [ ] Configure environment-specific settings
- [ ] Review security settings
- [ ] Set up rate limiting (future)
- [ ] Implement request validation (enhanced)

### Scaling Options

**Horizontal Scaling**:
- Multiple app instances behind load balancer
- Shared PostgreSQL database
- Shared Redis for caching

**Vertical Scaling**:
- Increase machine resources
- Tune Python/database parameters
- Optimize graph traversal

**Graph Optimization**:
- Implement node pruning (remove old nodes)
- Use time-decay for risk (older risks matter less)
- Partition graph by user cohort

---

## Next Steps (Phase 2)

- [ ] Redis caching layer
- [ ] Time-decay for risk scores
- [ ] Clustering detection algorithm
- [ ] Explanation field in risk response
- [ ] Neo4j integration option
- [ ] Dashboard/visualization
- [ ] API authentication
- [ ] Rate limiting
- [ ] Advanced monitoring

---

## Support

For issues or questions:
1. Check logs: `docker-compose logs -f app`
2. Review config: `docker-compose config`
3. Test connectivity: `curl http://localhost:8000/health`
4. Check GitHub issues: https://github.com/apatha32/RiskMesh/issues

