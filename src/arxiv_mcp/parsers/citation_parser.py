"""
Citation parser module - wrapper around the existing citations utility.

This module provides the CitationParser class that was expected by the fastmcp_tools.py
imports. It acts as a bridge to the existing working implementation.
"""

# Import the working implementation from utils
from ..utils.citations import CitationParser as _CitationParser

# Re-export the class so it can be imported as expected
CitationParser = _CitationParser

__all__ = ["CitationParser"]
