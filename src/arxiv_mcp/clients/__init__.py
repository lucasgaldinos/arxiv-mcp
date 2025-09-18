"""
Clients module for external service interactions.
Extracted from the main __init__.py for better modularity.
"""

import asyncio
from io import BytesIO
from typing import Any

import aiohttp

from ..exceptions import ArxivMCPError
from ..utils.logging import structured_logger
from ..utils.metrics import MetricsCollector


class AsyncArxivDownloader:
    """Asynchronous ArXiv paper downloader with rate limiting and error handling."""

    def __init__(self, requests_per_second: float = 2.0, burst_size: int = 5):
        self.requests_per_second = requests_per_second
        self.burst_size = burst_size
        self.semaphore = asyncio.Semaphore(burst_size)
        self.last_request_times = []
        self.logger = structured_logger()
        self.metrics = MetricsCollector()

    async def _rate_limit(self):
        """Implement rate limiting based on requests per second."""
        current_time = asyncio.get_event_loop().time()

        # Remove old timestamps
        cutoff_time = current_time - 1.0
        self.last_request_times = [t for t in self.last_request_times if t > cutoff_time]

        # If we're at the limit, wait
        if len(self.last_request_times) >= self.requests_per_second:
            sleep_time = 1.0 - (current_time - self.last_request_times[0])
            if sleep_time > 0:
                await asyncio.sleep(sleep_time)

        self.last_request_times.append(current_time)

    async def download(self, arxiv_id: str, timeout: int = 60) -> BytesIO:
        """Download a paper from ArXiv with enhanced validation."""
        async with self.semaphore:
            await self._rate_limit()

            url = f"https://arxiv.org/e-print/{arxiv_id}"
            self.logger.info(f"Downloading ArXiv paper {arxiv_id} from {url}")

            try:
                async with (
                    aiohttp.ClientSession() as session,
                    session.get(url, timeout=aiohttp.ClientTimeout(total=timeout)) as response,
                ):
                    if response.status == 200:
                        # Validate Content-Type
                        content_type = response.headers.get('Content-Type', '').lower()
                        self.logger.debug(f"Response Content-Type: {content_type}")
                        
                        # Expected content types for ArXiv e-prints
                        valid_types = [
                            'application/gzip',
                            'application/x-gzip', 
                            'application/octet-stream',
                            'application/x-tar',
                            'text/plain',  # Sometimes single .tex files
                        ]
                        
                        # Check if content type is valid (allowing empty content-type for compatibility)
                        if content_type and not any(valid_type in content_type for valid_type in valid_types):
                            self.logger.warning(f"Unexpected Content-Type '{content_type}' for {arxiv_id}")
                            # Don't fail immediately - ArXiv sometimes returns incorrect headers
                        
                        content = await response.read()
                        
                        # Validate content is not empty
                        if not content:
                            raise ArxivMCPError(f"Empty response for {arxiv_id}")
                        
                        # Basic content validation - check if it looks like expected formats
                        if len(content) < 100:  # Suspiciously small
                            self.logger.warning(f"Suspiciously small content for {arxiv_id}: {len(content)} bytes")
                            # Try to decode as text to see if it's an error message
                            try:
                                text_content = content.decode('utf-8', errors='ignore')
                                if 'error' in text_content.lower() or 'not found' in text_content.lower():
                                    raise ArxivMCPError(f"ArXiv returned error for {arxiv_id}: {text_content[:200]}")
                            except:
                                pass
                        
                        self.metrics.increment_counter(
                            "downloads", {"arxiv_id": arxiv_id, "status": "success"}
                        )
                        self.logger.info(
                            f"Successfully downloaded paper {arxiv_id}, size: {len(content)} bytes, type: {content_type}"
                        )
                        return BytesIO(content)
                        
                    elif response.status == 404:
                        self.metrics.increment_counter(
                            "downloads", {"arxiv_id": arxiv_id, "status": "not_found"}
                        )
                        raise ArxivMCPError(f"Paper {arxiv_id} not found on ArXiv (HTTP 404)")
                    else:
                        self.metrics.increment_counter(
                            "downloads", {"arxiv_id": arxiv_id, "status": "error"}
                        )
                        raise ArxivMCPError(f"Failed to download {arxiv_id}: HTTP {response.status}")
                        
            except aiohttp.ClientTimeout:
                self.metrics.increment_counter(
                    "downloads", {"arxiv_id": arxiv_id, "status": "timeout"}
                )
                self.logger.error(f"Timeout downloading {arxiv_id} after {timeout}s")
                raise ArxivMCPError(f"Download timeout for {arxiv_id} after {timeout}s")
            except Exception as e:
                self.metrics.increment_counter(
                    "downloads", {"arxiv_id": arxiv_id, "status": "error"}
                )
                self.logger.exception(f"Error downloading {arxiv_id}: {str(e)}")
                raise ArxivMCPError(f"Download failed for {arxiv_id}: {str(e)}")

    async def get_metadata(self, arxiv_id: str) -> dict[str, Any]:
        """Get metadata for an ArXiv paper."""
        # Placeholder for metadata retrieval
        # In a real implementation, this would query the ArXiv API
        self.logger.info(f"Retrieving metadata for {arxiv_id}")
        return {
            "id": arxiv_id,
            "title": "Placeholder Title",
            "authors": ["Placeholder Author"],
            "abstract": "Placeholder abstract",
            "categories": ["cs.AI"],
        }
