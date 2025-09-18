"""
Workspace-aware path resolution utilities for MCP tools.
Attempts to detect and resolve paths relative to the VS Code workspace root.
"""

import os
from pathlib import Path
from typing import Optional


class WorkspacePathResolver:
    """Resolves file paths relative to the VS Code workspace root."""
    
    def __init__(self):
        self._workspace_root: Optional[Path] = None
        self._detect_workspace_root()
    
    def _detect_workspace_root(self) -> None:
        """Attempt to detect the VS Code workspace root directory."""
        
        # Method 1: Look for VS Code workspace indicators
        current = Path.cwd()
        
        # Search up the directory tree for workspace indicators
        for parent in [current] + list(current.parents):
            # Check for VS Code workspace file
            if any(parent.glob("*.code-workspace")):
                self._workspace_root = parent
                return
                
            # Check for .vscode directory
            if (parent / ".vscode").exists():
                self._workspace_root = parent
                return
                
            # Check for common project root indicators
            root_indicators = [
                "pyproject.toml", "setup.py", "requirements.txt",
                ".git", "package.json", "Cargo.toml", "go.mod"
            ]
            
            if any((parent / indicator).exists() for indicator in root_indicators):
                self._workspace_root = parent
                return
                
        # Method 2: Check environment variables that VS Code might set
        env_workspace = os.environ.get("VSCODE_WORKSPACE_FOLDER")
        if env_workspace and Path(env_workspace).exists():
            self._workspace_root = Path(env_workspace)
            return
            
        # Method 3: Check if we're in a known workspace structure
        # Look for arxiv-mcp-improved specific indicators
        for parent in [current] + list(current.parents):
            if (parent / "src" / "arxiv_mcp").exists() and (parent / "pyproject.toml").exists():
                self._workspace_root = parent
                return
                
        # Fallback: use current working directory
        self._workspace_root = current
    
    def get_workspace_root(self) -> Path:
        """Get the detected workspace root directory."""
        return self._workspace_root or Path.cwd()
    
    def resolve_output_path(self, output_dir: str) -> str:
        """Resolve output directory relative to workspace root.
        
        Args:
            output_dir: Output directory path (may be relative or absolute)
            
        Returns:
            Absolute path to output directory
        """
        if os.path.isabs(output_dir):
            return output_dir
            
        # Resolve relative to workspace root
        workspace_root = self.get_workspace_root()
        resolved_path = workspace_root / output_dir
        
        return str(resolved_path.resolve())
    
    def is_workspace_relative(self, path: str) -> bool:
        """Check if a path is within the detected workspace."""
        try:
            abs_path = Path(path).resolve()
            workspace_root = self.get_workspace_root().resolve()
            return abs_path.is_relative_to(workspace_root)
        except (ValueError, OSError):
            return False
    
    def make_workspace_relative(self, path: str) -> str:
        """Convert absolute path to workspace-relative path if possible.
        
        Args:
            path: Absolute or relative path
            
        Returns:
            Path relative to workspace root, or original path if not in workspace
        """
        try:
            abs_path = Path(path).resolve()
            workspace_root = self.get_workspace_root().resolve()
            
            if abs_path.is_relative_to(workspace_root):
                return str(abs_path.relative_to(workspace_root))
            else:
                return path
        except (ValueError, OSError):
            return path
            
    def get_debug_info(self) -> dict:
        """Get debug information about workspace detection."""
        return {
            "detected_workspace_root": str(self.get_workspace_root()),
            "current_working_directory": str(Path.cwd()),
            "vscode_workspace_env": os.environ.get("VSCODE_WORKSPACE_FOLDER"),
            "workspace_indicators_found": self._find_workspace_indicators(),
        }
    
    def _find_workspace_indicators(self) -> list[str]:
        """Find workspace indicators in the detected root."""
        workspace_root = self.get_workspace_root()
        indicators = []
        
        # Check for various indicators
        if (workspace_root / ".vscode").exists():
            indicators.append(".vscode/")
        if list(workspace_root.glob("*.code-workspace")):
            indicators.append("*.code-workspace files")
        if (workspace_root / ".git").exists():
            indicators.append(".git/")
        if (workspace_root / "pyproject.toml").exists():
            indicators.append("pyproject.toml")
        if (workspace_root / "src" / "arxiv_mcp").exists():
            indicators.append("src/arxiv_mcp/")
            
        return indicators


# Global instance for use across the application
workspace_resolver = WorkspacePathResolver()