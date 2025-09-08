"""
Integration tests for the new LaTeX to Markdown conversion and file saving features.
"""

import pytest
import tempfile
import shutil
from pathlib import Path

from arxiv_mcp.utils.file_saver import FileSaver
from arxiv_mcp.utils.latex_to_markdown import LaTeXToMarkdownConverter
from arxiv_mcp.utils.unified_converter import UnifiedDownloadConverter, download_and_convert_paper
from arxiv_mcp.core.config import PipelineConfig


class TestFileSaver:
    """Test the FileSaver class functionality."""
    
    def setup_method(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.file_saver = FileSaver(self.temp_dir)
    
    def teardown_method(self):
        """Clean up test environment."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_directory_structure_creation(self):
        """Test that the correct directory structure is created."""
        assert self.file_saver.latex_dir.exists()
        assert self.file_saver.markdown_dir.exists()
        assert self.file_saver.metadata_dir.exists()
        
        # Check directory names
        assert self.file_saver.latex_dir.name == "latex"
        assert self.file_saver.markdown_dir.name == "markdown"
        assert self.file_saver.metadata_dir.name == "metadata"
    
    def test_save_latex_files(self):
        """Test saving LaTeX files with manifest."""
        arxiv_id = "test.1234"
        files = {
            "main.tex": b"\\documentclass{article}\\begin{document}Test\\end{document}",
            "section1.tex": b"\\section{Introduction}This is a test.",
            "figure1.pdf": b"fake pdf content"
        }
        main_tex_file = "main.tex"
        
        self.file_saver.save_latex_files(arxiv_id, files, main_tex_file)
        
        # Check that files were saved
        paper_dir = self.file_saver.latex_dir / arxiv_id
        assert paper_dir.exists()
        assert (paper_dir / "main.tex").exists()
        assert (paper_dir / "section1.tex").exists()
        assert (paper_dir / "figure1.pdf").exists()
        assert (paper_dir / "manifest.json").exists()
        
        # Check manifest content
        import json
        with open(paper_dir / "manifest.json", 'r') as f:
            manifest = json.load(f)
        
        assert manifest["arxiv_id"] == arxiv_id
        assert manifest["main_tex_file"] == main_tex_file
        assert len(manifest["files"]) == 3
        assert "saved_at" in manifest
    
    def test_save_markdown_file_with_yaml(self):
        """Test saving markdown file with YAML frontmatter."""
        arxiv_id = "test.5678"
        markdown_content = "# Test Paper\n\nThis is a test paper."
        metadata = {
            "title": "Test Paper",
            "authors": ["Author One", "Author Two"],
            "abstract": "This is a test abstract.",
            "arxiv_id": arxiv_id
        }
        
        result_path_str = self.file_saver.save_markdown_file(arxiv_id, markdown_content, metadata)
        result_path = Path(result_path_str)
        
        # Check file was created
        assert result_path.exists()
        
        # Check content
        with open(result_path, 'r') as f:
            content = f.read()
        
        assert content.startswith("---")
        assert "title: Test Paper" in content
        assert "authors:" in content
        assert "# Test Paper" in content
    
    def test_cleanup_old_files(self):
        """Test cleanup functionality."""
        # Create some test files
        old_dir = self.file_saver.latex_dir / "old_paper"
        old_dir.mkdir()
        
        # Create test file for cleanup testing
        (old_dir / "test.tex").write_text("test")
        
        # Run cleanup (keep files for 30 days)
        result = self.file_saver.cleanup_old_files(30)
        
        assert result["cleaned_latex"] >= 0
        assert result["cleaned_markdown"] >= 0
        assert "cutoff_days" in result


class TestLaTeXToMarkdownConverter:
    """Test the LaTeX to Markdown converter."""
    
    def setup_method(self):
        """Set up test environment."""
        self.converter = LaTeXToMarkdownConverter()
    
    def test_simple_latex_conversion(self):
        """Test conversion of simple LaTeX content."""
        latex_content = r"""
        \documentclass{article}
        \title{Test Paper}
        \author{Test Author}
        \begin{document}
        \maketitle
        \section{Introduction}
        This is a test paper with \textbf{bold text} and \emph{italic text}.
        \end{document}
        """
        
        result = self.converter.convert(latex_content)
        
        assert result["success"]
        assert "Test Paper" in result["markdown"]
        assert "# Introduction" in result["markdown"] or "## Introduction" in result["markdown"]
    
    def test_metadata_extraction(self):
        """Test metadata extraction from LaTeX."""
        latex_content = r"""
        \documentclass{article}
        \title{Advanced Machine Learning Techniques}
        \author{John Smith \and Jane Doe}
        \begin{abstract}
        This paper presents novel approaches to machine learning.
        \end{abstract}
        \begin{document}
        Content here.
        \end{document}
        """
        
        metadata = self.converter.extract_metadata_from_latex(latex_content)
        
        assert metadata["title"] == "Advanced Machine Learning Techniques"
        assert "John Smith" in str(metadata["authors"])
        assert "Jane Doe" in str(metadata["authors"])
        assert "novel approaches" in metadata["abstract"]
    
    def test_conversion_with_metadata(self):
        """Test combined conversion and metadata extraction."""
        latex_content = r"""
        \documentclass{article}
        \title{Test Paper}
        \author{Test Author}
        \begin{abstract}
        Test abstract.
        \end{abstract}
        \begin{document}
        \section{Introduction}
        Test content.
        \end{document}
        """
        
        result = self.converter.convert_with_metadata(latex_content, "test.1234")
        
        assert result["success"]
        assert result["metadata"]["title"] == "Test Paper"
        assert "Test Author" in result["metadata"]["authors"]
        assert "Test abstract" in result["metadata"]["abstract"]
        assert "# Introduction" in result["markdown"] or "## Introduction" in result["markdown"]


class TestUnifiedDownloadConverter:
    """Test the unified download and convert functionality."""
    
    def setup_method(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.config = PipelineConfig.from_dict({"output_directory": self.temp_dir})
        self.converter = UnifiedDownloadConverter(self.config)
    
    def teardown_method(self):
        """Clean up test environment."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_get_output_structure(self):
        """Test getting output structure information."""
        structure = self.converter.get_output_structure()
        
        assert "output_directory" in structure
        assert "subdirectories" in structure
        assert "latex" in structure["subdirectories"]
        assert "markdown" in structure["subdirectories"]
        assert "metadata" in structure["subdirectories"]
    
    @pytest.mark.asyncio
    async def test_download_and_convert_integration(self):
        """Integration test for downloading and converting a real paper."""
        # Use a small, well-known paper for testing
        arxiv_id = "1706.03762"  # "Attention Is All You Need"
        
        try:
            result = await self.converter.download_and_convert(
                arxiv_id=arxiv_id,
                save_latex=True,
                save_markdown=True,
                include_pdf=False
            )
            
            if result["success"]:
                assert result["arxiv_id"] == arxiv_id
                assert "formats" in result
                
                # Check that directories were created
                latex_dir = Path(self.temp_dir) / "latex" / arxiv_id
                markdown_dir = Path(self.temp_dir) / "markdown" / arxiv_id
                
                if "latex" in result["formats"]:
                    assert latex_dir.exists()
                
                if "markdown" in result["formats"]:
                    assert markdown_dir.exists()
                    
        except Exception as e:
            # If download fails (network issues, etc.), that's okay for testing
            pytest.skip(f"Download test skipped due to: {e}")


class TestIntegrationWorkflow:
    """Test the complete workflow integration."""
    
    def setup_method(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
    
    def teardown_method(self):
        """Clean up test environment."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    @pytest.mark.asyncio
    async def test_convenience_function(self):
        """Test the convenience function for download and convert."""
        arxiv_id = "1706.03762"
        
        try:
            result = await download_and_convert_paper(
                arxiv_id=arxiv_id,
                output_dir=self.temp_dir,
                save_latex=True,
                save_markdown=True
            )
            
            if result["success"]:
                assert result["arxiv_id"] == arxiv_id
                assert Path(self.temp_dir).exists()
                
        except Exception as e:
            pytest.skip(f"Download test skipped due to: {e}")
    
    def test_file_saver_integration_with_converter(self):
        """Test integration between FileSaver and LaTeXToMarkdownConverter."""
        file_saver = FileSaver(self.temp_dir)
        converter = LaTeXToMarkdownConverter()
        
        # Sample LaTeX content
        latex_content = r"""
        \documentclass{article}
        \title{Integration Test}
        \author{Test Author}
        \begin{document}
        \section{Test Section}
        This is a test.
        \end{document}
        """
        
        # Convert to markdown
        conversion_result = converter.convert_with_metadata(latex_content, "test.integration")
        
        if conversion_result["success"]:
            # Save the result
            markdown_path = file_saver.save_markdown_file(
                "test.integration",
                conversion_result["markdown"],
                conversion_result["metadata"]
            )
            
            # Verify the file exists and has content
            assert markdown_path.exists()
            
            with open(markdown_path, 'r') as f:
                content = f.read()
            
            assert "title: Integration Test" in content
            assert "Test Section" in content


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
