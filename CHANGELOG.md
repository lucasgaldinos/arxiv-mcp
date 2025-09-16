# Changelog# Changelog

All notable changes to this project will be documented in this file.All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),

and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]## [Unreleased]

### Added### Added

- **PDF Support**: Complete PDF file saving functionality for ArXiv papers- Comprehensive workspace organization enforcement

- PDF directory structure in output/pdf/ with organized arxiv_id subdirectories- Enterprise-grade directory structure with performance-optimized cache placement

- save_pdf_file method in FileSaver class for proper PDF persistence- Enhanced development tool configuration with .dev/ structure integration

- PDF papers listing in get_output_structure for directory content tracking- Workspace compliance validation with 100% compliance achievement

- Symlinked runtime directories for backward compatibility (logs/ → .dev/runtime/logs/, output/ → .dev/runtime/output/)

### Fixed

### Changed

- **Critical**: include_pdf parameter now correctly saves PDF files to disk

- **Critical**: Output directory path resolution - files now save to client's working directory instead of MCP server directory- **BREAKING**: Moved runtime artifacts to .dev/ structure while preserving performance-critical caches at root level

- PDF compilation integration - PDF content from pipeline now properly saved when include_pdf=true- Updated all development tools (pytest, mypy, ruff, coverage, rope) to use .dev/build/ cache directories

- Batch operations PDF support - include_pdf parameter working correctly in batch_download_and_convert- Enhanced configuration management with proper cache path handling

- Path resolution for both single and batch download operations using absolute paths- Improved workspace organization following enterprise development standards

### Changed### Technical Details

- FileSaver class now supports PDF files alongside LaTeX, Markdown, and metadata files- **Cache Strategy**: Performance-critical application caches remain at root level for optimal access patterns

- UnifiedDownloadConverter updated to handle PDF saving in download_and_convert workflow- **Development Isolation**: Build tools and development artifacts properly isolated in .dev/ structure  

- Output structure reporting now includes PDF directory information- **Backward Compatibility**: Created symlinks to maintain existing workflow compatibility

- Enhanced error handling for PDF saving operations with detailed logging- **Tool Integration**: All VS Code tasks properly configured to use `uv run` consistently

- **Compliance**: Achieved 100% workspace compliance according to enterprise standards

### Technical Details

### Files Moved

- **PDF Workflow**: Pipeline generates PDF content → FileSaver.save_pdf_file → Organized output/pdf/{arxiv_id}/{arxiv_id}.pdf structure

- **Path Resolution**: Fixed MCP server vs client working directory path resolution using os.getcwd() and absolute paths- `logs/` → `.dev/runtime/logs/` (symlinked for compatibility)

- **Integration**: PDF saving seamlessly integrated into existing LaTeX/Markdown conversion workflow- `output/` → `.dev/runtime/output/` (symlinked for compatibility)

- **Error Handling**: Proper exception handling with fallback to non-PDF operation if PDF compilation fails- `test_output/` → `.dev/artifacts/test_output/`

- `.ruff_cache/` → `.dev/build/ruff_cache/`

## [1.0.0] - 2025-09-16- `.ropeproject/` → `.dev/build/rope_cache/`

### Added### Performance-Critical Files Preserved at Root

- Initial ArXiv MCP server implementation- `cache/` - Unified cache systems

- FastMCP framework integration with 11 ArXiv tools- `batch_cache/` - Batch processing cache

- LaTeX to Markdown conversion with Pandoc- `dependency_cache/` - Dependency tracking cache

- ArXiv paper download and processing pipeline- `network_cache/` - Network request cache  

- Citation extraction and analysis tools- `notification_cache/` - Notification system cache

- Batch processing capabilities- `tag_cache/` - Tag analysis cache

- Comprehensive testing framework

- Documentation and workspace organization# Changelog

### Features## [2.4.6] - 2025-09-15

- Download ArXiv papers (source and compiled PDF)### Added

- Convert LaTeX to Markdown with metadata extraction

- Extract and analyze citations from papers- 🎯 **Comprehensive Markdown Quality Enhancement Pipeline**

- Batch download and convert multiple papers  - Created automated quality validation script (`scripts/validate_markdown_quality.py`)

- Search ArXiv database with advanced filtering  - Added 8-metric quality scoring system with 0.8 target threshold

- Performance metrics and processing analytics  - Implemented document structure enhancement with table of contents generation

- Enhanced cleanup with multi-temporal support  - Added proper heading anchor IDs for better navigation

- Quality validation for conversion output

### Fixed

### Architecture

- 🚫 **Duplicate YAML Frontmatter Issue** - Major quality improvement

- Modular pipeline design with pluggable processors  - Eliminated duplicate YAML blocks by detecting pandoc's automatic generation

- Unified converter for seamless format handling  - Enhanced existing YAML frontmatter instead of duplicating content

- File organization with structured output directories  - Added intelligent merging of pandoc and custom metadata

- Configuration management with production/development profiles- 📝 **LaTeX Comment Bleeding** - Enhanced text processing

- Comprehensive logging and error handling  - Improved LaTeX comment removal to prevent '%' characters in output

- Type-safe implementation with modern Python practices  - Enhanced pre-processing to handle various comment patterns
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
