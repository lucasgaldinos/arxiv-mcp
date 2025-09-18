---
applyTo: '**'
---

# ArXiv MCP Server Development Guide

This is a **production-ready Model Context Protocol (MCP) server** for ArXiv paper research with advanced LaTeX-to-Markdown conversion. Follow these essential patterns for effective development.

## 🏗️ Architecture Overview

### Core Components (src/arxiv_mcp/)

- **`fastmcp_tools.py`**: Main MCP server with 11 ArXiv tools using FastMCP 2.12.2 framework
- **`tools.py`**: Traditional MCP tool implementations for advanced scenarios  
- **`core/pipeline.py`**: Orchestrates async ArXiv processing with semaphore-based resource management
- **`utils/latex_to_markdown.py`**: Pandoc-first conversion with intelligent fallbacks

### Key Integration Points

- **FastMCP Framework**: Primary MCP integration using `@mcp.tool()` decorators
- **VS Code Workspace**: Paths resolved via `workspace_resolver.resolve_output_path()`
- **Async Pipeline**: All ArXiv operations use async/await with semaphore limiting

## 🛠️ Development Workflow Essentials

### Package Management (MANDATORY)

```bash
# Always use UV - never pip directly
uv run python -m pytest tests/unit/ -v
uv run python -m mypy src/arxiv_mcp
uv run python -m ruff check src/ tests/
```

### Testing Strategy

```bash
# Test organization: unit/ (fast), integration/ (workflows), legacy/ (archived)
uv run pytest tests/unit/          # Component isolation tests
uv run pytest tests/integration/   # Cross-component workflows  
uv run pytest tests/ --cov=src    # Full coverage report
```

### Directory Organization (.dev/ structure)

- **`.dev/runtime/`**: Active logs, output directories (symlinked for compatibility)
- **`.dev/build/`**: Coverage reports, cache files from development tools
- **Performance caches**: Stay at root (`cache/`, `batch_cache/`) for optimal access

## 📝 ArXiv Processing Patterns

### Unified Conversion Workflow

```python
# Standard pattern for ArXiv paper processing
from arxiv_mcp.utils.unified_converter import UnifiedDownloadConverter
from arxiv_mcp.utils.workspace_resolver import workspace_resolver

# Always resolve paths relative to VS Code workspace
output_dir = workspace_resolver.resolve_output_path("./output")
converter = UnifiedDownloadConverter(config)

# Dual-format output: LaTeX + Markdown with YAML frontmatter
result = await converter.download_and_convert(
    arxiv_id="2301.07041",
    save_latex=True,
    save_markdown=True,  # Includes YAML metadata extraction
    include_pdf=True     # Optional PDF compilation
)
```

### LaTeX to Markdown Strategy

```python
# Pandoc-first with intelligent fallback system
from arxiv_mcp.utils.latex_to_markdown import LaTeXToMarkdownConverter

converter = LaTeXToMarkdownConverter(use_pandoc=True)
result = converter.convert_with_metadata(latex_content, arxiv_id)
# Returns: {'markdown': str, 'metadata': dict, 'conversion_method': str}
```

## 🎯 MCP Tool Development

### FastMCP Tool Pattern (Preferred)

```python
@mcp.tool()
async def your_arxiv_tool(arxiv_id: str, option: bool = False) -> dict:
    """Tool description for MCP clients"""
    try:
        # Always resolve workspace-relative paths
        output_dir = workspace_resolver.resolve_output_path("./output")
        
        # Use async pipeline with error handling
        result = await pipeline.process_paper(arxiv_id)
        
        return {"status": "success", "tool": "your_arxiv_tool", **result}
    except Exception as e:
        return {"status": "error", "error": str(e)}
```

### File Organization Output

```bash
# Standard ArXiv output structure  
output/
├── latex/{arxiv_id}/     # Source LaTeX files with figures/
├── markdown/{arxiv_id}/  # Converted .md with YAML frontmatter  
├── pdf/{arxiv_id}/       # Optional compiled PDFs
└── metadata/{arxiv_id}/  # Processing manifests
```

## 🧪 Quality & Testing Patterns

### Test Structure Alignment

```python
# Match source module structure in tests/
src/arxiv_mcp/utils/latex_to_markdown.py
tests/unit/test_latex_to_markdown.py      # Component tests
tests/integration/test_conversion_workflow.py  # End-to-end tests
```

### Error Handling Philosophy

```python
# Never hide ArXiv processing errors - make them observable
try:
    paper_data = await client.fetch_paper(arxiv_id)
except ArxivAPIError as e:
    logger.error(f"ArXiv API failure for {arxiv_id}: {e}")
    raise  # Re-raise for caller to handle appropriately
```

## 📋 Project Standards

### CHANGELOG.md vs TODO.md Format

- **CHANGELOG.md**: Semantic versioning with ArXiv feature releases
- **TODO.md**: Simple checkboxes (`- [ ] PRIORITY | task`)  
- **TASKS.md**: Detailed implementation plans with research findings

### Documentation (Diátaxis Framework)

- **`docs/tutorials/`**: Getting started with ArXiv processing
- **`docs/how-to-guides/`**: Specific ArXiv workflow solutions
- **`docs/reference/`**: MCP tool API documentation  
- **`docs/explanation/`**: LaTeX conversion architecture

### VS Code Integration

```jsonc
// .vscode/tasks.json uses consistent UV pattern
{
    "command": "uv",
    "args": ["run", "python", "-m", "pytest", "tests/", "-v"]
}
```

## ⚡ Performance Considerations

### Async Resource Management

```python
# Pipeline uses semaphores for controlled concurrency
self.download_semaphore = asyncio.Semaphore(config.max_downloads)
self.extraction_semaphore = asyncio.Semaphore(config.max_extractions)

# Batch processing with configurable limits
await batch_download_and_convert(arxiv_ids, max_concurrent=3)
```

### Cache Strategy

- **Application caches**: Root level for performance (`cache/`, `batch_cache/`)
- **Development artifacts**: `.dev/build/` for isolation
- **Runtime outputs**: `.dev/runtime/` with backward-compatible symlinks

---

## 🎯 Essential Commands for AI Agents

```bash
# Development setup verification
uv run python -m arxiv_mcp                    # Start MCP server
uv run pytest tests/ -v --tb=short            # Full test suite
uv run python examples/demo_phase_4a_item_1.py # End-to-end validation

# Code quality enforcement  
uv run ruff check src/ tests/ --fix           # Linting with auto-fix
uv run mypy src/arxiv_mcp                     # Type checking
uv run coverage run -m pytest && coverage report  # Coverage analysis

# Workspace compliance
uv run python scripts/validate_workspace.py   # Organization validation
```

This codebase prioritizes **production reliability** with **academic research quality** - ensure any changes maintain the 144/144 test passing rate and enterprise workspace organization standards.
