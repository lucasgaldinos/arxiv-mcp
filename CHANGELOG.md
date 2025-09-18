# Changelog

## [Unreleased]

### Added (Major Improvements – 2025-09-17)

- Complete overhaul of ArXiv paper processing pipeline (systematic processing improvements)
- Paper-name–centric directory structure `{paper-name}/{latex,markdown,pdf,metadata}/`
  - Intelligent paper directory naming from metadata (e.g. `ashish-attention-all-you-need-1706/`)
  - Human-readable author–title–year patterns
  - Proper preservation of nested subdirectories (Figures/, vis/, etc.)
- Enhanced gzip/tar archive handling with native `application/gzip` detection & extraction
- Content-Type validation distinguishing LaTeX source vs PDF-only papers
- Robust error recovery (exponential backoff retries, fallback extraction strategies, multi-strategy main TeX detection)
- Intelligent filename generation (author-title-year-field kebab case)
- Workspace path resolver & intelligent naming integration across FileSaver / FastMCP tools
- PDF support: end-to-end saving, organized output structure, batch integration
- Symlinked runtime directories (`logs/`, `output/`) to `.dev/runtime/` for backward compatibility
- Enterprise workspace organization enforcement (100% compliance achieved)
- Markdown quality enhancement pipeline (8-metric scoring + TOC generation)

### Fixed

- Root cause: gzip handling errors ("not a gzip file") – resolved; success on complex multi-file papers
- Folder structure redesign (legacy `{format}/{arxiv_id}/` → new paper-centric layout)
- Automatic creation of nested extraction directories (Figures/, vis/)
- LaTeX→Markdown converter metadata passing & method integration
- Path resolution errors (eliminated absolute server path usage; now workspace-relative)
- include_pdf parameter reliably persists PDFs (single & batch operations)
- Batch PDF saving and structure reporting in `get_output_structure`
- Documentation broken links (README.md, TASKS.md, PROJECT_ROOT.md) fixed
- Duplicate / outdated TODO.md sections removed
- VS Code MCP configuration conflicts resolved (Phase 4 deployment)
- PDF saving fallback logic (graceful degradation when compilation fails)

### Changed

- BREAKING: Runtime artifacts relocated into `.dev/` (with symlinks) while performance-critical caches remain at root
- FileSaver enhanced: supports intelligent naming & PDF files
- UnifiedDownloadConverter extended for PDF saving workflow
- Output structure now includes PDF directory info & intelligent names
- Development tools (pytest, mypy, ruff, coverage, rope) configured to use `.dev/build/` caches
- Improved configuration & cache path management for enterprise standards
- File naming upgraded (e.g. `2412.08992v1.pdf` → `kandula-benchmarking-gpu-optimized-quantum-2024-ai.pdf`)

### Technical / Infrastructure

- WorkspacePathResolver & FilenameGenerator foundational utilities
- Comprehensive workspace compliance validation tooling
- Error handling standardized with explicit logging & observable failures
- PDF workflow: pipeline → FileSaver.save_pdf_file → structured output/pdf/{arxiv_id}/{arxiv_id}.pdf
- Symlink strategy enables legacy path compatibility without structural regressions
- Centralized cache strategy (root-level performance caches vs `.dev/` development artifacts)
- All VS Code tasks normalized to `uv run` environment pattern

### Directory Structure Changes

- `logs/` → `.dev/runtime/logs/` (symlink)
- `output/` → `.dev/runtime/output/` (symlink)
- `test_output/` → `.dev/artifacts/test_output/`
- `.ruff_cache/` → `.dev/build/ruff_cache/`
- `.ropeproject/` → `.dev/build/rope_cache/`

### Performance-Critical Caches (Remain at Root)

- `cache/`, `batch_cache/`, `dependency_cache/`, `network_cache/`, `notification_cache/`, `tag_cache/`

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/) and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
