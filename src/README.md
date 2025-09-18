# Source Code (src/)

This directory contains the main source code for the ArXiv MCP server, organized in a modular architecture.

## 📁 Architecture Overview

```text
src/arxiv_mcp/
├── __init__.py          # Package initialization and main exports
├── __main__.py          # CLI entry point
├── exceptions.py        # Custom exception hierarchy
├── models.py           # Pydantic data models
├── tools.py            # MCP tool implementations
├── fastmcp_tools.py    # FastMCP integration layer
├── core/               # Core business logic and configuration
├── clients/            # External API clients (ArXiv, etc.)
├── processors/         # Document processing engines
├── parsers/            # Content parsing and extraction
├── analyzers/          # Content analysis and intelligence
└── utils/              # Shared utilities and helpers
```text

## 🏗️ Module Responsibilities

### Core Package Files

- **`__init__.py`**: Package exports and version info
- **`__main__.py`**: Command-line interface entry point
- **`exceptions.py`**: ArXivMCPError hierarchy and error handling
- **`models.py`**: Pydantic models for data validation
- **`tools.py`**: Main MCP tool function implementations
- **`fastmcp_tools.py`**: FastMCP framework integration

### Package Modules

#### `core/` - Business Logic Core

- Configuration management
- Application lifecycle
- Business rules and validation
- Cross-cutting concerns

#### `clients/` - External Integration

- ArXiv API client
- HTTP client abstractions
- Rate limiting and retry logic
- External service adapters

#### `processors/` - Document Processing

- LaTeX processing and conversion
- PDF extraction and parsing
- Markdown generation
- Format transformation pipelines

#### `parsers/` - Content Extraction

- Document structure analysis
- Metadata extraction
- Citation parsing
- Content normalization

#### `analyzers/` - Intelligence Layer

- Content analysis and categorization
- Citation network analysis
- Quality metrics and scoring
- Trending and recommendation logic

#### `utils/` - Shared Utilities

- File operations and I/O
- Text processing helpers
- Logging and metrics
- Common algorithms

## 🔧 Development Guidelines

### Import Standards

```python
# Internal imports - relative within package
from .models import Paper, SearchQuery
from .exceptions import ArXivMCPError

# Cross-module imports - absolute
from arxiv_mcp.core.config import get_config
from arxiv_mcp.utils.files import save_file
```python

### Module Design Principles

1. **Single Responsibility**: Each module has one clear purpose
2. **Loose Coupling**: Minimal dependencies between modules
3. **High Cohesion**: Related functionality grouped together
4. **Explicit Dependencies**: Clear imports and interfaces

### Adding New Functionality

1. **Identify the layer**: Core, client, processor, parser, analyzer, or utility?
2. **Check existing modules**: Can it fit in an existing module?
3. **Create new module**: If needed, follow naming conventions
4. **Update `__init__.py`**: Export public interfaces
5. **Add tests**: Create corresponding test files

## 📋 Code Standards

### Module Documentation

```python
"""Module for ArXiv paper processing and conversion.

This module provides functionality for downloading ArXiv papers,
converting LaTeX to Markdown, and extracting metadata.

Example:
    >>> from arxiv_mcp.processors import LaTeXProcessor
    >>> processor = LaTeXProcessor()
    >>> result = processor.convert_to_markdown(latex_content)
"""
```text

### Public Interface Guidelines

- Use `__all__` to define public exports
- Prefix private functions with `_`
- Document all public functions with docstrings
- Use type hints for all function signatures

---

_This modular architecture supports scalability, maintainability, and testability of the ArXiv MCP server._
