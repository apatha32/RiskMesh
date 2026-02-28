"""
Load testing script for RiskMesh using Locust
Tests performance goals:
- 1000 events/second
- Propagation <10ms
- End-to-end <50ms
"""
from locust import HttpUser, task, between, events
import json
import random
import logging
import time

logger = logging.getLogger(__name__)


class RiskMeshUser(HttpUser):
    """Simulated RiskMesh user for load testing."""
    
    wait_time = between(0.01, 0.1)  # 10-100ms between requests
    
    def on_start(self):
        """Initialize user."""
        self.user_ids = [f"user_{i}" for i in range(1, 101)]
        self.device_ids = [f"device_{i}" for i in range(1, 51)]
        self.merchant_ids = [f"merchant_{i}" for i in range(1, 21)]
        self.ips = [
            f"{random.randint(1, 255)}.{random.randint(1, 255)}.{random.randint(1, 255)}.{random.randint(1, 255)}"
            for _ in range(50)
        ]
    
    @task(1)
    def send_normal_event(self):
        """Send a normal transaction event."""
        payload = {
            "user_id": random.choice(self.user_ids),
            "device_id": random.choice(self.device_ids),
            "ip_address": random.choice(self.ips),
            "merchant_id": random.choice(self.merchant_ids),
            "transaction_amount": round(random.uniform(10, 500), 2)
        }
        
        with self.client.post(
            "/api/event",
            json=payload,
            catch_response=True
        ) as response:
            if response.status_code == 200:
                response.success()
                # Log latency
                logger.debug(f"Event processed in {response.elapsed.total_seconds() * 1000:.2f}ms")
            else:
                response.failure(f"Failed with status {response.status_code}")
    
    @task(1)
    def send_high_risk_event(self):
        """Send a high-risk transaction."""
        payload = {
            "user_id": f"user_{random.randint(1, 100)}",
            "device_id": f"device_new_{random.randint(1000, 9999)}",  # New device
            "ip_address": f"{random.randint(1, 255)}.{random.randint(1, 255)}.{random.randint(1, 255)}.{random.randint(1, 255)}",  # New IP
            "merchant_id": f"merchant_new_{random.randint(100, 999)}",  # New merchant
            "transaction_amount": round(random.uniform(2000, 5000), 2)  # High amount
        }
        
        with self.client.post(
            "/api/event",
            json=payload,
            catch_response=True
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Failed with status {response.status_code}")
    
    @task(1)
    def get_stats(self):
        """Get system statistics."""
        with self.client.get("/api/stats", catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Failed with status {response.status_code}")
    
    @task(1)
    def health_check(self):
        """Check health endpoint."""
        with self.client.get("/health", catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Failed with status {response.status_code}")


# Global stats tracking
request_times = []
event_count = 0


@events.request.add_listener
def on_request(request_type, name, response_time, response_length, response, context, exception, **kwargs):
    """Track request metrics."""
    global request_times, event_count
    
    if request_type == "POST" and "/api/event" in name:
        request_times.append(response_time)
        event_count += 1
        
        if len(request_times) >= 1000:
            avg_time = sum(request_times) / len(request_times)
            p95_time = sorted(request_times)[int(len(request_times) * 0.95)]
            p99_time = sorted(request_times)[int(len(request_times) * 0.99)]
            max_time = max(request_times)
            
            logger.info(f"\n=== Performance Metrics ===")
            logger.info(f"Events processed: {event_count}")
            logger.info(f"Avg latency: {avg_time:.2f}ms")
            logger.info(f"P95 latency: {p95_time:.2f}ms")
            logger.info(f"P99 latency: {p99_time:.2f}ms")
            logger.info(f"Max latency: {max_time:.2f}ms")
            
            # Check against MVP goals
            if avg_time < 50:
                logger.info("✓ Average latency goal achieved (<50ms)")
            else:
                logger.warning("✗ Average latency above goal (>50ms)")
            
            request_times = []


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    """Print final stats when test stops."""
    logger.info("\n=== Final Test Summary ===")
    logger.info(f"Total events processed: {event_count}")
    logger.info(f"Test duration: {environment.stats.total.response_times[-1] / 1000:.2f}s")
    
    # Calculate throughput
    if environment.stats.total.num_requests > 0:
        throughput = event_count / (environment.stats.total.response_times[-1] / 1000) if environment.stats.total.response_times else 0
        logger.info(f"Throughput: {throughput:.0f} events/second")
        
        if throughput >= 1000:
            logger.info("✓ Throughput goal achieved (>=1000 events/sec)")
        else:
            logger.warning(f"✗ Throughput below goal (<1000 events/sec): {throughput:.0f}")

