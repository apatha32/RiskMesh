"""
Risk Engine - Main orchestrator
"""
from typing import Dict, Any
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class RiskEngine:
    """
    Main risk calculation engine.
    
    Orchestrates:
    - Graph updates
    - Base risk calculation
    - Risk propagation
    - Result persistence
    """
    
    def __init__(self, graph_store, propagator, base_risk_calc, database):
        """
        Initialize risk engine.
        
        Args:
            graph_store: GraphStore instance
            propagator: RiskPropagator instance
            base_risk_calc: BaseRiskCalculator instance
            database: Database connection
        """
        self.graph_store = graph_store
        self.propagator = propagator
        self.base_risk_calc = base_risk_calc
        self.database = database
    
    def process_event(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process transaction event end-to-end.
        
        Flow:
        1. Add/update nodes for user, device, ip, merchant
        2. Add/update edges
        3. Calculate base risk
        4. Run propagation
        5. Store in database
        6. Return result
        
        Args:
            event: Event with user_id, device_id, ip_address, merchant_id, transaction_amount
            
        Returns:
            Result with risk_score, propagation_depth, timestamp
        """
        import time
        start_time = time.time()
        
        user_id = event.get("user_id")
        device_id = event.get("device_id")
        ip_address = event.get("ip_address")
        merchant_id = event.get("merchant_id")
        amount = event.get("transaction_amount", 0.0)
        
        # Step 1: Add/update nodes
        self.graph_store.add_node(f"user_{user_id}", "user", 0.0)
        self.graph_store.add_node(f"device_{device_id}", "device", 0.0)
        self.graph_store.add_node(f"ip_{ip_address}", "ip", 0.0)
        self.graph_store.add_node(f"merchant_{merchant_id}", "merchant", 0.0)
        
        # Step 2: Add/update edges
        self.graph_store.add_edge(f"user_{user_id}", f"device_{device_id}", weight=0.8)
        self.graph_store.add_edge(f"user_{user_id}", f"ip_{ip_address}", weight=0.7)
        self.graph_store.add_edge(f"device_{device_id}", f"ip_{ip_address}", weight=0.9)
        self.graph_store.add_edge(f"device_{device_id}", f"merchant_{merchant_id}", weight=0.6)
        
        # Step 3: Calculate base risk
        base_risk = self.base_risk_calc.calculate(event, self.graph_store)
        
        # Update source node with base risk
        self.graph_store.update_node_risk(f"user_{user_id}", base_risk)
        
        # Step 4: Run propagation
        propagation_start = time.time()
        risk_updates = self.propagator.propagate(self.graph_store, f"user_{user_id}", base_risk)
        propagation_time = (time.time() - propagation_start) * 1000  # ms
        
        # Apply risk updates to graph
        propagation_depth = 0
        for node_id, risk_score in risk_updates.items():
            self.graph_store.update_node_risk(node_id, risk_score)
            # Track max depth
            if node_id != f"user_{user_id}":
                depth = len(self.graph_store.get_neighbors(f"user_{user_id}", depth=1))
                propagation_depth = max(propagation_depth, depth)
        
        # Get final risk score
        final_user_node = self.graph_store.get_node(f"user_{user_id}")
        final_risk = final_user_node['risk_score'] if final_user_node else base_risk
        
        # Step 5: Store in database
        from uuid import uuid4
        transaction_id = str(uuid4())
        
        try:
            db_session = self.database.get_session()
            from app.db.models import TransactionModel
            
            transaction = TransactionModel(
                id=transaction_id,
                user_id=user_id,
                device_id=device_id,
                ip_address=ip_address,
                merchant_id=merchant_id,
                transaction_amount=amount,
                risk_score=final_risk,
                propagation_depth=propagation_depth,
                timestamp=datetime.utcnow()
            )
            
            db_session.add(transaction)
            db_session.commit()
            logger.info(f"Transaction {transaction_id} stored in database")
        except Exception as e:
            logger.error(f"Failed to store transaction: {e}")
        finally:
            if 'db_session' in locals():
                db_session.close()
        
        # Calculate total latency
        total_time = (time.time() - start_time) * 1000  # ms
        
        # Step 6: Return result
        result = {
            "transaction_id": transaction_id,
            "risk_score": round(final_risk, 3),
            "base_risk": round(base_risk, 3),
            "propagation_depth": propagation_depth,
            "propagation_latency_ms": round(propagation_time, 2),
            "total_latency_ms": round(total_time, 2),
            "timestamp": datetime.utcnow()
        }
        
        logger.info(f"Event processed: {result}")
        return result
