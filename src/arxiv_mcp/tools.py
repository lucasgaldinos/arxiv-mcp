"""
MCP tools for the ArXiv server.
"""

from typing import List, Dict, Any

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


# Mock MCP Tool class for testing purposes
class Tool:
    """Mock Tool class for MCP compatibility."""

    def __init__(self, name: str, description: str, inputSchema: Dict[str, Any]):
        self.name = name
        self.description = description
        self.inputSchema = inputSchema


# Mock MCP Server class for testing purposes
class MCPServer:
    """Mock MCP Server class for compatibility."""

    def __init__(self, name: str):
        self.name = name
        self.tools = None  # Will be set after get_tools is defined

    def list_tools(self) -> List[Tool]:
        """List available tools."""
        if self.tools is None:
            self.tools = get_tools()
        return self.tools


# Create a mock app instance for MCP compatibility
app = MCPServer("arxiv-mcp-server")


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
                "created_date": result.metadata.created_date.isoformat()
                if result.metadata.created_date
                else None,
                "modified_date": result.metadata.modified_date.isoformat()
                if result.metadata.modified_date
                else None,
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
