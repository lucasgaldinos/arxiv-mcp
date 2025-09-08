"""
Comprehensive input validation and sanitization.
Extracted from the main __init__.py for better modularity.
"""

import re
from pathlib import Path


class ArxivValidator:
    """Comprehensive input validation and sanitization"""

    @staticmethod
    def validate_arxiv_id(arxiv_id: str) -> bool:
        """Validate arXiv ID format"""
        # Support both new format (YYMM.NNNN) and old format (subject-class/YYMMnnn)
        pattern = r"^(\d{4}\.\d{4,5}(v\d+)?|\w+[-.]?\w+/\d{7}(v\d+)?)$"
        return bool(re.match(pattern, arxiv_id.strip()))

    @staticmethod
    def sanitize_file_path(path: str) -> str:
        """Sanitize file paths to prevent traversal"""
        # Remove any dangerous characters and path traversal attempts
        path = re.sub(r'[<>:"|?*]', "_", path)
        path = re.sub(r"\.\./", "", path)
        path = re.sub(r"\.\.$", "", path)
        return path.strip()

    @staticmethod
    def validate_archive_member(base_path: Path, member_name: str) -> bool:
        """Validate archive member path for safety"""
        try:
            target = (base_path / member_name).resolve()
            return str(target).startswith(str(base_path.resolve()))
        except (OSError, ValueError):
            return False
