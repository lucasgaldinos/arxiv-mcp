# ArXiv MCP Server API
        
**Version:** 0.2.0  
**Generated:** 2025-09-08T02:19:05.489047

Comprehensive API documentation for the ArXiv MCP server

## MCP Tools Overview

The ArXiv MCP server provides the following tools:

### search_arxiv

Search ArXiv papers by query terms

**Parameters:**

**Returns:** TextContent with tool output

### get_paper_details

Get detailed information about a specific ArXiv paper

**Parameters:**

**Returns:** TextContent with tool output

### process_multiple_papers

Process multiple ArXiv papers concurrently

**Parameters:**

**Returns:** TextContent with tool output

### get_pipeline_status

Get current pipeline status and metrics

**Parameters:**

**Returns:** TextContent with tool output

### health_check

Check system health and status

**Parameters:**

**Returns:** TextContent with tool output

### export_search_results

Export search results to various formats

**Parameters:**

**Returns:** TextContent with tool output

### extract_citations

Extract and parse citations from paper text

**Parameters:**

**Returns:** TextContent with tool output

### parse_citations_from_arxiv

Extract citations from a specific ArXiv paper

**Parameters:**

**Returns:** TextContent with tool output

### generate_api_docs

Generate API documentation from code annotations

**Parameters:**

**Returns:** TextContent with tool output


## Modules

### tools

MCP tools for the ArXiv serve        Tool(
            name="search_arxiv",
            description="Search ArXiv papers with advanced filters",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query for ArXiv papers"
                    },
                    "max_results": {
                        "type": "integer",
                        "description": "Maximum number of results to return",
                        "default": 10
                    },
                    "categories": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "ArXiv categories to filter by (e.g., ['cs.AI', 'stat.ML'])"
                    },
                    "authors": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Author names to filter by"
                    },
                    "date_from": {
                        "type": "string",
                        "description": "Start date for filtering (YYYY-MM-DD format)"
                    },
                    "date_to": {
                        "type": "string",
                        "description": "End date for filtering (YYYY-MM-DD format)"
                    },
                    "sort_by": {
                        "type": "string",
                        "enum": ["relevance", "lastUpdatedDate", "submittedDate"],
                        "description": "Sort results by",
                        "default": "relevance"
                    }
                },
                "required": ["query"]
            }
        ),he main __init__.py for better modularity.

#### Functions

##### (async) list_tools

List available MCP tools.

##### (async) call_tool

Handle MCP tool calls.

##### (async) main

Main entry point for the MCP server.

### exceptions

Custom exception classes for the ArXiv MCP server.
Extracted from the main __init__.py for better modularity.

#### Classes

##### ArxivError

Base exception for the ArXiv MCP server.

##### ProcessingError

Exception raised for general processing errors.

##### DownloadError

Exception raised for errors during file download.

##### ExtractionError

Exception raised for errors during archive extraction.

##### CompilationError

Exception raised for errors during LaTeX compilation.

##### ValidationError

Exception raised for input validation errors.

### __init__



### config

Configuration management for the ArXiv MCP server.
Provides centralized configuration for all processing components.
This module provides backward compatibility while the enhanced_config module
provides the full-featured configuration management.

#### Classes

##### PipelineConfig

Legacy configuration class for backward compatibility.

#### Functions

##### load_config

Load configuration from file or use defaults.
This function provides backward compatibility while using the enhanced configuration system.

### pipeline

Core pipeline orchestration for the ArXiv MCP server.
Extracted from the main __init__.py for better modularity.

#### Classes

##### ArxivPipeline

Enhanced ArXiv processing pipeline with async support and comprehensive error handling.

### __init__



### enhanced_config

Enhanced configuration management with YAML, JSON, and environment variable support.
Addresses the critic's recommendation for moving beyond hardcoded configuration.

#### Classes

##### PipelineConfig

Enhanced configuration for the ArXiv processing pipeline with validation.

##### ConfigurationManager

Enhanced configuration manager supporting multiple sources and formats.

#### Functions

##### load_config

Legacy function for backward compatibility.

##### get_pipeline_config

Get typed pipeline configuration.

### arxiv_api

ArXiv API client for searching and retrieving paper metadata.
Implements the missing search functionality identified in TODO.md.

#### Classes

##### ArxivAPIClient

Client for ArXiv API search and metadata retrieval.

#### Functions

##### (async) search_by_title

Search papers by title.

##### (async) search_by_author

Search papers by author.

##### (async) search_recent_papers

Search recent papers in a category.

### __init__

Clients module for external service interactions.
Extracted from the main __init__.py for better modularity.

#### Classes

##### AsyncArxivDownloader

Asynchronous ArXiv paper downloader with rate limiting and error handling.

### __init__

Processors module for document processing functionality.
Extracted from the main __init__.py for better modularity.

#### Classes

##### LaTeXProcessor

Enhanced LaTeX processor with compilation and parsing capabilities.

##### PDFProcessor

Enhanced PDF processor with text extraction and analysis.

### metrics

Comprehensive metrics collection for observability.
Extracted from the main __init__.py for better modularity.

#### Classes

##### MetricsCollector

Comprehensive metrics collection for observability

### docs_generator

API documentation generator for the ArXiv MCP server.

This module generates comprehensive API documentation from code annotations,
docstrings, and type hints, providing both Markdown and HTML output formats.

#### Classes

##### ParameterDoc

Documentation for a function/method parameter.

##### ToolDoc

Documentation for an MCP tool.

##### ModuleDoc

Documentation for a module.

##### APIDocumentation

Complete API documentation.

##### DocGenerator

Generates API documentation from code annotations.

#### Functions

##### generate_api_docs

Convenience function to generate API documentation.

Args:
    source_path: Path to the source code directory
    output_path: Path to save documentation
    formats: List of output formats ('markdown', 'json')

Returns:
    APIDocumentation object

### validation

Comprehensive input validation and sanitization.
Extracted from the main __init__.py for better modularity.

#### Classes

##### ArxivValidator

Comprehensive input validation and sanitization

### optional_deps

Optional dependencies management with graceful fallbacks.

This module provides utilities for handling optional dependencies and implementing
graceful fallbacks when dependencies are not available.

#### Classes

##### OptionalDependency

Manages optional dependencies with graceful fallbacks.

#### Functions

##### optional_import

Get an optional dependency manager.

##### requires_optional_dep

Decorator that requires an optional dependency.

##### get_available_features

Get a dictionary of available optional features.

##### check_optional_dependencies

Check all optional dependencies and return status information.

##### warn_missing_dependencies

Warn about any missing optional dependencies.

##### safe_import_nltk

Safely import NLTK with fallback.

##### safe_import_matplotlib

Safely import matplotlib with fallback.

##### safe_import_pandas

Safely import pandas with fallback.

##### safe_import_numpy

Safely import numpy with fallback.

##### _init_warnings

Initialize warnings for missing dependencies.

### __init__



### retry

Retry utilities for error recovery.
Simple, low-effort retry mechanisms for failed operations.

#### Functions

##### async_retry

Async retry decorator with exponential backoff.

Args:
    retries: Maximum number of retry attempts
    delay: Initial delay between retries in seconds
    backoff: Multiplier for delay between retries
    exceptions: Exception type(s) to catch and retry on

##### sync_retry

Synchronous retry decorator with exponential backoff.

### citations

Citation parsing and reference extraction for academic papers.

This module provides comprehensive citation parsing capabilities with support
for multiple citation formats (APA, MLA, IEEE, BibTeX) and reference extraction
from academic papers.

#### Classes

##### CitationFormat

Supported citation formats.

##### Citation

Represents a parsed citation.

##### CitationParser

Intelligent citation parser with multiple format support.

#### Functions

##### extract_citations_from_pdf_text

Convenience function to extract citations from PDF text.

##### format_citations_as_bibliography

Format multiple citations as a bibliography.

### logging

Enhanced logging configuration with structured JSON output.
Extracted from the main __init__.py for better modularity.

#### Functions

##### setup_logging

Configures structured JSON logging.

##### structured_logger

Get a structured logger instance.

