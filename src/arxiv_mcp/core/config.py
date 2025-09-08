"""
Configuration management for the ArXiv MCP server.
Provides centralized configuration for all processing components.
This module provides backward compatibility while the enhanced_config module
provides the full-featured configuration management.
"""

from typing import Dict, Any, Optional

# Import enhanced configuration components
from .enhanced_config import (
    PipelineConfig as EnhancedPipelineConfig,
    ConfigurationManager,
)


# Legacy PipelineConfig for backward compatibility
class PipelineConfig:
    """Legacy configuration class for backward compatibility."""

    def __init__(self, **kwargs):
        """Initialize with enhanced config backend."""
        self._enhanced_config = EnhancedPipelineConfig(**kwargs)

    @property
    def max_downloads(self) -> int:
        return self._enhanced_config.max_downloads

    @property
    def max_extractions(self) -> int:
        return self._enhanced_config.max_extractions

    @property
    def max_compilations(self) -> int:
        return self._enhanced_config.max_compilations

    @property
    def requests_per_second(self) -> float:
        return self._enhanced_config.requests_per_second

    @property
    def burst_size(self) -> int:
        return self._enhanced_config.burst_size

    @property
    def download_timeout(self) -> int:
        return self._enhanced_config.download_timeout

    @property
    def extraction_timeout(self) -> int:
        return self._enhanced_config.extraction_timeout

    @property
    def compilation_timeout(self) -> int:
        return self._enhanced_config.compilation_timeout

    @property
    def cache_ttl(self) -> int:
        return self._enhanced_config.cache_ttl

    @property
    def enable_sandboxing(self) -> bool:
        return self._enhanced_config.enable_sandboxing

    @property
    def generate_tex_files(self) -> bool:
        return self._enhanced_config.generate_tex_files

    @property
    def output_directory(self) -> str:
        return self._enhanced_config.output_directory

    @property
    def preserve_intermediates(self) -> bool:
        return self._enhanced_config.preserve_intermediates

    @property
    def max_files_per_archive(self) -> int:
        return self._enhanced_config.max_files_per_archive

    @classmethod
    def from_dict(cls, config_dict: Dict[str, Any]) -> "PipelineConfig":
        """Create PipelineConfig from dictionary."""
        return cls(**config_dict)


def load_config(config_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Load configuration from file or use defaults.
    This function provides backward compatibility while using the enhanced configuration system.
    """
    enhanced_config = ConfigurationManager.load_config(config_path)
    return enhanced_config.to_dict()
