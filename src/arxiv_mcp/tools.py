"""
MCP tools for the ArXiv server.
Extracted from the main __init__.py for better modularity.
"""

import asyncio
from typing import Dict, Any, List
from mcp.server import Server
from mcp.types import Tool, TextContent

from .core.config import load_config, PipelineConfig
from .core.pipeline import ArxivPipeline
from .utils.logging import structured_logger
from .utils.validation import ArxivValidator
from .clients.arxiv_api import ArxivAPIClient


# Initialize components
logger = structured_logger()
validator = ArxivValidator()
config_dict = load_config()
config = PipelineConfig.from_dict(config_dict)
pipeline = ArxivPipeline(config)
arxiv_api = ArxivAPIClient(requests_per_second=config.requests_per_second)

# Initialize MCP server
app = Server("arxiv-mcp-improved")


@app.list_tools()
async def list_tools() -> List[Tool]:
    """List available MCP tools."""
    return [
        Tool(
            name="search_arxiv",
            description="Search ArXiv papers by query terms",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query for ArXiv papers",
                    },
                    "max_results": {
                        "type": "integer",
                        "description": "Maximum number of results to return",
                        "default": 10,
                    },
                },
                "required": ["query"],
            },
        ),
        Tool(
            name="get_paper_details",
            description="Get detailed information about a specific ArXiv paper",
            inputSchema={
                "type": "object",
                "properties": {
                    "arxiv_id": {
                        "type": "string",
                        "description": "ArXiv paper ID (e.g., '2301.00001')",
                    },
                    "include_pdf": {
                        "type": "boolean",
                        "description": "Whether to compile and include PDF analysis",
                        "default": True,
                    },
                },
                "required": ["arxiv_id"],
            },
        ),
        Tool(
            name="process_multiple_papers",
            description="Process multiple ArXiv papers concurrently",
            inputSchema={
                "type": "object",
                "properties": {
                    "arxiv_ids": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of ArXiv paper IDs",
                    },
                    "include_pdf": {
                        "type": "boolean",
                        "description": "Whether to compile and include PDF analysis",
                        "default": True,
                    },
                },
                "required": ["arxiv_ids"],
            },
        ),
        Tool(
            name="get_pipeline_status",
            description="Get current pipeline status and metrics",
            inputSchema={
                "type": "object",
                "properties": {},
                "additionalProperties": False,
            },
        ),
    ]


@app.call_tool()
async def call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
    """Handle MCP tool calls."""
    try:
        if name == "search_arxiv":
            # Real ArXiv API search implementation
            query = arguments["query"]
            max_results = arguments.get("max_results", 10)

            logger.info(f"Searching ArXiv API for: {query}")

            try:
                # Use real ArXiv API client
                result = await arxiv_api.search(query=query, max_results=max_results)

                # Format results for display
                formatted_results = []
                for paper in result["papers"]:
                    formatted_paper = {
                        "id": paper["id"],
                        "title": paper["title"],
                        "authors": paper["authors"],
                        "published": paper.get("published", "Unknown"),
                        "categories": paper["categories"],
                        "summary": paper["summary"][:300] + "..."
                        if len(paper["summary"]) > 300
                        else paper["summary"],
                    }
                    formatted_results.append(formatted_paper)

                return [
                    TextContent(
                        type="text",
                        text=f"ArXiv search results for '{query}':\n\nTotal results: {result['total_results']}\nReturned: {len(formatted_results)}\n\nPapers:\n"
                        + "\n".join(
                            [
                                f"[{i + 1}] {paper['id']}: {paper['title']}\n    Authors: {', '.join(paper['authors'])}\n    Published: {paper['published']}\n    Categories: {', '.join(paper['categories'])}\n    Summary: {paper['summary']}\n"
                                for i, paper in enumerate(formatted_results)
                            ]
                        ),
                    )
                ]

            except Exception as e:
                logger.error(f"ArXiv API search failed: {str(e)}")
                return [
                    TextContent(
                        type="text",
                        text=f"ArXiv search failed: {str(e)}\n\nFalling back to placeholder results:\n"
                        + f"Query: {query}\nMax results: {max_results}\n\nNote: Please check ArXiv API connectivity or rate limits.",
                    )
                ]

        elif name == "get_paper_details":
            arxiv_id = arguments["arxiv_id"]
            include_pdf = arguments.get("include_pdf", True)

            if not validator.validate_arxiv_id(arxiv_id):
                return [
                    TextContent(
                        type="text", text=f"Error: Invalid ArXiv ID format: {arxiv_id}"
                    )
                ]

            logger.info(f"Processing paper: {arxiv_id}")
            result = await pipeline.process_paper(arxiv_id, include_pdf)

            return [
                TextContent(type="text", text=f"Paper processing result:\n{result}")
            ]

        elif name == "process_multiple_papers":
            arxiv_ids = arguments["arxiv_ids"]
            include_pdf = arguments.get("include_pdf", True)

            # Validate all IDs
            invalid_ids = [
                id for id in arxiv_ids if not validator.validate_arxiv_id(id)
            ]
            if invalid_ids:
                return [
                    TextContent(
                        type="text",
                        text=f"Error: Invalid ArXiv ID formats: {invalid_ids}",
                    )
                ]

            logger.info(f"Processing {len(arxiv_ids)} papers")
            results = await pipeline.process_multiple_papers(arxiv_ids, include_pdf)

            return [
                TextContent(type="text", text=f"Batch processing results:\n{results}")
            ]

        elif name == "get_pipeline_status":
            status = pipeline.get_pipeline_status()

            return [TextContent(type="text", text=f"Pipeline status:\n{status}")]

        else:
            return [TextContent(type="text", text=f"Error: Unknown tool: {name}")]

    except Exception as e:
        logger.error(f"Tool call failed for {name}: {str(e)}")
        return [TextContent(type="text", text=f"Error: {str(e)}")]


async def main():
    """Main entry point for the MCP server."""
    # Import here to avoid circular imports
    from mcp.server.stdio import stdio_server

    logger.info("Starting ArXiv MCP server...")

    async with stdio_server() as (read_stream, write_stream):
        await app.run(read_stream, write_stream, app.create_initialization_options())


if __name__ == "__main__":
    asyncio.run(main())
