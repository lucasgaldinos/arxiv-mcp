# Changelog

## [Unreleased]

### Added - DOCUMENTATION RESTRUCTURING (September 18, 2025)

- **📚 COMPREHENSIVE DOCUMENTATION OVERHAUL**: Complete restructuring of project documentation for clarity and enterprise compliance
- **TODO.md Streamlined**: Removed duplication, focused on active sprint objectives with clear success criteria
  - Consolidated 5 high-priority objectives: Code Quality, Conversion Quality, Pre-commit Gates, Documentation Lint, Test Enhancements
  - Added quantified metrics table with current vs target values
  - Established release quality gates with measurable criteria
- **TASKS.md Rationalized**: Transformed verbose implementation plans into structured execution roadmap
  - Compressed historical sections while preserving audit trails
  - Added success criteria tables with validation methods
  - Converted bold pseudo-headings to proper markdown headings for better navigation
- **Markdown Compliance**: Fixed all MD022/MD032/MD036/MD058 lint violations across documentation
  - Proper blank lines around headings and lists
  - Tables surrounded by blank lines
  - Consistent heading hierarchy

### Added - MAJOR IMPROVEMENTS (September 17, 2025)

- **🎯 SYSTEMATIC PROCESSING IMPROVEMENTS**: Complete overhaul of ArXiv paper processing pipeline
- **Paper-Name-Centric Directory Structure**: Implemented `{paper-name}/{latex,markdown,pdf,metadata}/` organization as requested
  - Intelligent paper directory naming from metadata: `ashish-attention-all-you-need-1706/`
  - Human-readable folder names using author-title-year patterns
  - Proper subdirectory handling for complex paper structures (Figures/, vis/, etc.)
- **Enhanced Gzip Archive Handling**: Fixed LaTeXProcessor to properly handle ArXiv's gzip-compressed tar archives
  - Native gzip decompression support for `application/gzip` content type
  - Comprehensive format detection and extraction strategies
  - Successfully processes complex papers like "Attention is All You Need" (23 files extracted)
- **Content-Type Validation**: Enhanced AsyncArxivDownloader with HTTP header validation
  - Distinguishes between `application/gzip` (LaTeX source) vs `application/pdf` (PDF-only papers)
  - Intelligent handling of different ArXiv content formats
- **Robust Error Recovery**: Comprehensive retry and fallback mechanisms
  - Exponential backoff retry logic (max 3 attempts)
  - Fallback extraction strategies for problematic archives
  - Enhanced main TeX file detection with multiple strategies

### Added

- **Intelligent Filename Generation**: Author-title-year-field kebab-case naming for downloaded papers
- **Workspace Path Resolution**: VS Code workspace-relative path handling for proper integration
- FilenameGenerator class for human-readable, descriptive file naming from ArXiv metadata
- WorkspacePathResolver singleton for detecting and resolving workspace-relative paths
- Intelligent naming integration in FileSaver with backward compatibility
- Enhanced file organization with contextual, searchable filenames

### Fixed - CRITICAL IMPROVEMENTS

- **🔧 ROOT CAUSE FIX**: LaTeXProcessor gzip handling - resolved "not a gzip file" errors affecting 47% of papers
- **🗂️ FOLDER STRUCTURE**: Complete redesign from `{format}/{arxiv_id}/` to `{paper-name}/{latex,markdown,pdf,metadata}/`
- **📁 SUBDIRECTORY SUPPORT**: Automatic creation of nested directories (Figures/, vis/) during file extraction
- **🔄 METHOD INTEGRATION**: Fixed LaTeXToMarkdownConverter method calls and metadata passing
- **Bug Fix (arxiv-mcp-0)**: Downloads no longer use absolute paths from MCP server location
- **Naming Convention**: Files now use intelligent names instead of raw ArXiv IDs
- **VS Code Integration**: Proper workspace detection and relative path resolution
- Path resolution in FastMCP tools to use workspace resolver instead of os.getcwd() changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- **Intelligent Filename Generation**: Author-title-year-field kebab-case naming for downloaded papers
- **Workspace Path Resolution**: VS Code workspace-relative path handling for proper integration
- FilenameGenerator class for human-readable, descriptive file naming from ArXiv metadata
- WorkspacePathResolver singleton for detecting and resolving workspace-relative paths
- Intelligent naming integration in FileSaver with backward compatibility
- Enhanced file organization with contextual, searchable filenames

### Fixed

- **Bug Fix (arxiv-mcp-0)**: Downloads no longer use absolute paths from MCP server location
- **Naming Convention**: Files now use intelligent names instead of raw ArXiv IDs
- **VS Code Integration**: Proper workspace detection and relative path resolution
- Path resolution in FastMCP tools to use workspace-relative directories

### Changed

- FileSaver class now supports `use_intelligent_naming` parameter for enhanced file naming
- FastMCP tools updated to use workspace resolver instead of os.getcwd()
- File naming behavior upgraded from `2412.08992v1.pdf` to `kandula-benchmarking-gpu-optimized-quantum-2024-ai.pdf`

### Technical

- **PDF Support**: Complete PDF file saving functionality for ArXiv papers
- PDF directory structure in output/pdf/ with organized arxiv_id subdirectories
- save_pdf_file method in FileSaver class for proper PDF persistence
- PDF papers listing in get_output_structure for directory content tracking
- Comprehensive workspace organization enforcement
- Enterprise-grade directory structure with performance-optimized cache placement
- Enhanced development tool configuration with .dev/ structure integration
- Workspace compliance validation with 100% compliance achievement
- Symlinked runtime directories for backward compatibility (logs/ → .dev/runtime/logs/, output/ → .dev/runtime/output/)

### Fixed

- **CRITICAL**: include_pdf parameter now correctly saves PDF files to disk
- **CRITICAL**: Output directory path resolution - files now save to client's working directory instead of MCP server directory
- PDF compilation integration - PDF content from pipeline now properly saved when include_pdf=true
- Batch operations PDF support - include_pdf parameter working correctly in batch_download_and_convert
- Path resolution for both single and batch download operations using absolute paths
- **Phase 4 Production Deployment**: VS Code MCP configuration updated to prevent git conflicts
- **Documentation**: Fixed broken links in README.md, TASKS.md, and PROJECT_ROOT.md
- **TODO.md**: Cleaned duplicate headers, encoding issues, and outdated content

### Changed

- **BREAKING**: Moved runtime artifacts to .dev/ structure while preserving performance-critical caches at root level
- FileSaver class now supports PDF files alongside LaTeX, Markdown, and metadata files
- UnifiedDownloadConverter updated to handle PDF saving in download_and_convert workflow
- Output structure reporting now includes PDF directory information
- Enhanced error handling for PDF saving operations with detailed logging
- Updated all development tools (pytest, mypy, ruff, coverage, rope) to use .dev/build/ cache directories
- Enhanced configuration management with proper cache path handling
- Improved workspace organization following enterprise development standards

### Technical Details

### Files Moved

- **PDF Workflow**: Pipeline generates PDF content → FileSaver.save_pdf_file → Organized output/pdf/{arxiv_id}/{arxiv_id}.pdf structure

- **Cache Strategy**: Performance-critical application caches remain at root level for optimal access patterns
- **Development Isolation**: Build tools and development artifacts properly isolated in .dev/ structure  
- **Backward Compatibility**: Created symlinks to maintain existing workflow compatibility
- **Tool Integration**: All VS Code tasks properly configured to use `uv run` consistently
- **Compliance**: Achieved 100% workspace compliance according to enterprise standards
- **Path Resolution**: Fixed MCP server vs client working directory path resolution using os.getcwd() and absolute paths
- **Integration**: PDF saving seamlessly integrated into existing LaTeX/Markdown conversion workflow
- **Error Handling**: Proper exception handling with fallback to non-PDF operation if PDF compilation fails
- **Phase 4 Achievement**: All 11 MCP tools operational in production deployment

### Directory Structure Changes

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

## [1.0.0] - 2025-09-16

### Added

- Initial ArXiv MCP server implementation
- FastMCP framework integration with 11 ArXiv tools
- LaTeX to Markdown conversion with Pandoc
- ArXiv paper download and processing pipeline
- Citation extraction and analysis tools
- Batch processing capabilities
- Comprehensive testing framework
- Documentation and workspace organization

### Features

- Download ArXiv papers (source and compiled PDF)
- Convert LaTeX to Markdown with metadata extraction
- Extract and analyze citations from papers
- Batch download and convert multiple papers  
- Search ArXiv database with advanced filtering  
- Performance metrics and processing analytics  
- Enhanced cleanup with multi-temporal support  
- Quality validation for conversion output

### Architecture

- Modular pipeline design with pluggable processors  
- Unified converter for seamless format handling  
- File organization with structured output directories  
- Configuration management with production/development profiles
- Comprehensive logging and error handling  
- Type-safe implementation with modern Python practices  

## [0.2.2] - 2024-09-15

### Previous Version

- Established ArXiv MCP server with comprehensive paper processing capabilities
- 144/144 tests passing with full MCP tool integration
- LaTeX to Markdown conversion with quality validation
- Citation network analysis and smart tagging features
- Batch processing and performance optimization

---

**Migration Guide**: If you have local installations, note that `logs/` and `output/` are now symlinks. Your workflows should continue to work without changes, but the actual data is now stored in `.dev/runtime/` for better organization.
