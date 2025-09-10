#!/usr/bin/env python3
"""
ArXiv MCP Server using FastMCP - Fixed version for VS Code integration.
"""
import asyncio
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from fastmcp import FastMCP
from arxiv_mcp.clients.arxiv_api import ArxivAPIClient
from arxiv_mcp.core.pipeline import ArxivPipeline
from arxiv_mcp.core.config import PipelineConfig

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
        else:
            return {
                "status": "error",
                "arxiv_id": arxiv_id,
                "error": result.get("error", "Unknown error occurred"),
            }
    except Exception as e:
        return {"status": "error", "error": str(e)}


@mcp.tool()
async def download_and_convert_paper(
    arxiv_id: str,
    output_dir: str = "./output",
    save_latex: bool = True,
    save_markdown: bool = True,
    include_pdf: bool = False,
) -> dict:
    """Download and convert an ArXiv paper to multiple formats"""
    try:
        from arxiv_mcp.utils.unified_converter import download_and_convert_paper

        result = await download_and_convert_paper(
            arxiv_id=arxiv_id,
            output_dir=output_dir,
            save_latex=save_latex,
            save_markdown=save_markdown,
        )

        return {"status": "success", "tool": "download_and_convert_paper", **result}

    except Exception as e:
        return {
            "status": "error",
            "tool": "download_and_convert_paper",
            "error": f"Unified download and convert failed: {str(e)}",
        }


@mcp.tool()
async def batch_download_and_convert(
    arxiv_ids: list[str],
    output_dir: str = "./output",
    save_latex: bool = True,
    save_markdown: bool = True,
    include_pdf: bool = False,
    max_concurrent: int = 3,
) -> dict:
    """Batch download and convert multiple ArXiv papers"""
    try:
        from arxiv_mcp.core.config import PipelineConfig
        from arxiv_mcp.utils.unified_converter import UnifiedDownloadConverter

        config = PipelineConfig.from_dict({"output_directory": output_dir})
        converter = UnifiedDownloadConverter(config)

        result = await converter.batch_download_and_convert(
            arxiv_ids=arxiv_ids,
            save_latex=save_latex,
            save_markdown=save_markdown,
            include_pdf=include_pdf,
            max_concurrent=max_concurrent,
        )

        return {"status": "success", "tool": "batch_download_and_convert", **result}

    except Exception as e:
        return {
            "status": "error",
            "tool": "batch_download_and_convert",
            "error": f"Batch download and convert failed: {str(e)}",
        }


@mcp.tool()
def get_output_structure(output_dir: str = "./output") -> dict:
    """Get information about the output directory structure"""
    try:
        from arxiv_mcp.core.config import PipelineConfig
        from arxiv_mcp.utils.unified_converter import UnifiedDownloadConverter

        config = PipelineConfig.from_dict({"output_directory": output_dir})
        converter = UnifiedDownloadConverter(config)

        structure = converter.get_output_structure()

        return {"status": "success", "tool": "get_output_structure", **structure}

    except Exception as e:
        return {
            "status": "error",
            "tool": "get_output_structure",
            "error": f"Getting output structure failed: {str(e)}",
        }


@mcp.tool()
def validate_conversion_quality(arxiv_id: str, output_dir: str = "./output") -> dict:
    """Validate the quality of LaTeX to Markdown conversion"""
    try:
        from arxiv_mcp.core.config import PipelineConfig
        from arxiv_mcp.utils.unified_converter import UnifiedDownloadConverter

        config = PipelineConfig.from_dict({"output_directory": output_dir})
        converter = UnifiedDownloadConverter(config)

        quality_result = converter.validate_conversion_quality(arxiv_id)

        return {
            "status": "success",
            "tool": "validate_conversion_quality",
            **quality_result,
        }

    except Exception as e:
        return {
            "status": "error",
            "tool": "validate_conversion_quality",
            "error": f"Quality validation failed: {str(e)}",
        }


@mcp.tool()
def cleanup_output(output_dir: str = "./output", days_old: int = 30) -> dict:
    """Clean up old output files"""
    try:
        from arxiv_mcp.core.config import PipelineConfig
        from arxiv_mcp.utils.unified_converter import UnifiedDownloadConverter

        config = PipelineConfig.from_dict({"output_directory": output_dir})
        converter = UnifiedDownloadConverter(config)

        cleanup_result = converter.cleanup_output(days_old)

        return {"status": "success", "tool": "cleanup_output", **cleanup_result}

    except Exception as e:
        return {
            "status": "error",
            "tool": "cleanup_output",
            "error": f"Cleanup failed: {str(e)}",
        }


@mcp.tool()
def extract_citations(text: str) -> dict:
    """Extract citations from paper text"""
    try:
        from arxiv_mcp.parsers.citation_parser import CitationParser

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
        from arxiv_mcp.analyzers.network_analyzer import NetworkAnalyzer
        from arxiv_mcp.analyzers.network_analyzer import NetworkNode, NetworkEdge, NetworkType

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
        from arxiv_mcp.utils.metrics import PerformanceMetrics

        metrics = PerformanceMetrics()
        performance_data = metrics.get_performance_summary(time_range)

        return {
            "status": "success",
            "tool": "get_processing_metrics",
            "time_range": time_range,
            "metrics": performance_data,
        }
    except Exception as e:
        return {
            "status": "error",
            "tool": "get_processing_metrics",
            "error": f"Failed to get metrics: {str(e)}",
        }


def main():
    """Main entry point for the MCP server."""
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
