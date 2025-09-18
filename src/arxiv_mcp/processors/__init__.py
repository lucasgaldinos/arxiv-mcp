"""
Processors module for document processing functionality.
Extracted from the main __init__.py for better modularity.
"""

from io import BytesIO
from pathlib import Path
import gzip
import re
import subprocess
import tarfile
import tempfile
from typing import Any
import zipfile

from ..exceptions import CompilationError, ExtractionError
from ..utils.logging import structured_logger
from ..utils.metrics import MetricsCollector
from ..utils.validation import ArxivValidator

# Import the new DocumentProcessor
from .document_processor import (
    DocumentFormat,
    DocumentMetadata,
    DocumentProcessor,
    ProcessingResult,
)

__all__ = [
    "LaTeXProcessor",
    "PDFProcessor",
    "DocumentProcessor",
    "DocumentFormat",
    "DocumentMetadata",
    "ProcessingResult",
]


class LaTeXProcessor:
    """Enhanced LaTeX processor with compilation and parsing capabilities."""

    def __init__(
        self,
        compilation_timeout: int = 300,
        enable_sandboxing: bool = True,
        generate_tex_files: bool = True,
        output_directory: str = "./output",
        preserve_intermediates: bool = False,
    ):
        self.compilation_timeout = compilation_timeout
        self.enable_sandboxing = enable_sandboxing
        self.generate_tex_files = generate_tex_files
        self.output_directory = output_directory
        self.preserve_intermediates = preserve_intermediates
        self.logger = structured_logger()
        self.metrics = MetricsCollector()
        self.validator = ArxivValidator()

    def extract_archive(self, content: BytesIO, max_files: int = 1000) -> dict[str, bytes]:
        """Extract files from compressed archive with robust gzip/tar handling."""
        files = {}
        content.seek(0)
        raw_content = content.read()
        
        try:
            # First try gzip decompression (most common for ArXiv)
            try:
                with gzip.GzipFile(fileobj=BytesIO(raw_content)) as gz_file:
                    decompressed = gz_file.read()
                    self.logger.debug("Successfully decompressed gzip content")
                    
                    # Try as tar file after gzip decompression
                    try:
                        with tarfile.open(fileobj=BytesIO(decompressed), mode="r") as tf:
                            members = tf.getmembers()
                            if len(members) > max_files:
                                raise ExtractionError(
                                    f"Archive contains too many files: {len(members)} > {max_files}"
                                )
                            
                            for member in members:
                                if member.isfile():
                                    # Skip hidden files and unwanted files
                                    if member.name.startswith(".") or member.name.startswith("__"):
                                        continue
                                    
                                    file_obj = tf.extractfile(member)
                                    if file_obj:
                                        files[member.name] = file_obj.read()
                            
                            if files:
                                self.logger.info(f"Extracted {len(files)} files from gzip-compressed tar archive")
                                return files
                    except tarfile.TarError as e:
                        self.logger.debug(f"Gzip decompressed content is not a tar file: {e}")
                        
                    # If not a tar file, check if it's a single tex file
                    try:
                        text_content = decompressed.decode("utf-8", errors="ignore")
                        if "\\documentclass" in text_content or "\\begin{document}" in text_content:
                            files["main.tex"] = decompressed
                            self.logger.info("Extracted single LaTeX file from gzip archive")
                            return files
                    except Exception:
                        pass
                        
            except gzip.BadGzipFile:
                self.logger.debug("Content is not gzip compressed")
            except Exception as e:
                self.logger.debug(f"Gzip decompression failed: {e}")

            # Try ZIP format
            try:
                content.seek(0)
                with zipfile.ZipFile(content, "r") as zf:
                    if len(zf.namelist()) > max_files:
                        raise ExtractionError(
                            f"Archive contains too many files: {len(zf.namelist())} > {max_files}"
                        )

                    for name in zf.namelist():
                        if not name.endswith("/"):  # Skip directories
                            files[name] = zf.read(name)
                    
                    if files:
                        self.logger.info(f"Extracted {len(files)} files from ZIP archive")
                        return files
            except zipfile.BadZipFile:
                self.logger.debug("Content is not a ZIP file")

            # Try uncompressed TAR
            try:
                content.seek(0)
                with tarfile.open(fileobj=content, mode="r") as tf:
                    members = tf.getmembers()
                    if len(members) > max_files:
                        raise ExtractionError(
                            f"Archive contains too many files: {len(members)} > {max_files}"
                        )

                    for member in members:
                        if member.isfile():
                            file_obj = tf.extractfile(member)
                            if file_obj:
                                files[member.name] = file_obj.read()
                    
                    if files:
                        self.logger.info(f"Extracted {len(files)} files from uncompressed tar archive")
                        return files
            except tarfile.TarError as e:
                self.logger.debug(f"Content is not a valid tar file: {e}")

            # Last resort: try as single LaTeX file
            try:
                text_content = raw_content.decode("utf-8", errors="ignore")
                if "\\documentclass" in text_content or "\\begin{document}" in text_content:
                    files["main.tex"] = raw_content
                    self.logger.info("Treated content as single LaTeX file")
                    return files
            except Exception:
                pass

            # If all extraction methods fail
            if not files:
                raise ExtractionError("Could not extract any files from archive - unsupported format or corrupted content")

        except Exception as e:
            if isinstance(e, ExtractionError):
                raise
            raise ExtractionError(f"Archive extraction failed: {str(e)}")

        self.logger.info(f"Extracted {len(files)} files from archive")
        return files

    def find_main_tex_file(self, files: dict[str, bytes]) -> str | None:
        """Find the main TeX file in the extracted files."""
        tex_files = [name for name in files if name.endswith(".tex")]

        if not tex_files:
            return None

        # Look for common main file patterns
        main_patterns = [
            r"main\.tex$",
            r"paper\.tex$",
            r"manuscript\.tex$",
            r"article\.tex$",
        ]

        for pattern in main_patterns:
            for tex_file in tex_files:
                if re.search(pattern, tex_file, re.IGNORECASE):
                    return tex_file

        # Look for files with \documentclass
        for tex_file in tex_files:
            try:
                content = files[tex_file].decode("utf-8", errors="ignore")
                if r"\documentclass" in content:
                    return tex_file
            except Exception:
                continue

        # Return the first .tex file as fallback
        return tex_files[0] if tex_files else None

    def compile_latex(self, files: dict[str, bytes], main_file: str) -> bytes:
        """Compile LaTeX files to PDF."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Write all files to temp directory
            for filename, content in files.items():
                file_path = Path(temp_dir) / filename
                file_path.parent.mkdir(parents=True, exist_ok=True)
                file_path.write_bytes(content)

            # Compile with pdflatex
            main_path = Path(temp_dir) / main_file

            try:
                # Run pdflatex twice for references
                for i in range(2):
                    result = subprocess.run(
                        [
                            "pdflatex",
                            "-interaction=nonstopmode",
                            "-output-directory",
                            temp_dir,
                            str(main_path),
                        ],
                        check=False,
                        timeout=self.compilation_timeout,
                        capture_output=True,
                        text=True,
                        cwd=temp_dir,
                    )

                    if result.returncode != 0 and i == 1:  # Only fail on second run
                        self.logger.error(f"LaTeX compilation failed: {result.stderr}")
                        raise CompilationError(f"LaTeX compilation failed: {result.stderr}")

                # Read the generated PDF
                pdf_name = main_path.stem + ".pdf"
                pdf_path = Path(temp_dir) / pdf_name

                if pdf_path.exists():
                    return pdf_path.read_bytes()
                raise CompilationError("PDF file was not generated")

            except subprocess.TimeoutExpired:
                raise CompilationError(
                    f"LaTeX compilation timed out after {self.compilation_timeout}s"
                )
            except FileNotFoundError:
                raise CompilationError("pdflatex not found. Please install a LaTeX distribution.")

    def extract_text_from_tex(self, tex_content: str) -> str:
        """Extract readable text from LaTeX source."""
        # Remove comments
        tex_content = re.sub(r"%.*$", "", tex_content, flags=re.MULTILINE)

        # Remove common LaTeX commands but keep their content
        tex_content = re.sub(r"\\[a-zA-Z]+\{([^}]*)\}", r"\1", tex_content)
        tex_content = re.sub(r"\\[a-zA-Z]+\[[^\]]*\]\{([^}]*)\}", r"\1", tex_content)

        # Remove math environments
        tex_content = re.sub(r"\$[^$]*\$", " [MATH] ", tex_content)
        tex_content = re.sub(
            r"\\begin\{equation\}.*?\\end\{equation\}",
            " [EQUATION] ",
            tex_content,
            flags=re.DOTALL,
        )

        # Remove other environments but keep content
        tex_content = re.sub(r"\\begin\{[^}]*\}", "", tex_content)
        tex_content = re.sub(r"\\end\{[^}]*\}", "", tex_content)

        # Clean up whitespace
        tex_content = re.sub(r"\s+", " ", tex_content)

        return tex_content.strip()


class PDFProcessor:
    """Enhanced PDF processor with text extraction and analysis."""

    def __init__(self):
        self.logger = structured_logger()
        self.metrics = MetricsCollector()

    def extract_text_from_pdf(self, pdf_content: bytes) -> str:
        """Extract text from PDF content."""
        try:
            from io import BytesIO

            from pypdf import PdfReader

            pdf_reader = PdfReader(BytesIO(pdf_content))
            text = ""

            for page in pdf_reader.pages:
                text += page.extract_text() + "\n"

            return text.strip()

        except ImportError:
            self.logger.warning("pypdf not available, PDF text extraction disabled")
            return "[PDF text extraction requires pypdf]"
        except Exception as e:
            self.logger.exception(f"PDF text extraction failed: {str(e)}")
            return f"[PDF text extraction failed: {str(e)}]"

    def get_pdf_metadata(self, pdf_content: bytes) -> dict[str, Any]:
        """Extract metadata from PDF."""
        try:
            from io import BytesIO

            from pypdf import PdfReader

            pdf_reader = PdfReader(BytesIO(pdf_content))
            metadata = pdf_reader.metadata

            return {
                "title": metadata.get("/Title", ""),
                "author": metadata.get("/Author", ""),
                "subject": metadata.get("/Subject", ""),
                "creator": metadata.get("/Creator", ""),
                "pages": len(pdf_reader.pages),
            }

        except ImportError:
            return {"error": "pypdf not available"}
        except Exception as e:
            return {"error": str(e)}
