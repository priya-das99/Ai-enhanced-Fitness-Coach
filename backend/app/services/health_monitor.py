# app/services/health_monitor.py
# Health monitoring and recovery service

import time
import logging
import threading
from typing import Dict, Optional
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class HealthMonitor:
    """Monitor system health and trigger recovery actions"""
    
    def __init__(self):
        self.error_counts = {}  # user_id -> error_count
        self.last_error_time = {}  # user_id -> timestamp
        self.system_errors = 0
        self.last_system_error = None
        self.lock = threading.Lock()
        
        # Thresholds
        self.max_user_errors = 3  # Max errors per user in time window
        self.max_system_errors = 10  # Max system errors in time window
        self.error_window = 300  # 5 minutes
        self.recovery_delay = 60  # 1 minute recovery delay
        
        # Circuit breaker state
        self.circuit_open = False
        self.circuit_open_time = None
    
    def record_user_error(self, user_id: int, error_type: str = "general"):
        """Record an error for a specific user"""
        with self.lock:
            current_time = time.time()
            
            # Reset counter if outside time window
            if user_id in self.last_error_time:
                if current_time - self.last_error_time[user_id] > self.error_window:
                    self.error_counts[user_id] = 0
            
            # Increment error count
            self.error_counts[user_id] = self.error_counts.get(user_id, 0) + 1
            self.last_error_time[user_id] = current_time
            
            logger.warning(f"User {user_id} error #{self.error_counts[user_id]} ({error_type})")
            
            # Check if user has too many errors
            if self.error_counts[user_id] >= self.max_user_errors:
                logger.error(f"User {user_id} has exceeded error threshold ({self.max_user_errors})")
                return True  # User should get rate limited
            
            return False
    
    def record_system_error(self, error_type: str = "general"):
        """Record a system-wide error"""
        with self.lock:
            current_time = time.time()
            
            # Reset counter if outside time window
            if self.last_system_error and current_time - self.last_system_error > self.error_window:
                self.system_errors = 0
            
            # Increment system error count
            self.system_errors += 1
            self.last_system_error = current_time
            
            logger.error(f"System error #{self.system_errors} ({error_type})")
            
            # Check if system has too many errors
            if self.system_errors >= self.max_system_errors:
                logger.critical(f"System has exceeded error threshold ({self.max_system_errors}) - opening circuit breaker")
                self.circuit_open = True
                self.circuit_open_time = current_time
                return True  # Circuit breaker should open
            
            return False
    
    def is_circuit_open(self) -> bool:
        """Check if circuit breaker is open"""
        with self.lock:
            if not self.circuit_open:
                return False
            
            # Check if recovery time has passed
            if self.circuit_open_time and time.time() - self.circuit_open_time > self.recovery_delay:
                logger.info("Circuit breaker recovery time elapsed - attempting to close circuit")
                self.circuit_open = False
                self.circuit_open_time = None
                self.system_errors = 0  # Reset error count
                return False
            
            return True
    
    def should_rate_limit_user(self, user_id: int) -> bool:
        """Check if user should be rate limited"""
        with self.lock:
            if user_id not in self.error_counts:
                return False
            
            current_time = time.time()
            
            # Reset if outside time window
            if user_id in self.last_error_time:
                if current_time - self.last_error_time[user_id] > self.error_window:
                    self.error_counts[user_id] = 0
                    return False
            
            return self.error_counts[user_id] >= self.max_user_errors
    
    def get_health_status(self) -> Dict:
        """Get current health status"""
        with self.lock:
            return {
                'circuit_open': self.circuit_open,
                'system_errors': self.system_errors,
                'active_user_errors': len([uid for uid, count in self.error_counts.items() if count > 0]),
                'last_system_error': self.last_system_error,
                'circuit_open_time': self.circuit_open_time
            }
    
    def reset_user_errors(self, user_id: int):
        """Reset error count for a user (after successful operation)"""
        with self.lock:
            if user_id in self.error_counts:
                self.error_counts[user_id] = 0
    
    def force_circuit_close(self):
        """Manually close circuit breaker (admin action)"""
        with self.lock:
            self.circuit_open = False
            self.circuit_open_time = None
            self.system_errors = 0
            logger.info("Circuit breaker manually closed")

# Global health monitor instance
_health_monitor = HealthMonitor()

def get_health_monitor() -> HealthMonitor:
    """Get the global health monitor instance"""
    return _health_monitor