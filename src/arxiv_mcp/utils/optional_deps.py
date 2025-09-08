"""
Optional dependencies management with graceful fallbacks.

This module provides utilities for handling optional dependencies and implementing
graceful fallbacks when dependencies are not available.
"""

import warnings
from typing import Any, Optional, Callable, Dict
import importlib
from functools import wraps


class OptionalDependency:
    """Manages optional dependencies with graceful fallbacks."""

    def __init__(self, name: str, package: str = None, feature: str = None):
        self.name = name
        self.package = package or name
        self.feature = feature or name
        self._module = None
        self._available = None

    @property
    def available(self) -> bool:
        """Check if the optional dependency is available."""
        if self._available is None:
            try:
                self._module = importlib.import_module(self.package)
                self._available = True
            except ImportError:
                self._available = False
        return self._available

    @property
    def module(self) -> Optional[Any]:
        """Get the imported module if available."""
        if self.available:
            return self._module
        return None

    def require(self) -> Any:
        """Require the dependency, raising ImportError if not available."""
        if not self.available:
            raise ImportError(
                f"The '{self.name}' package is required for {self.feature} functionality. "
                f"Install it with: pip install {self.name}"
            )
        return self.module

    def warn_if_missing(self, message: str = None) -> None:
        """Warn if the dependency is missing."""
        if not self.available:
            msg = (
                message
                or f"'{self.name}' not available. {self.feature} functionality will be limited."
            )
            warnings.warn(msg, UserWarning, stacklevel=2)


# Define optional dependencies
OPTIONAL_DEPS = {
    # NLP dependencies
    "nltk": OptionalDependency("nltk", feature="advanced text processing"),
    "spacy": OptionalDependency("spacy", feature="advanced NLP"),
    "textblob": OptionalDependency("textblob", feature="sentiment analysis"),
    # Visualization dependencies
    "matplotlib": OptionalDependency("matplotlib", feature="plotting"),
    "plotly": OptionalDependency("plotly", feature="interactive visualization"),
    "networkx": OptionalDependency("networkx", feature="network analysis"),
    # Advanced parsing dependencies
    "lxml": OptionalDependency("lxml", feature="XML/HTML parsing"),
    "pdfminer": OptionalDependency("pdfminer.six", "pdfminer", "advanced PDF parsing"),
    "docx": OptionalDependency("python-docx", "docx", "Word document processing"),
    # Document format dependencies (NEW - Phase 4A)
    "odfpy": OptionalDependency("odfpy", feature="OpenDocument (ODT) processing"),
    "striprtf": OptionalDependency("striprtf", feature="RTF document processing"),
    "docx2txt": OptionalDependency(
        "docx2txt", feature="alternative DOCX text extraction"
    ),
    # ML dependencies
    "sklearn": OptionalDependency("scikit-learn", "sklearn", "machine learning"),
    "pandas": OptionalDependency("pandas", feature="data analysis"),
    "numpy": OptionalDependency("numpy", feature="numerical computing"),
}


def optional_import(dep_name: str) -> OptionalDependency:
    """Get an optional dependency manager."""
    if dep_name not in OPTIONAL_DEPS:
        raise ValueError(f"Unknown optional dependency: {dep_name}")
    return OPTIONAL_DEPS[dep_name]


def requires_optional_dep(dep_name: str, fallback_return=None):
    """Decorator that requires an optional dependency."""

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            dep = optional_import(dep_name)
            if not dep.available:
                if fallback_return is not None:
                    dep.warn_if_missing(
                        f"Function '{func.__name__}' requires {dep.name}"
                    )
                    return fallback_return
                else:
                    dep.require()  # This will raise ImportError
            return func(*args, **kwargs)

        return wrapper

    return decorator


def get_available_features() -> Dict[str, bool]:
    """Get a dictionary of available optional features."""
    return {name: dep.available for name, dep in OPTIONAL_DEPS.items()}


def check_optional_dependencies() -> Dict[str, Any]:
    """Check all optional dependencies and return status information."""
    status = {}
    for name, dep in OPTIONAL_DEPS.items():
        status[name] = {
            "available": dep.available,
            "feature": dep.feature,
            "package": dep.package,
        }
    return status


def warn_missing_dependencies() -> None:
    """Warn about any missing optional dependencies."""
    missing = []
    for name, dep in OPTIONAL_DEPS.items():
        if not dep.available:
            missing.append(f"  - {dep.name}: {dep.feature}")

    if missing:
        warning_msg = (
            "Some optional dependencies are missing. Install them for enhanced functionality:\n"
            + "\n".join(missing)
            + "\n\nInstall with: pip install arxiv-mcp-improved[nlp,visualization,advanced-parsing,ml]"
        )
        warnings.warn(warning_msg, UserWarning, stacklevel=2)


# Enhanced import functions with fallbacks
def safe_import(module_name: str, package_name: str = None, feature_name: str = None):
    """
    Safely import a module with fallback.

    Args:
        module_name: Name of the module to import
        package_name: Package name for installation (defaults to module_name)
        feature_name: Feature description (defaults to module_name)

    Returns:
        Module if available, None otherwise
    """
    try:
        return importlib.import_module(module_name)
    except ImportError:
        if feature_name:
            warnings.warn(
                f"Optional dependency '{module_name}' not available. "
                f"{feature_name} functionality will be limited.",
                UserWarning,
                stacklevel=2,
            )
        return None


def safe_import_nltk():
    """Safely import NLTK with fallback."""
    dep = optional_import("nltk")
    if dep.available:
        import nltk

        # Try to download required data if not present, but don't block
        try:
            nltk.data.find("tokenizers/punkt")
        except LookupError:
            # Don't download during import - just warn
            warnings.warn(
                "NLTK punkt tokenizer not found. Some functionality may be limited. "
                "Run 'python -c \"import nltk; nltk.download('punkt')\"' to install.",
                UserWarning,
            )
        return nltk
    return None


def safe_import_matplotlib():
    """Safely import matplotlib with fallback."""
    dep = optional_import("matplotlib")
    if dep.available:
        import matplotlib

        matplotlib.use("Agg")  # Use non-interactive backend
        import matplotlib.pyplot as plt

        return plt
    return None


def safe_import_pandas():
    """Safely import pandas with fallback."""
    dep = optional_import("pandas")
    return dep.module if dep.available else None


def safe_import_numpy():
    """Safely import numpy with fallback."""
    dep = optional_import("numpy")
    return dep.module if dep.available else None


# Initialize warnings for missing dependencies at module import
def _init_warnings():
    """Initialize warnings for missing dependencies."""
    # Only warn about core optional dependencies when explicitly requested
    # Don't warn on import to avoid issues during testing/development
    pass


# Run initialization
_init_warnings()
