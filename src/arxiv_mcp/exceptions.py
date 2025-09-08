"""
Custom exception classes for the ArXiv MCP server.
Extracted from the main __init__.py for better modularity.
"""


class ArxivMCPError(Exception):
    """Base exception for the ArXiv MCP server."""
    pass


class DownloadError(ArxivMCPError):
    """Exception raised for errors during file download."""
    pass


class ExtractionError(ArxivMCPError):
    """Exception raised for errors during archive extraction."""
    pass


class CompilationError(ArxivMCPError):
    """Exception raised for errors during LaTeX compilation."""
    pass


class ValidationError(ArxivMCPError):
    """Exception raised for input validation errors."""
    pass
