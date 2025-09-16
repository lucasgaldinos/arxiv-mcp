<!--
 * @Author: Zerui Han <hanzr.nju@outlook.com>
 * @Date: 2025-06-12 17:13:25
 * @Description: 
 * @FilePath: /arxiv-mcp/README.md
 * @LastEditTime: 2025-06-12 20:03:30
-->

# ArXiv Enhanced MCP Server

**🚀 Production Status: FULLY OPERATIONAL** | **📊 Tests: 144/144 Passing** | **🔧 MCP Tools: 11/11 Working** | **🧹 Repository: Enterprise Organized**

A comprehensive Model Context Protocol (MCP) server for downloading, processing, and converting ArXiv papers with advanced LaTeX to Markdown conversion capabilities.

## 🎯 Production Validation

✅ **All Tools Verified Working** (v2.4.2):

- 🔍 ArXiv paper search with advanced filters
- 📥 Paper download and LaTeX extraction
- 📄 Content processing and text extraction
- 🔗 Citation extraction and bibliography generation
- 📊 Performance metrics and monitoring
- 🕸️ Citation network analysis with NetworkX
- ⚡ Batch processing with concurrent operations
- ✅ Quality validation and conversion assessment
- 📁 Output management and file organization
- 🔧 Complete MCP server integration
- 🎯 Comprehensive processing tools testing

**Recent Enhancements (v2.4.2)**:

- ✅ **Comprehensive Testing**: 144/144 tests passing with 8 new processing tools tests
- ✅ **Real Academic Content**: Validation with real transformer/attention mechanism research
- ✅ **AutoSummarizer Enhancement**: Variable length summaries with confidence scoring
- ✅ **Citation Parser Improvements**: Real citation extraction (Vaswani et al., Devlin et al.)
- ✅ **Smart Tagger Implementation**: Academic terminology detection and categorization
- ✅ **Type Safety**: Enhanced Pydantic 2.11.7 integration with robust validation
- ✅ **Development Tools**: UV package manager for fast dependency management

[**View Full Production Status Report →**](PRODUCTION_STATUS.md)

## 🗂️ Enterprise Repository Organization

✅ **Professional Development Standards**:

- **Clean Git History**: Only source code and configurations tracked
- **Comprehensive .gitignore**: 160+ patterns for Python, IDE, OS, and cache files
- **Runtime Data Excluded**: Cache databases, logs, and temporary files properly isolated
- **Team-Ready**: Optimized for collaboration and CI/CD workflows
- **Documentation Framework**: Diátaxis structure (tutorials, how-to guides, reference, explanations)

## 📚 Documentation Structure

This project follows the **Diátaxis documentation framework** for optimal user experience:

- **[📖 Tutorials](docs/tutorials/)** - Learning-oriented guides for new users
- **[🛠️ How-To Guides](docs/how-to-guides/)** - Problem-solving guides for specific tasks
- **[📋 Reference](docs/reference/)** - Information-oriented API documentation
- **[💡 Explanation](docs/explanation/)** - Understanding-oriented architecture docs
- **[📦 Legacy](docs/legacy/)** - Historical documentation and migration guides

[**→ Explore Complete Documentation**](docs/README.md)

## 🏗️ Development Environment

✅ **Enterprise Development Standards**:

- **Package Management**: UV (faster than pip, with lockfile support)
- **Type Safety**: Pydantic 2.11.7 for robust data validation
- **Testing**: 144/144 tests passing with comprehensive coverage
- **Code Quality**: Automated linting, formatting, and type checking
- **Pre-commit Hooks**: Quality gates for consistent code standards

## 🚀 Features

### Core Capabilities

- **Flexible Input**: Accepts ArXiv IDs (e.g., `1706.03762`) or full ArXiv URLs
- **LaTeX Source Priority**: Downloads and extracts `.tex` files from paper source archives
- **PDF Fallback**: Converts PDFs to text when LaTeX source unavailable
- **File Organization**: Saves papers in organized directory structure (`latex/`, `markdown/`, `metadata/`)
- **Batch Processing**: Process multiple papers concurrently with configurable limits

### New Enhanced Features

- **LaTeX to Markdown Conversion**: High-quality conversion with pandoc integration and fallback methods
- **YAML Frontmatter**: Automatic metadata extraction and YAML header generation
- **Unified Download+Convert**: Single-command workflow for download and multi-format conversion
- **Quality Validation**: Assess conversion quality and detect potential issues
- **Output Management**: Organized file structure with manifest tracking and cleanup utilities

### Advanced Processing

- **Citation Analysis**: Extract and parse citations from papers
- **Network Analysis**: Analyze citation networks and research connections
- **Dependency Tracking**: Monitor package dependencies and versions
- **Performance Metrics**: Track processing statistics and optimization data

## 📁 Project Organization

This project follows **enterprise development standards** for optimal workflow:

```bash
arxiv-mcp-improved/
├── src/                    # Source code
├── tests/                  # Test files (unit/integration/legacy/fixtures)
├── docs/                   # Diátaxis documentation framework
│   ├── tutorials/          # Learning-oriented guides
│   ├── how-to-guides/      # Problem-solving guides
│   ├── reference/          # API documentation
│   ├── explanation/        # Architecture and design
│   └── legacy/             # Historical documentation
├── examples/               # Usage examples and demos
├── config/                 # Configuration files
├── scripts/                # Utility and automation scripts
├── cache/                  # Performance-critical cache systems (root level)
│   ├── arxiv/              # ArXiv API cache
│   ├── dependencies/       # Package dependency cache
│   ├── network/            # Network analysis cache
│   ├── notifications/      # Paper notification cache
│   ├── reading/            # Reading list cache
│   ├── tags/               # Smart tagging cache
│   ├── trending/           # Trending analysis cache
│   └── temp/               # Temporary cache
├── batch_cache/            # Batch processing cache (performance-critical)
├── dependency_cache/       # Dependency tracking cache (performance-critical) 
├── network_cache/          # Network request cache (performance-critical)
├── notification_cache/     # Notification system cache (performance-critical)
├── tag_cache/              # Tag analysis cache (performance-critical)
└── .dev/                  # Development artifacts (excluded from git)
    ├── build/              # Tool caches (pytest, mypy, ruff, coverage, rope)
    ├── runtime/            # Runtime data (logs → logs/, output → output/)
    │   ├── logs/           # Application logs (symlinked as logs/)
    │   └── output/         # Generated outputs (symlinked as output/)
    ├── cache/              # Development cache overflow
    ├── artifacts/          # Test outputs and reports  
    ├── temp/               # True temporary files (__pycache__, scratch)
    └── debug/              # Debugging and investigation tools
```

See [Development Guidelines](.github/instructions/development-guidelines.instructions.md) for detailed organization principles.

## 📁 Output Structure

When using the enhanced features, papers are organized as follows:

```bash
.dev/runtime/output/
├── latex/
│   └── {arxiv_id}/
│       ├── main.tex
│       ├── figures/
│       ├── sections/
│       └── manifest.json
├── markdown/
│   └── {arxiv_id}/
│       ├── {arxiv_id}.md      # Converted markdown with YAML frontmatter
│       └── metadata.json     # Extracted metadata
└── metadata/
    └── {arxiv_id}/
        └── processing_info.json
```

## 🛠 Usage

### Basic Paper Fetching

```python
# Fetch paper content (LaTeX preferred, PDF fallback)
await fetch_arxiv_paper_content("2301.07041")
```

### Enhanced Download and Convert

```python
# Download and convert to multiple formats
await download_and_convert_paper(
    arxiv_id="2301.07041",
    output_dir="./research_papers",
    save_latex=True,
    save_markdown=True
)
```

### Batch Processing

```python
# Process multiple papers concurrently
await batch_download_and_convert(
    arxiv_ids=["2301.07041", "1706.03762", "2012.11467"],
    output_dir="./batch_papers",
    max_concurrent=3
)
```

### Quality Validation

```python
# Validate conversion quality
quality_report = validate_conversion_quality("2301.07041")
print(f"Quality score: {quality_report['quality_score']}")
```

## 📋 Available Tools

### Core Tools

- `fetch_arxiv_paper_content` - Download and extract paper content
- `get_processing_metrics` - Get performance statistics
- `configure_pipeline` - Configure processing parameters

### Enhanced Tools

- `download_and_convert_paper` - Unified download and multi-format conversion
- `batch_download_and_convert` - Batch processing multiple papers
- `get_output_structure` - View organized output directory structure
- `validate_conversion_quality` - Assess LaTeX to Markdown conversion quality
- `cleanup_output` - Clean up old files and manage storage

### Analysis Tools

- `extract_citations` - Parse citations from paper text
- `parse_bibliography` - Format bibliography entries
- `check_dependencies` - Analyze package dependencies
- `analyze_citation_network` - Study research connections

## 🔧 Configuration

### Basic Configuration

Create `config/arxiv_mcp_production.json`:

```json
{
    "output_directory": "./arxiv_papers",
    "download_timeout": 30,
    "max_files_per_archive": 200,
    "latex_cleanup_enabled": true,
    "conversion_method": "pandoc_primary"
}
```

### Advanced Options

```json
{
    "performance_tracking": true,
    "concurrent_downloads": 3,
    "quality_validation": true,
    "metadata_extraction": true,
    "yaml_frontmatter": true,
    "cleanup_days": 30
}
```

## 📦 Installation

### Requirements

- **Python 3.11+** (required for modern async features)
- **UV Package Manager** (for fast dependency management)
- **Pandoc** (for LaTeX to Markdown conversion)
- **MarkItDown** (PDF fallback conversion)

### Quick Setup

```bash
# Clone the repository
git clone https://github.com/your-repo/arxiv-mcp-improved
cd arxiv-mcp-improved

# Install dependencies with UV (recommended)
uv sync

# Install pandoc for LaTeX conversion
# Ubuntu/Debian:
sudo apt-get install pandoc texlive-xetex

# macOS:
brew install pandoc

# Windows:
# Install from https://pandoc.org/installing.html
```

### Verify Installation

```bash
# Run the test suite to verify installation
uv run pytest tests/ -v

# Check MCP server functionality
uv run python -m arxiv_mcp --help
```

### Development Setup

```bash
# Install development dependencies
uv sync --all-extras

# Install pre-commit hooks
uv run pre-commit install

# Run quality checks
uv run ruff check src/ tests/
uv run mypy src/
```

## 🔍 Quality Assessment

The enhanced conversion system provides quality metrics:

- **Compression Ratio**: Measures content preservation during conversion
- **Structure Preservation**: Counts section headers and organization
- **Math Expression Handling**: Tracks mathematical notation conversion
- **Issue Detection**: Identifies unconverted LaTeX commands and environments

## 📈 Performance Features

- **Concurrent Processing**: Configurable parallel downloads
- **Caching**: Intelligent caching to avoid re-processing
- **Metrics Tracking**: Monitor download speeds and conversion quality
- **Resource Management**: Automatic cleanup and storage optimization

## 📝 Conversion Methods

1. **Pandoc Primary**: High-quality conversion with pandoc (recommended)
1. **Regex Fallback**: Pattern-based conversion for simple documents
1. **Hybrid Approach**: Combines both methods for optimal results

## 🤝 Contributing

We welcome contributions! Please follow our enterprise development standards:

### Development Workflow

1. **Fork** the repository and create a feature branch
1. **Follow** the [Development Guidelines](.github/instructions/development-guidelines.instructions.md)
1. **Write tests** for new functionality (maintain 85%+ coverage)
1. **Update documentation** following the Diátaxis framework
1. **Run quality checks** and ensure all tests pass
1. **Submit** a pull request with clear description

### Code Quality Standards

- **Type Safety**: Full type hints with Pydantic validation
- **Testing**: Comprehensive test coverage with unit/integration tests
- **Documentation**: Clear docstrings and user-facing documentation
- **Formatting**: Automated code formatting with Black and Ruff
- **Architecture**: Follow established patterns and SOLID principles

### Getting Started

```bash
# Setup development environment
uv sync --all-extras
uv run pre-commit install

# Run the full test suite
uv run pytest tests/ -v --cov=src/

# Validate workspace organization
uv run python scripts/validate_workspace.py
```

## 📄 License

MIT License - see [LICENSE](LICENSE) file for details.

## 🔗 Links

- **[📖 Documentation](docs/README.md)** - Complete user and developer guides
- **[🚀 Production Status](PRODUCTION_STATUS.md)** - Current operational status
- **[📋 TODO](TODO.md)** - Development roadmap and priorities
- **[📝 Changelog](CHANGELOG.md)** - Version history and changes
- **[🛠️ Development Guidelines](.github/instructions/development-guidelines.instructions.md)** - Standards and practices

______________________________________________________________________

**Last Updated**: January 2025 - v2.4.2\
**Maintenance**: Active development with enterprise standards\
**Support**: See [How-To Guides](docs/how-to-guides/) for troubleshooting

## 📸 Example

![arxiv-mcp](https://github.com/user-attachments/assets/d965e081-ec07-43ca-b9a2-619107c10ad2)
