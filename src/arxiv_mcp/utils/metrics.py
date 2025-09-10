"""
Comprehensive metrics collection for observability.
Extracted from the main __init__.py for better modularity.
"""

import time
from collections import defaultdict
from typing import Dict, Any, Optional, Union, List


class MetricsCollector:
    """Comprehensive metrics collection for observability"""

    def __init__(self):
        self.counters: Dict[str, int] = defaultdict(int)
        self.timers: Dict[str, List[float]] = defaultdict(list)
        self.gauges: Dict[str, float] = defaultdict(float)
        self.start_times: Dict[str, float] = {}

    def start_timer(self, operation: str, identifier: Optional[str] = None) -> str:
        """Start timing an operation"""
        key = f"{operation}:{identifier}" if identifier else operation
        self.start_times[key] = time.time()
        return key

    def end_timer(self, timer_key: str, success: bool = True) -> float:
        """End timing and record the duration"""
        if timer_key in self.start_times:
            duration = time.time() - self.start_times[timer_key]
            self.timers[timer_key].append(duration)
            self.counters[f"{timer_key}:{'success' if success else 'failure'}"] += 1
            del self.start_times[timer_key]
            return duration
        return 0.0

    def increment_counter(
        self,
        name: str,
        value: Union[int, Dict[str, Any]] = 1,
        tags: Optional[Dict[str, Any]] = None,
    ):
        """
        Increment a counter metric.

        Args:
            name: Counter name
            value: Either an integer increment value, or tags dict (for backward compatibility)
            tags: Optional tags/metadata (when value is int)
        """
        # Handle backward compatibility where value was passed as tags
        if isinstance(value, dict):
            tags = value
            value = 1

        # Store the increment
        self.counters[name] += value

        # Store tags if provided (for potential future use)
        if tags:
            tag_key = f"{name}_tags"
            if tag_key not in self.counters:
                self.counters[tag_key] = []
            self.counters[tag_key].append(tags)

    def set_gauge(self, name: str, value: float):
        """Set a gauge metric"""
        self.gauges[name] = value

    def get_metrics(self) -> dict:
        """Get current metrics summary"""
        return {
            "counters": dict(self.counters),
            "timers": {
                k: {
                    "count": len(v),
                    "avg": sum(v) / len(v) if v else 0,
                    "min": min(v) if v else 0,
                    "max": max(v) if v else 0,
                }
                for k, v in self.timers.items()
            },
            "gauges": dict(self.gauges),
        }

    def get_all_metrics(self) -> dict:
        """Alias for get_metrics for backward compatibility"""
        return self.get_metrics()


class PerformanceMetrics:
    """Performance metrics aggregation and analysis"""
    
    def __init__(self):
        self.collector = MetricsCollector()
        
    def get_performance_summary(self, time_range: str = "24h") -> Dict[str, Any]:
        """
        Get performance summary for the specified time range.
        
        Args:
            time_range: Time range for metrics (e.g., "1h", "24h", "7d")
            
        Returns:
            Dictionary containing performance metrics
        """
        metrics = self.collector.get_metrics()
        
        # Calculate summary statistics
        summary = {
            "time_range": time_range,
            "total_operations": sum(metrics["counters"].values()),
            "timer_stats": {},
            "counters": metrics["counters"],
            "gauges": metrics["gauges"],
        }
        
        # Process timer statistics
        for timer_name, durations in metrics["timers"].items():
            if durations:
                summary["timer_stats"][timer_name] = {
                    "count": len(durations),
                    "avg_duration": sum(durations) / len(durations),
                    "min_duration": min(durations),
                    "max_duration": max(durations),
                    "total_duration": sum(durations),
                }
        
        # Add performance insights
        summary["insights"] = self._generate_insights(summary)
        
        return summary
        
    def _generate_insights(self, summary: Dict[str, Any]) -> List[str]:
        """Generate performance insights from metrics"""
        insights = []
        
        # Check for slow operations
        for timer_name, stats in summary["timer_stats"].items():
            if stats["avg_duration"] > 30:  # Slow if > 30 seconds average
                insights.append(f"Operation '{timer_name}' is running slowly (avg: {stats['avg_duration']:.2f}s)")
                
        # Check for high error rates
        for counter_name, count in summary["counters"].items():
            if "failure" in counter_name and count > 0:
                total_ops = summary["counters"].get(counter_name.replace("failure", "success"), 0) + count
                error_rate = (count / total_ops) * 100 if total_ops > 0 else 0
                if error_rate > 10:  # Error rate > 10%
                    insights.append(f"High error rate for '{counter_name}': {error_rate:.1f}%")
        
        if not insights:
            insights.append("Performance looks good - no issues detected")
            
        return insights
