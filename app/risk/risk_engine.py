"""
Risk Engine - Main orchestrator
"""
from typing import Dict, Any, Optional
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
    - Caching
    - Time decay
    - Clustering detection
    - Risk explanation
    """
    
    def __init__(self, graph_store, propagator, base_risk_calc, database, 
                 cache=None, time_decay=None, clustering_detector=None, explainer=None):
        """
        Initialize risk engine.
        
        Args:
            graph_store: GraphStore instance
            propagator: RiskPropagator instance
            base_risk_calc: BaseRiskCalculator instance
            database: Database connection
            cache: RedisCache instance (optional)
            time_decay: TimeDecayCalculator instance (optional)
            clustering_detector: ClusteringDetector instance (optional)
            explainer: RiskExplainer instance (optional)
        """
        self.graph_store = graph_store
        self.propagator = propagator
        self.base_risk_calc = base_risk_calc
        self.database = database
        self.cache = cache
        self.time_decay = time_decay
        self.clustering_detector = clustering_detector
        self.explainer = explainer
    
    def process_event(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process transaction event end-to-end with Phase 2 enhancements.
        
        Flow:
        1. Check cache for user risk
        2. Add/update nodes for user, device, ip, merchant
        3. Add/update edges
        4. Calculate base risk
        5. Apply time decay to nearby nodes
        6. Run propagation
        7. Detect clustering/fraud rings
        8. Generate explanation
        9. Store in database
        10. Update cache
        11. Return result
        
        Args:
            event: Event with user_id, device_id, ip_address, merchant_id, transaction_amount
            
        Returns:
            Result with risk_score, propagation_depth, timestamp, explanation, clustering_info
        """
        import time
        start_time = time.time()
        
        user_id = event.get("user_id")
        device_id = event.get("device_id")
        ip_address = event.get("ip_address")
        merchant_id = event.get("merchant_id")
        amount = event.get("transaction_amount", 0.0)
        
        # Step 1: Check cache
        cached_risk = None
        if self.cache:
            try:
                cached_risk = self.cache.get_user_risk(user_id)
                if cached_risk:
                    logger.info(f"Cache hit for user {user_id}: {cached_risk}")
            except Exception as e:
                logger.warning(f"Cache lookup failed: {e}")
        
        # If we have cached risk and it's recent enough, use it with small update
        if cached_risk and cached_risk > 0.7:
            logger.debug(f"Using cached risk for user {user_id}")
            # Still do minimal processing
            base_risk = cached_risk
        else:
            # Step 2: Add/update nodes
            self.graph_store.add_node(f"user_{user_id}", "user", 0.0)
            self.graph_store.add_node(f"device_{device_id}", "device", 0.0)
            self.graph_store.add_node(f"ip_{ip_address}", "ip", 0.0)
            self.graph_store.add_node(f"merchant_{merchant_id}", "merchant", 0.0)
            
            # Step 3: Add/update edges
            self.graph_store.add_edge(f"user_{user_id}", f"device_{device_id}", weight=0.8)
            self.graph_store.add_edge(f"user_{user_id}", f"ip_{ip_address}", weight=0.7)
            self.graph_store.add_edge(f"device_{device_id}", f"ip_{ip_address}", weight=0.9)
            self.graph_store.add_edge(f"device_{device_id}", f"merchant_{merchant_id}", weight=0.6)
            
            # Step 4: Calculate base risk
            base_risk = self.base_risk_calc.calculate(event, self.graph_store)
            
            # Step 5: Apply time decay to nearby nodes
            if self.time_decay:
                try:
                    self.time_decay.apply_decay_to_graph(self.graph_store)
                except Exception as e:
                    logger.warning(f"Time decay failed: {e}")
            
            # Update source node with base risk
            self.graph_store.update_node_risk(f"user_{user_id}", base_risk)
            
            # Step 6: Run propagation
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
        
        # Step 7: Detect clustering/fraud rings
        clusters = None
        clustering_boost = 0.0
        if self.clustering_detector:
            try:
                clusters = self.clustering_detector.detect_all_clusters(self.graph_store)
                if clusters and clusters.get('rings'):
                    # If user is part of fraud ring, boost risk
                    clustering_boost = 0.15
                    final_risk = min(1.0, final_risk + clustering_boost)
                    logger.info(f"Fraud ring detected for user {user_id}, boosted risk to {final_risk}")
            except Exception as e:
                logger.warning(f"Clustering detection failed: {e}")
                clusters = None
        
        # Step 8: Generate explanation
        explanation = None
        if self.explainer:
            try:
                # Calculate propagated risk (risk after applying propagation formula)
                propagated_risk = base_risk
                if 'risk_updates' in locals():
                    max_propagated = base_risk
                    for node_id, risk_score in risk_updates.items():
                        if node_id != f"user_{user_id}":
                            max_propagated = max(max_propagated, risk_score)
                    propagated_risk = max_propagated
                
                # Calculate age (days since first transaction)
                age_days = 0.0
                user_node = self.graph_store.get_node(f"user_{user_id}")
                if user_node and 'last_seen' in user_node:
                    from datetime import datetime
                    age_seconds = (datetime.utcnow() - user_node['last_seen']).total_seconds()
                    age_days = max(0, age_seconds / (24 * 3600))
                
                # Decayed risk is the base risk after time decay
                decayed_risk = final_risk - clustering_boost  # Remove cluster boost to get decayed value
                
                explanation = self.explainer.explain_final_risk(
                    base_risk=round(base_risk, 3),
                    propagated_risk=round(propagated_risk, 3),
                    age_days=age_days,
                    decayed_risk=round(decayed_risk, 3),
                    cluster_boost=round(clustering_boost, 3)
                )
            except Exception as e:
                logger.warning(f"Explanation generation failed: {e}")
                explanation = {"recommendation": "review", "reason": str(e)}
        
        # Step 9: Store in database
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
        
        # Step 10: Update cache
        if self.cache and final_risk > 0.3:
            try:
                self.cache.set_user_risk(user_id, final_risk, ttl_minutes=30)
                logger.info(f"Cached risk for user {user_id}: {final_risk}")
            except Exception as e:
                logger.warning(f"Cache update failed: {e}")
        
        # Calculate total latency
        total_time = (time.time() - start_time) * 1000  # ms
        
        # Step 11: Return result
        result = {
            "transaction_id": transaction_id,
            "risk_score": round(final_risk, 3),
            "base_risk": round(base_risk, 3),
            "propagation_depth": propagation_depth,
            "clustering_boost": round(clustering_boost, 3),
            "propagation_latency_ms": round(propagation_time if 'propagation_time' in locals() else 0, 2),
            "total_latency_ms": round(total_time, 2),
            "timestamp": datetime.utcnow(),
            "explanation": explanation,
            "clustering_info": clusters,
            "cached": cached_risk is not None
        }
        
        logger.info(f"Event processed: {result}")
        return result
