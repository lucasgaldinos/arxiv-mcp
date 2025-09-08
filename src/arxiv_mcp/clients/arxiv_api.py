"""
ArXiv API client for searching and retrieving paper metadata.
Implements the missing search functionality identified in TODO.md.
"""

import asyncio
import aiohttp
import xml.etree.ElementTree as ET
from typing import Dict, List, Any, Optional
from urllib.parse import urlencode, quote
from datetime import datetime

from ..utils.logging import structured_logger
from ..exceptions import ArxivError


class ArxivAPIClient:
    """Client for ArXiv API search and metadata retrieval."""

    BASE_URL = "http://export.arxiv.org/api/query"
    NAMESPACE = {
        "atom": "http://www.w3.org/2005/Atom",
        "opensearch": "http://a9.com/-/spec/opensearch/1.1/",
        "arxiv": "http://arxiv.org/schemas/atom",
    }

    def __init__(self, requests_per_second: float = 2.0):
        self.logger = structured_logger()
        self.rate_limit_delay = 1.0 / requests_per_second
        self.last_request_time = 0

    async def _rate_limit(self):
        """Enforce rate limiting between requests."""
        current_time = asyncio.get_event_loop().time()
        time_since_last = current_time - self.last_request_time

        if time_since_last < self.rate_limit_delay:
            await asyncio.sleep(self.rate_limit_delay - time_since_last)

        self.last_request_time = asyncio.get_event_loop().time()

    async def search(
        self,
        query: str,
        max_results: int = 10,
        start: int = 0,
        sort_by: str = "relevance",
        sort_order: str = "descending",
        categories: Optional[List[str]] = None,
        authors: Optional[List[str]] = None,
        date_range: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """
        Search ArXiv papers using the API.

        Args:
            query: Search query string
            max_results: Maximum number of results to return
            start: Starting index for pagination
            sort_by: Sort by 'relevance', 'lastUpdatedDate', or 'submittedDate'
            sort_order: 'ascending' or 'descending'
            categories: List of arXiv categories to filter by
            authors: List of author names to search for
            date_range: Dict with 'from' and 'to' dates (YYYY-MM-DD format)

        Returns:
            Dictionary with search results and metadata
        """
        try:
            await self._rate_limit()

            # Build search query
            search_query = self._build_search_query(
                query, categories, authors, date_range
            )

            # Build API parameters
            params = {
                "search_query": search_query,
                "start": start,
                "max_results": min(max_results, 2000),  # ArXiv API limit
                "sortBy": sort_by,
                "sortOrder": sort_order,
            }

            url = f"{self.BASE_URL}?{urlencode(params)}"
            self.logger.info(f"Searching ArXiv API: {url}")

            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    if response.status != 200:
                        raise ArxivError(f"ArXiv API request failed: {response.status}")

                    content = await response.text()
                    return self._parse_response(content)

        except Exception as e:
            self.logger.error(f"ArXiv API search failed: {str(e)}")
            raise ArxivError(f"Search failed: {str(e)}")

    def _build_search_query(
        self,
        query: str,
        categories: Optional[List[str]] = None,
        authors: Optional[List[str]] = None,
        date_range: Optional[Dict[str, str]] = None,
    ) -> str:
        """Build ArXiv API search query string."""
        query_parts = []

        # Main query
        if query.strip():
            # Search in title, abstract, and keywords
            escaped_query = quote(query)
            query_parts.append(f'(ti:"{escaped_query}" OR abs:"{escaped_query}")')

        # Category filters
        if categories:
            cat_query = " OR ".join([f"cat:{cat}" for cat in categories])
            query_parts.append(f"({cat_query})")

        # Author filters
        if authors:
            auth_query = " OR ".join([f'au:"{author}"' for author in authors])
            query_parts.append(f"({auth_query})")

        # Date range filters
        if date_range:
            if "from" in date_range:
                query_parts.append(f"submittedDate:[{date_range['from']}* TO *]")
            if "to" in date_range:
                query_parts.append(f"submittedDate:[* TO {date_range['to']}*]")

        # Combine with AND
        final_query = " AND ".join(query_parts) if query_parts else "all"

        self.logger.info(f"Built search query: {final_query}")
        return final_query

    def _parse_response(self, xml_content: str) -> Dict[str, Any]:
        """Parse ArXiv API XML response."""
        try:
            root = ET.fromstring(xml_content)

            # Extract metadata using proper namespaces
            total_results_elem = root.find(".//opensearch:totalResults", self.NAMESPACE)
            start_index_elem = root.find(".//opensearch:startIndex", self.NAMESPACE)
            items_per_page_elem = root.find(
                ".//opensearch:itemsPerPage", self.NAMESPACE
            )

            total_results = (
                int(total_results_elem.text) if total_results_elem is not None else 0
            )
            start_index = (
                int(start_index_elem.text) if start_index_elem is not None else 0
            )
            items_per_page = (
                int(items_per_page_elem.text) if items_per_page_elem is not None else 0
            )

            # Extract papers
            papers = []
            for entry in root.findall(".//atom:entry", self.NAMESPACE):
                paper = self._parse_paper_entry(entry)
                papers.append(paper)

            return {
                "total_results": total_results,
                "start_index": start_index,
                "items_per_page": items_per_page,
                "papers": papers,
                "query_time": datetime.now().isoformat(),
            }

        except ET.ParseError as e:
            self.logger.error(f"Failed to parse ArXiv API response: {str(e)}")
            raise ArxivError(f"Invalid XML response from ArXiv API: {str(e)}")

    def _parse_paper_entry(self, entry) -> Dict[str, Any]:
        """Parse individual paper entry from XML."""
        paper = {}

        # Basic metadata with safe extraction
        id_elem = entry.find(".//atom:id", self.NAMESPACE)
        paper["id"] = id_elem.text.split("/")[-1] if id_elem is not None else "unknown"

        title_elem = entry.find(".//atom:title", self.NAMESPACE)
        paper["title"] = (
            title_elem.text.strip() if title_elem is not None else "No title"
        )

        summary_elem = entry.find(".//atom:summary", self.NAMESPACE)
        paper["summary"] = (
            summary_elem.text.strip() if summary_elem is not None else "No summary"
        )

        # Dates
        published = entry.find(".//atom:published", self.NAMESPACE)
        if published is not None:
            paper["published"] = published.text

        updated = entry.find(".//atom:updated", self.NAMESPACE)
        if updated is not None:
            paper["updated"] = updated.text

        # Authors
        authors = []
        for author in entry.findall(".//atom:author", self.NAMESPACE):
            name_elem = author.find(".//atom:name", self.NAMESPACE)
            if name_elem is not None:
                authors.append(name_elem.text)
        paper["authors"] = authors

        # Categories
        categories = []
        for category in entry.findall(".//atom:category", self.NAMESPACE):
            term = category.get("term")
            if term:
                categories.append(term)
        paper["categories"] = categories

        # Links
        links = {}
        for link in entry.findall(".//atom:link", self.NAMESPACE):
            rel = link.get("rel")
            href = link.get("href")
            if rel and href:
                links[rel] = href
        paper["links"] = links

        # ArXiv specific fields
        arxiv_comment = entry.find(".//arxiv:comment", self.NAMESPACE)
        if arxiv_comment is not None:
            paper["comment"] = arxiv_comment.text

        arxiv_journal = entry.find(".//arxiv:journal_ref", self.NAMESPACE)
        if arxiv_journal is not None:
            paper["journal_ref"] = arxiv_journal.text

        arxiv_doi = entry.find(".//arxiv:doi", self.NAMESPACE)
        if arxiv_doi is not None:
            paper["doi"] = arxiv_doi.text

        return paper

    async def get_paper_metadata(self, arxiv_id: str) -> Dict[str, Any]:
        """Get metadata for a specific ArXiv paper."""
        result = await self.search(query="", max_results=1)
        # Build query for specific paper
        url = f"{self.BASE_URL}?id_list={arxiv_id}"

        await self._rate_limit()

        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status != 200:
                    raise ArxivError(
                        f"Failed to fetch paper {arxiv_id}: {response.status}"
                    )

                content = await response.text()
                result = self._parse_response(content)

                if not result["papers"]:
                    raise ArxivError(f"Paper {arxiv_id} not found")

                return result["papers"][0]


# Helper functions for common search patterns
async def search_by_title(title: str, max_results: int = 5) -> List[Dict[str, Any]]:
    """Search papers by title."""
    client = ArxivAPIClient()
    result = await client.search(query=title, max_results=max_results)
    return result["papers"]


async def search_by_author(author: str, max_results: int = 10) -> List[Dict[str, Any]]:
    """Search papers by author."""
    client = ArxivAPIClient()
    result = await client.search(query="", authors=[author], max_results=max_results)
    return result["papers"]


async def search_recent_papers(
    category: str, days: int = 7, max_results: int = 20
) -> List[Dict[str, Any]]:
    """Search recent papers in a category."""
    from datetime import datetime, timedelta

    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)

    client = ArxivAPIClient()
    result = await client.search(
        query="",
        categories=[category],
        date_range={
            "from": start_date.strftime("%Y-%m-%d"),
            "to": end_date.strftime("%Y-%m-%d"),
        },
        max_results=max_results,
        sort_by="submittedDate",
        sort_order="descending",
    )
    return result["papers"]
