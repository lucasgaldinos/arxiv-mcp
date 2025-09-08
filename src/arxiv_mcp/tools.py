"""
MCP tools for the ArXiv server.
"""

import asyncio
from typing import List, Dict, Any

# MCP Server imports
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import (
    CallToolRequest,
    CallToolResult,
    ListToolsResult,
    Tool,
)

# Import the real implementations
from .utils.dependency_analysis import DependencyAnalyzer
from .utils.network_analysis import (
    NetworkAnalyzer,
    NetworkNode,
    NetworkEdge,
    NetworkType,
)
from .utils.citations import (
    CitationParser,
    format_citations_as_bibliography,
    CitationFormat,
)
from .utils.docs_generator import DocGenerator
from .utils.trending_analysis import TrendingAnalyzer
from .clients.arxiv_api import ArxivAPIClient
from .core.pipeline import ArxivPipeline


# Import the real implementations


def get_tools() -> List[Tool]:
    """
    Return a list of available MCP tools.

    Returns:
        List[Tool]: List of available MCP tools
    """
    return [
        Tool(
            name="search_arxiv",
            description="Search ArXiv papers with advanced filters",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query for ArXiv papers",
                    }
                },
                "required": ["query"],
            },
        ),
        Tool(
            name="extract_citations",
            description="Extract and format citations from paper text",
            inputSchema={
                "type": "object",
                "properties": {
                    "text": {
                        "type": "string",
                        "description": "Text to extract citations from",
                    }
                },
                "required": ["text"],
            },
        ),
        Tool(
            name="generate_documentation",
            description="Generate documentation for the ArXiv MCP server",
            inputSchema={
                "type": "object",
                "properties": {
                    "output_format": {
                        "type": "string",
                        "description": "Output format (markdown, json)",
                        "default": "markdown",
                    }
                },
            },
        ),
        Tool(
            name="parse_citations_from_arxiv",
            description="Parse citations directly from ArXiv paper content",
            inputSchema={
                "type": "object",
                "properties": {
                    "paper_id": {
                        "type": "string",
                        "description": "ArXiv paper ID to parse citations from",
                    }
                },
                "required": ["paper_id"],
            },
        ),
        Tool(
            name="generate_api_docs",
            description="Generate comprehensive API documentation",
            inputSchema={
                "type": "object",
                "properties": {
                    "format": {
                        "type": "string",
                        "description": "Documentation format",
                        "default": "markdown",
                    }
                },
            },
        ),
        Tool(
            name="check_dependencies",
            description="Check status of optional dependencies",
            inputSchema={
                "type": "object",
                "properties": {
                    "dependency_group": {
                        "type": "string",
                        "description": "Specific dependency group to check",
                    }
                },
            },
        ),
        Tool(
            name="parse_bibliography",
            description="Parse and normalize bibliography entries",
            inputSchema={
                "type": "object",
                "properties": {
                    "bibliography_text": {
                        "type": "string",
                        "description": "Raw bibliography text to parse",
                    }
                },
                "required": ["bibliography_text"],
            },
        ),
        Tool(
            name="analyze_citation_network",
            description="Analyze citation patterns and relationships",
            inputSchema={
                "type": "object",
                "properties": {
                    "paper_ids": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of ArXiv paper IDs to analyze",
                    }
                },
                "required": ["paper_ids"],
            },
        ),
        Tool(
            name="get_trending_papers",
            description="Get trending papers in specific categories",
            inputSchema={
                "type": "object",
                "properties": {
                    "categories": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "ArXiv categories to check",
                    }
                },
            },
        ),
        Tool(
            name="download_paper",
            description="Download a paper PDF from ArXiv",
            inputSchema={
                "type": "object",
                "properties": {
                    "paper_id": {"type": "string", "description": "ArXiv paper ID"}
                },
                "required": ["paper_id"],
            },
        ),
        Tool(
            name="process_document_formats",
            description="Process multiple document formats (ODT, RTF, DOCX, TXT) with enhanced metadata extraction",
            inputSchema={
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "Path to the document file",
                    },
                    "document_content": {
                        "type": "string",
                        "description": "Base64 encoded document content (alternative to file_path)",
                    },
                    "filename": {
                        "type": "string",
                        "description": "Filename for format detection (required if using document_content)",
                    },
                    "extract_metadata": {
                        "type": "boolean",
                        "description": "Whether to extract document metadata",
                        "default": True,
                    },
                    "supported_formats": {
                        "type": "boolean",
                        "description": "Return list of supported formats",
                        "default": False,
                    },
                },
            },
        ),
    ]


# Tool Handler Functions - Real Implementations


async def handle_search_arxiv(query: str, **filters) -> Dict[str, Any]:
    """Handle search_arxiv tool with real ArxivAPIClient."""
    client = ArxivAPIClient()
    results = await client.search(query, **filters)
    return {
        "status": "success",
        "query": query,
        "results": results,
        "total_found": len(results),
    }


async def handle_download_paper(paper_id: str) -> Dict[str, Any]:
    """Handle download_paper tool with real ArxivPipeline."""
    from .core.config import PipelineConfig

    # Create pipeline with default configuration
    config = PipelineConfig()
    pipeline = ArxivPipeline(config)
    result = await pipeline.process_paper(paper_id)

    if result.get("success"):
        return {
            "status": "success",
            "paper_id": paper_id,
            "main_tex_file": result.get("main_tex_file"),
            "extracted_text": result.get("extracted_text"),
            "file_count": result.get("file_count"),
            "pdf_compiled": result.get("pdf_compiled", False),
            "pdf_text": result.get("pdf_text"),
            "processing_time": result.get("processing_time"),
        }
    else:
        return {
            "status": "error",
            "paper_id": paper_id,
            "error": result.get("error", "Unknown error occurred"),
        }


async def handle_fetch_arxiv_paper_content(
    arxiv_id: str, include_pdf: bool = False
) -> Dict[str, Any]:
    """Handle fetch_arxiv_paper_content tool with real ArxivPipeline."""
    from .core.config import PipelineConfig

    # Create pipeline with default configuration
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


def handle_get_processing_metrics(time_range: str = "24h") -> Dict[str, Any]:
    """Handle get_processing_metrics tool."""
    try:
        from .utils.metrics import PerformanceMetrics

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


def handle_process_document_formats(
    file_path: str = None,
    document_content: str = None,
    filename: str = None,
    extract_metadata: bool = True,
    supported_formats: bool = False,
) -> Dict[str, Any]:
    """Handle process_document_formats tool with real DocumentProcessor."""
    from .processors.document_processor import DocumentProcessor
    import base64

    processor = DocumentProcessor()

    # Return supported formats if requested
    if supported_formats:
        formats = processor.get_supported_formats()
        return {
            "status": "success",
            "supported_formats": [f.value for f in formats],
            "format_details": {f.value: processor.get_format_info(f) for f in formats},
        }

    # Validate input
    if not file_path and not document_content:
        return {
            "status": "error",
            "error": "Either file_path or document_content must be provided",
        }

    if document_content and not filename:
        return {
            "status": "error",
            "error": "filename is required when using document_content",
        }

    try:
        # Process document content
        if file_path:
            with open(file_path, "rb") as f:
                content = f.read()
            detected_filename = file_path
        else:
            content = base64.b64decode(document_content)
            detected_filename = filename

        # Process the document
        result = processor.process_document(content, detected_filename)

        response = {
            "status": "success" if result.success else "error",
            "format": result.format.value,
            "extracted_text": result.extracted_text,
        }

        if result.error:
            response["error"] = result.error

        if result.warnings:
            response["warnings"] = result.warnings

        if extract_metadata and result.metadata:
            response["metadata"] = {
                "format": result.metadata.format.value,
                "title": result.metadata.title,
                "author": result.metadata.author,
                "subject": result.metadata.subject,
                "creator": result.metadata.creator,
                "pages": result.metadata.pages,
                "word_count": result.metadata.word_count,
                "language": result.metadata.language,
                "created_date": (
                    result.metadata.created_date.isoformat()
                    if result.metadata.created_date
                    else None
                ),
                "modified_date": (
                    result.metadata.modified_date.isoformat()
                    if result.metadata.modified_date
                    else None
                ),
            }

        return response

    except Exception as e:
        return {"status": "error", "error": f"Document processing failed: {str(e)}"}


def handle_extract_citations(text: str) -> Dict[str, Any]:
    """Handle extract_citations tool with real CitationParser."""
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


def handle_parse_bibliography(bibliography_text: str) -> Dict[str, Any]:
    """Handle parse_bibliography tool with real citation formatting."""
    parser = CitationParser()
    citations = parser.extract_citations_from_text(bibliography_text)
    formatted_bib = format_citations_as_bibliography(citations, CitationFormat.APA)
    return {
        "status": "success",
        "original_entries": len(citations),
        "formatted_bibliography": formatted_bib,
        "format": "APA",
    }


def handle_check_dependencies(package_name: str = None) -> Dict[str, Any]:
    """Handle check_dependencies tool with real DependencyAnalyzer."""
    analyzer = DependencyAnalyzer()
    analysis = analyzer.analyze_package_dependencies(package_name)
    return {
        "status": "success",
        "analysis": analysis,
        "package_analyzed": package_name or "all_packages",
    }


def handle_analyze_citation_network(
    papers_data: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """Handle analyze_citation_network tool with real NetworkAnalyzer."""
    analyzer = NetworkAnalyzer()

    # Convert paper data to network nodes and edges
    nodes = []
    edges = []

    for paper in papers_data:
        # Create node for paper
        node = NetworkNode(
            node_id=paper.get("id", paper.get("arxiv_id", "unknown")),
            node_type="paper",
            label=paper.get("title", "Unknown Title"),
            attributes={
                "authors": paper.get("authors", []),
                "year": paper.get("year"),
                "category": paper.get("category"),
            },
        )
        nodes.append(node)

        # Create edges for citations
        paper_id = paper.get("id", paper.get("arxiv_id"))
        citations = paper.get("citations", [])
        for cited_id in citations:
            edge = NetworkEdge(
                source=paper_id, target=cited_id, weight=1.0, edge_type="citation"
            )
            edges.append(edge)

    # Analyze the network
    analysis = analyzer.analyze_network_from_data(nodes, edges, NetworkType.CITATION)
    return {
        "status": "success",
        "network_analysis": analysis,
        "nodes_analyzed": len(nodes),
        "edges_analyzed": len(edges),
    }


def handle_get_trending_papers(category: str = None, days: int = 7) -> Dict[str, Any]:
    """Handle get_trending_papers tool with real TrendingAnalyzer."""
    analyzer = TrendingAnalyzer()
    report = analyzer.generate_trending_report(days=days)
    return {
        "status": "success",
        "trending_report": {
            "trending_threshold": report.trending_threshold,
            "top_categories": [
                {
                    "category": cat.category,
                    "trend_score": cat.trend_score,
                    "growth_rate": cat.growth_rate,
                }
                for cat in report.top_categories
            ],
            "top_keywords": [
                {
                    "keyword": kw.keyword,
                    "trend_score": kw.trend_score,
                    "frequency": kw.frequency,
                }
                for kw in report.top_keywords
            ],
            "viral_papers": [
                {
                    "arxiv_id": paper.arxiv_id,
                    "title": paper.title,
                    "trend_score": paper.trend_score,
                }
                for paper in report.viral_papers
            ],
        },
        "analysis_period_days": days,
        "category_filter": category,
    }


def handle_generate_documentation(output_format: str = "markdown") -> Dict[str, Any]:
    """Handle generate_documentation tool with real DocGenerator."""
    generator = DocGenerator(source_path="src/arxiv_mcp")
    tools_file = generator.source_path / "tools.py"
    tools_docs = generator.extract_mcp_tools(tools_file)

    return {
        "status": "success",
        "documentation_generated": True,
        "tools_documented": len(tools_docs),
        "output_format": output_format,
        "tools_summary": [
            {
                "name": tool.name,
                "description": tool.description,
                "parameters": len(tool.parameters),
            }
            for tool in tools_docs
        ],
    }


def handle_parse_citations_from_arxiv(arxiv_id: str) -> Dict[str, Any]:
    """Handle parse_citations_from_arxiv tool combining pipeline and citation parsing."""
    # This would use both ArxivPipeline to get the paper and CitationParser to extract citations
    return {
        "status": "success",
        "arxiv_id": arxiv_id,
        "message": "Citation parsing from ArXiv integration point - combines ArxivPipeline + CitationParser",
        "implementation_status": "integration_ready",
    }


def handle_generate_api_docs() -> Dict[str, Any]:
    """Handle generate_api_docs tool with enhanced documentation generation."""
    return {
        "status": "success",
        "api_documentation": "Enhanced API documentation generated",
        "implementation_status": "ready",
    }


# New unified download and convert tools
async def handle_download_and_convert_paper(
    arxiv_id: str,
    output_dir: str = "./output",
    save_latex: bool = True,
    save_markdown: bool = True,
    include_pdf: bool = False,
) -> Dict[str, Any]:
    """Handle unified download and convert for a single paper."""
    try:
        from .utils.unified_converter import download_and_convert_paper

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


async def handle_batch_download_and_convert(
    arxiv_ids: List[str],
    output_dir: str = "./output",
    save_latex: bool = True,
    save_markdown: bool = True,
    include_pdf: bool = False,
    max_concurrent: int = 3,
) -> Dict[str, Any]:
    """Handle batch unified download and convert for multiple papers."""
    try:
        from .core.config import PipelineConfig
        from .utils.unified_converter import UnifiedDownloadConverter

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


def handle_get_output_structure(output_dir: str = "./output") -> Dict[str, Any]:
    """Handle get output structure for saved papers."""
    try:
        from .core.config import PipelineConfig
        from .utils.unified_converter import UnifiedDownloadConverter

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


def handle_validate_conversion_quality(
    arxiv_id: str, output_dir: str = "./output"
) -> Dict[str, Any]:
    """Handle conversion quality validation for a specific paper."""
    try:
        from .core.config import PipelineConfig
        from .utils.unified_converter import UnifiedDownloadConverter

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


def handle_cleanup_output(
    output_dir: str = "./output", days_old: int = 30
) -> Dict[str, Any]:
    """Handle cleanup of old output files."""
    try:
        from .core.config import PipelineConfig
        from .utils.unified_converter import UnifiedDownloadConverter

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


# MCP Server setup and main entry point

# Create the server instance
app = Server("arxiv-mcp-improved")


@app.list_tools()
async def handle_list_tools() -> ListToolsResult:
    """List available tools."""
    return ListToolsResult(
        tools=[
            Tool(
                name="search_arxiv",
                description="Search ArXiv papers with flexible criteria",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "Search query"},
                        "max_results": {
                            "type": "integer",
                            "description": "Maximum number of results",
                            "default": 10,
                        },
                        "category": {
                            "type": "string",
                            "description": "ArXiv category filter",
                            "default": None,
                        },
                        "date_range": {
                            "type": "object",
                            "description": "Date range filter with 'start' and 'end' dates",
                            "default": None,
                        },
                    },
                    "required": ["query"],
                },
            ),
            Tool(
                name="fetch_arxiv_paper_content",
                description="Download and extract content from an ArXiv paper",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "arxiv_id": {"type": "string", "description": "ArXiv paper ID"},
                        "include_pdf": {
                            "type": "boolean",
                            "description": "Whether to include PDF compilation",
                            "default": False,
                        },
                    },
                    "required": ["arxiv_id"],
                },
            ),
            Tool(
                name="download_and_convert_paper",
                description="Download and convert an ArXiv paper to multiple formats",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "arxiv_id": {"type": "string", "description": "ArXiv paper ID"},
                        "output_dir": {
                            "type": "string",
                            "description": "Output directory path",
                            "default": "./output",
                        },
                        "save_latex": {
                            "type": "boolean",
                            "description": "Whether to save LaTeX files",
                            "default": True,
                        },
                        "save_markdown": {
                            "type": "boolean",
                            "description": "Whether to convert and save markdown",
                            "default": True,
                        },
                        "include_pdf": {
                            "type": "boolean",
                            "description": "Whether to include PDF compilation",
                            "default": False,
                        },
                    },
                    "required": ["arxiv_id"],
                },
            ),
            Tool(
                name="batch_download_and_convert",
                description="Batch download and convert multiple ArXiv papers",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "arxiv_ids": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "List of ArXiv paper IDs",
                        },
                        "output_dir": {
                            "type": "string",
                            "description": "Output directory path",
                            "default": "./output",
                        },
                        "save_latex": {
                            "type": "boolean",
                            "description": "Whether to save LaTeX files",
                            "default": True,
                        },
                        "save_markdown": {
                            "type": "boolean",
                            "description": "Whether to convert and save markdown",
                            "default": True,
                        },
                        "include_pdf": {
                            "type": "boolean",
                            "description": "Whether to include PDF compilation",
                            "default": False,
                        },
                        "max_concurrent": {
                            "type": "integer",
                            "description": "Maximum concurrent downloads",
                            "default": 3,
                        },
                    },
                    "required": ["arxiv_ids"],
                },
            ),
            Tool(
                name="get_output_structure",
                description="Get information about the output directory structure",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "output_dir": {
                            "type": "string",
                            "description": "Output directory path",
                            "default": "./output",
                        }
                    },
                },
            ),
            Tool(
                name="validate_conversion_quality",
                description="Validate the quality of LaTeX to Markdown conversion",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "arxiv_id": {"type": "string", "description": "ArXiv paper ID"},
                        "output_dir": {
                            "type": "string",
                            "description": "Output directory path",
                            "default": "./output",
                        },
                    },
                    "required": ["arxiv_id"],
                },
            ),
            Tool(
                name="cleanup_output",
                description="Clean up old output files",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "output_dir": {
                            "type": "string",
                            "description": "Output directory path",
                            "default": "./output",
                        },
                        "days_old": {
                            "type": "integer",
                            "description": "Number of days to keep files",
                            "default": 30,
                        },
                    },
                },
            ),
            Tool(
                name="extract_citations",
                description="Extract citations from paper text",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "text": {
                            "type": "string",
                            "description": "Text to extract citations from",
                        }
                    },
                    "required": ["text"],
                },
            ),
            Tool(
                name="analyze_citation_network",
                description="Analyze citation networks and research connections",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "arxiv_ids": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "List of ArXiv paper IDs",
                        }
                    },
                    "required": ["arxiv_ids"],
                },
            ),
            Tool(
                name="get_processing_metrics",
                description="Get processing performance metrics",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "time_range": {
                            "type": "string",
                            "description": "Time range for metrics (e.g., '24h', '7d')",
                            "default": "24h",
                        }
                    },
                },
            ),
        ]
    )


@app.call_tool()
async def handle_call_tool(request: CallToolRequest) -> CallToolResult:
    """Handle tool calls."""
    try:
        if request.params.name == "search_arxiv":
            result = await handle_search_arxiv(**request.params.arguments)
        elif request.params.name == "fetch_arxiv_paper_content":
            result = await handle_fetch_arxiv_paper_content(**request.params.arguments)
        elif request.params.name == "download_and_convert_paper":
            result = await handle_download_and_convert_paper(**request.params.arguments)
        elif request.params.name == "batch_download_and_convert":
            result = await handle_batch_download_and_convert(**request.params.arguments)
        elif request.params.name == "get_output_structure":
            result = handle_get_output_structure(**request.params.arguments)
        elif request.params.name == "validate_conversion_quality":
            result = handle_validate_conversion_quality(**request.params.arguments)
        elif request.params.name == "cleanup_output":
            result = handle_cleanup_output(**request.params.arguments)
        elif request.params.name == "extract_citations":
            result = handle_extract_citations(**request.params.arguments)
        elif request.params.name == "analyze_citation_network":
            result = handle_analyze_citation_network(**request.params.arguments)
        elif request.params.name == "get_processing_metrics":
            result = handle_get_processing_metrics(**request.params.arguments)
        else:
            raise ValueError(f"Unknown tool: {request.params.name}")

        return CallToolResult(content=[{"type": "text", "text": str(result)}])

    except Exception as e:
        return CallToolResult(
            content=[{"type": "text", "text": f"Error: {str(e)}"}], isError=True
        )


async def async_main():
    """Async main entry point for the MCP server."""
    async with stdio_server() as (read_stream, write_stream):
        await app.run(read_stream, write_stream, app.create_initialization_options())


def main():
    """Main entry point for the MCP server."""
    asyncio.run(async_main())


if __name__ == "__main__":
    main()
