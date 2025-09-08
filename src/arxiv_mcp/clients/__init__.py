"""
Clients module for external service interactions.
Extracted from the main __init__.py for better modularity.
"""
from typing import Dict, Any
import asyncio
import aiohttp
from io import BytesIO
from ..utils.logging import structured_logger
from ..utils.metrics import MetricsCollector
from ..exceptions import ArxivMCPError


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
        """Download a paper from ArXiv."""
        async with self.semaphore:
            await self._rate_limit()
            
            url = f"https://arxiv.org/e-print/{arxiv_id}"
            self.logger.info(f"Downloading ArXiv paper {arxiv_id} from {url}")
            
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(url, timeout=aiohttp.ClientTimeout(total=timeout)) as response:
                        if response.status == 200:
                            content = await response.read()
                            self.metrics.increment_counter("downloads", {"arxiv_id": arxiv_id, "status": "success"})
                            self.logger.info(f"Successfully downloaded paper {arxiv_id}, size: {len(content)} bytes")
                            return BytesIO(content)
                        else:
                            self.metrics.increment_counter("downloads", {"arxiv_id": arxiv_id, "status": "error"})
                            raise ArxivMCPError(f"Failed to download {arxiv_id}: HTTP {response.status}")
            except Exception as e:
                self.metrics.increment_counter("downloads", {"arxiv_id": arxiv_id, "status": "error"})
                self.logger.error(f"Error downloading {arxiv_id}: {str(e)}")
                raise ArxivMCPError(f"Download failed for {arxiv_id}: {str(e)}")

    async def get_metadata(self, arxiv_id: str) -> Dict[str, Any]:
        """Get metadata for an ArXiv paper."""
        # Placeholder for metadata retrieval
        # In a real implementation, this would query the ArXiv API
        self.logger.info(f"Retrieving metadata for {arxiv_id}")
        return {
            "id": arxiv_id,
            "title": "Placeholder Title",
            "authors": ["Placeholder Author"],
            "abstract": "Placeholder abstract",
            "categories": ["cs.AI"]
        }
