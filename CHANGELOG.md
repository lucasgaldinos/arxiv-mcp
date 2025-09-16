# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- Comprehensive workspace organization enforcement
- Enterprise-grade directory structure with performance-optimized cache placement
- Enhanced development tool configuration with .dev/ structure integration
- Workspace compliance validation with 100% compliance achievement
- Symlinked runtime directories for backward compatibility (logs/ → .dev/runtime/logs/, output/ → .dev/runtime/output/)

### Changed

- **BREAKING**: Moved runtime artifacts to .dev/ structure while preserving performance-critical caches at root level
- Updated all development tools (pytest, mypy, ruff, coverage, rope) to use .dev/build/ cache directories
- Enhanced configuration management with proper cache path handling
- Improved workspace organization following enterprise development standards

### Technical Details

- **Cache Strategy**: Performance-critical application caches remain at root level for optimal access patterns
- **Development Isolation**: Build tools and development artifacts properly isolated in .dev/ structure  
- **Backward Compatibility**: Created symlinks to maintain existing workflow compatibility
- **Tool Integration**: All VS Code tasks properly configured to use `uv run` consistently
- **Compliance**: Achieved 100% workspace compliance according to enterprise standards

### Files Moved

- `logs/` → `.dev/runtime/logs/` (symlinked for compatibility)
- `output/` → `.dev/runtime/output/` (symlinked for compatibility)
- `test_output/` → `.dev/artifacts/test_output/`
- `.ruff_cache/` → `.dev/build/ruff_cache/`
- `.ropeproject/` → `.dev/build/rope_cache/`

### Performance-Critical Files Preserved at Root

- `cache/` - Unified cache systems
- `batch_cache/` - Batch processing cache
- `dependency_cache/` - Dependency tracking cache
- `network_cache/` - Network request cache  
- `notification_cache/` - Notification system cache
- `tag_cache/` - Tag analysis cache

# Changelog

## [2.4.6] - 2025-09-15

### Added

- 🎯 **Comprehensive Markdown Quality Enhancement Pipeline**
  - Created automated quality validation script (`scripts/validate_markdown_quality.py`)
  - Added 8-metric quality scoring system with 0.8 target threshold
  - Implemented document structure enhancement with table of contents generation
  - Added proper heading anchor IDs for better navigation

### Fixed

- 🚫 **Duplicate YAML Frontmatter Issue** - Major quality improvement
  - Eliminated duplicate YAML blocks by detecting pandoc's automatic generation
  - Enhanced existing YAML frontmatter instead of duplicating content
  - Added intelligent merging of pandoc and custom metadata
- 📝 **LaTeX Comment Bleeding** - Enhanced text processing
  - Improved LaTeX comment removal to prevent '%' characters in output
  - Enhanced pre-processing to handle various comment patterns
  - Fixed malformed abstracts with incomplete sentences
- 🔗 **Figure Reference Formatting** - Professional academic presentation
  - Fixed malformed references like `Fig.[\[fig:1\]](#fig:1){reference-type="ref"}`
  - Converted to clean format: `Figure 1`
  - Enhanced table and equation references processing
- 🧹 **Post-Processing Pipeline** - Academic markdown standards
  - Added comprehensive post-processing for pandoc output
  - Implemented figure reference cleaning and normalization
  - Enhanced document structure with professional organization

### Enhanced

- 📊 **Quality Validation System** - Measurable improvement tracking
  - Weighted scoring across 8 quality dimensions
  - Detailed issue identification and reporting
  - Automated pass/fail assessment with configurable thresholds
- 🎨 **Document Structure** - Academic paper organization
  - Automatic table of contents generation for papers with 3+ headings
  - Consistent heading hierarchy with anchor links
  - Enhanced content organization and readability

### Performance

- ✅ **Quality Score Achievement**: Papers with proper structure now achieve 0.8+ quality scores
- 🎯 **Test Results**: 1911.03674 achieved 0.856 score (above 0.8 threshold)
- 📈 **Conversion Success**: 50% pass rate on test corpus with enhanced pipeline

## [0.2.2] - 2024-09-15

### Previous Version

- Established ArXiv MCP server with comprehensive paper processing capabilities
- 144/144 tests passing with full MCP tool integration
- LaTeX to Markdown conversion with quality validation
- Citation network analysis and smart tagging features
- Batch processing and performance optimization

---

**Migration Guide**: If you have local installations, note that `logs/` and `output/` are now symlinks. Your workflows should continue to work without changes, but the actual data is now stored in `.dev/runtime/` for better organization.
