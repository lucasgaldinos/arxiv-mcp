"""
Enhanced ArXiv LaTeX content fetcher.
Provides the fetch_arxiv_paper_content functionality that downloads and extracts LaTeX source files.
"""

import asyncio
import aiohttp
import tarfile
import gzip
import io
from typing import Dict, List, Any, Optional
from pathlib import Path

from ..utils.logging import structured_logger
from ..utils.validation import ArxivValidator
from ..exceptions import ArxivError, DownloadError


class ArxivLatexFetcher:
    """Enhanced ArXiv LaTeX content fetcher with robust file handling."""

    def __init__(self):
        self.logger = structured_logger()
        self.validator = ArxivValidator()

    async def fetch_arxiv_paper_content(
        self, arxiv_id: str, save_to_disk: bool = True, output_dir: str = "./arxiv_papers"
    ) -> Dict[str, Any]:
        """
        Fetch and extract LaTeX source files from ArXiv.

        Args:
            arxiv_id: ArXiv paper ID (e.g., "2404.04895v2", "1001.4197")
            save_to_disk: Whether to save files to disk
            output_dir: Directory to save files to

        Returns:
            Dict containing:
            - arxiv_id: The paper ID
            - success: Whether the operation succeeded
            - files: Dict of filename -> content for all extracted files
            - main_tex_file: Name of the main .tex file
            - latex_content: Content of main .tex file
            - total_files: Number of files extracted
            - file_list: List of all filenames
            - saved_to: Directory path if saved to disk
            - error: Error message if failed
        """
        self.logger.info(f"Fetching LaTeX content for ArXiv paper {arxiv_id}")

        try:
            # Validate ArXiv ID
            if not self.validator.validate_arxiv_id(arxiv_id):
                raise ArxivError(f"Invalid ArXiv ID format: {arxiv_id}")

            # Clean up arxiv_id (remove version if present for URL)
            clean_id = arxiv_id.split("v")[0] if "v" in arxiv_id else arxiv_id

            # Download source archive
            source_url = f"https://arxiv.org/e-print/{clean_id}"
            self.logger.info(f"Downloading from {source_url}")

            async with aiohttp.ClientSession() as session:
                async with session.get(source_url) as response:
                    if response.status != 200:
                        raise DownloadError(
                            f"Failed to download {arxiv_id}: HTTP {response.status}"
                        )

                    source_content = await response.read()
                    self.logger.info(f"Downloaded {len(source_content)} bytes")

            # Extract files from archive
            files = await self._extract_archive(source_content, arxiv_id)

            # Find main .tex file
            main_tex_file = self._find_main_tex_file(files)

            # Get LaTeX content
            latex_content = ""
            if main_tex_file and main_tex_file in files:
                latex_content = files[main_tex_file].decode("utf-8", errors="ignore")

            # Save to disk if requested
            saved_to = None
            if save_to_disk:
                saved_to = await self._save_files_to_disk(files, arxiv_id, output_dir)

            result = {
                "arxiv_id": arxiv_id,
                "success": True,
                "files": {
                    name: content.decode("utf-8", errors="ignore")
                    for name, content in files.items()
                },
                "main_tex_file": main_tex_file,
                "latex_content": latex_content,
                "total_files": len(files),
                "file_list": list(files.keys()),
                "saved_to": saved_to,
            }

            self.logger.info(f"Successfully fetched {len(files)} files for {arxiv_id}")
            return result

        except Exception as e:
            self.logger.error(f"Failed to fetch LaTeX content for {arxiv_id}: {str(e)}")
            return {
                "arxiv_id": arxiv_id,
                "success": False,
                "error": str(e),
                "files": {},
                "main_tex_file": None,
                "latex_content": "",
                "total_files": 0,
                "file_list": [],
                "saved_to": None,
            }

    async def batch_fetch_papers(
        self, arxiv_ids: List[str], save_to_disk: bool = True, output_dir: str = "./arxiv_papers"
    ) -> List[Dict[str, Any]]:
        """
        Fetch multiple papers concurrently.

        Args:
            arxiv_ids: List of ArXiv paper IDs
            save_to_disk: Whether to save files to disk
            output_dir: Directory to save files to

        Returns:
            List of results from fetch_arxiv_paper_content
        """
        self.logger.info(f"Starting batch fetch for {len(arxiv_ids)} papers")

        tasks = [
            self.fetch_arxiv_paper_content(arxiv_id, save_to_disk, output_dir)
            for arxiv_id in arxiv_ids
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Process results and handle exceptions
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                processed_results.append(
                    {
                        "arxiv_id": arxiv_ids[i],
                        "success": False,
                        "error": str(result),
                        "files": {},
                        "main_tex_file": None,
                        "latex_content": "",
                        "total_files": 0,
                        "file_list": [],
                        "saved_to": None,
                    }
                )
            else:
                processed_results.append(result)

        self.logger.info(f"Batch fetch completed for {len(arxiv_ids)} papers")
        return processed_results

    async def _extract_archive(self, content: bytes, arxiv_id: str) -> Dict[str, bytes]:
        """Extract files from various archive formats."""
        files = {}

        try:
            # Try gzip first (most common)
            try:
                with gzip.GzipFile(fileobj=io.BytesIO(content)) as gz_file:
                    decompressed = gz_file.read()
                    # Check if it's a tar file
                    with tarfile.open(fileobj=io.BytesIO(decompressed), mode="r") as tar:
                        files = self._extract_tar_files(tar)
                        if files:
                            return files
            except Exception:
                pass

            # Try tar directly
            try:
                with tarfile.open(fileobj=io.BytesIO(content), mode="r") as tar:
                    files = self._extract_tar_files(tar)
                    if files:
                        return files
            except Exception:
                pass

            # Try as single .tex file
            try:
                # Check if content looks like LaTeX
                text_content = content.decode("utf-8", errors="ignore")
                if "\\documentclass" in text_content or "\\begin{document}" in text_content:
                    files[f"{arxiv_id}.tex"] = content
                    return files
            except Exception:
                pass

            # If nothing works, save as raw file for investigation
            files[f"{arxiv_id}.raw"] = content
            return files

        except Exception as e:
            self.logger.error(f"Archive extraction failed for {arxiv_id}: {str(e)}")
            raise DownloadError(f"Failed to extract archive for {arxiv_id}: {str(e)}")

    def _extract_tar_files(self, tar: tarfile.TarFile) -> Dict[str, bytes]:
        """Extract files from tar archive."""
        files = {}

        for member in tar.getmembers():
            if member.isfile():
                # Skip hidden files and unwanted files
                if member.name.startswith(".") or member.name.startswith("__"):
                    continue

                try:
                    file_obj = tar.extractfile(member)
                    if file_obj:
                        content = file_obj.read()
                        # Use just the filename, not the full path
                        filename = Path(member.name).name
                        files[filename] = content
                except Exception as e:
                    self.logger.warning(f"Failed to extract {member.name}: {str(e)}")
                    continue

        return files

    def _find_main_tex_file(self, files: Dict[str, bytes]) -> Optional[str]:
        """Find the main .tex file in the extracted files."""
        tex_files = [name for name in files.keys() if name.endswith(".tex")]

        if not tex_files:
            return None

        # Priority patterns for main file detection
        main_patterns = [
            r"^main\.tex$",
            r"^paper\.tex$",
            r"^manuscript\.tex$",
            r"^article\.tex$",
            r".*main.*\.tex$",
        ]

        import re

        # Check patterns in order of priority
        for pattern in main_patterns:
            for tex_file in tex_files:
                if re.match(pattern, tex_file, re.IGNORECASE):
                    return tex_file

        # If no pattern matches, return the first .tex file
        return tex_files[0]

    async def _save_files_to_disk(
        self, files: Dict[str, bytes], arxiv_id: str, output_dir: str
    ) -> str:
        """Save extracted files to disk."""
        paper_dir = Path(output_dir) / arxiv_id
        paper_dir.mkdir(parents=True, exist_ok=True)

        for filename, content in files.items():
            file_path = paper_dir / filename
            file_path.write_bytes(content)

        self.logger.info(f"Saved {len(files)} files to {paper_dir}")
        return str(paper_dir)
