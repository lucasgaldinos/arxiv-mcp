"""Integration tests for UnifiedDownloadConverter with REAL coverage measurement.

This test suite only mocks the actual network download from arXiv while letting
all other code paths execute normally to achieve real coverage measurement.
"""
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
    return PipelineConfig.from_dict({
        "output_directory": temp_dir,
        "download_timeout": 30,
        "max_files_per_archive": 100,
        "compilation_timeout": 30,  # Use the correct field name
        "preserve_intermediates": True  # Keep files for testing
    })


@pytest.fixture
def converter(config):
    """Create UnifiedDownloadConverter instance."""
    return UnifiedDownloadConverter(config)


def create_realistic_arxiv_content(title="Test Paper", main_file="main.tex"):
    """Create realistic arXiv tar.gz content for testing."""
    latex_content = f"""\\documentclass{{article}}
\\usepackage{{amsmath}}
\\usepackage{{amsfonts}}
\\usepackage{{amssymb}}
\\title{{{title}}}
\\author{{Test Author}}
\\date{{\\today}}

\\begin{{abstract}}
This is a comprehensive test abstract that should provide sufficient content
for the unified converter to process through all its code paths. It includes
mathematical content $E = mc^2$ and references to sections.
\\end{{abstract}}

\\begin{{document}}
\\maketitle

\\section{{Introduction}}
This is the introduction section with some \\textbf{{bold}} and \\emph{{italic}} text.
We reference equation \\ref{{eq:test}} below.

\\section{{Methods}}
Here we describe the methodology with mathematical notation:
\\begin{{equation}}
\\label{{eq:test}}
f(x) = \\sum_{{i=1}}^{{n}} x_i^2
\\end{{equation}}

\\subsection{{Subsection Example}}
This is a subsection to test hierarchical structure.

\\section{{Results}}
The results show that the algorithm performs well.

\\section{{Discussion}}
This section discusses the implications of the results.

\\section{{Conclusion}}
In conclusion, this test demonstrates the unified converter functionality.

\\bibliographystyle{{plain}}
\\bibliography{{references}}

\\end{{document}}"""

    bib_content = """@article{testpaper2024,
    title={A Test Reference Paper for Coverage Testing},
    author={Test Author and Another Author},
    journal={Journal of Test Coverage},
    volume={42},
    number={1},
    pages={1--10},
    year={2024},
    publisher={Test Publisher}
}

@book{testbook2023,
    title={Test Book for Bibliography},
    author={Book Author},
    publisher={Test Press},
    year={2023}
}"""

    # Create tar.gz structure like arXiv provides
    tar_buffer = io.BytesIO()
    with tarfile.open(fileobj=tar_buffer, mode='w') as tar:
        # Main LaTeX file
        latex_info = tarfile.TarInfo(name=main_file)
        latex_bytes = latex_content.encode('utf-8')
        latex_info.size = len(latex_bytes)
        tar.addfile(latex_info, io.BytesIO(latex_bytes))

        # Bibliography file
        bib_info = tarfile.TarInfo(name='references.bib')
        bib_bytes = bib_content.encode('utf-8')
        bib_info.size = len(bib_bytes)
        tar.addfile(bib_info, io.BytesIO(bib_bytes))

        # Additional file to test multi-file handling
        readme_content = "This is the README file for the test paper."
        readme_info = tarfile.TarInfo(name='README.txt')
        readme_bytes = readme_content.encode('utf-8')
        readme_info.size = len(readme_bytes)
        tar.addfile(readme_info, io.BytesIO(readme_bytes))

    # Compress with gzip (as arXiv does)
    tar_buffer.seek(0)
    gzip_buffer = io.BytesIO()
    with gzip.GzipFile(fileobj=gzip_buffer, mode='wb') as gz:
        gz.write(tar_buffer.getvalue())

    gzip_buffer.seek(0)
    return gzip_buffer.getvalue()


class TestUnifiedDownloadConverterRealCoverage:
    """Integration tests targeting REAL coverage measurement for unified_converter.py."""

    def test_constructor_real_coverage(self, config):
        """Test constructor with real instantiation (lines 20-30)."""
        converter = UnifiedDownloadConverter(config)

        # Verify real object creation
        assert converter.config == config
        assert converter.pipeline is not None
        assert converter.file_saver is not None
        assert converter.markdown_converter is not None

    @pytest.mark.asyncio
    async def test_latex_only_conversion_real_coverage(self, converter):
        """Test LaTeX-only conversion path with real execution (lines 49-89)."""
        arxiv_id = "2401.12345"  # Valid arXiv ID format
        mock_arxiv_data = create_realistic_arxiv_content("LaTeX Only Test")

        # Only mock the network download - everything else is real
        with patch('arxiv_mcp.clients.AsyncArxivDownloader.download', new_callable=AsyncMock) as mock_download:
            mock_download.return_value = io.BytesIO(mock_arxiv_data)

            # Execute real conversion with LaTeX only
            result = await converter.download_and_convert(
                arxiv_id=arxiv_id,
                save_latex=True,
                save_markdown=False,
                include_pdf=False  # Skip PDF to avoid compilation complexity
            )

            # Verify real execution results
            assert result["success"] is True
            assert result["arxiv_id"] == arxiv_id
            assert "latex" in result["formats"]
            assert "markdown" not in result["formats"]

            # Check that real files were created
            latex_dir = Path(converter.config.output_directory) / "latex" / arxiv_id
            assert latex_dir.exists()
            assert (latex_dir / "main.tex").exists()
            assert (latex_dir / "references.bib").exists()
            assert (latex_dir / "manifest.json").exists()

            # Verify summary data from real processing
            assert result["summary"]["main_tex_file"] == "main.tex"
            assert result["summary"]["total_files"] == 3
            assert result["summary"]["extracted_text_length"] > 100

    @pytest.mark.asyncio
    async def test_markdown_only_conversion_real_coverage(self, converter):
        """Test markdown-only conversion path with real execution (lines 89-123)."""
        arxiv_id = "2401.67890"  # Valid arXiv ID format
        mock_arxiv_data = create_realistic_arxiv_content("Markdown Only Test")

        # Only mock the network download
        with patch('arxiv_mcp.clients.AsyncArxivDownloader.download', new_callable=AsyncMock) as mock_download:
            mock_download.return_value = io.BytesIO(mock_arxiv_data)

            # Execute real conversion with markdown only
            result = await converter.download_and_convert(
                arxiv_id=arxiv_id,
                save_latex=False,
                save_markdown=True,
                include_pdf=False
            )

            # Verify real execution results
            assert result["success"] is True
            assert result["arxiv_id"] == arxiv_id
            assert "markdown" in result["formats"]
            assert "latex" not in result["formats"]

            # Check that real markdown file was created
            markdown_dir = Path(converter.config.output_directory) / "markdown" / arxiv_id
            assert markdown_dir.exists()
            markdown_file = markdown_dir / f"{arxiv_id}.md"
            assert markdown_file.exists()

            # Verify the markdown content was actually processed
            content = markdown_file.read_text()
            assert "title: Markdown Only Test" in content
            assert "Introduction" in content
            assert "Methods" in content

    @pytest.mark.asyncio
    async def test_both_formats_conversion_real_coverage(self, converter):
        """Test both formats conversion with real execution (lines 83-143)."""
        arxiv_id = "2401.11111"  # Valid arXiv ID format
        mock_arxiv_data = create_realistic_arxiv_content("Both Formats Test")

        # Only mock the network download
        with patch('arxiv_mcp.clients.AsyncArxivDownloader.download', new_callable=AsyncMock) as mock_download:
            mock_download.return_value = io.BytesIO(mock_arxiv_data)

            # Execute real conversion with both formats
            result = await converter.download_and_convert(
                arxiv_id=arxiv_id,
                save_latex=True,
                save_markdown=True,
                include_pdf=False
            )

            # Verify real execution results
            assert result["success"] is True
            assert result["arxiv_id"] == arxiv_id
            assert "latex" in result["formats"]
            assert "markdown" in result["formats"]

            # Check that both real output directories exist
            base_dir = Path(converter.config.output_directory)
            latex_dir = base_dir / "latex" / arxiv_id
            markdown_dir = base_dir / "markdown" / arxiv_id

            assert latex_dir.exists()
            assert markdown_dir.exists()

            # Verify key files exist
            assert (latex_dir / "main.tex").exists()
            assert (latex_dir / "references.bib").exists()
            assert (markdown_dir / f"{arxiv_id}.md").exists()

            # Verify the conversion actually happened
            markdown_content = (markdown_dir / f"{arxiv_id}.md").read_text()
            assert "Both Formats Test" in markdown_content
            assert "Introduction" in markdown_content

    @pytest.mark.asyncio
    async def test_error_handling_real_coverage(self, converter):
        """Test error handling paths with real execution (lines 135-143)."""
        arxiv_id = "2401.22222"  # Valid arXiv ID format

        # Test network error scenario
        with patch('arxiv_mcp.clients.AsyncArxivDownloader.download', new_callable=AsyncMock) as mock_download:
            mock_download.side_effect = Exception("Network timeout for testing")

            result = await converter.download_and_convert(
                arxiv_id=arxiv_id,
                save_latex=True,
                save_markdown=True
            )

            # Verify error handling was executed
            assert result["success"] is False
            assert result["arxiv_id"] == arxiv_id
            assert "Network timeout for testing" in result["error"]

    @pytest.mark.asyncio
    async def test_different_main_file_real_coverage(self, converter):
        """Test handling different main file names (lines 49-143)."""
        arxiv_id = "2401.33333"  # Valid arXiv ID format
        mock_arxiv_data = create_realistic_arxiv_content("Different Main File", main_file="paper.tex")

        # Only mock the network download
        with patch('arxiv_mcp.clients.AsyncArxivDownloader.download', new_callable=AsyncMock) as mock_download:
            mock_download.return_value = io.BytesIO(mock_arxiv_data)

            # Execute real conversion
            result = await converter.download_and_convert(
                arxiv_id=arxiv_id,
                save_latex=True,
                save_markdown=True,
                include_pdf=False
            )

            # Verify real execution with different main file
            assert result["success"] is True
            assert result["summary"]["main_tex_file"] == "paper.tex"

            # Check that files were created with correct names
            latex_dir = Path(converter.config.output_directory) / "latex" / arxiv_id
            assert (latex_dir / "paper.tex").exists()
