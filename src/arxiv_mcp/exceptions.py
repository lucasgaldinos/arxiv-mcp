"""
Custom exception classes for the ArXiv MCP server.
Extracted from the main __init__.py for better modularity.
"""


class ArxivError(Exception):
    """Base exception for the ArXiv MCP server."""

    pass


class ProcessingError(ArxivError):
    """Exception raised for general processing errors."""

    pass


class DownloadError(ArxivError):
    """Exception raised for errors during file download."""

    pass


class ExtractionError(ArxivError):
    """Exception raised for errors during archive extraction."""

    pass


class CompilationError(ArxivError):
    """Exception raised for errors during LaTeX compilation."""

    pass


class ValidationError(ArxivError):
    """Exception raised for input validation errors."""

    pass


# Legacy aliases for backward compatibility
ArxivMCPError = ArxivError
