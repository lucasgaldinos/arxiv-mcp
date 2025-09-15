"""
Enhanced ArXiv MCP Features

This module provides enhanced functionality and improvements over the base ArXiv MCP system,
including multi-temporal cleanup APIs, advanced integration capabilities, and improved
system interfaces.
"""

from .multi_temporal_cleanup import (
    EnhancedCleanupAdapter,
    MultiTemporalParser,
    TimeSpec,
    TimeUnit,
    create_enhanced_adapter,
)

__all__ = [
    "EnhancedCleanupAdapter",
    "MultiTemporalParser",
    "TimeSpec",
    "TimeUnit",
    "create_enhanced_adapter",
]

__version__ = "1.0.0"
