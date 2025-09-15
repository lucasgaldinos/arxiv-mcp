"""
Custom exception classes for the ArXiv MCP server.
Extracted from the main __init__.py for better modularity.
"""


class ArxivError(Exception):
    """Base exception for the ArXiv MCP server."""


class ProcessingError(ArxivError):
    """Exception raised for general processing errors."""


class DownloadError(ArxivError):
    """Exception raised for errors during file download."""


class ExtractionError(ArxivError):
    """Exception raised for errors during archive extraction."""


class CompilationError(ArxivError):
    """Exception raised for errors during LaTeX compilation."""


class ValidationError(ArxivError):
    """Exception raised for input validation errors."""


# Legacy aliases for backward compatibility
ArxivMCPError = ArxivError
