"""
Prometheus Metrics
"""
from prometheus_client import Counter, Histogram, Gauge
import logging

logger = logging.getLogger(__name__)

# Counters
request_counter = Counter('riskmesh_requests_total', 'Total requests processed')
error_counter = Counter('riskmesh_errors_total', 'Total errors')

# Histograms
request_latency = Histogram('riskmesh_request_latency_ms', 'Request latency in milliseconds')
propagation_latency = Histogram('riskmesh_propagation_latency_ms', 'Risk propagation latency in milliseconds')

# Gauges
graph_node_count = Gauge('riskmesh_graph_nodes', 'Total nodes in graph')
graph_edge_count = Gauge('riskmesh_graph_edges', 'Total edges in graph')
event_rate = Gauge('riskmesh_event_rate', 'Events processed per second')
