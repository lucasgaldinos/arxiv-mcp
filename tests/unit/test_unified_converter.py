"""Test suite for UnifiedDownloadConverter with integration approach for real coverage."""

import gzip
import io
from pathlib import Path
import shutil
import tarfile
import tempfile
from unittest.mock import AsyncMock, patch

import pytest

from arxiv_mcp.core.config import PipelineConfig
from arxiv_mcp.utils.unified_converter import UnifiedDownloadConverter


@pytest.fixture
def temp_dir():
    """Create temporary directory for testing."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def config(temp_dir):
    """Create test configuration with temporary directory."""
    return PipelineConfig.from_dict(
        {"output_directory": temp_dir, "download_timeout": 30, "max_files_per_archive": 100}
    )


@pytest.fixture
def converter(config):
    """Create UnifiedDownloadConverter instance."""
    return UnifiedDownloadConverter(config)


class TestUnifiedDownloadConverter:
    """Test UnifiedDownloadConverter with integration approach for real coverage measurement."""

    def test_constructor(self, config):
        """Test UnifiedDownloadConverter constructor (lines 20-30)."""
        converter = UnifiedDownloadConverter(config)

        assert converter.config == config
        assert converter.pipeline is not None
        assert converter.file_saver is not None
        assert converter.markdown_converter is not None

    @pytest.mark.asyncio
    async def test_download_and_convert_integration_real_coverage(self, converter):
        """Integration test targeting real coverage of lines 49-143 in unified_converter.py.

        This test only mocks the network download, allowing the entire unified_converter
        logic to execute and be tracked by coverage.
        """
        arxiv_id = "test.paper"

        # Create realistic LaTeX content
        latex_content = b"""\\documentclass{article}
\\title{Test Paper for Coverage}
\\author{Test Author}
\\begin{abstract}
This is a test abstract for measuring coverage.
\\end{abstract}
\\begin{document}
\\maketitle
\\section{Introduction}
This is the introduction section.
\\section{Methods}
This section describes the methods.
\\section{Results}
Here are the test results.
\\section{Conclusion}
This is the conclusion.
\\end{document}"""

        # Create a tar.gz-like structure that mimics arXiv format

        # Create a tar archive in memory
        tar_buffer = io.BytesIO()
        with tarfile.open(fileobj=tar_buffer, mode="w") as tar:
            # Add the main LaTeX file
            latex_info = tarfile.TarInfo(name="main.tex")
            latex_info.size = len(latex_content)
            tar.addfile(latex_info, io.BytesIO(latex_content))

            # Add a bibliography file
            bib_content = (
                b"@article{test2024, title={Test Reference}, author={Test Author}, year={2024}}"
            )
            bib_info = tarfile.TarInfo(name="references.bib")
            bib_info.size = len(bib_content)
            tar.addfile(bib_info, io.BytesIO(bib_content))

        # Compress with gzip (as arXiv does)
        tar_buffer.seek(0)
        gzip_buffer = io.BytesIO()
        with gzip.GzipFile(fileobj=gzip_buffer, mode="wb") as gz:
            gz.write(tar_buffer.getvalue())

        gzip_buffer.seek(0)
        mock_arxiv_response = gzip_buffer.getvalue()

        # Only mock the actual network download - everything else should be real
        with patch(
            "arxiv_mcp.clients.AsyncArxivDownloader.download", new_callable=AsyncMock
        ) as mock_download:
            mock_download.return_value = io.BytesIO(mock_arxiv_response)

            # Test LaTeX-only path (should exercise lines 83-89)
            result = await converter.download_and_convert(
                arxiv_id=arxiv_id,
                save_latex=True,
                save_markdown=False,
                include_pdf=False,  # Skip PDF to avoid compilation issues
            )

            # Verify real execution occurred
            assert result["success"] is True
            assert result["arxiv_id"] == arxiv_id
            assert "latex" in result["formats"]
            assert "markdown" not in result["formats"]
            assert result["summary"]["main_tex_file"] == "main.tex"
            assert result["summary"]["total_files"] == 2  # main.tex + references.bib
            assert result["summary"]["extracted_text_length"] > 0

            # Verify files were actually created (real file operations)
            latex_dir = Path(converter.config.output_directory) / "latex" / arxiv_id
            assert latex_dir.exists()
            assert (latex_dir / "main.tex").exists()
            assert (latex_dir / "manifest.json").exists()

    @pytest.mark.asyncio
    async def test_download_and_convert_markdown_integration_real_coverage(self, converter):
        """Integration test for markdown conversion targeting lines 89-143."""
        arxiv_id = "test.markdown"

        # Create LaTeX content optimized for markdown conversion
        latex_content = b"""\\documentclass{article}
\\title{Markdown Test Paper}
\\author{Markdown Test Author}
\\begin{abstract}
This tests the markdown conversion path.
\\end{abstract}
\\begin{document}
\\maketitle
\\section{Introduction}
This section will be converted to markdown.
\\textbf{Bold text} and \\emph{italic text} for testing.
\\subsection{Subsection}
Testing subsection conversion.
\\end{document}"""

        # Create tar.gz structure
        import gzip
        import tarfile

        tar_buffer = io.BytesIO()
        with tarfile.open(fileobj=tar_buffer, mode="w") as tar:
            latex_info = tarfile.TarInfo(name="paper.tex")
            latex_info.size = len(latex_content)
            tar.addfile(latex_info, io.BytesIO(latex_content))

        tar_buffer.seek(0)
        gzip_buffer = io.BytesIO()
        with gzip.GzipFile(fileobj=gzip_buffer, mode="wb") as gz:
            gz.write(tar_buffer.getvalue())

        gzip_buffer.seek(0)
        mock_arxiv_response = gzip_buffer.getvalue()

        # Only mock network download
        with patch(
            "arxiv_mcp.clients.AsyncArxivDownloader.download", new_callable=AsyncMock
        ) as mock_download:
            mock_download.return_value = io.BytesIO(mock_arxiv_response)

            # Test markdown-only path (should exercise lines 89-123)
            result = await converter.download_and_convert(
                arxiv_id=arxiv_id, save_latex=False, save_markdown=True, include_pdf=False
            )

            # Verify real execution
            assert result["success"] is True
            assert result["arxiv_id"] == arxiv_id
            assert "markdown" in result["formats"]
            assert "latex" not in result["formats"]
            assert "metadata" in result
            assert result["files"]["markdown"]["file"] is not None

            # Verify actual file creation
            markdown_dir = Path(converter.config.output_directory) / "markdown" / arxiv_id
            assert markdown_dir.exists()
            markdown_file = markdown_dir / f"{arxiv_id}.md"
            assert markdown_file.exists()

            # Check that the content was actually converted
            content = markdown_file.read_text()
            assert "title: Markdown Test Paper" in content
            assert "# Introduction" in content or "## Introduction" in content

    @pytest.mark.asyncio
    async def test_download_and_convert_both_formats_integration_real_coverage(self, converter):
        """Integration test for both formats targeting full coverage of lines 83-143."""
        arxiv_id = "test.both"

        # Create comprehensive LaTeX content
        latex_content = b"""\\documentclass{article}
\\title{Complete Test Paper}
\\author{Complete Test Author}
\\date{\\today}
\\begin{abstract}
This comprehensive test covers both LaTeX and markdown paths.
\\end{abstract}
\\begin{document}
\\maketitle
\\tableofcontents
\\section{Introduction}
This is a comprehensive test of the unified converter.
\\section{Literature Review}
Testing multiple sections for coverage.
\\section{Methodology}
More content for thorough testing.
\\section{Results and Discussion}
Results section with detailed content.
\\section{Conclusion}
Final section for complete testing.
\\bibliography{references}
\\end{document}"""

        # Create tar.gz with multiple files
        import gzip
        import tarfile

        tar_buffer = io.BytesIO()
        with tarfile.open(fileobj=tar_buffer, mode="w") as tar:
            # Main LaTeX file
            latex_info = tarfile.TarInfo(name="manuscript.tex")
            latex_info.size = len(latex_content)
            tar.addfile(latex_info, io.BytesIO(latex_content))

            # Bibliography
            bib_content = b"""@article{test2024,
    title={Test Reference Paper},
    author={Reference Author},
    journal={Test Journal},
    year={2024}
}"""
            bib_info = tarfile.TarInfo(name="references.bib")
            bib_info.size = len(bib_content)
            tar.addfile(bib_info, io.BytesIO(bib_content))

            # Additional file
            readme_content = b"This is a test README file."
            readme_info = tarfile.TarInfo(name="README.txt")
            readme_info.size = len(readme_content)
            tar.addfile(readme_info, io.BytesIO(readme_content))

        tar_buffer.seek(0)
        gzip_buffer = io.BytesIO()
        with gzip.GzipFile(fileobj=gzip_buffer, mode="wb") as gz:
            gz.write(tar_buffer.getvalue())

        gzip_buffer.seek(0)
        mock_arxiv_response = gzip_buffer.getvalue()

        # Only mock network download
        with patch(
            "arxiv_mcp.clients.AsyncArxivDownloader.download", new_callable=AsyncMock
        ) as mock_download:
            mock_download.return_value = io.BytesIO(mock_arxiv_response)

            # Test both formats (should exercise lines 83-143 comprehensively)
            result = await converter.download_and_convert(
                arxiv_id=arxiv_id, save_latex=True, save_markdown=True, include_pdf=False
            )

            # Verify comprehensive execution
            assert result["success"] is True
            assert result["arxiv_id"] == arxiv_id
            assert "latex" in result["formats"]
            assert "markdown" in result["formats"]
            assert result["summary"]["main_tex_file"] == "manuscript.tex"
            assert result["summary"]["total_files"] == 3

            # Verify both output directories exist
            base_dir = Path(converter.config.output_directory)
            latex_dir = base_dir / "latex" / arxiv_id
            markdown_dir = base_dir / "markdown" / arxiv_id

            assert latex_dir.exists()
            assert markdown_dir.exists()
            assert (latex_dir / "manuscript.tex").exists()
            assert (markdown_dir / f"{arxiv_id}.md").exists()

    @pytest.mark.asyncio
    async def test_download_and_convert_error_handling_real_coverage(self, converter):
        """Test error handling paths for real coverage (lines 51-58, 135-143)."""
        arxiv_id = "test.error"

        # Test network error (should hit exception handling lines 135-143)
        with patch(
            "arxiv_mcp.clients.AsyncArxivDownloader.download", new_callable=AsyncMock
        ) as mock_download:
            mock_download.side_effect = Exception("Simulated network error")

            result = await converter.download_and_convert(
                arxiv_id=arxiv_id, save_latex=True, save_markdown=True
            )

            assert result["success"] is False
            assert result["arxiv_id"] == arxiv_id
            assert "Simulated network error" in result["error"]


@pytest.fixture
def temp_dir():
    """Create temporary directory for testing."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def config(temp_dir):
    """Create test configuration with temporary directory."""
    return PipelineConfig.from_dict(
        {"output_directory": temp_dir, "download_timeout": 30, "max_files_per_archive": 100}
    )


@pytest.fixture
def converter(config):
    """Create UnifiedDownloadConverter instance."""
    return UnifiedDownloadConverter(config)


class TestUnifiedDownloadConverter:
    """Test UnifiedDownloadConverter with real code execution (minimal external mocking)."""

    def test_constructor(self, config):
        """Test UnifiedDownloadConverter constructor (lines 20-30)."""
        converter = UnifiedDownloadConverter(config)

        assert converter.config == config
        assert converter.pipeline is not None
        assert converter.file_saver is not None
        assert converter.markdown_converter is not None

    @pytest.mark.asyncio
    async def test_download_and_convert_minimal_mock_real_execution(self, converter):
        """Test download_and_convert with minimal mocking for real code coverage (lines 49-143)."""
        arxiv_id = "1234.5678"

        # Create realistic mock data that mimics what the real arXiv would return
        mock_source_bytes = b"mock tar.gz content"

        # Mock file content that looks like a real arXiv paper structure
        mock_extracted_files = {
            "main.tex": b"""\\documentclass{article}
\\title{Test Paper Title}
\\author{Test Author}
\\begin{abstract}
This is a test abstract for coverage testing.
\\end{abstract}
\\begin{document}
\\maketitle
\\section{Introduction}
This is the introduction section.
\\section{Methods}
This describes the methods used.
\\section{Results}
These are the results obtained.
\\section{Conclusion}
This is the conclusion.
\\end{document}""",
            "references.bib": b"@article{test2024, title={Test Reference}, author={Test Author}, year={2024}}",
            "figure1.pdf": b"mock PDF content",
        }

        # Only mock external network calls and file I/O - let everything else execute real code
        with (
            patch(
                "arxiv_mcp.clients.AsyncArxivDownloader.download", new_callable=AsyncMock
            ) as mock_download,
            patch(
                "arxiv_mcp.processors.LaTeXProcessor.extract_archive",
                return_value=mock_extracted_files,
            ),
            patch(
                "arxiv_mcp.processors.LaTeXProcessor.compile_latex",
                side_effect=Exception("PDF compilation disabled for test"),
            ),
            patch(
                "arxiv_mcp.utils.file_saver.FileSaver.save_latex_files",
                return_value={"path": f"/test/latex/{arxiv_id}", "saved": True},
            ),
            patch(
                "arxiv_mcp.utils.file_saver.FileSaver.save_markdown_file",
                return_value=f"/test/markdown/{arxiv_id}.md",
            ),
            patch(
                "arxiv_mcp.utils.file_saver.FileSaver.save_metadata",
                return_value=f"/test/metadata/{arxiv_id}.json",
            ),
        ):
            # Configure the download mock to return our test data
            mock_download.return_value = io.BytesIO(mock_source_bytes)

            # Test LaTeX only conversion (should hit lines 83-87)
            result = await converter.download_and_convert(
                arxiv_id=arxiv_id, save_latex=True, save_markdown=False, include_pdf=False
            )

            # Verify the result structure and that real code paths were executed
            assert result["success"] is True
            assert result["arxiv_id"] == arxiv_id
            assert "latex" in result["formats"]
            assert "markdown" not in result["formats"]
            assert result["summary"]["main_tex_file"] == "main.tex"
            assert result["summary"]["total_files"] == 3
            assert (
                result["summary"]["extracted_text_length"] > 0
            )  # Just check it's a positive number

    @pytest.mark.asyncio
    async def test_download_and_convert_markdown_real_execution(self, converter):
        """Test download_and_convert with markdown conversion for real code coverage (lines 89-123)."""
        arxiv_id = "1234.5678"

        # Create realistic mock data
        mock_source_bytes = b"mock tar.gz content"
        mock_extracted_files = {
            "main.tex": b"""\\documentclass{article}
\\title{Test Markdown Paper}
\\author{Test Author for Markdown}
\\begin{abstract}
This tests markdown conversion paths.
\\end{abstract}
\\begin{document}
\\maketitle
\\section{Introduction}
Content for markdown testing.
\\end{document}"""
        }

        # Mock external dependencies but let the core logic execute
        with (
            patch(
                "arxiv_mcp.clients.AsyncArxivDownloader.download", new_callable=AsyncMock
            ) as mock_download,
            patch(
                "arxiv_mcp.processors.LaTeXProcessor.extract_archive",
                return_value=mock_extracted_files,
            ),
            patch(
                "arxiv_mcp.processors.LaTeXProcessor.compile_latex",
                side_effect=Exception("PDF compilation disabled for test"),
            ),
            patch(
                "arxiv_mcp.utils.file_saver.FileSaver.save_markdown_file",
                return_value=f"/test/markdown/{arxiv_id}.md",
            ),
            patch(
                "arxiv_mcp.utils.file_saver.FileSaver.save_metadata",
                return_value=f"/test/metadata/{arxiv_id}.json",
            ),
        ):
            mock_download.return_value = io.BytesIO(mock_source_bytes)

            # Test markdown only conversion (should hit lines 89-123)
            result = await converter.download_and_convert(
                arxiv_id=arxiv_id, save_latex=False, save_markdown=True, include_pdf=False
            )

            # Verify the result and that real code paths were executed
            assert result["success"] is True
            assert result["arxiv_id"] == arxiv_id
            assert "markdown" in result["formats"]
            assert "latex" not in result["formats"]
            assert "metadata" in result
            assert result["files"]["markdown"]["file"] == f"/test/markdown/{arxiv_id}.md"

    @pytest.mark.asyncio
    async def test_download_and_convert_both_formats_real_execution(self, converter):
        """Test download_and_convert with both formats for real code coverage (lines 83-143)."""
        arxiv_id = "1234.5678"

        # Create realistic mock data
        mock_source_bytes = b"mock tar.gz content"
        mock_extracted_files = {
            "main.tex": b"""\\documentclass{article}
\\title{Both Formats Test Paper}
\\author{Test Author Both}
\\begin{abstract}
This tests both LaTeX and markdown paths.
\\end{abstract}
\\begin{document}
\\maketitle
\\section{Introduction}
Content for both format testing.
\\end{document}"""
        }

        # Mock external dependencies but let the core logic execute
        with (
            patch(
                "arxiv_mcp.clients.AsyncArxivDownloader.download", new_callable=AsyncMock
            ) as mock_download,
            patch(
                "arxiv_mcp.processors.LaTeXProcessor.extract_archive",
                return_value=mock_extracted_files,
            ),
            patch(
                "arxiv_mcp.processors.LaTeXProcessor.compile_latex",
                side_effect=Exception("PDF compilation disabled for test"),
            ),
            patch(
                "arxiv_mcp.utils.file_saver.FileSaver.save_latex_files",
                return_value={"path": f"/test/latex/{arxiv_id}", "saved": True},
            ),
            patch(
                "arxiv_mcp.utils.file_saver.FileSaver.save_markdown_file",
                return_value=f"/test/markdown/{arxiv_id}.md",
            ),
            patch(
                "arxiv_mcp.utils.file_saver.FileSaver.save_metadata",
                return_value=f"/test/metadata/{arxiv_id}.json",
            ),
        ):
            mock_download.return_value = io.BytesIO(mock_source_bytes)

            # Test both formats (should hit lines 83-143)
            result = await converter.download_and_convert(
                arxiv_id=arxiv_id, save_latex=True, save_markdown=True, include_pdf=False
            )

            # Verify the result and that real code paths were executed
            assert result["success"] is True
            assert result["arxiv_id"] == arxiv_id
            assert "latex" in result["formats"]
            assert "markdown" in result["formats"]
            assert result["files"]["latex"]["saved"] is True
            assert result["files"]["markdown"]["file"] == f"/test/markdown/{arxiv_id}.md"

    @pytest.mark.asyncio
    async def test_download_and_convert_error_paths_real_execution(self, converter):
        """Test download_and_convert error handling for real code coverage (lines 51-58, 135-143)."""
        arxiv_id = "1234.5678"

        # Test case 1: Network download failure (should hit exception handling lines 135-143)
        with patch(
            "arxiv_mcp.clients.AsyncArxivDownloader.download", new_callable=AsyncMock
        ) as mock_download:
            mock_download.side_effect = Exception("Network error for testing")

            result = await converter.download_and_convert(
                arxiv_id=arxiv_id, save_latex=True, save_markdown=True
            )

            assert result["success"] is False
            assert result["arxiv_id"] == arxiv_id
            assert "Network error for testing" in result["error"]
