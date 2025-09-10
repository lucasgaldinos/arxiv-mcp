# ArXiv MCP Server - Documentation Index

## 📁 **Current Active Documents** (Root Level)

### Primary Documentation

- **[README.md](README.md)** - Main project overview and getting started guide
- **[TODO.md](TODO.md)** - **SINGLE SOURCE OF TRUTH** for development priorities and roadmap  
- **[CHANGELOG.md](CHANGELOG.md)** - Version history and release notes
- **[PRODUCTION_STATUS.md](PRODUCTION_STATUS.md)** - Current production validation status

### Project Files

- **[pyproject.toml](pyproject.toml)** - Python project configuration and dependencies
- **[uv.lock](uv.lock)** - Locked dependency versions

---

## 📚 **Technical Documentation** (docs/)

### Current Documentation

- **[docs/LATEX_MARKDOWN_PROCESSING.md](docs/LATEX_MARKDOWN_PROCESSING.md)** - LaTeX to Markdown conversion guide
- **[docs/api/api_documentation.md](docs/api/api_documentation.md)** - API reference and usage examples

### Archived Documentation

- **[docs/archive/september-2025/](docs/archive/september-2025/)** - Historical development reports
  - Contains TODO file history, implementation reports, and completion summaries
  - See [archive README](docs/archive/september-2025/README.md) for details

---

## ⚙️ **Configuration Files**

### GitHub Configuration

- **[.github/copilot-instructions.md](.github/copilot-instructions.md)** - Copilot development guidelines
- **[.github/instructions/](.github/instructions/)** - Development rules and guidelines  
- **[.github/prompts/](.github/prompts/)** - Development prompt templates

### Project Configuration

- **[config/](config/)** - ArXiv MCP server configuration files
  - YAML and JSON configuration examples

---

## 🧪 **Development Files**

### Source Code

- **[src/arxiv_mcp/](src/arxiv_mcp/)** - Main application source code
- **[tests/](tests/)** - Test suite (112 tests, 100% passing)

### Examples

- **[examples/](examples/)** - Usage examples and demos

---

## 📋 **Documentation Standards**

### Current Organization Principles

1. **Root Level**: Only active, current documentation
2. **docs/**: Technical documentation and guides  
3. **docs/archive/**: Historical reports organized by date
4. **Single Source of Truth**: No duplicate TODO or status files

### File Naming Conventions

- **ALL_CAPS.md**: Project-level documents (README, TODO, CHANGELOG)
- **lowercase_with_underscores.md**: Technical documentation
- **CamelCase.md**: Legacy files (being phased out)

### Single Source of Truth Rule

- **Only ONE TODO.md**: Never create multiple TODO files (TODO_MASTER.md, TODO_ENHANCED.md, etc.)
- **Archive Old Versions**: Move superseded TODO files to docs/archive/ with date stamps
- **Clear Ownership**: Each document type should have one authoritative version

---

## 🔄 **Recent Organization Changes** (September 10, 2025)

### Consolidated Files

- Merged 3 TODO files → Single **TODO.md**
- Moved historical summaries → **docs/archive/september-2025/**
- Removed duplicate documentation

### Archived Documents

- `TODO_ENHANCED.md` → Archive (superseded by TODO.md)
- `TODO_REORGANIZED.md` → Archive (superseded by TODO.md)  
- `IMPLEMENTATION_SUMMARY.md` → Archive (historical)
- `COMPLETION_SUMMARY.md` → Archive (historical)
- `TESTING_ENHANCEMENT_SUMMARY.md` → Archive (historical)
- `UPDATE.md` → Archive (historical)

---

## 🎯 **Quick Navigation**

### For Users

- **Getting Started**: [README.md](README.md)
- **Current Status**: [PRODUCTION_STATUS.md](PRODUCTION_STATUS.md)
- **API Reference**: [docs/api/api_documentation.md](docs/api/api_documentation.md)

### For Developers

- **Development Priorities**: [TODO.md](TODO.md)
- **Development Rules**: [.github/copilot-instructions.md](.github/copilot-instructions.md)
- **Test Suite**: [tests/](tests/)

### For Contributors

- **Project History**: [CHANGELOG.md](CHANGELOG.md)
- **Historical Context**: [docs/archive/september-2025/](docs/archive/september-2025/)
- **Configuration**: [config/](config/)

---

*Last Updated: September 10, 2025*  
*Organization Status: ✅ Clean and Consolidated*
