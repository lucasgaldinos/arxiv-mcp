"""
Tests for the enhanced DocumentProcessor functionality (Phase 4A).
Tests additional document format support: ODT, RTF, DOCX.
"""

import pytest
from io import BytesIO
import zipfile

from arxiv_mcp.processors.document_processor import (
    DocumentProcessor,
    DocumentFormat,
)


class TestDocumentProcessor:
    """Test the DocumentProcessor functionality."""

    def setup_method(self):
        """Set up test environment."""
        self.processor = DocumentProcessor()

    def test_processor_initialization(self):
        """Test DocumentProcessor initialization."""
        assert hasattr(self.processor, "detect_format")
        assert hasattr(self.processor, "process_document")
        assert hasattr(self.processor, "get_supported_formats")
        assert hasattr(self.processor, "get_format_info")

    def test_format_detection_by_extension(self):
        """Test format detection based on file extension."""
        test_cases = [
            ("document.pdf", DocumentFormat.PDF),
            ("paper.tex", DocumentFormat.LATEX),
            ("article.odt", DocumentFormat.ODT),
            ("memo.rtf", DocumentFormat.RTF),
            ("report.docx", DocumentFormat.DOCX),
            ("notes.txt", DocumentFormat.TXT),
        ]

        for filename, expected_format in test_cases:
            detected = self.processor.detect_format(b"test content", filename)
            assert detected == expected_format

    def test_format_detection_by_content(self):
        """Test format detection based on content signature."""
        test_cases = [
            (b"%PDF-1.4", DocumentFormat.PDF),
            (b"\\documentclass{article}", DocumentFormat.LATEX),
            (b"{\\rtf1\\ansi", DocumentFormat.RTF),
        ]

        for content, expected_format in test_cases:
            detected = self.processor.detect_format(content)
            assert detected == expected_format

    def test_text_processing(self):
        """Test plain text processing."""
        text_content = b"This is a test document.\n\nIt has multiple paragraphs."

        result = self.processor.process_document(text_content, "test.txt")

        assert result.success is True
        assert result.format == DocumentFormat.TXT
        assert "test document" in result.extracted_text
        assert result.metadata.format == DocumentFormat.TXT
        assert result.metadata.word_count > 0

    def test_rtf_processing(self):
        """Test RTF document processing."""
        rtf_content = b"""{\\rtf1\\ansi\\deff0 {\\fonttbl {\\f0 Times New Roman;}}
\\f0\\fs24 This is a \\b bold \\b0 test document with RTF formatting.
\\par
This is a second paragraph.
}"""

        result = self.processor.process_document(rtf_content, "test.rtf")

        assert result.success is True
        assert result.format == DocumentFormat.RTF
        assert "test document" in result.extracted_text
        assert "second paragraph" in result.extracted_text
        assert result.metadata.format == DocumentFormat.RTF

    def test_odt_processing_structure(self):
        """Test ODT document structure detection."""
        # Create a minimal ODT-like ZIP structure
        odt_buffer = BytesIO()
        with zipfile.ZipFile(odt_buffer, "w") as zf:
            zf.writestr("META-INF/manifest.xml", '<?xml version="1.0"?>')
            zf.writestr(
                "content.xml",
                """<?xml version="1.0"?>
                <office:document-content>
                    <office:body>
                        <office:text>
                            <text:p>This is a test ODT document.</text:p>
                            <text:p>This is another paragraph.</text:p>
                        </office:text>
                    </office:body>
                </office:document-content>""",
            )
            zf.writestr(
                "meta.xml",
                """<?xml version="1.0"?>
                <office:document-meta>
                    <office:meta>
                        <dc:title>Test ODT Document</dc:title>
                        <dc:creator>Test Author</dc:creator>
                        <dc:subject>Testing</dc:subject>
                    </office:meta>
                </office:document-meta>""",
            )

        odt_content = odt_buffer.getvalue()

        # Test format detection
        detected_format = self.processor.detect_format(odt_content, "test.odt")
        assert detected_format == DocumentFormat.ODT

        # Test processing
        result = self.processor.process_document(odt_content, "test.odt")

        assert result.success is True
        assert result.format == DocumentFormat.ODT
        assert "test odt document" in result.extracted_text.lower()
        assert result.metadata.title == "Test ODT Document"
        assert result.metadata.author == "Test Author"

    def test_supported_formats(self):
        """Test getting supported formats."""
        formats = self.processor.get_supported_formats()

        assert DocumentFormat.PDF in formats
        assert DocumentFormat.LATEX in formats
        assert DocumentFormat.ODT in formats
        assert DocumentFormat.RTF in formats
        assert DocumentFormat.DOCX in formats
        assert DocumentFormat.TXT in formats

    def test_format_info(self):
        """Test getting format information."""
        odt_info = self.processor.get_format_info(DocumentFormat.ODT)

        assert odt_info["name"] == "OpenDocument Text"
        assert ".odt" in odt_info["extensions"]
        assert odt_info["requires_external"] is False

        docx_info = self.processor.get_format_info(DocumentFormat.DOCX)

        assert docx_info["name"] == "Microsoft Word Document"
        assert ".docx" in docx_info["extensions"]
        assert docx_info["requires_external"] is True
        assert "python-docx" in docx_info["optional_dependency"]

    def test_docx_manual_processing(self):
        """Test DOCX processing without python-docx (manual mode)."""
        # Create a minimal DOCX-like ZIP structure
        docx_buffer = BytesIO()
        with zipfile.ZipFile(docx_buffer, "w") as zf:
            zf.writestr("[Content_Types].xml", '<?xml version="1.0"?>')
            zf.writestr(
                "word/document.xml",
                """<?xml version="1.0"?>
                <w:document>
                    <w:body>
                        <w:p>
                            <w:r><w:t>This is a test DOCX document.</w:t></w:r>
                        </w:p>
                        <w:p>
                            <w:r><w:t>This is another paragraph.</w:t></w:r>
                        </w:p>
                    </w:body>
                </w:document>""",
            )

        docx_content = docx_buffer.getvalue()

        # Test format detection
        detected_format = self.processor.detect_format(docx_content, "test.docx")
        assert detected_format == DocumentFormat.DOCX

        # Test processing (should fall back to manual mode)
        result = self.processor.process_document(docx_content, "test.docx")

        assert result.success is True
        assert result.format == DocumentFormat.DOCX
        assert "test docx document" in result.extracted_text.lower()

    def test_error_handling(self):
        """Test error handling for invalid documents."""
        # Test with invalid ZIP content for ODT
        invalid_content = b"This is not a valid ODT file"

        result = self.processor.process_document(invalid_content, "test.odt")

        assert result.success is False
        assert result.error is not None
        assert "Invalid ODT file" in result.error

    def test_metadata_extraction(self):
        """Test metadata extraction capabilities."""
        test_text = b"This is a sample document for testing metadata extraction."

        result = self.processor.process_document(test_text, "sample.txt")

        assert result.success is True
        assert result.metadata.format == DocumentFormat.TXT
        assert (
            result.metadata.word_count == 9
        )  # "This is a sample document for testing metadata extraction."

    def test_large_document_handling(self):
        """Test handling of larger documents."""
        # Create a larger text document
        large_text = "This is a sentence. " * 1000
        large_content = large_text.encode("utf-8")

        result = self.processor.process_document(large_content, "large.txt")

        assert result.success is True
        assert result.format == DocumentFormat.TXT
        assert len(result.extracted_text) > 10000
        assert result.metadata.word_count > 3000


class TestDocumentProcessorIntegration:
    """Integration tests for DocumentProcessor with pipeline."""

    def test_format_detection_edge_cases(self):
        """Test edge cases in format detection."""
        processor = DocumentProcessor()

        # Test empty content
        result = processor.detect_format(b"", "test.txt")
        assert result == DocumentFormat.TXT

        # Test content without filename
        result = processor.detect_format(b"%PDF-1.4")
        assert result == DocumentFormat.PDF

        # Test conflicting signals (filename vs content)
        result = processor.detect_format(b"\\documentclass{article}", "test.pdf")
        assert result == DocumentFormat.PDF  # Extension takes precedence

    def test_unicode_handling(self):
        """Test Unicode text handling."""
        processor = DocumentProcessor()

        # Test UTF-8 content with special characters
        unicode_text = "Tëst dócümënt wïth spëçïál çhäräçtërs: 中文, русский, العربية"
        unicode_content = unicode_text.encode("utf-8")

        result = processor.process_document(unicode_content, "unicode.txt")

        assert result.success is True
        assert "Tëst dócümënt" in result.extracted_text
        assert "中文" in result.extracted_text
        assert result.metadata.word_count > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
