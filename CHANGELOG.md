# Changelog

All notable changes to the ArXiv MCP Improved project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.2.0] - 2025-01-09

### Added

- **Modular Architecture**: Complete refactoring of monolithic structure into specialized modules
  - `src/arxiv_mcp/core/`: Core pipeline orchestration and configuration management
  - `src/arxiv_mcp/clients/`: External service interaction (ArXiv API, rate limiting)
  - `src/arxiv_mcp/processors/`: Document processing (LaTeX, PDF, text extraction)
  - `src/arxiv_mcp/utils/`: Utilities (logging, metrics, validation)
  - `src/arxiv_mcp/tools.py`: MCP tool implementations

- **Enhanced Configuration Management**:
  - YAML and JSON configuration file support
  - Environment variable overrides
  - Default configuration discovery
  - Configuration validation and type checking
  - Production and development configuration examples

- **Comprehensive Error Handling**:
  - Custom exception hierarchy (`ArxivMCPError`, `DownloadError`, `ExtractionError`, `CompilationError`)
  - Graceful degradation for optional dependencies
  - Structured error reporting and logging

- **Advanced Features**:
  - Asynchronous pipeline processing with semaphore-based resource management
  - Rate limiting with configurable requests per second and burst size
  - Caching system with SQLite backend
  - Structured JSON logging with rotation
  - Comprehensive metrics collection
  - Input validation and sanitization
  - Sandboxed LaTeX compilation
  - Parallel processing of multiple papers

- **Testing Infrastructure**:
  - Comprehensive test suite covering all components
  - Integration tests for modular architecture
  - Dependency management tests
  - Configuration flexibility tests

- **Documentation**:
  - Knowledge base organization in `.github/.knowledge_base/`
  - Tool usage documentation with reliability and speed assessments
  - Copilot instructions for development workflow
  - Configuration examples and best practices

### Changed

- **Breaking Change**: Migrated from monolithic to modular architecture
- Updated dependency management for better separation of concerns
- Enhanced logging with structured JSON output and configurable levels
- Improved ArXiv ID validation with support for both old and new formats

### Security

- Added path traversal protection for archive extraction
- Implemented sandboxing for LaTeX compilation
- Added file size and archive member count limits
- Input sanitization for all user-provided data

### Performance

- Asynchronous processing with configurable concurrency limits
- Intelligent rate limiting to respect ArXiv API guidelines
- Efficient caching mechanism with TTL support
- Resource management with semaphores for downloads, extractions, and compilations

## [0.1.0] - Initial Release

### Added

- Basic ArXiv paper fetching functionality
- LaTeX source extraction and PDF fallback
- Simple MCP server implementation
- Basic error handling and logging
