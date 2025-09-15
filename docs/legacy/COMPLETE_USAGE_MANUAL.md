# ArXiv MCP Server - Complete Usage Manual

## 🎯 Overview

The ArXiv MCP Server provides 10 powerful tools for academic research workflows, from paper discovery to analysis and organization. This manual covers all input parameters, usage patterns, and best practices.

## 🛠️ Tool Reference

### 1. Search ArXiv (`mcp_arxiv-mcp-dev_search_arxiv`)

**Purpose**: Search ArXiv database for academic papers

**Parameters**:

- `query` (required): Search terms (e.g., "quantum computing", "machine learning")
- `category` (optional): ArXiv category filter (e.g., "cs.AI", "quant-ph")
- `max_results` (optional): Maximum papers to return (default: 10, max: 50)

**Usage Examples**:

```json
// Basic search
{
  "query": "quantum computing algorithms",
  "max_results": 20
}

// Category-specific search
{
  "query": "neural networks",
  "category": "cs.AI",
  "max_results": 15
}
```

**Output**: List of papers with metadata (title, authors, abstract, ArXiv ID)

______________________________________________________________________

### 2. Download and Convert Paper (`mcp_arxiv-mcp-dev_download_and_convert_paper`)

**Purpose**: Download a single paper and convert to multiple formats

**Parameters**:

- `arxiv_id` (required): ArXiv paper ID (e.g., "2109.02873v2")
- `include_pdf` (optional): Download PDF files (default: false)
- `output_dir` (optional): Output directory (default: "./output")
- `save_latex` (optional): Save LaTeX source (default: true)
- `save_markdown` (optional): Convert to Markdown (default: true)

**Usage Examples**:

```json
// Basic download (LaTeX + Markdown, no PDF)
{
  "arxiv_id": "2109.02873v2"
}

// Full download with PDF
{
  "arxiv_id": "2301.00003",
  "include_pdf": true,
  "output_dir": "./research_papers",
  "save_latex": true,
  "save_markdown": true
}

// Markdown only
{
  "arxiv_id": "1905.09692",
  "save_latex": false,
  "save_markdown": true
}
```

**Output**: Downloaded files in organized directory structure with manifest

______________________________________________________________________

### 3. Fetch Paper Content (`mcp_arxiv-mcp-dev_fetch_arxiv_paper_content`)

**Purpose**: Extract and return full paper content as text

**Parameters**:

- `arxiv_id` (required): ArXiv paper ID
- `include_pdf` (optional): Include PDF content (default: false)

**Usage Examples**:

```json
// Get text content only
{
  "arxiv_id": "2109.02873v2"
}

// Include PDF content
{
  "arxiv_id": "2301.00003",
  "include_pdf": true
}
```

**Output**: Full paper content as structured text

______________________________________________________________________

### 4. Batch Download and Convert (`mcp_arxiv-mcp-dev_batch_download_and_convert`)

**Purpose**: Download and convert multiple papers simultaneously

**Parameters**:

- `arxiv_ids` (required): Array of ArXiv paper IDs
- `include_pdf` (optional): Download PDFs for all papers (default: false)
- `max_concurrent` (optional): Maximum concurrent downloads (default: 3, max: 5)
- `output_dir` (optional): Output directory (default: "./output")
- `save_latex` (optional): Save LaTeX sources (default: true)
- `save_markdown` (optional): Convert to Markdown (default: true)

**Usage Examples**:

```json
// Basic batch download
{
  "arxiv_ids": ["2109.02873v2", "2001.05661", "1905.09692"]
}

// High-performance batch with PDFs
{
  "arxiv_ids": ["2301.00003", "2109.02873v2", "2001.05661"],
  "include_pdf": true,
  "max_concurrent": 5,
  "output_dir": "./batch_research"
}

// Conservative batch processing
{
  "arxiv_ids": ["1905.09692", "2301.00003"],
  "max_concurrent": 1,
  "save_latex": false,
  "save_markdown": true
}
```

**Output**: Batch processing results with success/failure statistics

______________________________________________________________________

### 5. Extract Citations (`mcp_arxiv-mcp-dev_extract_citations`)

**Purpose**: Extract citation references from paper text

**Parameters**:

- `text` (required): Paper text content to analyze

**Usage Examples**:

```json
{
  "text": "The groundbreaking work by Feynman (1982) introduced quantum simulation concepts. Later advances by Lloyd (1996) and Abrams & Lloyd (1997) expanded these ideas..."
}
```

**Output**: List of extracted citations with metadata

______________________________________________________________________

### 6. Analyze Citation Network (`mcp_arxiv-mcp-dev_analyze_citation_network`)

**Purpose**: Analyze relationships and networks between papers

**Parameters**:

- `arxiv_ids` (required): Array of ArXiv paper IDs to analyze

**Usage Examples**:

```json
// Simple network analysis
{
  "arxiv_ids": ["2109.02873v2", "2001.05661"]
}

// Complex network analysis
{
  "arxiv_ids": ["2109.02873v2", "2001.05661", "1905.09692", "2301.00003"]
}
```

**Output**: Network analysis with nodes, edges, clustering, and connectivity metrics

______________________________________________________________________

### 7. Get Processing Metrics (`mcp_arxiv-mcp-dev_get_processing_metrics`)

**Purpose**: Retrieve system performance and processing statistics

**Parameters**:

- `time_range` (optional): Time window for metrics (default: "24h")

**Usage Examples**:

```json
// Last 24 hours
{
  "time_range": "24h"
}

// Last week
{
  "time_range": "7d"
}

// Last hour
{
  "time_range": "1h"
}
```

**Output**: Performance metrics, counters, and system health indicators

______________________________________________________________________

### 8. Validate Conversion Quality (`mcp_arxiv-mcp-dev_validate_conversion_quality`)

**Purpose**: Assess quality of LaTeX to Markdown conversion

**Parameters**:

- `arxiv_id` (required): ArXiv paper ID to validate
- `output_dir` (optional): Directory containing converted files (default: "./output")

**Usage Examples**:

```json
// Validate specific paper
{
  "arxiv_id": "2109.02873v2"
}

// Validate with custom output directory
{
  "arxiv_id": "2301.00003",
  "output_dir": "./research_papers"
}
```

**Output**: Quality assessment with scores, issues, and improvement suggestions

______________________________________________________________________

### 9. Get Output Structure (`mcp_arxiv-mcp-dev_get_output_structure`)

**Purpose**: Analyze and report output directory organization

**Parameters**:

- `output_dir` (optional): Directory to analyze (default: "./output")

**Usage Examples**:

```json
// Default output directory
{}

// Custom directory
{
  "output_dir": "./my_research"
}
```

**Output**: Directory structure analysis with file counts and organization

______________________________________________________________________

### 10. Cleanup Output (`mcp_arxiv-mcp-dev_cleanup_output`)

**Purpose**: Remove old files and maintain clean workspace

**Parameters**:

- `days_old` (optional): Age threshold for cleanup (default: 30)
- `output_dir` (optional): Directory to clean (default: "./output")

**Usage Examples**:

```json
// Clean files older than 30 days
{}

// Aggressive cleanup (7 days)
{
  "days_old": 7
}

// Conservative cleanup (90 days)
{
  "days_old": 90,
  "output_dir": "./archive"
}
```

**Output**: Cleanup statistics and removed file counts

______________________________________________________________________

## 🔄 Common Workflows

### Academic Literature Review

1. Search for papers: `search_arxiv`
1. Download relevant papers: `batch_download_and_convert`
1. Analyze citation networks: `analyze_citation_network`
1. Validate conversions: `validate_conversion_quality`

### Single Paper Deep Dive

1. Search for specific paper: `search_arxiv`
1. Download with full content: `download_and_convert_paper` (include_pdf: true)
1. Extract full text: `fetch_arxiv_paper_content`
1. Extract citations: `extract_citations`

### System Maintenance

1. Check performance: `get_processing_metrics`
1. Analyze organization: `get_output_structure`
1. Clean old files: `cleanup_output`

## ⚡ Performance Guidelines

### Optimal Batch Processing

- Use `max_concurrent: 3` for standard networks
- Use `max_concurrent: 5` for high-performance systems
- Use `max_concurrent: 1` for limited bandwidth

### Storage Management

- LaTeX files are larger but preserve original formatting
- Markdown files are smaller and more readable
- PDFs add significant storage overhead
- Use cleanup regularly for long-term projects

### Error Handling

- All tools return status indicators
- Failed operations include error details
- Batch operations report per-item success/failure
- Validation tools highlight conversion issues

## 🎯 Best Practices

1. **Start Small**: Test with single papers before batch operations
1. **Monitor Storage**: Use `get_output_structure` to track space usage
1. **Validate Quality**: Run `validate_conversion_quality` on important papers
1. **Clean Regularly**: Use `cleanup_output` to maintain workspace
1. **Check Performance**: Monitor with `get_processing_metrics`

## 📊 Output Structure

```
output/
├── latex/           # LaTeX source files
│   └── {arxiv_id}/
│       ├── manifest.json
│       ├── main.tex
│       └── figures/
├── markdown/        # Converted markdown files
│   └── {arxiv_id}/
│       └── {arxiv_id}.md
└── metadata/        # Paper metadata
    └── {arxiv_id}.json
```

## 🔧 Troubleshooting

### Common Issues

- **Network timeouts**: Reduce `max_concurrent` for batch operations
- **Storage full**: Run `cleanup_output` or increase disk space
- **Conversion errors**: Check `validate_conversion_quality` for specific issues
- **PDF issues**: Some papers may have restricted PDF access

### Error Codes

- `status: "success"`: Operation completed successfully
- `status: "error"`: Operation failed, check error message
- `status: "partial"`: Batch operation with some failures

This manual provides complete coverage of all ArXiv MCP Server capabilities for academic research workflows.
