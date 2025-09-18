# Examples

This directory contains practical examples and usage demonstrations for the ArXiv MCP server.

## 📁 Example Categories

```text
examples/
├── basic/                  # Simple usage examples
├── advanced/              # Complex integration scenarios
├── integrations/          # Third-party service integrations
├── workflows/             # Complete workflow demonstrations
├── jupyter/               # Jupyter notebook examples
└── README.md             # This file
```text

## 🚀 Quick Start Examples

### Basic Paper Download

```python
# Download and convert a single ArXiv paper
from arxiv_mcp import download_and_convert_paper

result = await download_and_convert_paper(
    title="Attention Is All You Need",
    output_format="markdown"
)

print(f"Paper saved to: {result.output_path}")
```text

### Batch Processing

```python
# Process multiple papers at once
from arxiv_mcp import batch_download_and_convert

papers = [
    "Attention Is All You Need",
    "BERT: Pre-training of Deep Bidirectional Transformers",
    "GPT-3: Language Models are Few-Shot Learners"
]

results = await batch_download_and_convert(
    titles=papers,
    max_concurrency=3
)
```text

### Citation Analysis

```python
# Analyze citation networks
from arxiv_mcp import analyze_citation_network

network = await analyze_citation_network(
    root_paper="Attention Is All You Need",
    max_depth=2
)

print(f"Found {len(network.citations)} related papers")
```text

## 📚 Available Examples

### Current Examples

- **`demo_phase_4a_item_1.py`**: Basic MCP tool demonstration

### Planned Examples

#### `basic/`

- **`simple_download.py`**: Download single paper
- **`format_conversion.py`**: Convert between formats
- **`metadata_extraction.py`**: Extract paper metadata

#### `advanced/`

- **`custom_processing.py`**: Custom LaTeX processing
- **`bulk_analysis.py`**: Large-scale paper analysis
- **`performance_tuning.py`**: Optimization techniques

#### `integrations/`

- **`claude_integration.py`**: Use with Claude AI
- **`jupyter_notebook.py`**: Jupyter integration
- **`vscode_extension.py`**: VS Code integration

#### `workflows/`

- **`research_pipeline.py`**: Complete research workflow
- **`literature_review.py`**: Automated literature review
- **`paper_comparison.py`**: Compare multiple papers

## 🔧 Running Examples

### Prerequisites

```bash
# Install dependencies
uv sync

# Set up configuration
cp config/arxiv_mcp_example.yaml config/local.yaml
```text

### Basic Examples

```bash
# Run simple download example
uv run python examples/basic/simple_download.py

# Run with custom config
uv run python examples/basic/simple_download.py --config config/development.yaml
```bash

### Advanced Examples

```bash
# Run performance benchmarks
uv run python examples/advanced/performance_tuning.py

# Run integration tests
uv run python examples/integrations/claude_integration.py
```bash

## 📋 Example Standards

### Code Structure

```python
"""
Example: {Brief Description}

This example demonstrates {specific functionality} and shows
how to {achieve specific goal}.

Requirements:
- arxiv-mcp-improved
- Additional dependencies if any

Usage:
    python example_name.py [options]
"""

import asyncio
from arxiv_mcp import some_function

async def main():
    """Main example function."""
    # Example implementation
    pass

if __name__ == "__main__":
    asyncio.run(main())
```text

### Documentation Requirements

- Clear purpose and use case
- Prerequisites and dependencies
- Step-by-step execution
- Expected outputs
- Troubleshooting tips

---

_Examples should be runnable, educational, and demonstrate real-world usage patterns._
