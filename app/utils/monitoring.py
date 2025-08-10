"""
System Monitoring and Error Tracking
"""

import asyncio
import json
import time
import traceback
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from collections import defaultdict, deque
from pathlib import Path

import psutil
from loguru import logger


class SystemMonitor:
    """Monitor system health and track errors"""
    
    def __init__(self):
        self.error_history = deque(maxlen=1000)  # Keep last 1000 errors
        self.performance_metrics = deque(maxlen=100)  # Keep last 100 metrics
        self.endpoint_stats = defaultdict(lambda: {"calls": 0, "errors": 0, "avg_time": 0})
        self.start_time = datetime.now()
        
    def log_error(self, error: Exception, context: str = "", endpoint: str = "", user_data: Dict = None):
        """Log an error with context"""
        error_data = {
            "timestamp": datetime.now().isoformat(),
            "error_type": type(error).__name__,
            "error_message": str(error),
            "context": context,
            "endpoint": endpoint,
            "traceback": traceback.format_exc(),
            "user_data": user_data or {}
        }
        
        self.error_history.append(error_data)
        
        # Update endpoint stats
        if endpoint:
            self.endpoint_stats[endpoint]["errors"] += 1
        
        logger.error(f"🚨 Error in {context}: {error}")
    
    def log_endpoint_call(self, endpoint: str, duration: float, success: bool = True):
        """Log API endpoint performance"""
        stats = self.endpoint_stats[endpoint]
        stats["calls"] += 1
        
        # Calculate running average
        if stats["calls"] == 1:
            stats["avg_time"] = duration
        else:
            stats["avg_time"] = (stats["avg_time"] * (stats["calls"] - 1) + duration) / stats["calls"]
        
        if not success:
            stats["errors"] += 1
    
    def capture_system_metrics(self):
        """Capture current system performance metrics"""
        try:
            cpu_percent = psutil.cpu_percent(interval=None)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            metrics = {
                "timestamp": datetime.now().isoformat(),
                "cpu_percent": cpu_percent,
                "memory_percent": memory.percent,
                "memory_available": memory.available,
                "disk_percent": disk.percent,
                "disk_free": disk.free,
                "process_count": len(psutil.pids())
            }
            
            self.performance_metrics.append(metrics)
            return metrics
            
        except Exception as e:
            logger.warning(f"Failed to capture system metrics: {e}")
            return {}
    
    def get_error_summary(self, hours: int = 24) -> Dict:
        """Get error summary for the last N hours"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        recent_errors = [
            error for error in self.error_history
            if datetime.fromisoformat(error["timestamp"]) > cutoff_time
        ]
        
        # Count by error type
        error_counts = defaultdict(int)
        endpoint_errors = defaultdict(int)
        
        for error in recent_errors:
            error_counts[error["error_type"]] += 1
            if error["endpoint"]:
                endpoint_errors[error["endpoint"]] += 1
        
        return {
            "total_errors": len(recent_errors),
            "error_types": dict(error_counts),
            "endpoint_errors": dict(endpoint_errors),
            "recent_errors": recent_errors[-10:],  # Last 10 errors
            "timeframe_hours": hours
        }
    
    def get_performance_summary(self) -> Dict:
        """Get system performance summary"""
        if not self.performance_metrics:
            return {"status": "no_data"}
        
        latest = self.performance_metrics[-1]
        
        # Calculate averages over last 10 readings
        recent_metrics = list(self.performance_metrics)[-10:]
        avg_cpu = sum(m["cpu_percent"] for m in recent_metrics) / len(recent_metrics)
        avg_memory = sum(m["memory_percent"] for m in recent_metrics) / len(recent_metrics)
        
        return {
            "current": latest,
            "averages": {
                "cpu_percent": round(avg_cpu, 2),
                "memory_percent": round(avg_memory, 2)
            },
            "uptime_hours": (datetime.now() - self.start_time).total_seconds() / 3600
        }
    
    def get_endpoint_stats(self) -> Dict:
        """Get API endpoint statistics"""
        stats = {}
        for endpoint, data in self.endpoint_stats.items():
            error_rate = (data["errors"] / data["calls"]) * 100 if data["calls"] > 0 else 0
            stats[endpoint] = {
                "total_calls": data["calls"],
                "total_errors": data["errors"],
                "error_rate_percent": round(error_rate, 2),
                "avg_response_time": round(data["avg_time"], 3)
            }
        return stats
    
    def health_check(self) -> Dict:
        """Comprehensive health check"""
        metrics = self.capture_system_metrics()
        error_summary = self.get_error_summary(hours=1)  # Last hour
        
        # Determine health status
        health_status = "healthy"
        issues = []
        
        if metrics.get("cpu_percent", 0) > 90:
            health_status = "warning"
            issues.append("High CPU usage")
        
        if metrics.get("memory_percent", 0) > 90:
            health_status = "warning"
            issues.append("High memory usage")
        
        if metrics.get("disk_percent", 0) > 95:
            health_status = "critical"
            issues.append("Low disk space")
        
        if error_summary["total_errors"] > 10:
            health_status = "warning"
            issues.append(f"High error rate: {error_summary['total_errors']} errors in last hour")
        
        return {
            "status": health_status,
            "timestamp": datetime.now().isoformat(),
            "issues": issues,
            "metrics": metrics,
            "error_summary": error_summary
        }
    
    def export_diagnostics(self) -> Dict:
        """Export comprehensive diagnostics data"""
        return {
            "system_info": {
                "uptime_hours": (datetime.now() - self.start_time).total_seconds() / 3600,
                "start_time": self.start_time.isoformat()
            },
            "performance": self.get_performance_summary(),
            "errors": self.get_error_summary(hours=24),
            "endpoints": self.get_endpoint_stats(),
            "health": self.health_check()
        }


# Global monitor instance
system_monitor = SystemMonitor()


def monitor_endpoint(endpoint_name: str):
    """Decorator to monitor endpoint performance"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            success = True
            
            try:
                result = await func(*args, **kwargs)
                return result
            except Exception as e:
                success = False
                system_monitor.log_error(e, context=f"Endpoint {endpoint_name}", endpoint=endpoint_name)
                raise
            finally:
                duration = time.time() - start_time
                system_monitor.log_endpoint_call(endpoint_name, duration, success)
        
        return wrapper
    return decorator


def log_error_context(error: Exception, context: str = "", **extra_data):
    """Helper function to log errors with context"""
    system_monitor.log_error(error, context=context, user_data=extra_data)
