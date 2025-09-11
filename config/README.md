# Configuration

This directory contains configuration files and templates for the ArXiv MCP server.

## 📁 Configuration Files

```
config/
├── arxiv_mcp_example.yaml     # Example configuration with all options
├── arxiv_mcp_production.json  # Production-ready configuration
├── development.yaml           # Development environment config
├── testing.yaml              # Test environment config
└── README.md                  # This file
```

## ⚙️ Configuration Options

### Basic Configuration

```yaml
# Basic ArXiv MCP server configuration
server:
  name: "arxiv-mcp-server"
  version: "1.0.0"
  
arxiv:
  api_url: "http://export.arxiv.org/api/query"
  rate_limit: 3  # requests per second
  
output:
  base_directory: ".dev/runtime/output"
  formats: ["latex", "markdown", "metadata"]
```

### Advanced Features

```yaml
# Advanced configuration options
processing:
  latex_processor:
    timeout: 60
    max_file_size: "10MB"
    
  citation_analysis:
    enabled: true
    confidence_threshold: 0.8
    
caching:
  enabled: true
  cache_directory: "cache"
  ttl: 3600  # 1 hour
```

## 🔧 Environment-Specific Configs

### Development (`development.yaml`)

- Debug logging enabled
- Relaxed rate limits
- Local cache paths
- Development output directories

### Testing (`testing.yaml`)  

- Test-specific settings
- Mock service endpoints
- Temporary directories
- Minimal caching

### Production (`arxiv_mcp_production.json`)

- Production-optimized settings
- Strict error handling
- Performance monitoring
- Secure defaults

## 📋 Configuration Management

### Loading Configuration

```python
from arxiv_mcp.core.config import load_config

# Load default configuration
config = load_config()

# Load specific environment
config = load_config("config/production.yaml")
```

### Environment Variables

Override configuration with environment variables:

```bash
export ARXIV_MCP_OUTPUT_DIR=".dev/runtime/output"
export ARXIV_MCP_LOG_LEVEL="DEBUG"
export ARXIV_MCP_CACHE_ENABLED="true"
```

### Validation

All configuration files are validated against the schema defined in `src/arxiv_mcp/models.py`.

---

*Configuration should be environment-aware, secure by default, and easy to override for different deployment scenarios.*
