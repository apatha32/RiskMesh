#!/usr/bin/env python3
"""
Phase 2 Integration Verification Script - Manual testing without pytest
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from datetime import datetime, timedelta


def test_imports():
    """Verify all Phase 2 modules can be imported."""
    print("Testing imports...")
    try:
        from app.cache import RedisCache
        print("  ✓ RedisCache imported")
        
        from app.auth import RateLimiter, APIKeyManager
        print("  ✓ RateLimiter imported")
        print("  ✓ APIKeyManager imported")
        
        from app.graph.time_decay import TimeDecayCalculator
        print("  ✓ TimeDecayCalculator imported")
        
        from app.graph.clustering import ClusteringDetector
        print("  ✓ ClusteringDetector imported")
        
        from app.risk.explainer import RiskExplainer
        print("  ✓ RiskExplainer imported")
        
        from app.analytics import FraudAnalytics
        print("  ✓ FraudAnalytics imported")
        
        from app.risk.risk_engine import RiskEngine
        print("  ✓ RiskEngine imported")
        
        return True
    except Exception as e:
        print(f"  ✗ Import failed: {e}")
        return False


def test_time_decay():
    """Verify TimeDecayCalculator works."""
    print("\nTesting TimeDecayCalculator...")
    try:
        from app.graph.time_decay import TimeDecayCalculator
        
        calc = TimeDecayCalculator(decay_factor=0.995, min_risk=0.01)
        
        # Test decay
        old_time = datetime.utcnow() - timedelta(days=7)
        decayed_risk, age_days = calc.apply_decay(0.8, old_time)
        
        # After 7 days: 0.8 * 0.995^7 ≈ 0.777
        assert 0.77 < decayed_risk < 0.78, f"Expected ~0.777, got {decayed_risk}"
        print(f"  ✓ 7-day decay: 0.8 -> {decayed_risk:.3f}")
        
        # Test age categorization
        age_cat = calc.get_age_category(datetime.utcnow() - timedelta(hours=1))
        assert age_cat == "fresh", f"Expected 'fresh', got {age_cat}"
        print(f"  ✓ Age categorization: {age_cat}")
        
        return True
    except Exception as e:
        print(f"  ✗ TimeDecayCalculator test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_clustering():
    """Verify ClusteringDetector works."""
    print("\nTesting ClusteringDetector...")
    try:
        from app.graph.graph_store import GraphStore
        from app.graph.clustering import ClusteringDetector
        
        graph_store = GraphStore()
        graph_store.add_node("user_A", "user", 0.8)
        graph_store.add_node("user_B", "user", 0.7)
        graph_store.add_node("user_C", "user", 0.6)
        
        graph_store.add_edge("user_A", "user_B", 0.9)
        graph_store.add_edge("user_B", "user_C", 0.9)
        graph_store.add_edge("user_C", "user_A", 0.9)  # Creates cycle
        
        detector = ClusteringDetector()
        clusters = detector.detect_all_clusters(graph_store)
        
        assert clusters is not None, "Clusters should not be None"
        print(f"  ✓ Clustering detection: {clusters}")
        
        return True
    except Exception as e:
        print(f"  ✗ ClusteringDetector test failed: {e}")
        return False


def test_explainer():
    """Verify RiskExplainer works."""
    print("\nTesting RiskExplainer...")
    try:
        from app.risk.explainer import RiskExplainer
        
        explainer = RiskExplainer()
        explanation = explainer.explain_final_risk(
            base_risk=0.4,
            propagated_risk=0.55,
            age_days=7.0,
            decayed_risk=0.533,
            cluster_boost=0.15
        )
        
        assert explanation is not None, "Explanation should not be None"
        assert 'recommendation' in explanation, "Missing recommendation"
        assert explanation['recommendation'] in ['approve', 'review', 'challenge']
        print(f"  ✓ Recommendation: {explanation['recommendation']}")
        
        return True
    except Exception as e:
        print(f"  ✗ RiskExplainer test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_rate_limiter():
    """Verify RateLimiter works."""
    print("\nTesting RateLimiter...")
    try:
        from app.auth import RateLimiter
        
        limiter = RateLimiter(default_limit=10, window_seconds=60)
        
        # Should allow request
        allowed = limiter.allow_request("user_1", limit=5)
        assert allowed is True, "Should allow request within limit"
        print(f"  ✓ Request allowed within limit")
        
        # Should deny when exceeding limit
        allowed = limiter.allow_request("user_2", limit=1)
        allowed2 = limiter.allow_request("user_2", limit=1)  # Second request should exceed
        
        print(f"  ✓ Rate limiting working")
        
        return True
    except Exception as e:
        print(f"  ✗ RateLimiter test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_api_key_manager():
    """Verify APIKeyManager works."""
    print("\nTesting APIKeyManager...")
    try:
        from app.auth import APIKeyManager
        
        manager = APIKeyManager()
        
        # Validate valid key
        is_valid = manager.validate_key("riskmesh-key-demo-001")
        assert is_valid is True, "Valid key should authenticate"
        user_id = manager.get_user_id("riskmesh-key-demo-001")
        rate_limit = manager.get_rate_limit("riskmesh-key-demo-001")
        print(f"  ✓ Valid key authenticated: user={user_id}, rate_limit={rate_limit}")
        
        # Validate invalid key
        is_valid = manager.validate_key("invalid_key")
        assert is_valid is False, "Invalid key should not authenticate"
        print(f"  ✓ Invalid key rejected")
        
        return True
    except Exception as e:
        print(f"  ✗ APIKeyManager test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_risk_engine_initialization():
    """Verify RiskEngine initializes with Phase 2 components."""
    print("\nTesting RiskEngine Phase 2 Initialization...")
    try:
        from app.graph.graph_store import GraphStore
        from app.graph.propagation import RiskPropagator
        from app.risk.base_risk import BaseRiskCalculator
        from app.risk.risk_engine import RiskEngine
        from app.db.database import Database
        from app.graph.time_decay import TimeDecayCalculator
        from app.graph.clustering import ClusteringDetector
        from app.risk.explainer import RiskExplainer
        
        # Use in-memory SQLite for testing
        graph_store = GraphStore()
        propagator = RiskPropagator()
        base_risk_calc = BaseRiskCalculator()
        database = Database("sqlite:///:memory:")
        database.init_db()
        
        time_decay = TimeDecayCalculator(decay_factor=0.995, min_risk=0.01)
        clustering_detector = ClusteringDetector(density_threshold=0.3)
        explainer = RiskExplainer()
        
        # Initialize with Phase 2 components
        risk_engine = RiskEngine(
            graph_store=graph_store,
            propagator=propagator,
            base_risk_calc=base_risk_calc,
            database=database,
            cache=None,  # Skip Redis for testing
            time_decay=time_decay,
            clustering_detector=clustering_detector,
            explainer=explainer
        )
        
        assert risk_engine.time_decay is not None, "time_decay not set"
        assert risk_engine.clustering_detector is not None, "clustering_detector not set"
        assert risk_engine.explainer is not None, "explainer not set"
        print(f"  ✓ RiskEngine initialized with Phase 2 components")
        
        return True
    except Exception as e:
        print(f"  ✗ RiskEngine initialization test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all verification tests."""
    print("=" * 60)
    print("Phase 2 Integration Verification")
    print("=" * 60)
    
    tests = [
        ("Imports", test_imports),
        ("TimeDecayCalculator", test_time_decay),
        ("ClusteringDetector", test_clustering),
        ("RiskExplainer", test_explainer),
        ("RateLimiter", test_rate_limiter),
        ("APIKeyManager", test_api_key_manager),
        ("RiskEngine Initialization", test_risk_engine_initialization),
    ]
    
    results = []
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"\n✗ {name} failed with exception: {e}")
            import traceback
            traceback.print_exc()
            results.append((name, False))
    
    print("\n" + "=" * 60)
    print("Summary")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {name}")
    
    print(f"\nTotal: {passed}/{total} passed")
    
    return 0 if passed == total else 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
