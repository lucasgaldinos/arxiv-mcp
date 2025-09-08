"""
Comprehensive metrics collection for observability.
Extracted from the main __init__.py for better modularity.
"""

import time
from collections import defaultdict
from typing import Dict, Any, Optional, Union


class MetricsCollector:
    """Comprehensive metrics collection for observability"""

    def __init__(self):
        self.counters = defaultdict(int)
        self.timers = defaultdict(list)
        self.gauges = defaultdict(float)
        self.start_times = {}

    def start_timer(self, operation: str, identifier: str = None) -> str:
        """Start timing an operation"""
        key = f"{operation}:{identifier}" if identifier else operation
        self.start_times[key] = time.time()
        return key

    def end_timer(self, timer_key: str, success: bool = True):
        """End timing and record the duration"""
        if timer_key in self.start_times:
            duration = time.time() - self.start_times[timer_key]
            self.timers[timer_key].append(duration)
            self.counters[f"{timer_key}:{'success' if success else 'failure'}"] += 1
            del self.start_times[timer_key]
            return duration
        return 0

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
