# RiskMesh MVP

Real Time Graph Based Risk Propagation Engine

## 🎯 Vision

RiskMesh is a fraud intelligence engine that models relationships between users, devices, IPs, and transactions as a graph and propagates risk dynamically across connected entities.

Instead of scoring each transaction independently, it scores based on network effects.

## 🧱 Architecture

**Zero Cost - Fully Local - Free & Open Source**

- **FastAPI**: REST API for events
- **NetworkX**: In-memory graph for relationships
- **PostgreSQL**: Transaction persistence
- **Redis**: Caching layer (optional Phase 2)
- **Prometheus**: Metrics and observability
- **Docker Compose**: Local orchestration

## 🔄 Data Flow

```
Transaction → API → Graph Update → Risk Calculation → Propagation → Response
                                        ↓
                                   PostgreSQL
```

**Target**: <50ms end-to-end latency

## 🧠 Core Concepts

### Entities (Nodes)
- User
- Device
- IP
- Card
- Merchant

### Relationships (Edges)
- user uses device
- user uses IP
- card used at merchant
- device connects from IP

Each edge has a weight for propagation.

### Risk Propagation Formula

```
NewRisk(node) = BaseRisk + alpha × sum(neighborRisk × edgeWeight)
```

Where:
- `alpha` = 0.5 (propagation coefficient)
- `depth` = 2 hops (propagation depth)
- Only propagate when incoming risk > threshold

## 📁 Project Structure

```
riskmesh/
├── app/
│   ├── main.py                 # FastAPI app entry
│   ├── api/
│   │   └── routes.py           # API endpoints
│   ├── graph/
│   │   ├── graph_store.py      # NetworkX graph
│   │   └── propagation.py      # Risk propagation
│   ├── risk/
│   │   ├── base_risk.py        # Base risk rules
│   │   └── risk_engine.py      # Orchestrator
│   ├── db/
│   │   ├── models.py           # SQLAlchemy models
│   │   └── database.py         # DB connection
│   └── metrics/
│       └── metrics.py          # Prometheus metrics
├── tests/
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
├── prometheus.yml
├── load_test.py
└── README.md
```

## 🚀 Getting Started

### Prerequisites
- Docker & Docker Compose
- Python 3.11+

### Installation

```bash
cd riskmesh
docker-compose up -d
```

This starts:
- FastAPI app on `http://localhost:8000`
- PostgreSQL on `localhost:5432`
- Redis on `localhost:6379`
- Prometheus on `http://localhost:9090`

### API Endpoints

#### Health Check
```bash
curl http://localhost:8000/health
```

#### Process Event
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

#### Get Statistics
```bash
curl http://localhost:8000/api/stats
```

#### Prometheus Metrics
```bash
curl http://localhost:8000/metrics
```

## 📊 Performance Goals

- **Throughput**: 1000 events/second locally
- **Propagation**: <10ms
- **End-to-end**: <50ms
- **Memory**: Stable growth

## 🧪 Load Testing

Using Locust:

```bash
locust -f load_test.py --host http://localhost:8000
```

Then open `http://localhost:8089` to start load testing.

## 🧠 What's Next (Phase 2)

- Redis caching for hot nodes
- Time decay for risk scores
- Clustering detection
- Explanation field in responses
- Neo4j integration
- Dashboard

## 📝 Development Workflow

Each module has clear responsibilities:

1. **graph_store.py**: Manage entities and relationships
2. **propagation.py**: Algorithm for risk propagation
3. **base_risk.py**: Initial risk calculation
4. **risk_engine.py**: Orchestrate the flow
5. **routes.py**: Expose as API
6. **metrics.py**: Track performance

## 🔒 MVP Constraints

- ✅ Backend focused
- ✅ Fully local
- ✅ No paid services
- ❌ No dashboard/frontend
- ❌ No cloud deployment
- ❌ No Kubernetes

## 🏆 Recruiter Highlights

- Graph modeling for fraud
- Low latency API design
- Dynamic risk propagation
- Real-time streaming behavior
- Observability with Prometheus
- Clean Docker setup
- Clear separation of concerns
- Production-ready architecture

## 📄 License

MIT

## 👤 Author

RiskMesh Team
