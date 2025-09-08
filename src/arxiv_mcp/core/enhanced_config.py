"""
Enhanced configuration management with YAML, JSON, and environment variable support.
Addresses the critic's recommendation for moving beyond hardcoded configuration.
"""
import os
import yaml
import json
from typing import Dict, Any, Optional, Union
from pathlib import Path
from dataclasses import dataclass, asdict

from ..exceptions import ArxivMCPError


@dataclass
class PipelineConfig:
    """Enhanced configuration for the ArXiv processing pipeline with validation."""

    # Core processing limits
    max_downloads: int = 5
    max_extractions: int = 3
    max_compilations: int = 2
    
    # Rate limiting
    requests_per_second: float = 2.0
    burst_size: int = 5
    
    # Timeouts (seconds)
    download_timeout: int = 60
    extraction_timeout: int = 30
    compilation_timeout: int = 300
    
    # Caching
    cache_ttl: int = 3600
    
    # Validation and security
    enable_http_validation: bool = True
    max_file_size: int = 200 * 1024 * 1024  # 200MB
    max_files_per_archive: int = 1000
    enable_sandboxing: bool = True
    
    # Output configuration
    generate_tex_files: bool = True
    output_directory: str = "./output"
    preserve_intermediates: bool = False
    
    # Logging configuration
    log_level: str = "INFO"
    log_format: str = "json"
    log_file: Optional[str] = None
    
    # External service configuration
    openai_api_key: Optional[str] = None
    anthropic_api_key: Optional[str] = None
    firecrawl_api_key: Optional[str] = None

    def __post_init__(self):
        """Validate configuration after initialization."""
        self.validate()

    def validate(self) -> None:
        """Validate configuration parameters."""
        if self.max_downloads < 1:
            raise ArxivMCPError("max_downloads must be at least 1")
        
        if self.requests_per_second <= 0:
            raise ArxivMCPError("requests_per_second must be positive")
        
        if self.download_timeout < 1:
            raise ArxivMCPError("download_timeout must be at least 1 second")
        
        if self.max_file_size < 1024:  # At least 1KB
            raise ArxivMCPError("max_file_size must be at least 1024 bytes")
        
        if self.log_level not in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]:
            raise ArxivMCPError(f"Invalid log_level: {self.log_level}")
        
        if self.log_format not in ["json", "text"]:
            raise ArxivMCPError(f"Invalid log_format: {self.log_format}")

    @classmethod
    def from_dict(cls, config_dict: Dict[str, Any]) -> "PipelineConfig":
        """Create a PipelineConfig instance from a dictionary with validation."""
        # Filter only known fields to avoid TypeError
        known_fields = {field.name for field in cls.__dataclass_fields__.values()}
        filtered_dict = {k: v for k, v in config_dict.items() if k in known_fields}
        
        return cls(**filtered_dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary."""
        return asdict(self)

    def merge_with(self, other_config: Dict[str, Any]) -> "PipelineConfig":
        """Create a new config by merging with another config dictionary."""
        current_dict = self.to_dict()
        current_dict.update(other_config)
        return self.from_dict(current_dict)


class ConfigurationManager:
    """Enhanced configuration manager supporting multiple sources and formats."""
    
    DEFAULT_CONFIG_PATHS = [
        "arxiv_mcp_config.yaml",
        "arxiv_mcp_config.yml",
        "arxiv_mcp_config.json",
        "config/arxiv_mcp.yaml",
        "config/arxiv_mcp.yml", 
        "config/arxiv_mcp.json",
        ".arxiv_mcp.yaml",
        ".arxiv_mcp.yml",
        ".arxiv_mcp.json"
    ]
    
    ENV_PREFIX = "ARXIV_MCP_"
    
    @classmethod
    def load_config(cls, config_path: Optional[Union[str, Path]] = None) -> PipelineConfig:
        """
        Load configuration from multiple sources with priority order:
        1. Explicit config file path
        2. Environment variables
        3. Default config file locations
        4. Default values
        """
        # Start with default configuration
        config_dict = cls._get_default_config()
        
        # Load from config file (explicit path or search default locations)
        file_config = cls._load_from_file(config_path)
        if file_config:
            config_dict.update(file_config)
        
        # Override with environment variables
        env_config = cls._load_from_environment()
        config_dict.update(env_config)
        
        return PipelineConfig.from_dict(config_dict)
    
    @classmethod
    def _get_default_config(cls) -> Dict[str, Any]:
        """Get default configuration values."""
        return {
            "max_downloads": 5,
            "max_extractions": 3,
            "max_compilations": 2,
            "requests_per_second": 2.0,
            "burst_size": 5,
            "download_timeout": 60,
            "extraction_timeout": 30,
            "compilation_timeout": 300,
            "cache_ttl": 3600,
            "enable_http_validation": True,
            "max_file_size": 100 * 1024 * 1024,
            "max_files_per_archive": 1000,
            "enable_sandboxing": True,
            "generate_tex_files": True,
            "output_directory": "./output",
            "preserve_intermediates": False,
            "log_level": "INFO",
            "log_format": "json",
            "log_file": None,
            "openai_api_key": None,
            "anthropic_api_key": None,
            "firecrawl_api_key": None
        }
    
    @classmethod
    def _load_from_file(cls, config_path: Optional[Union[str, Path]] = None) -> Optional[Dict[str, Any]]:
        """Load configuration from YAML or JSON file."""
        if config_path:
            # Use explicit path
            paths_to_try = [Path(config_path)]
        else:
            # Search default locations
            paths_to_try = [Path(p) for p in cls.DEFAULT_CONFIG_PATHS]
        
        for path in paths_to_try:
            if path.exists() and path.is_file():
                try:
                    return cls._parse_config_file(path)
                except Exception as e:
                    # Log warning but continue searching
                    print(f"Warning: Failed to parse config file {path}: {e}")
                    continue
        
        return None
    
    @classmethod
    def _parse_config_file(cls, path: Path) -> Dict[str, Any]:
        """Parse YAML or JSON configuration file."""
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Determine file format from extension
        if path.suffix.lower() in ['.yaml', '.yml']:
            try:
                return yaml.safe_load(content) or {}
            except yaml.YAMLError as e:
                raise ArxivMCPError(f"Invalid YAML in config file {path}: {e}")
        
        elif path.suffix.lower() == '.json':
            try:
                return json.loads(content)
            except json.JSONDecodeError as e:
                raise ArxivMCPError(f"Invalid JSON in config file {path}: {e}")
        
        else:
            raise ArxivMCPError(f"Unsupported config file format: {path.suffix}")
    
    @classmethod
    def _load_from_environment(cls) -> Dict[str, Any]:
        """Load configuration from environment variables."""
        config = {}
        
        # Define environment variable mappings
        env_mappings = {
            f"{cls.ENV_PREFIX}MAX_DOWNLOADS": ("max_downloads", int),
            f"{cls.ENV_PREFIX}MAX_EXTRACTIONS": ("max_extractions", int),
            f"{cls.ENV_PREFIX}MAX_COMPILATIONS": ("max_compilations", int),
            f"{cls.ENV_PREFIX}REQUESTS_PER_SECOND": ("requests_per_second", float),
            f"{cls.ENV_PREFIX}BURST_SIZE": ("burst_size", int),
            f"{cls.ENV_PREFIX}DOWNLOAD_TIMEOUT": ("download_timeout", int),
            f"{cls.ENV_PREFIX}EXTRACTION_TIMEOUT": ("extraction_timeout", int),
            f"{cls.ENV_PREFIX}COMPILATION_TIMEOUT": ("compilation_timeout", int),
            f"{cls.ENV_PREFIX}CACHE_TTL": ("cache_ttl", int),
            f"{cls.ENV_PREFIX}ENABLE_HTTP_VALIDATION": ("enable_http_validation", cls._parse_bool),
            f"{cls.ENV_PREFIX}MAX_FILE_SIZE": ("max_file_size", int),
            f"{cls.ENV_PREFIX}MAX_FILES_PER_ARCHIVE": ("max_files_per_archive", int),
            f"{cls.ENV_PREFIX}ENABLE_SANDBOXING": ("enable_sandboxing", cls._parse_bool),
            f"{cls.ENV_PREFIX}GENERATE_TEX_FILES": ("generate_tex_files", cls._parse_bool),
            f"{cls.ENV_PREFIX}OUTPUT_DIRECTORY": ("output_directory", str),
            f"{cls.ENV_PREFIX}PRESERVE_INTERMEDIATES": ("preserve_intermediates", cls._parse_bool),
            f"{cls.ENV_PREFIX}LOG_LEVEL": ("log_level", str),
            f"{cls.ENV_PREFIX}LOG_FORMAT": ("log_format", str),
            f"{cls.ENV_PREFIX}LOG_FILE": ("log_file", str),
            f"{cls.ENV_PREFIX}OPENAI_API_KEY": ("openai_api_key", str),
            f"{cls.ENV_PREFIX}ANTHROPIC_API_KEY": ("anthropic_api_key", str),
            f"{cls.ENV_PREFIX}FIRECRAWL_API_KEY": ("firecrawl_api_key", str),
        }
        
        for env_var, (config_key, converter) in env_mappings.items():
            value = os.getenv(env_var)
            if value is not None:
                try:
                    config[config_key] = converter(value)
                except (ValueError, TypeError) as e:
                    raise ArxivMCPError(f"Invalid value for {env_var}: {value} ({e})")
        
        return config
    
    @staticmethod
    def _parse_bool(value: str) -> bool:
        """Parse boolean from string."""
        if isinstance(value, bool):
            return value
        
        lower_value = value.lower().strip()
        if lower_value in ('true', '1', 'yes', 'on', 'enable', 'enabled'):
            return True
        elif lower_value in ('false', '0', 'no', 'off', 'disable', 'disabled'):
            return False
        else:
            raise ValueError(f"Cannot parse '{value}' as boolean")
    
    @classmethod
    def save_config(cls, config: PipelineConfig, path: Union[str, Path]) -> None:
        """Save configuration to file."""
        path = Path(path)
        config_dict = config.to_dict()
        
        # Ensure directory exists
        path.parent.mkdir(parents=True, exist_ok=True)
        
        if path.suffix.lower() in ['.yaml', '.yml']:
            with open(path, 'w', encoding='utf-8') as f:
                yaml.safe_dump(config_dict, f, default_flow_style=False, indent=2)
        
        elif path.suffix.lower() == '.json':
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(config_dict, f, indent=2, ensure_ascii=False)
        
        else:
            raise ArxivMCPError(f"Unsupported config file format: {path.suffix}")


# Backward compatibility functions
def load_config(config_path: Optional[Union[str, Path]] = None) -> Dict[str, Any]:
    """Legacy function for backward compatibility."""
    config = ConfigurationManager.load_config(config_path)
    return config.to_dict()


def get_pipeline_config(config_path: Optional[Union[str, Path]] = None) -> PipelineConfig:
    """Get typed pipeline configuration."""
    return ConfigurationManager.load_config(config_path)
