<!--
 * @Author: Zerui Han <hanzr.nju@outlook.com>
 * @Date: 2025-06-12 17:13:25
 * @Description: 
 * @FilePath: /arxiv-mcp/README.md
 * @LastEditTime: 2025-06-12 20:03:30
-->
# ArXiv Enhanced MCP Server

**🚀 Production Status: FULLY OPERATIONAL** | **📊 Tests: 112/112 Passing** | **🔧 MCP Tools: 10/10 Working** | **🧹 Repository: Professionally Organized**

A comprehensive Model Context Protocol (MCP) server for downloading, processing, and converting ArXiv papers with advanced LaTeX to Markdown conversion capabilities.

## 🎯 Production Validation

✅ **All Tools Verified Working** (v2.2.0):

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

**Recent Fixes (v2.2.0)**:

- ✅ **Citation Extraction**: Fixed missing dependencies, now fully functional
- ✅ **Performance Metrics**: Added comprehensive metrics collection and analysis
- ✅ **Network Analysis**: Enhanced citation network analysis with NetworkX support
- ✅ **Configuration**: Improved config file discovery (VS Code workspace support)
- ✅ **Figure Handling**: Better image format conversion (PDF → PNG paths)

[**View Full Production Status Report →**](PRODUCTION_STATUS.md)

## 🗂️ Repository Organization

✅ **Professional Development Standards**:

- **Clean Git History**: Only source code and configs tracked
- **Comprehensive .gitignore**: 160+ patterns for Python, IDE, OS, and cache files
- **Runtime Data Excluded**: Cache databases, logs, and temporary files properly ignored
- **Team-Ready**: Optimized for collaboration and CI/CD workflows

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

This project follows a "Surgical Organization" approach for optimal development workflow:

```bash
arxiv-mcp-improved/
├── src/              # Source code
├── tests/            # Test files
├── docs/             # Documentation
├── examples/         # Usage examples
├── cache/            # Working cache systems (preserved)
├── batch_cache/      # Batch processing cache
├── tag_cache/        # Tag cache system  
├── network_cache/    # Network cache
└── .dev/            # Development artifacts
    ├── build/        # Coverage reports, build outputs
    ├── runtime/      # Logs, generated outputs
    ├── temp/         # Temporary files
    └── artifacts/    # CI/CD artifacts
```

See `.dev/ORGANIZATION_GUIDELINES.md` for detailed organization principles.

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

- Python 3.8+
- `pandoc` (for LaTeX to Markdown conversion)
- `markitdown` (PDF fallback conversion)

### Setup

```bash
# Clone the repository
git clone https://github.com/your-repo/arxiv-mcp-improved

# Install dependencies
cd arxiv-mcp-improved
uv sync

# Install pandoc for LaTeX conversion
# Ubuntu/Debian:
sudo apt-get install pandoc texlive-xetex

# macOS:
brew install pandoc
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
2. **Regex Fallback**: Pattern-based conversion for simple documents
3. **Hybrid Approach**: Combines both methods for optimal results

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Update documentation
5. Submit a pull request

## 📄 License

MIT License - see LICENSE file for details.

## 📸 Example

![arxiv-mcp](https://github.com/user-attachments/assets/d965e081-ec07-43ca-b9a2-619107c10ad2)
