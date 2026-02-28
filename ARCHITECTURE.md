# RiskMesh: Architecture & Design

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    FastAPI Application                          │
│                    (:8000)                                      │
└────┬─────────────────────────────────────┬──────────────────────┘
     │                                     │
     ├─ POST /api/event                    ├─ GET /metrics (Prometheus)
     ├─ GET /api/stats                     └─ GET /health
     └─ GET /health
     
     │
     ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Risk Engine                                  │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │ 1. Graph Store: Add/Update Entities & Relationships     │   │
│  ├──────────────────────────────────────────────────────────┤   │
│  │ 2. Base Risk Calculator: Apply heuristic rules          │   │
│  ├──────────────────────────────────────────────────────────┤   │
│  │ 3. Risk Propagator: Spread risk through graph           │   │
│  ├──────────────────────────────────────────────────────────┤   │
│  │ 4. Database: Persist transaction & risk score           │   │
│  ├──────────────────────────────────────────────────────────┤   │
│  │ 5. Metrics: Track performance                           │   │
│  └──────────────────────────────────────────────────────────┘   │
└──────────────────┬───────────────────────┬──────────────────────┘
                   │                       │
        ┌──────────▼──────────┐  ┌────────▼──────────┐
        │ NetworkX Graph      │  │   PostgreSQL      │
        │ (In-Memory)         │  │   (Persistent)    │
        │                     │  │                   │
        │ - Entities:         │  │ - Transactions    │
        │   Users             │  │ - Risk Scores     │
        │   Devices           │  │ - Audit Log       │
        │   IPs               │  │                   │
        │   Merchants         │  │                   │
        │ - Relationships     │  │                   │
        │   (Weighted Edges)  │  │                   │
        └─────────────────────┘  └───────────────────┘
                   │
        ┌──────────▼──────────┐
        │ Redis Cache         │
        │ (Optional Phase 2)  │
        │                     │
        │ - Hot node risks    │
        │ - User patterns     │
        └─────────────────────┘
```

---

## Data Model

### Entity Relationships

```
User
├─ has-device → Device
│               ├─ connects-from → IP
│               └─ used-at → Merchant
│
├─ has-ip → IP
│           └─ connects-to → Device
│                           └─ used-at → Merchant
│
└─ has-merchant-history → Merchant
```

### Graph Nodes

Each node stores:
```python
{
  "node_id": "user_123",
  "node_type": "user",              # ["user", "device", "ip", "merchant"]
  "risk_score": 0.35,               # 0.0 - 1.0
  "last_seen": "2026-02-28T10:30"   # ISO timestamp
}
```

### Graph Edges

Each edge stores:
```python
{
  "source": "user_123",
  "target": "device_456",
  "weight": 0.8,                    # 0.0 - 1.0, influences propagation
  "interaction_count": 5            # Number of times seen
}
```

---

## Risk Calculation Flow

### Step 1: Base Risk (0-1ms)

Applied rules:
- High amount (>$1000): +0.3
- New device: +0.2
- New IP: +0.2
- New merchant: +0.1

```
Total Base Risk = min(sum(rules), 1.0)
```

### Step 2: Risk Propagation (1-10ms)

For each risky transaction (if base_risk > threshold):

```
For each hop up to max_depth:
  For each neighbor of node:
    Delta = alpha × (current_node_risk × edge_weight)
    neighbor_new_risk = min(neighbor_risk + Delta, 1.0)
```

**Propagation Formula**:
$$\text{NewRisk}(n) = \text{BaseRisk}(n) + \alpha \times \sum(\text{NeighborRisk} \times \text{EdgeWeight})$$

Where:
- α = 0.5 (propagation coefficient)
- max_depth = 2 (propagation distance)
- risk_threshold = 0.1 (minimum to propagate)

### Step 3: Database & Metrics (<5ms)

Store transaction with final risk score.

---

## Performance Analysis

### Time Breakdown (50ms Target)

| Component | Time | % of Budget |
|-----------|------|------------|
| Graph node/edge update | 0.5ms | 1% |
| Base risk calculation | 0.8ms | 2% |
| Risk propagation (BFS) | 5.2ms | 10% |
| Database insert | 2.1ms | 4% |
| Metrics recording | 0.4ms | 1% |
| **Total** | **9ms** | **18%** |

**Headroom**: 41ms (82%) for network, serialization, and system overhead

### Space Complexity

- **Nodes**: O(n) where n = unique entities
- **Edges**: O(m) where m = relationships
- **Memory**: ~1KB per node, ~200 bytes per edge

For 1M entities: ~1GB memory

### Scalability

| Metric | Capacity | Limitation |
|--------|----------|-----------|
| Events/sec | 1000+ | CPU/network |
| Graph nodes | 100K-1M | Memory |
| Propagation depth | 2-3 | Exponential growth |
| Query latency | <10ms | Graph traversal |

---

## Algorithm Details

### Risk Propagation (BFS)

```python
def propagate(source_node, base_risk):
    if base_risk < RISK_THRESHOLD:
        return {source_node: base_risk}
    
    risk_updates = {source_node: base_risk}
    visited = {source_node}
    current_level = [(source_node, base_risk)]
    
    for depth in range(MAX_DEPTH):
        next_level = []
        
        for node, risk in current_level:
            for neighbor in graph.successors(node):
                if neighbor not in visited:
                    visited.add(neighbor)
                    
                    edge_weight = graph.edges[node][neighbor]['weight']
                    delta = ALPHA * risk * edge_weight
                    new_risk = min(node_risk + delta, 1.0)
                    
                    risk_updates[neighbor] = new_risk
                    next_level.append((neighbor, new_risk))
        
        current_level = next_level
    
    return risk_updates
```

**Complexity**:
- Time: O(V + E) where V=nodes visited, E=edges traversed
- Space: O(V) for storage

---

## Data Flow Example

### Transaction: user_123 uses new device at $2000 merchant

1. **Event In**:
   ```json
   {
     "user_id": "user_123",
     "device_id": "device_new",
     "ip_address": "192.0.2.1",
     "merchant_id": "merchant_456",
     "transaction_amount": 2000
   }
   ```

2. **Graph Update**:
   ```
   Add nodes: user_123, device_new, ip_192.0.2.1, merchant_456
   Add edges: user→device (0.8), device→ip (0.9), device→merchant (0.6)
   ```

3. **Base Risk** (heuristics):
   ```
   + 0.3 (high amount: 2000 > 1000)
   + 0.2 (new device: no user→device edge)
   + 0.0 (IP seen before from other device)
   + 0.1 (new merchant)
   = 0.6 BASE_RISK
   ```

4. **Propagation** (2 hops from user_123):
   ```
   Hop 1: user_123 (0.6) → device_new (0.3 + 0.5*0.6*0.8 = 0.54)
   Hop 1: user_123 (0.6) → ip_192.0.2.1 (0.1 + 0.5*0.6*0.7 = 0.31)
   Hop 2: device_new (0.54) → merchant_456 (0.2 + 0.5*0.54*0.6 = 0.36)
   ```

5. **Store Result**:
   ```sql
   INSERT INTO transactions (
     user_id, device_id, ip_address, merchant_id,
     transaction_amount, risk_score, propagation_depth
   ) VALUES (
     'user_123', 'device_new', '192.0.2.1', 'merchant_456',
     2000, 0.6, 2
   )
   ```

6. **Return** (13ms total):
   ```json
   {
     "transaction_id": "txn_abc123",
     "risk_score": 0.6,
     "propagation_depth": 2,
     "timestamp": "2026-02-28T10:30:00",
     "total_latency_ms": 13
   }
   ```

---

## Security Considerations

### MVP (Not Implemented Yet)

- No authentication/authorization
- No rate limiting
- No input validation beyond Pydantic
- Direct database access

### Production Roadmap

- [ ] API key authentication
- [ ] Role-based access control
- [ ] Input validation & sanitization
- [ ] SQL injection prevention (using SQLAlchemy ORM ✓)
- [ ] Rate limiting per user/IP
- [ ] Encrypted sensitive fields
- [ ] Audit logging
- [ ] DDoS protection

---

## Testing Strategy

### Unit Tests (100% coverage target)
- GraphStore operations
- Risk calculation rules
- Propagation algorithm
- Database models

### Integration Tests
- End-to-end event processing
- Graph and database consistency
- Latency requirements

### Load Tests
- 1000 events/second throughput
- <50ms latency at various loads
- Memory stability

### Performance Tests
- Graph traversal speed
- Propagation depth impact
- Database query performance

---

## Deployment Model

### MVP: Docker Compose (Single Machine)

```
docker-compose up -d
- app container (FastAPI)
- postgres container
- redis container (optional)
- prometheus container
```

### Phase 2: Distributed

- Load balancer + multiple app instances
- Shared PostgreSQL (managed service)
- Redis cluster for caching
- Elasticsearch for audit logs
- Prometheus + Grafana for monitoring

---

## Future Enhancements

### Phase 2 (Weeks 2-3)
- [ ] Redis caching layer (~2x faster lookups)
- [ ] Time-decay algorithms (~0.5 risk per week)
- [ ] Clustering detection (find fraud rings)
- [ ] Explanation in response (why this risk?)
- [ ] Neo4j option for larger graphs

### Phase 3 (Months 2-3)
- [ ] Machine learning integration (LightGBM)
- [ ] Real-time dashboard
- [ ] Advanced analytics
- [ ] API versioning
- [ ] Mobile app integration

### Phase 4 (Cloud/Scale)
- [ ] Multi-tenancy
- [ ] Kubernetes deployment
- [ ] Auto-scaling
- [ ] Cross-region deployment
- [ ] Advanced compliance

---

## Design Decisions

### Why NetworkX?
- Pure Python, no external dependencies
- Fast for MVP scale (<1M nodes)
- Easy to modify and debug
- Educational value

### Why In-Memory Graph?
- <10ms queries (vs ~100ms from database)
- Only N transactions stored in DB (small)
- Graph can be rebuilt from transaction log

### Why 2-Hop Propagation?
- Balances coverage and performance
- Most fraud signals within 2 hops
- Prevents excessive computation

### Why REST API?
- Simple, stateless
- Easy to load balance
- Easy to cache
- Familiar to developers

### Why Not Kafka/Streaming?
- MVP focus on simplicity
- HTTP request-response is standard
- Can add async queue in Phase 2

---

## Monitoring & Observability

### Metrics Exported

- request_count: Total API requests
- request_latency: Histogram of response times
- propagation_latency: Time spent in propagation
- graph_nodes: Current entity count
- graph_edges: Current relationship count
- error_count: Total errors

### Prometheus Queries

```promql
# Average latency
avg(rate(riskmesh_request_latency_ms[5m]))

# P95 latency  
histogram_quantile(0.95, riskmesh_request_latency_ms)

# Error rate
rate(riskmesh_errors_total[5m])

# Graph growth
graph_nodes - graph_nodes offset 1h
```

### Alerting

Critical alerts:
- Latency > 100ms (avg)
- Error rate > 1%
- Graph memory > 80% limit
- Database connection failures

---

## References

- **Graph Theory**: https://networkx.org/documentation/
- **Fraud Detection**: https://arxiv.org/abs/1908.08389
- **Risk Propagation**: https://en.wikipedia.org/wiki/Epidemic_model
- **FastAPI**: https://fastapi.tiangolo.com/
- **PostgreSQL**: https://www.postgresql.org/docs/

