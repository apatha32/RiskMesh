"""
Load testing script using Locust
"""
from locust import HttpUser, task, between
import json
import random
import logging

logger = logging.getLogger(__name__)


class RiskMeshUser(HttpUser):
    """Simulated RiskMesh user."""
    
    wait_time = between(0.1, 0.5)
    
    @task
    def send_event(self):
        """Send a transaction event."""
        payload = {
            "user_id": f"user_{random.randint(1, 100)}",
            "device_id": f"device_{random.randint(1, 50)}",
            "ip_address": f"{random.randint(1, 255)}.{random.randint(1, 255)}.{random.randint(1, 255)}.{random.randint(1, 255)}",
            "merchant_id": f"merchant_{random.randint(1, 20)}",
            "transaction_amount": round(random.uniform(10, 5000), 2)
        }
        
        self.client.post("/api/event", json=payload)
