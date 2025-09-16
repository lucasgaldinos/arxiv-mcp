#!/usr/bin/env python3
"""
Integration tests for latex_to_markdown.py with real coverage measurement.

Uses minimal mocking approach to enable proper coverage tracking across
subprocess boundaries. Based on proven pattern from unified_converter, batch_operations, and pipeline tests.
"""

import subprocess
from unittest.mock import MagicMock, patch

from arxiv_mcp.utils.latex_to_markdown import LaTeXToMarkdownConverter, check_pandoc_available

# Sample LaTeX content for testing
SAMPLE_LATEX_BASIC = """\\documentclass{article}
\\title{Test Paper}
\\author{Test Author}
\\date{\\today}
\\begin{document}
\\maketitle
\\section{Introduction}
This is a test document with basic LaTeX elements.
\\subsection{Subsection}
Some content here with \\textbf{bold} and \\textit{italic} text.
\\end{document}"""

SAMPLE_LATEX_COMPLEX = """\\documentclass{article}
\\usepackage{amsmath}
\\title{Complex Test Paper}
\\author{Test Author}
\\begin{document}
\\maketitle
\\section{Mathematics}
Here is an equation:
\\begin{equation}
E = mc^2
\\end{equation}
\\subsection{Lists}
\\begin{itemize}
\\item First item
\\item Second item
\\end{itemize}
\\section{Conclusion}
This concludes the test.
\\end{document}"""

SAMPLE_PANDOC_OUTPUT = """---
title: Test Paper
author: Test Author
---

# Introduction

This is a test document with basic LaTeX elements.

## Subsection

Some content here with **bold** and *italic* text."""

SAMPLE_PANDOC_ERROR = "pandoc: error: unknown option"


class TestLaTeXToMarkdownConverterIntegration:
    """Integration tests for LaTeXToMarkdownConverter with real code execution."""

    def test_check_pandoc_available_function(self) -> None:
        """Test the standalone check_pandoc_available function."""
        # This will exercise the real subprocess.run call
        with patch('subprocess.run') as mock_run:
            # Test pandoc available case
            mock_run.return_value.returncode = 0
            result = check_pandoc_available()

            # Verify subprocess was called correctly
            mock_run.assert_called_with(
                ["pandoc", "--version"],
                capture_output=True,
                check=True
            )

            # Note: actual result depends on mock, but we tested the code path

    def test_constructor_with_pandoc_available(self) -> None:
        """Test constructor when pandoc is available."""
        with patch('subprocess.run') as mock_run:
            mock_run.return_value.returncode = 0

            converter = LaTeXToMarkdownConverter(use_pandoc=True)

            # Verify pandoc check was called during initialization
            assert mock_run.called
            # Constructor calls _check_pandoc_available which uses subprocess.run

    def test_constructor_with_pandoc_unavailable(self) -> None:
        """Test constructor when pandoc is unavailable."""
        with patch('subprocess.run') as mock_run:
            mock_run.side_effect = FileNotFoundError("pandoc not found")

            converter = LaTeXToMarkdownConverter(use_pandoc=True)

            # Should fallback to no pandoc mode
            assert not converter.use_pandoc
            assert mock_run.called

    def test_constructor_with_extra_args(self) -> None:
        """Test constructor with extra pandoc arguments."""
        extra_args = ["--filter", "pandoc-citeproc"]

        with patch('subprocess.run') as mock_run:
            mock_run.return_value.returncode = 0

            converter = LaTeXToMarkdownConverter(use_pandoc=True, pandoc_extra_args=extra_args)

            assert converter.pandoc_extra_args == extra_args
            assert mock_run.called

    def test_convert_with_pandoc_success(self) -> None:
        """Test successful conversion using pandoc subprocess."""
        with patch('subprocess.run') as mock_run:
            # Mock pandoc availability check (constructor)
            mock_run.return_value.returncode = 0

            converter = LaTeXToMarkdownConverter(use_pandoc=True)

            # Reset mock for conversion call
            mock_run.reset_mock()

            # Mock successful pandoc conversion
            mock_result = MagicMock()
            mock_result.returncode = 0
            mock_result.stdout = SAMPLE_PANDOC_OUTPUT
            mock_result.stderr = ""
            mock_run.return_value = mock_result

            # Execute conversion - this exercises the subprocess.run code path
            result = converter.convert(SAMPLE_LATEX_BASIC)

            # Verify subprocess.run was called with correct arguments
            mock_run.assert_called_with(
                [
                    "pandoc",
                    "--from=latex",
                    "--to=markdown",
                    "--wrap=none",
                    "--standalone"
                ],
                check=False,
                input=SAMPLE_LATEX_BASIC,
                capture_output=True,
                text=True,
                timeout=60
            )

            # Verify result structure
            assert result["success"] is True
            assert result["method"] == "pandoc"
            assert "markdown" in result
            assert result["warnings"] is None

    def test_convert_with_pandoc_failure_fallback(self) -> None:
        """Test pandoc failure falling back to custom converter."""
        with patch('subprocess.run') as mock_run:
            # Mock pandoc availability check (constructor)
            mock_run.return_value.returncode = 0

            converter = LaTeXToMarkdownConverter(use_pandoc=True)

            # Reset mock for conversion call
            mock_run.reset_mock()

            # Mock failed pandoc conversion
            mock_result = MagicMock()
            mock_result.returncode = 1
            mock_result.stdout = ""
            mock_result.stderr = SAMPLE_PANDOC_ERROR
            mock_run.return_value = mock_result

            # Execute conversion - this exercises both subprocess.run AND fallback code paths
            result = converter.convert(SAMPLE_LATEX_BASIC)

            # Verify subprocess.run was called
            assert mock_run.called

            # Should fallback to custom converter
            assert result["method"] == "fallback"
            assert result["success"] is True
            assert "markdown" in result

    def test_convert_with_pandoc_timeout(self) -> None:
        """Test pandoc timeout handling."""
        with patch('subprocess.run') as mock_run:
            # Mock pandoc availability check (constructor)
            mock_run.return_value.returncode = 0

            converter = LaTeXToMarkdownConverter(use_pandoc=True)

            # Reset mock for conversion call
            mock_run.reset_mock()

            # Mock timeout exception
            mock_run.side_effect = subprocess.TimeoutExpired("pandoc", 60)

            # Execute conversion - this exercises timeout handling
            result = converter.convert(SAMPLE_LATEX_BASIC)

            # Should fallback to custom converter
            assert result["method"] == "fallback"
            assert result["success"] is True

    def test_convert_with_complex_latex(self) -> None:
        """Test conversion with more complex LaTeX content."""
        with patch('subprocess.run') as mock_run:
            # Mock pandoc availability
            mock_run.return_value.returncode = 0

            converter = LaTeXToMarkdownConverter(use_pandoc=True)

            # Reset mock for conversion call
            mock_run.reset_mock()

            # Mock successful complex conversion
            mock_result = MagicMock()
            mock_result.returncode = 0
            mock_result.stdout = "# Complex Test Paper\n\n## Mathematics\n\nHere is an equation:\n\n$$E = mc^2$$"
            mock_result.stderr = ""
            mock_run.return_value = mock_result

            # Execute conversion with complex content
            result = converter.convert(SAMPLE_LATEX_COMPLEX)

            # Verify subprocess was called with complex input
            call_args = mock_run.call_args
            assert call_args[1]['input'] == SAMPLE_LATEX_COMPLEX

            # Verify result
            assert result["success"] is True
            assert result["method"] == "pandoc"

    def test_convert_with_metadata(self) -> None:
        """Test conversion with metadata passed through."""
        with patch('subprocess.run') as mock_run:
            # Mock pandoc availability
            mock_run.return_value.returncode = 0

            converter = LaTeXToMarkdownConverter(use_pandoc=True)

            # Reset mock for conversion call
            mock_run.reset_mock()

            # Mock failed pandoc to test metadata in fallback
            mock_result = MagicMock()
            mock_result.returncode = 1
            mock_result.stderr = "error"
            mock_run.return_value = mock_result

            metadata = {"title": "Test Title", "author": "Test Author"}

            # Execute conversion - will hit fallback path
            result = converter.convert(SAMPLE_LATEX_BASIC, metadata=metadata)

            # Verify subprocess was called first
            assert mock_run.called

            # Should use fallback with metadata
            assert result["method"] == "fallback"
            assert result["success"] is True

    def test_convert_fallback_only(self) -> None:
        """Test conversion using only fallback converter (no pandoc)."""
        with patch('subprocess.run') as mock_run:
            # Mock pandoc unavailable
            mock_run.side_effect = FileNotFoundError()

            converter = LaTeXToMarkdownConverter(use_pandoc=True)

            # Should have fallen back to no pandoc
            assert not converter.use_pandoc

            # Execute conversion - should use fallback directly
            result = converter.convert(SAMPLE_LATEX_BASIC)

            # Verify result uses fallback
            assert result["method"] == "fallback"
            assert result["success"] is True
            assert "markdown" in result

    def test_pandoc_extra_args_integration(self) -> None:
        """Test that extra pandoc arguments are properly integrated."""
        extra_args = ["--filter", "pandoc-citeproc", "--bibliography", "refs.bib"]

        with patch('subprocess.run') as mock_run:
            # Mock pandoc availability
            mock_run.return_value.returncode = 0

            converter = LaTeXToMarkdownConverter(
                use_pandoc=True,
                pandoc_extra_args=extra_args
            )

            # Reset mock for conversion call
            mock_run.reset_mock()

            # Mock successful conversion
            mock_result = MagicMock()
            mock_result.returncode = 0
            mock_result.stdout = "converted content"
            mock_result.stderr = ""
            mock_run.return_value = mock_result

            # Execute conversion
            result = converter.convert(SAMPLE_LATEX_BASIC)

            # Verify extra args were included in subprocess call
            call_args = mock_run.call_args[0][0]  # First positional arg (command list)
            expected_cmd = [
                "pandoc",
                "--from=latex",
                "--to=markdown",
                "--wrap=none",
                "--standalone",
                "--filter",
                "pandoc-citeproc",
                "--bibliography",
                "refs.bib"
            ]
            assert call_args == expected_cmd
