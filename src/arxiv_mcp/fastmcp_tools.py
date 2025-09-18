#!/usr/bin/env python3
"""
ArXiv MCP Server using FastMCP - Fixed version for VS Code integration.
"""

from dataclasses import dataclass
from pathlib import Path
import sys

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from fastmcp import FastMCP

from arxiv_mcp.analyzers.network_analyzer import NetworkAnalyzer, NetworkNode, NetworkType

# Core imports
from arxiv_mcp.clients.arxiv_api import ArxivAPIClient
from arxiv_mcp.core.config import PipelineConfig
from arxiv_mcp.core.pipeline import ArxivPipeline

# Enhanced feature imports
from arxiv_mcp.enhanced.multi_temporal_cleanup import create_enhanced_adapter

# Parser and analyzer imports
from arxiv_mcp.parsers.citation_parser import CitationParser
from arxiv_mcp.utils.metrics import PerformanceMetrics

# Utils imports - moved from function level to top level
from arxiv_mcp.utils.unified_converter import (
    UnifiedDownloadConverter,
    download_and_convert_paper,
)
from arxiv_mcp.utils.workspace_resolver import workspace_resolver


@dataclass
class BatchConversionParams:
    """Parameters for batch download and conversion operations."""
    arxiv_ids: list[str]
    output_dir: str = "./output"
    save_latex: bool = True
    save_markdown: bool = True
    include_pdf: bool = False
    max_concurrent: int = 3

# Create FastMCP server instance
mcp = FastMCP("arxiv-mcp-improved")


@mcp.tool()
async def search_arxiv(
    query: str,
    max_results: int = 10,
    category: str = None,
) -> dict:
    """Search ArXiv papers with flexible criteria"""
    try:
        client = ArxivAPIClient()
        filters = {"max_results": max_results}
        if category:
            filters["category"] = category

        results = await client.search(query, **filters)
        return {
            "status": "success",
            "query": query,
            "results": results,
            "total_found": len(results),
        }
    except Exception as e:
        return {"status": "error", "error": str(e)}


@mcp.tool()
async def fetch_arxiv_paper_content(
    arxiv_id: str,
    include_pdf: bool = False,
) -> dict:
    """Download and extract content from an ArXiv paper"""
    try:
        config = PipelineConfig()
        pipeline = ArxivPipeline(config)
        result = await pipeline.process_paper(arxiv_id, include_pdf=include_pdf)

        if result.get("success"):
            return {
                "status": "success",
                "arxiv_id": arxiv_id,
                "content": result.get("extracted_text", ""),
                "main_tex_file": result.get("main_tex_file"),
                "file_count": result.get("file_count"),
                "pdf_compiled": result.get("pdf_compiled", False),
                "pdf_text": result.get("pdf_text"),
                "processing_time": result.get("processing_time"),
                "metadata": result.get("metadata", {}),
            }
        return {
            "status": "error",
            "arxiv_id": arxiv_id,
            "error": result.get("error", "Unknown error occurred"),
        }
    except Exception as e:
        return {"status": "error", "error": str(e)}


@mcp.tool()
async def download_and_convert_paper_tool(
    arxiv_id: str,
    output_dir: str = "./output",
    save_latex: bool = True,
    save_markdown: bool = True,
    include_pdf: bool = False,
) -> dict:
    """Download and convert an ArXiv paper to multiple formats"""
    try:
        # Resolve output directory relative to VS Code workspace root
        resolved_output_dir = workspace_resolver.resolve_output_path(output_dir)

        result = await download_and_convert_paper(
            arxiv_id=arxiv_id,
            output_dir=resolved_output_dir,
            save_latex=save_latex,
            save_markdown=save_markdown,
            include_pdf=include_pdf,
        )
    except Exception as e:
        return {
            "status": "error",
            "tool": "download_and_convert_paper",
            "error": f"Unified download and convert failed: {str(e)}",
        }
    else:
        return {"status": "success", "tool": "download_and_convert_paper", **result}


@mcp.tool()
async def batch_download_and_convert(
    arxiv_ids: list[str],
    output_dir: str = "./output",
    save_latex: bool = True,
    save_markdown: bool = True,
    include_pdf: bool = False,
) -> dict:
    """Batch download and convert multiple ArXiv papers

    Args:
        arxiv_ids: List of ArXiv paper IDs to process
        output_dir: Output directory for converted files
        save_latex: Whether to save LaTeX source files
        save_markdown: Whether to save converted Markdown files
        include_pdf: Whether to include PDF files
    """
    try:
        # Use fixed max_concurrent to reduce parameter count
        max_concurrent = 3

        # Create parameters object to reduce complexity
        params = BatchConversionParams(
            arxiv_ids=arxiv_ids,
            output_dir=output_dir,
            save_latex=save_latex,
            save_markdown=save_markdown,
            include_pdf=include_pdf,
            max_concurrent=max_concurrent,
        )

        # Resolve output directory relative to VS Code workspace root
        resolved_output_dir = workspace_resolver.resolve_output_path(params.output_dir)

        config = PipelineConfig.from_dict({"output_directory": resolved_output_dir})
        converter = UnifiedDownloadConverter(config)

        result = await converter.batch_download_and_convert(
            arxiv_ids=params.arxiv_ids,
            save_latex=params.save_latex,
            save_markdown=params.save_markdown,
            include_pdf=params.include_pdf,
            max_concurrent=params.max_concurrent,
        )
    except Exception as e:
        return {
            "status": "error",
            "tool": "batch_download_and_convert",
            "error": f"Batch download and convert failed: {str(e)}",
        }
    else:
        return {"status": "success", "tool": "batch_download_and_convert", **result}
@mcp.tool()
def get_output_structure(output_dir: str = "./output") -> dict:
    """Get information about the output directory structure"""
    try:
        config = PipelineConfig.from_dict({"output_directory": output_dir})
        converter = UnifiedDownloadConverter(config)
        structure = converter.get_output_structure()
    except Exception as e:
        return {
            "status": "error",
            "tool": "get_output_structure",
            "error": f"Getting output structure failed: {str(e)}",
        }
    else:
        return {"status": "success", "tool": "get_output_structure", **structure}


@mcp.tool()
def validate_conversion_quality(
    arxiv_id: str, output_dir: str = "./output", format_type: str = "both"
) -> dict:
    """Validate the quality of LaTeX to Markdown conversion with flexible format support

    Args:
        arxiv_id: ArXiv paper ID to validate
        output_dir: Output directory path
        format_type: Validation mode - "both", "latex_only", or "markdown_only"
    """
    try:
        config = PipelineConfig.from_dict({"output_directory": output_dir})
        converter = UnifiedDownloadConverter(config)
        quality_result = converter.validate_conversion_quality(arxiv_id, format_type)
    except Exception as e:
        return {
            "status": "error",
            "tool": "validate_conversion_quality",
            "error": f"Quality validation failed: {str(e)}",
        }
    else:
        return {
            "status": "success",
            "tool": "validate_conversion_quality",
            **quality_result,
        }


@mcp.tool()
def cleanup_output(output_dir: str = "./output", days_old: int = 30) -> dict:
    """Clean up old output files"""
    try:
        config = PipelineConfig.from_dict({"output_directory": output_dir})
        converter = UnifiedDownloadConverter(config)
        cleanup_result = converter.cleanup_output(days_old)
    except Exception as e:
        return {
            "status": "error",
            "tool": "cleanup_output",
            "error": f"Cleanup failed: {str(e)}",
        }
    else:
        return {"status": "success", "tool": "cleanup_output", **cleanup_result}


@mcp.tool()
def enhanced_cleanup_output(
    output_dir: str = "./output",
    time_spec: str = "30d",
    cleanup_type: str = "comprehensive"
) -> dict:
    """
    Enhanced cleanup with multi-temporal support (seconds to days precision).

    Args:
        output_dir: Output directory to clean
        time_spec: Time specification (e.g., '30s', '5m', '2h', '1d', '30d', '1h30m')
        cleanup_type: Type of cleanup ('files', 'batch', 'notifications', 'comprehensive')

    Returns:
        Dictionary with cleanup results
    """
    # Validate cleanup_type first
    if cleanup_type not in ["files", "batch", "notifications", "comprehensive"]:
        error_msg = (
            f"Unknown cleanup_type: {cleanup_type}. "
            "Must be one of: files, batch, notifications, comprehensive"
        )
        return {
            "status": "error",
            "tool": "enhanced_cleanup_output",
            "error": error_msg,
        }

    try:
        config = PipelineConfig.from_dict({"output_directory": output_dir})
        adapter = create_enhanced_adapter(config)

        if cleanup_type == "files":
            result = adapter.cleanup_files(time_spec, output_dir)
        elif cleanup_type == "batch":
            result = adapter.cleanup_batch_operations(time_spec)
        elif cleanup_type == "notifications":
            result = adapter.cleanup_notifications(time_spec)
        else:  # cleanup_type == "comprehensive"
            result = adapter.comprehensive_cleanup(time_spec, output_dir)
    except Exception as e:
        return {
            "status": "error",
            "tool": "enhanced_cleanup_output",
            "error": f"Enhanced cleanup failed: {str(e)}",
            "time_spec": time_spec,
            "cleanup_type": cleanup_type,
        }
    else:
        return {
            "status": "success",
            "tool": "enhanced_cleanup_output",
            "cleanup_type": cleanup_type,
            **result,
        }


@mcp.tool()
def extract_citations(text: str) -> dict:
    """Extract citations from paper text"""
    try:
        parser = CitationParser()
        citations = parser.extract_citations_from_text(text)
        return {
            "status": "success",
            "citations_found": len(citations),
            "citations": [
                {
                    "title": c.title,
                    "authors": c.authors,
                    "year": c.year,
                    "journal": c.journal,
                    "arxiv_id": c.arxiv_id,
                    "doi": c.doi,
                    "confidence": c.confidence,
                }
                for c in citations
            ],
        }
    except Exception as e:
        return {"status": "error", "error": str(e)}


@mcp.tool()
def analyze_citation_network(arxiv_ids: list[str]) -> dict:
    """Analyze citation networks and research connections"""
    try:
        analyzer = NetworkAnalyzer()

        # Create placeholder network analysis for the provided paper IDs
        nodes = []
        edges = []

        for paper_id in arxiv_ids:
            node = NetworkNode(
                node_id=paper_id,
                node_type="paper",
                label=f"Paper {paper_id}",
                attributes={"arxiv_id": paper_id},
            )
            nodes.append(node)

        # Analyze the network
        analysis = analyzer.analyze_network_from_data(nodes, edges, NetworkType.CITATION)
        return {
            "status": "success",
            "network_analysis": analysis,
            "nodes_analyzed": len(nodes),
            "edges_analyzed": len(edges),
        }
    except Exception as e:
        return {"status": "error", "error": str(e)}


@mcp.tool()
def get_processing_metrics(time_range: str = "24h") -> dict:
    """Get processing performance metrics"""
    try:
        metrics = PerformanceMetrics()
        performance_data = metrics.get_performance_summary(time_range)
    except Exception as e:
        return {
            "status": "error",
            "tool": "get_processing_metrics",
            "error": f"Failed to get metrics: {str(e)}",
        }
    else:
        return {
            "status": "success",
            "tool": "get_processing_metrics",
            "time_range": time_range,
            "metrics": performance_data,
        }


def main():
    """Main entry point for the MCP server."""
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
