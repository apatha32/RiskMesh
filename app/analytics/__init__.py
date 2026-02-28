"""
Fraud Analytics Module
Provides statistical insights and analysis
"""
import logging
from typing import Dict, Any, List
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class FraudAnalytics:
    """
    Analytics and reporting for fraud detection.
    
    Computes:
    - Risk distributions
    - False positive rates
    - Detection performance metrics
    - Trend analysis
    """
    
    def __init__(self, database):
        """
        Initialize analytics.
        
        Args:
            database: Database connection
        """
        self.db = database
    
    def get_risk_distribution(self, hours: int = 24) -> Dict[str, Any]:
        """
        Get risk score distribution.
        
        Args:
            hours: Lookback period
            
        Returns:
            Risk distribution stats
        """
        try:
            session = self.db.get_session()
            from app.db.models import TransactionModel
            
            cutoff = datetime.utcnow() - timedelta(hours=hours)
            transactions = session.query(TransactionModel).filter(
                TransactionModel.timestamp >= cutoff
            ).all()
            
            session.close()
            
            if not transactions:
                return {"error": "No transactions"}
            
            risks = [t.risk_score for t in transactions]
            
            return {
                "total_transactions": len(transactions),
                "mean_risk": round(sum(risks) / len(risks), 3),
                "median_risk": round(sorted(risks)[len(risks)//2], 3),
                "min_risk": round(min(risks), 3),
                "max_risk": round(max(risks), 3),
                "high_risk_count": sum(1 for r in risks if r > 0.6),
                "medium_risk_count": sum(1 for r in risks if 0.3 <= r <= 0.6),
                "low_risk_count": sum(1 for r in risks if r < 0.3),
                "percentiles": {
                    "p50": round(sorted(risks)[int(len(risks)*0.5)], 3),
                    "p95": round(sorted(risks)[int(len(risks)*0.95)], 3),
                    "p99": round(sorted(risks)[int(len(risks)*0.99)], 3)
                }
            }
        except Exception as e:
            logger.error(f"Risk distribution error: {e}")
            return {"error": str(e)}
    
    def get_user_behavior(self, user_id: str, days: int = 30) -> Dict[str, Any]:
        """
        Get user transaction behavior.
        
        Args:
            user_id: User ID
            days: Lookback period
            
        Returns:
            User behavior stats
        """
        try:
            session = self.db.get_session()
            from app.db.models import TransactionModel
            
            cutoff = datetime.utcnow() - timedelta(days=days)
            transactions = session.query(TransactionModel).filter(
                TransactionModel.user_id == user_id,
                TransactionModel.timestamp >= cutoff
            ).all()
            
            session.close()
            
            if not transactions:
                return {"user_id": user_id, "transactions": 0}
            
            # Analyze behavior
            amounts = [t.transaction_amount for t in transactions]
            risks = [t.risk_score for t in transactions]
            merchants = set(t.merchant_id for t in transactions)
            devices = set(t.device_id for t in transactions)
            ips = set(t.ip_address for t in transactions)
            
            return {
                "user_id": user_id,
                "total_transactions": len(transactions),
                "avg_amount": round(sum(amounts) / len(amounts), 2),
                "max_amount": round(max(amounts), 2),
                "min_amount": round(min(amounts), 2),
                "avg_risk": round(sum(risks) / len(risks), 3),
                "max_risk": round(max(risks), 3),
                "unique_merchants": len(merchants),
                "unique_devices": len(devices),
                "unique_ips": len(ips),
                "high_risk_ratio": round(sum(1 for r in risks if r > 0.6) / len(risks), 3),
                "trend": "increasing" if risks[-1] > sum(risks)/len(risks) else "stable"
            }
        except Exception as e:
            logger.error(f"User behavior error: {e}")
            return {"error": str(e)}
    
    def get_performance_metrics(self, hours: int = 24) -> Dict[str, Any]:
        """
        Get system performance metrics.
        
        Args:
            hours: Lookback period
            
        Returns:
            Performance stats
        """
        try:
            session = self.db.get_session()
            from app.db.models import TransactionModel
            
            cutoff = datetime.utcnow() - timedelta(hours=hours)
            transactions = session.query(TransactionModel).filter(
                TransactionModel.timestamp >= cutoff
            ).all()
            
            session.close()
            
            if not transactions:
                return {"error": "No transactions"}
            
            # Calculate metrics
            total = len(transactions)
            flagged = sum(1 for t in transactions if t.risk_score > 0.6)
            
            return {
                "total_transactions": total,
                "flagged_count": flagged,
                "flag_rate": round(flagged / total * 100, 2),
                "throughput_per_hour": total,
                "avg_propagation_depth": round(
                    sum(t.propagation_depth for t in transactions) / total, 2
                )
            }
        except Exception as e:
            logger.error(f"Performance metrics error: {e}")
            return {"error": str(e)}
    
    def get_top_risky_users(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get top risky users (by average risk).
        
        Args:
            limit: Number of users to return
            
        Returns:
            List of risky users
        """
        try:
            session = self.db.get_session()
            from sqlalchemy import func
            from app.db.models import TransactionModel
            
            # Group by user, calculate average risk
            results = session.query(
                TransactionModel.user_id,
                func.count(TransactionModel.id).label('count'),
                func.avg(TransactionModel.risk_score).label('avg_risk'),
                func.max(TransactionModel.risk_score).label('max_risk')
            ).group_by(
                TransactionModel.user_id
            ).order_by(
                func.avg(TransactionModel.risk_score).desc()
            ).limit(limit).all()
            
            session.close()
            
            return [
                {
                    "user_id": r[0],
                    "transaction_count": r[1],
                    "avg_risk": round(r[2], 3),
                    "max_risk": round(r[3], 3)
                }
                for r in results
            ]
        except Exception as e:
            logger.error(f"Top risky users error: {e}")
            return []
