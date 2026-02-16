"""Cost control and budget management for GenXAI."""

import sqlite3
from typing import Dict, Any, Optional
from datetime import datetime, timedelta, UTC
from dataclasses import dataclass
import os


# Token costs per 1K tokens (as of 2026)
TOKEN_COSTS = {
    "openai": {
        "gpt-4": {"prompt": 0.03, "completion": 0.06},
        "gpt-4-turbo": {"prompt": 0.01, "completion": 0.03},
        "gpt-3.5-turbo": {"prompt": 0.0015, "completion": 0.002},
    },
    "anthropic": {
        "claude-3-opus": {"prompt": 0.015, "completion": 0.075},
        "claude-3-sonnet": {"prompt": 0.003, "completion": 0.015},
        "claude-3-haiku": {"prompt": 0.00025, "completion": 0.00125},
    },
    "google": {
        "gemini-pro": {"prompt": 0.00025, "completion": 0.0005},
        "gemini-ultra": {"prompt": 0.01, "completion": 0.02},
    },
    "cohere": {
        "command": {"prompt": 0.001, "completion": 0.002},
        "command-light": {"prompt": 0.0003, "completion": 0.0006},
    },
}


@dataclass
class UsageRecord:
    """Token usage record."""
    user_id: str
    provider: str
    model: str
    prompt_tokens: int
    completion_tokens: int
    cost: float
    timestamp: datetime


class TokenUsageTracker:
    """Track LLM token usage."""
    
    def __init__(self, db_path: str = "genxai_usage.db"):
        """Initialize usage tracker.
        
        Args:
            db_path: Path to SQLite database
        """
        self.db_path = db_path
        self._init_db()
    
    def _init_db(self):
        """Initialize database schema."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS token_usage (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                provider TEXT NOT NULL,
                model TEXT NOT NULL,
                prompt_tokens INTEGER NOT NULL,
                completion_tokens INTEGER NOT NULL,
                cost REAL NOT NULL,
                timestamp TIMESTAMP NOT NULL
            )
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_user_timestamp 
            ON token_usage(user_id, timestamp)
        """)
        
        conn.commit()
        conn.close()
    
    def record_usage(
        self,
        user_id: str,
        provider: str,
        model: str,
        prompt_tokens: int,
        completion_tokens: int,
        cost: float
    ):
        """Record token usage.
        
        Args:
            user_id: User ID
            provider: LLM provider
            model: Model name
            prompt_tokens: Prompt tokens used
            completion_tokens: Completion tokens used
            cost: Cost in USD
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO token_usage 
            (user_id, provider, model, prompt_tokens, completion_tokens, cost, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (user_id, provider, model, prompt_tokens, completion_tokens, cost, datetime.now(UTC)))
        
        conn.commit()
        conn.close()
    
    def get_usage(
        self,
        user_id: str,
        period: str = "day"
    ) -> Dict[str, Any]:
        """Get usage statistics.
        
        Args:
            user_id: User ID
            period: Time period (day, week, month)
            
        Returns:
            Usage statistics
        """
        # Calculate time range
        now = datetime.now(UTC)
        if period == "day":
            start_time = now - timedelta(days=1)
        elif period == "week":
            start_time = now - timedelta(weeks=1)
        elif period == "month":
            start_time = now - timedelta(days=30)
        else:
            start_time = now - timedelta(days=1)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT 
                SUM(prompt_tokens) as total_prompt_tokens,
                SUM(completion_tokens) as total_completion_tokens,
                SUM(cost) as total_cost,
                COUNT(*) as request_count
            FROM token_usage
            WHERE user_id = ? AND timestamp >= ?
        """, (user_id, start_time))
        
        row = cursor.fetchone()
        
        # Get breakdown by provider/model
        cursor.execute("""
            SELECT provider, model, SUM(cost) as cost
            FROM token_usage
            WHERE user_id = ? AND timestamp >= ?
            GROUP BY provider, model
        """, (user_id, start_time))
        
        breakdown = {}
        for provider, model, cost in cursor.fetchall():
            if provider not in breakdown:
                breakdown[provider] = {}
            breakdown[provider][model] = cost
        
        conn.close()
        
        return {
            "period": period,
            "total_prompt_tokens": row[0] or 0,
            "total_completion_tokens": row[1] or 0,
            "total_cost": row[2] or 0.0,
            "request_count": row[3] or 0,
            "breakdown": breakdown
        }


class BudgetManager:
    """Manage user budgets."""
    
    def __init__(self, db_path: str = "genxai_budgets.db"):
        """Initialize budget manager.
        
        Args:
            db_path: Path to SQLite database
        """
        self.db_path = db_path
        self._init_db()
    
    def _init_db(self):
        """Initialize database schema."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS budgets (
                user_id TEXT PRIMARY KEY,
                amount REAL NOT NULL,
                period TEXT NOT NULL,
                created_at TIMESTAMP NOT NULL,
                updated_at TIMESTAMP NOT NULL
            )
        """)
        
        conn.commit()
        conn.close()
    
    def set_budget(
        self,
        user_id: str,
        amount: float,
        period: str = "month"
    ):
        """Set budget limit.
        
        Args:
            user_id: User ID
            amount: Budget amount in USD
            period: Budget period (day, week, month)
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        now = datetime.now(UTC)
        
        cursor.execute("""
            INSERT OR REPLACE INTO budgets (user_id, amount, period, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?)
        """, (user_id, amount, period, now, now))
        
        conn.commit()
        conn.close()
    
    def check_budget(self, user_id: str, usage_tracker: TokenUsageTracker) -> bool:
        """Check if user is within budget.
        
        Args:
            user_id: User ID
            usage_tracker: TokenUsageTracker instance
            
        Returns:
            True if within budget, False otherwise
        """
        # Get budget
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT amount, period FROM budgets WHERE user_id = ?
        """, (user_id,))
        
        row = cursor.fetchone()
        conn.close()
        
        if not row:
            # No budget set, allow
            return True
        
        amount, period = row
        
        # Get usage
        usage = usage_tracker.get_usage(user_id, period)
        
        return usage["total_cost"] < amount
    
    def get_remaining(self, user_id: str, usage_tracker: TokenUsageTracker) -> float:
        """Get remaining budget.
        
        Args:
            user_id: User ID
            usage_tracker: TokenUsageTracker instance
            
        Returns:
            Remaining budget in USD
        """
        # Get budget
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT amount, period FROM budgets WHERE user_id = ?
        """, (user_id,))
        
        row = cursor.fetchone()
        conn.close()
        
        if not row:
            return float('inf')
        
        amount, period = row
        
        # Get usage
        usage = usage_tracker.get_usage(user_id, period)
        
        return max(0, amount - usage["total_cost"])


class CostEstimator:
    """Estimate costs before execution."""
    
    def __init__(self, costs: Optional[Dict[str, Any]] = None):
        """Initialize cost estimator.
        
        Args:
            costs: Custom cost table (default: use built-in costs)
        """
        self.costs = costs or TOKEN_COSTS
    
    def estimate_cost(
        self,
        provider: str,
        model: str,
        prompt_tokens: int,
        estimated_completion_tokens: int
    ) -> float:
        """Estimate execution cost.
        
        Args:
            provider: LLM provider
            model: Model name
            prompt_tokens: Number of prompt tokens
            estimated_completion_tokens: Estimated completion tokens
            
        Returns:
            Estimated cost in USD
        """
        if provider not in self.costs:
            return 0.0
        
        if model not in self.costs[provider]:
            return 0.0
        
        model_costs = self.costs[provider][model]
        
        prompt_cost = (prompt_tokens / 1000) * model_costs["prompt"]
        completion_cost = (estimated_completion_tokens / 1000) * model_costs["completion"]
        
        return prompt_cost + completion_cost
    
    def estimate_workflow_cost(
        self,
        steps: list[Dict[str, Any]]
    ) -> float:
        """Estimate workflow cost.
        
        Args:
            steps: List of workflow steps with provider, model, tokens
            
        Returns:
            Estimated total cost
        """
        total_cost = 0.0
        
        for step in steps:
            cost = self.estimate_cost(
                step["provider"],
                step["model"],
                step["prompt_tokens"],
                step["estimated_completion_tokens"]
            )
            total_cost += cost
        
        return total_cost


class CostAlertManager:
    """Send alerts when costs exceed thresholds."""
    
    def __init__(self, db_path: str = "genxai_alerts.db"):
        """Initialize alert manager.
        
        Args:
            db_path: Path to SQLite database
        """
        self.db_path = db_path
        self._init_db()
    
    def _init_db(self):
        """Initialize database schema."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS cost_alerts (
                user_id TEXT PRIMARY KEY,
                threshold REAL NOT NULL,
                notification_method TEXT NOT NULL,
                last_alert TIMESTAMP
            )
        """)
        
        conn.commit()
        conn.close()
    
    def set_alert(
        self,
        user_id: str,
        threshold: float,
        notification_method: str = "email"
    ):
        """Set cost alert.
        
        Args:
            user_id: User ID
            threshold: Cost threshold in USD
            notification_method: Notification method (email, slack, webhook)
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT OR REPLACE INTO cost_alerts (user_id, threshold, notification_method)
            VALUES (?, ?, ?)
        """, (user_id, threshold, notification_method))
        
        conn.commit()
        conn.close()
    
    def check_and_notify(self, user_id: str, current_cost: float):
        """Check threshold and send notification.
        
        Args:
            user_id: User ID
            current_cost: Current cost
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT threshold, notification_method, last_alert
            FROM cost_alerts
            WHERE user_id = ?
        """, (user_id,))
        
        row = cursor.fetchone()
        
        if not row:
            conn.close()
            return
        
        threshold, notification_method, last_alert = row
        
        # Check if threshold exceeded
        if current_cost >= threshold:
            # Check if we already sent alert recently (within 1 hour)
            if last_alert:
                last_alert_time = datetime.fromisoformat(last_alert)
                if datetime.now(UTC) - last_alert_time < timedelta(hours=1):
                    conn.close()
                    return
            
            # Send notification
            self._send_notification(
                user_id,
                notification_method,
                current_cost,
                threshold
            )
            
            # Update last alert time
            cursor.execute("""
                UPDATE cost_alerts SET last_alert = ? WHERE user_id = ?
            """, (datetime.now(UTC), user_id))
            
            conn.commit()
        
        conn.close()
    
    def _send_notification(
        self,
        user_id: str,
        method: str,
        current_cost: float,
        threshold: float
    ):
        """Send notification.
        
        Args:
            user_id: User ID
            method: Notification method
            current_cost: Current cost
            threshold: Threshold
        """
        message = f"Cost alert: User {user_id} has exceeded threshold ${threshold:.2f}. Current cost: ${current_cost:.2f}"
        
        # Placeholder for actual notification implementation
        print(f"[{method.upper()}] {message}")


# Global instances
_usage_tracker = None
_budget_manager = None
_cost_estimator = None
_alert_manager = None


def get_usage_tracker() -> TokenUsageTracker:
    """Get global usage tracker."""
    global _usage_tracker
    if _usage_tracker is None:
        _usage_tracker = TokenUsageTracker()
    return _usage_tracker


def get_budget_manager() -> BudgetManager:
    """Get global budget manager."""
    global _budget_manager
    if _budget_manager is None:
        _budget_manager = BudgetManager()
    return _budget_manager


def get_cost_estimator() -> CostEstimator:
    """Get global cost estimator."""
    global _cost_estimator
    if _cost_estimator is None:
        _cost_estimator = CostEstimator()
    return _cost_estimator


def get_alert_manager() -> CostAlertManager:
    """Get global alert manager."""
    global _alert_manager
    if _alert_manager is None:
        _alert_manager = CostAlertManager()
    return _alert_manager
