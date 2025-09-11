# Project Root

This is the main directory of the ArXiv MCP (Model Context Protocol) server project.

## 📁 Project Structure Overview

```
arxiv-mcp-improved/
├── 📂 .dev/              # Development workspace - all build/runtime artifacts
├── 📂 .github/           # GitHub workflows, templates, and knowledge base
├── 📂 src/               # Source code - modular Python package architecture
├── 📂 tests/             # Test suites - organized by unit/integration/legacy
├── 📂 docs/              # Documentation - guides, API docs, examples
├── 📂 config/            # Configuration files and templates
├── 📂 examples/          # Usage examples and demonstrations
├── 📂 scripts/           # Development and automation scripts
├── 📂 cache/             # Working cache systems (preserved)
├── 📂 batch_cache/       # Batch processing cache (preserved)
├── 📂 tag_cache/         # Tag cache system (preserved)
├── 📂 network_cache/     # Network cache (preserved)
├── 📄 README.md          # Main project documentation
├── 📄 pyproject.toml     # Python project configuration
└── 📄 *.md               # Additional Extremely necessary documentation files
```

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- UV package manager

### Installation

```bash
# Clone the repository
git clone https://github.com/lucasgaldinos/arxiv-mcp.git
cd arxiv-mcp-improved

# Install dependencies
uv sync

# Run tests to verify installation
uv run python -m pytest tests/ -v
```

### Basic Usage

```bash
# Start the MCP server
uv run python -m arxiv_mcp

# Run example scripts
uv run python examples/demo_phase_4a_item_1.py
```

## 📚 Documentation Navigation

- **📖 [User Guide](docs/guides/)** - Getting started and usage examples
- **🔧 [API Documentation](docs/api/)** - Technical reference
- **💡 [Examples](examples/)** - Practical usage demonstrations
- **⚙️ [Configuration](config/)** - Setup and configuration options
- **🧪 [Testing](tests/)** - Test suite organization and guidelines
- **🛠️ [Development](.dev/)** - Development workspace and artifacts

## 🏗️ Architecture Principles

### Organization Philosophy

This project follows **"Surgical Organization"** principles:

- **Preserve Working Systems**: Critical cache systems left untouched
- **Clear Separation**: Source, tests, docs, and runtime artifacts organized separately
- **Developer-Friendly**: `.dev/` workspace for all development artifacts
- **Documentation-First**: Every directory has README.md with purpose and guidelines

### Modular Design

- **`src/arxiv_mcp/`**: Modular Python package with clear responsibilities
- **`tests/`**: Organized by test type (unit/integration) for scalability
- **`.dev/`**: All development artifacts isolated from production code
- **`docs/`**: Audience-based documentation (users, developers, API)

## 🔧 Development Workflow

### Testing

```bash
# Run all tests
uv run python -m pytest tests/ -v

# Run specific test categories
uv run python -m pytest tests/unit/ -v      # Fast unit tests
uv run python -m pytest tests/integration/ -v  # Integration tests

# Generate coverage report
uv run python -m pytest tests/ --cov=src --cov-report=html:.dev/build/htmlcov/
```

### Development Tasks

```bash
# View available tasks
uv run python -m scripts.validate_workspace

# Format code
uv run python -m black src/ tests/

# Type checking
uv run python -m mypy src/arxiv_mcp
```

## 📋 Project Standards

### Directory Guidelines

- **Source Code**: All Python code in `src/arxiv_mcp/`
- **Tests**: Mirror source structure in `tests/unit/` and `tests/integration/`
- **Documentation**: Audience-specific in `docs/guides/`, `docs/api/`, etc.
- **Runtime Artifacts**: Development outputs in `.dev/` subdirectories
- **Configuration**: Environment-specific configs in `config/`

### Code Standards

- **Python Style**: Black formatting, type hints required
- **Documentation**: Docstrings for all public functions
- **Testing**: Unit tests for components, integration tests for workflows
- **Error Handling**: Custom exception hierarchy in `exceptions.py`

## 🎯 Contributing

1. **Read the documentation** in `docs/guides/`
2. **Understand the architecture** by exploring `src/README.md`
3. **Follow test patterns** described in `tests/README.md`
4. **Use the development workspace** in `.dev/` for all artifacts
5. **Maintain documentation** - update README.md files when changing structure

## 📊 Project Status

- **Tests**: ✅ 130/130 passing
- **Coverage**: ✅ Comprehensive test coverage
- **Organization**: ✅ Enterprise-grade structure
- **Documentation**: ✅ Complete README.md hierarchy
- **Development Workflow**: ✅ Optimized for productivity

---

*This project demonstrates enterprise-grade Python package organization with comprehensive documentation, testing, and development workflow optimization.*
