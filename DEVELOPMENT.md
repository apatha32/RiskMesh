# RiskMesh Development Guide

## Architecture Overview

RiskMesh is a modular fraud intelligence engine with clear separation of concerns:

```
API Request
    ↓
API Routes (/app/api/routes.py)
    ↓
Risk Engine (/app/risk/risk_engine.py)
    ├─→ Base Risk Calculator (/app/risk/base_risk.py)
    ├─→ Graph Store (/app/graph/graph_store.py)
    ├─→ Risk Propagator (/app/graph/propagation.py)
    ├─→ Database (/app/db/database.py)
    └─→ Metrics (/app/metrics/metrics.py)
    ↓
Response (with risk_score, propagation_depth, transaction_id)
```

## Module Responsibilities

### GraphStore (`app/graph/graph_store.py`)

**Purpose**: Manages NetworkX directed graph of entities and relationships

**Key Methods**:
- `add_node(node_id, node_type, risk_score)` - Add/update entity
- `add_edge(source, target, weight)` - Add/update relationship
- `get_neighbors(node_id, depth)` - Find connected nodes
- `update_node_risk(node_id, risk_score)` - Update node risk

**Design**:
- Directed graph (user → device, device → IP)
- Node attributes: type, risk_score, last_seen
- Edge attributes: weight, interaction_count
- All in-memory for <10ms access

### RiskPropagator (`app/graph/propagation.py`)

**Purpose**: Propagates risk through graph using BFS algorithm

**Formula**:
```
NewRisk(node) = BaseRisk + alpha × sum(neighborRisk × edgeWeight)
```

**Key Parameters**:
- `alpha = 0.5` - Propagation coefficient (0.0-1.0)
- `max_depth = 2` - How many hops to propagate
- `risk_threshold = 0.1` - Minimum risk to trigger propagation

**Design**:
- Breadth-first search for efficiency
- Risk capped at 1.0
- Early exit if below threshold

### BaseRiskCalculator (`app/risk/base_risk.py`)

**Purpose**: Calculates initial risk for transaction

**Rules**:
1. High amount: +0.3 if > $1000
2. New device: +0.2 if user-device edge missing
3. New IP: +0.2 if user-IP edge missing
4. New merchant: +0.1 if merchant unseen

**Design**:
- Rule-based (easy to modify)
- Future: plug in LightGBM/ML model
- Combined risk capped at 1.0

### RiskEngine (`app/risk/risk_engine.py`)

**Purpose**: Orchestrates entire flow

**Flow**:
1. Create/update graph nodes (user, device, IP, merchant)
2. Create/update edges between entities
3. Calculate base risk
4. Run risk propagation
5. Store result in database
6. Record metrics

### Database (`app/db/database.py` & `models.py`)

**Purpose**: Persist transaction records

**Schema**:
```sql
CREATE TABLE transactions (
  id VARCHAR PRIMARY KEY,
  user_id VARCHAR,
  device_id VARCHAR,
  ip_address VARCHAR,
  merchant_id VARCHAR,
  transaction_amount FLOAT,
  risk_score FLOAT,
  propagation_depth INTEGER,
  timestamp DATETIME
);
```

**Design**:
- Graph lives in memory (fast)
- Only transactions recorded (small storage)
- No graph persistence in MVP

### API Routes (`app/api/routes.py`)

**Purpose**: HTTP interface to engine

**Endpoints**:
- `POST /api/event` - Process transaction, return risk
- `GET /api/stats` - Graph statistics
- `GET /health` - Health check
- `GET /metrics` - Prometheus metrics

---

## Development Workflow

### Set Up Development Environment

```bash
# Install dependencies
pip install -r requirements.txt

# Run tests
pytest tests/ -v

# Run specific test
pytest tests/test_graph_store.py::test_add_node -v
```

### Adding New Features

**Example: Add new risk rule**

1. Update `BaseRiskCalculator.calculate()`:

```python
# Add new rule
def calculate(self, event, graph):
    risk = 0.0
    
    # Existing rules...
    
    # New rule: Velocity check
    recent_count = self.count_recent_transactions(event["user_id"])
    if recent_count > 5:  # 5+ transactions in last 10 mins
        risk += 0.25
    
    return min(risk, 1.0)
```

2. Write test:

```python
# tests/test_base_risk.py
def test_velocity_rule_increases_risk(calculator, graph):
    # Setup: user with recent transactions
    # Execute
    risk = calculator.calculate(event, graph)
    # Assert: risk includes velocity component
    assert risk >= 0.25
```

3. Run tests:
```bash
pytest tests/test_base_risk.py -v
```

4. Commit:
```bash
git commit -m "Add velocity check to base risk calculation"
```

### Testing Patterns

**Unit Tests** (isolated):
```python
def test_single_responsibility():
    component = Component()
    result = component.do_something()
    assert result == expected
```

**Integration Tests** (end-to-end):
```python
def test_full_flow(risk_engine):
    event = {...}
    result = risk_engine.process_event(event)
    assert "risk_score" in result
```

**Fixture Pattern** (reusable):
```python
@pytest.fixture
def graph():
    return GraphStore()

def test_something(graph):
    graph.add_node(...)
    # test using graph
```

---

## Code Style

Follow PEP 8 with these conventions:

```python
# Imports: standard, then third-party, then local
import logging
from typing import Dict, List

import networkx as nx
from fastapi import FastAPI

from app.graph.graph_store import GraphStore

# Docstrings: Module, class, function
"""Module docstring."""

class MyClass:
    """Class docstring."""
    
    def my_method(self):
        """Method docstring with description and Args/Returns."""
        pass

# Type hints
def calculate_risk(event: Dict[str, Any], graph: GraphStore) -> float:
    """Calculate risk."""
    pass

# Logging
logger = logging.getLogger(__name__)
logger.info("Event processed with risk %.3f", risk_score)
```

---

## Performance Considerations

### Latency Targets

- **Base risk calculation**: <1ms
- **Risk propagation**: <10ms  
- **Database insert**: <5ms
- **Total end-to-end**: <50ms

### Profiling

Profile slow endpoints:

```bash
# Add to app code
from line_profiler import LineProfiler

profiler = LineProfiler()
profiler.add_function(risk_engine.process_event)
profiler.enable()

# ... run requests ...

profiler.print_stats()
```

### Optimization Checklist

- [ ] Graph queries are <10ms
- [ ] Propagation depth limited to 2
- [ ] No N+1 database queries
- [ ] Risk threshold prevents unnecessary propagation
- [ ] No memory leaks (graph bounded)

---

## Common Tasks

### Debug a Failing Test

```bash
# Run with verbose output
pytest tests/test_something.py -vv

# Run with print statements
pytest tests/test_something.py -s

# Run with debugger
pytest tests/test_something.py --pdb
```

### Add a New Endpoint

```python
# app/api/routes.py
@router.post("/api/new-endpoint")
async def new_endpoint(request: NewRequest):
    """Documentation."""
    result = RISK_ENGINE.do_something(request)
    return NewResponse(result=result)
```

### Add a Metric

```python
# app/metrics/metrics.py
new_counter = Counter('riskmesh_something', 'Description')

# Use in code
new_counter.inc()
histogram.observe(value)
gauge.set(value)
```

### Create a Database Migration

```python
# app/db/models.py
class NewModel(Base):
    __tablename__ = "new_table"
    id = Column(String, primary_key=True)
    # ... columns ...

# In app startup
database.init_db()  # Creates tables
```

---

## Git Workflow

```bash
# Create feature branch
git checkout -b feature/new-risk-rule

# Make changes, commit
git add app/risk/base_risk.py tests/test_base_risk.py
git commit -m "Add new risk rule: velocity check"

# Push to GitHub
git push origin feature/new-risk-rule

# Create pull request on GitHub
# After review and merge, delete branch
```

### Commit Message Format

```
<type>: <subject>

<body>

<footer>
```

Types: `feat`, `fix`, `test`, `docs`, `refactor`, `perf`

Example:
```
feat: add velocity-based risk rule

Add check for high transaction frequency. Users with 5+ transactions
in 10 minutes get +0.25 risk increase.

See #42
```

---

## Documentation

### Update README

Every feature should update README with:
- What it does
- How to use it
- Performance implications

### Add Docstrings

```python
def process_event(self, event: Dict[str, Any]) -> Dict[str, Any]:
    """
    Process transaction event end-to-end.
    
    Responsible for:
    1. Adding/updating graph nodes and edges
    2. Calculating base risk
    3. Propagating risk through graph
    4. Storing in database
    
    Args:
        event: Transaction with user_id, device_id, ip_address, ...
        
    Returns:
        Result with transaction_id, risk_score, propagation_depth
        
    Raises:
        DatabaseError: If database insert fails
        
    Performance:
        Target <50ms end-to-end
    """
```

---

## Debugging Tips

### Enable Debug Logging

```python
# In app/main.py
logging.basicConfig(level=logging.DEBUG)
```

### Print Graph State

```python
# In code
print(f"Nodes: {graph.graph.nodes(data=True)}")
print(f"Edges: {graph.graph.edges(data=True)}")
```

### Inspect Propagation

```python
# In propagator
logger.debug(f"Propagating from {source}: base_risk={base_risk}")
logger.debug(f"Updated {node_id}: {risk_updates[node_id]}")
```

---

## Contributing

1. Fork the repo
2. Create feature branch
3. Write tests
4. Ensure all tests pass
5. Make commit
6. Push and create pull request
7. Wait for review
8. Merge!

Thank you for contributing!

