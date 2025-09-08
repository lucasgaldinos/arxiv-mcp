"""
Enhanced document processor supporting multiple formats beyond PDF/LaTeX.
This extends the existing processing pipeline to support OpenDocument (.odt) and RTF formats.
"""

from typing import Dict, Any, Optional, List, Union
import re
from pathlib import Path
from io import BytesIO
import zipfile
from dataclasses import dataclass
from enum import Enum

from ..utils.logging import structured_logger
from ..utils.metrics import MetricsCollector
from ..utils.validation import ArxivValidator
from ..exceptions import ProcessingError


class DocumentFormat(Enum):
    """Supported document formats."""

    PDF = "pdf"
    LATEX = "latex"
    ODT = "odt"
    RTF = "rtf"
    DOCX = "docx"
    TXT = "txt"


@dataclass
class DocumentMetadata:
    """Metadata extracted from documents."""

    format: DocumentFormat
    title: Optional[str] = None
    author: Optional[str] = None
    subject: Optional[str] = None
    creator: Optional[str] = None
    pages: Optional[int] = None
    word_count: Optional[int] = None
    language: Optional[str] = None
    created_date: Optional[str] = None
    modified_date: Optional[str] = None


@dataclass
class ProcessingResult:
    """Result of document processing."""

    success: bool
    extracted_text: str
    metadata: DocumentMetadata
    format: DocumentFormat
    error: Optional[str] = None
    warnings: List[str] = None


class DocumentProcessor:
    """Enhanced document processor supporting multiple formats."""

    def __init__(self):
        self.logger = structured_logger()
        self.metrics = MetricsCollector()
        self.validator = ArxivValidator()

    def detect_format(
        self, content: Union[bytes, str], filename: Optional[str] = None
    ) -> DocumentFormat:
        """Detect document format from content or filename."""

        # Try filename extension first
        if filename:
            ext = Path(filename).suffix.lower()
            format_map = {
                ".pdf": DocumentFormat.PDF,
                ".tex": DocumentFormat.LATEX,
                ".odt": DocumentFormat.ODT,
                ".rtf": DocumentFormat.RTF,
                ".docx": DocumentFormat.DOCX,
                ".txt": DocumentFormat.TXT,
            }
            if ext in format_map:
                return format_map[ext]

        # Analyze content signature
        if isinstance(content, str):
            content = content.encode("utf-8")

        # Check magic bytes
        if content.startswith(b"%PDF-"):
            return DocumentFormat.PDF
        elif content.startswith(b"PK\x03\x04"):
            # ZIP-based formats (ODT, DOCX)
            try:
                with zipfile.ZipFile(BytesIO(content), "r") as zf:
                    if "META-INF/manifest.xml" in zf.namelist():
                        return DocumentFormat.ODT
                    elif "[Content_Types].xml" in zf.namelist():
                        return DocumentFormat.DOCX
            except zipfile.BadZipFile:
                pass
        elif content.startswith(b"{\\rtf"):
            return DocumentFormat.RTF
        elif b"\\documentclass" in content[:1024]:
            return DocumentFormat.LATEX

        # Default to plain text
        return DocumentFormat.TXT

    def process_document(
        self, content: bytes, filename: Optional[str] = None
    ) -> ProcessingResult:
        """Process document and extract text and metadata."""

        format_type = self.detect_format(content, filename)

        try:
            if format_type == DocumentFormat.ODT:
                return self._process_odt(content)
            elif format_type == DocumentFormat.RTF:
                return self._process_rtf(content)
            elif format_type == DocumentFormat.DOCX:
                return self._process_docx(content)
            elif format_type == DocumentFormat.TXT:
                return self._process_txt(content)
            else:
                return ProcessingResult(
                    success=False,
                    extracted_text="",
                    metadata=DocumentMetadata(format=format_type),
                    format=format_type,
                    error=f"Format {format_type.value} not implemented in DocumentProcessor",
                )

        except Exception as e:
            self.logger.error(
                f"Document processing failed for {format_type.value}: {str(e)}"
            )
            return ProcessingResult(
                success=False,
                extracted_text="",
                metadata=DocumentMetadata(format=format_type),
                format=format_type,
                error=str(e),
            )

    def _process_odt(self, content: bytes) -> ProcessingResult:
        """Process OpenDocument Text (.odt) files."""

        try:
            # ODT files are ZIP archives
            with zipfile.ZipFile(BytesIO(content), "r") as zf:
                # Extract content.xml which contains the text
                if "content.xml" not in zf.namelist():
                    raise ProcessingError("Invalid ODT file: content.xml not found")

                content_xml = zf.read("content.xml").decode("utf-8")

                # Extract metadata if available
                metadata = DocumentMetadata(format=DocumentFormat.ODT)
                if "meta.xml" in zf.namelist():
                    meta_xml = zf.read("meta.xml").decode("utf-8")
                    metadata = self._extract_odt_metadata(meta_xml)

                # Extract text from content.xml
                extracted_text = self._extract_text_from_odt_xml(content_xml)

                return ProcessingResult(
                    success=True,
                    extracted_text=extracted_text,
                    metadata=metadata,
                    format=DocumentFormat.ODT,
                )

        except zipfile.BadZipFile:
            raise ProcessingError("Invalid ODT file: not a valid ZIP archive")
        except Exception as e:
            raise ProcessingError(f"ODT processing failed: {str(e)}")

    def _process_rtf(self, content: bytes) -> ProcessingResult:
        """Process Rich Text Format (.rtf) files."""

        try:
            # RTF is text-based format
            rtf_text = content.decode("utf-8", errors="ignore")

            # Extract metadata
            metadata = self._extract_rtf_metadata(rtf_text)

            # Extract plain text
            extracted_text = self._extract_text_from_rtf(rtf_text)

            return ProcessingResult(
                success=True,
                extracted_text=extracted_text,
                metadata=metadata,
                format=DocumentFormat.RTF,
            )

        except Exception as e:
            raise ProcessingError(f"RTF processing failed: {str(e)}")

    def _process_docx(self, content: bytes) -> ProcessingResult:
        """Process Microsoft Word (.docx) files."""

        try:
            # Try python-docx first, fallback to manual parsing
            try:
                from docx import Document
                from io import BytesIO

                doc = Document(BytesIO(content))

                # Extract text
                paragraphs = []
                for paragraph in doc.paragraphs:
                    if paragraph.text.strip():
                        paragraphs.append(paragraph.text)

                extracted_text = "\n\n".join(paragraphs)

                # Extract metadata
                metadata = DocumentMetadata(
                    format=DocumentFormat.DOCX,
                    title=doc.core_properties.title,
                    author=doc.core_properties.author,
                    subject=doc.core_properties.subject,
                    created_date=str(doc.core_properties.created)
                    if doc.core_properties.created
                    else None,
                    modified_date=str(doc.core_properties.modified)
                    if doc.core_properties.modified
                    else None,
                )

                return ProcessingResult(
                    success=True,
                    extracted_text=extracted_text,
                    metadata=metadata,
                    format=DocumentFormat.DOCX,
                )

            except ImportError:
                # Fallback to manual ZIP parsing
                return self._process_docx_manual(content)

        except Exception as e:
            raise ProcessingError(f"DOCX processing failed: {str(e)}")

    def _process_txt(self, content: bytes) -> ProcessingResult:
        """Process plain text files."""

        try:
            # Try UTF-8 first, fallback to other encodings
            for encoding in ["utf-8", "latin-1", "cp1252"]:
                try:
                    text = content.decode(encoding)
                    break
                except UnicodeDecodeError:
                    continue
            else:
                text = content.decode("utf-8", errors="ignore")

            # Basic metadata
            metadata = DocumentMetadata(
                format=DocumentFormat.TXT, word_count=len(text.split())
            )

            return ProcessingResult(
                success=True,
                extracted_text=text,
                metadata=metadata,
                format=DocumentFormat.TXT,
            )

        except Exception as e:
            raise ProcessingError(f"TXT processing failed: {str(e)}")

    def _extract_text_from_odt_xml(self, xml_content: str) -> str:
        """Extract text from ODT content.xml."""

        # Remove XML tags and extract text
        text = re.sub(r"<[^>]+>", " ", xml_content)

        # Clean up whitespace
        text = re.sub(r"\s+", " ", text).strip()

        return text

    def _extract_odt_metadata(self, meta_xml: str) -> DocumentMetadata:
        """Extract metadata from ODT meta.xml."""

        metadata = DocumentMetadata(format=DocumentFormat.ODT)

        # Extract title
        title_match = re.search(r"<dc:title>([^<]+)</dc:title>", meta_xml)
        if title_match:
            metadata.title = title_match.group(1)

        # Extract author
        author_match = re.search(r"<dc:creator>([^<]+)</dc:creator>", meta_xml)
        if author_match:
            metadata.author = author_match.group(1)

        # Extract subject
        subject_match = re.search(r"<dc:subject>([^<]+)</dc:subject>", meta_xml)
        if subject_match:
            metadata.subject = subject_match.group(1)

        return metadata

    def _extract_text_from_rtf(self, rtf_content: str) -> str:
        """Extract plain text from RTF content."""

        # Remove RTF control words and groups
        text = re.sub(r"\\[a-z]+\d*\s?", " ", rtf_content)
        text = re.sub(r"[{}]", " ", text)

        # Clean up whitespace
        text = re.sub(r"\s+", " ", text).strip()

        return text

    def _extract_rtf_metadata(self, rtf_content: str) -> DocumentMetadata:
        """Extract metadata from RTF content."""

        metadata = DocumentMetadata(format=DocumentFormat.RTF)

        # Extract title
        title_match = re.search(r"\\title\s+([^}]+)", rtf_content)
        if title_match:
            metadata.title = title_match.group(1).strip()

        # Extract author
        author_match = re.search(r"\\author\s+([^}]+)", rtf_content)
        if author_match:
            metadata.author = author_match.group(1).strip()

        return metadata

    def _process_docx_manual(self, content: bytes) -> ProcessingResult:
        """Manual DOCX processing when python-docx is not available."""

        try:
            with zipfile.ZipFile(BytesIO(content), "r") as zf:
                # Extract document.xml which contains the text
                if "word/document.xml" not in zf.namelist():
                    raise ProcessingError(
                        "Invalid DOCX file: word/document.xml not found"
                    )

                document_xml = zf.read("word/document.xml").decode("utf-8")

                # Extract text from XML
                text = re.sub(r"<[^>]+>", " ", document_xml)
                text = re.sub(r"\s+", " ", text).strip()

                # Basic metadata
                metadata = DocumentMetadata(format=DocumentFormat.DOCX)

                return ProcessingResult(
                    success=True,
                    extracted_text=text,
                    metadata=metadata,
                    format=DocumentFormat.DOCX,
                    warnings=[
                        "Used manual parsing: install python-docx for better support"
                    ],
                )

        except zipfile.BadZipFile:
            raise ProcessingError("Invalid DOCX file: not a valid ZIP archive")

    def get_supported_formats(self) -> List[DocumentFormat]:
        """Get list of supported document formats."""
        return list(DocumentFormat)

    def get_format_info(self, format_type: DocumentFormat) -> Dict[str, Any]:
        """Get information about a specific format."""

        format_info = {
            DocumentFormat.PDF: {
                "name": "Portable Document Format",
                "extensions": [".pdf"],
                "requires_external": False,
                "description": "Adobe PDF format",
            },
            DocumentFormat.LATEX: {
                "name": "LaTeX Document",
                "extensions": [".tex", ".latex"],
                "requires_external": False,
                "description": "LaTeX typesetting format",
            },
            DocumentFormat.ODT: {
                "name": "OpenDocument Text",
                "extensions": [".odt"],
                "requires_external": False,
                "description": "Open standard document format",
            },
            DocumentFormat.RTF: {
                "name": "Rich Text Format",
                "extensions": [".rtf"],
                "requires_external": False,
                "description": "Microsoft Rich Text Format",
            },
            DocumentFormat.DOCX: {
                "name": "Microsoft Word Document",
                "extensions": [".docx"],
                "requires_external": True,
                "optional_dependency": "python-docx",
                "description": "Microsoft Word format",
            },
            DocumentFormat.TXT: {
                "name": "Plain Text",
                "extensions": [".txt"],
                "requires_external": False,
                "description": "Plain text format",
            },
        }

        return format_info.get(format_type, {})
