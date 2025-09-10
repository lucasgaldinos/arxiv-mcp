"""
Network analyzer module - wrapper around the existing network_analysis utility.

This module provides the NetworkAnalyzer and related classes that were expected by 
the fastmcp_tools.py imports. It acts as a bridge to the existing working implementation.
"""

# Import the working implementation from utils
from ..utils.network_analysis import (
    NetworkAnalyzer as _NetworkAnalyzer,
    NetworkNode as _NetworkNode,
    NetworkEdge as _NetworkEdge,
    NetworkType as _NetworkType,
)

# Re-export the classes so they can be imported as expected
NetworkAnalyzer = _NetworkAnalyzer
NetworkNode = _NetworkNode  
NetworkEdge = _NetworkEdge
NetworkType = _NetworkType

__all__ = ["NetworkAnalyzer", "NetworkNode", "NetworkEdge", "NetworkType"]
