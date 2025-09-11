# TODO - ArXiv MCP Server

## 🎯 Project Mission

**Simple MCP server for ArXiv paper fetching with LaTeX-to-Markdown conversion**

- Primary: Download ArXiv papers (.tex files preferred, PDF fallback)
  - must download to specified output directory.
- Secondary: Convert to Markdown for easy consumption
  - using pandoc might be an option. Should explore best LATEX to markdown conversion tools.
- Scope: Focus on core functionality, avoid feature creep

---

## 🔥 Critical Priorities (Must Fix)

### ❌ Blocking Issues

- [ ] **Papers not being saved to files** ⚠️
  - Papers processed in memory but NOT saved to configured output directory (`{$current_workspace_folder}/output/{latex,markdown,pdf,metadata}/`)
  - Fix file persistence in ArxivPipeline
  - **Priority**: URGENT - core functionality broken
  - **Estimate**: 2-4 hours

### 🧪 Testing Quality

- [ ] **Fix mock test failures** (8/143 tests failing)
  - Async/await compatibility issues in test_arxiv_api_comprehensive.py
  - Mock configuration problems causing test hangs
  - **Priority**: HIGH - testing infrastructure broken  
  - **Estimate**: 4-6 hours

---

## 🎯 High Priority (Core Features)

### 📁 File Management & Output

- [ ] **Output directory organization**
  - Structured saving: `output/{latex,markdown,metadata}/`
  - File naming conventions
  - **Success criteria**: Papers saved to disk with proper structure
  - **Estimate**: 4-6 hours

- [ ] **Enhanced LaTeX processing**
  - Better .tex file extraction and cleaning
  - Improve conversion quality
  - **Success criteria**: 90%+ successful LaTeX→Markdown conversion
  - **Estimate**: 8-12 hours

### 🔍 Core API Features

- [ ] **ArXiv search improvements**
  - Better query handling and filters
  - Result pagination
  - **Success criteria**: Reliable search with 10+ results per query
  - **Estimate**: 6-8 hours

- [ ] **Error handling & recovery**
  - Graceful fallbacks (LaTeX→PDF→Text)
  - Better error messages
  - **Success criteria**: <5% unhandled errors
  - **Estimate**: 4-6 hours

---

## 📈 Medium Priority (Quality & Polish)

### 🧹 Code Quality

- [ ] **Documentation updates**
  - Update README with current features
  - API documentation
  - **Estimate**: 2-4 hours

- [ ] **Type safety**
  - Complete Pydantic v2 integration
  - Type hint coverage >90%
  - **Estimate**: 6-8 hours

### ⚡ Performance

- [ ] **Batch processing**
  - Process multiple papers concurrently
  - Progress tracking
  - **Estimate**: 6-10 hours

- [ ] **Caching improvements**
  - SQLite persistence for metadata
  - Cache invalidation strategy
  - **Estimate**: 4-6 hours

---

## 🔧 Low Priority (Future Enhancements)

### 🎨 User Experience

- [ ] **Configuration validation**
  - Startup checks with helpful errors
  - **Estimate**: 2-3 hours

- [ ] **Progress indicators**
  - Real-time processing feedback
  - **Estimate**: 3-4 hours

### 📊 Analytics (Optional)

- [ ] **Basic usage tracking**
  - Search patterns, popular papers
  - **Estimate**: 4-6 hours

---

## ✅ Completed Features

### v2.1.0 Achievements

- ✅ **Comprehensive testing infrastructure** (127/127 core tests passing)
- ✅ **VS Code Testing UI integration** with debug support
- ✅ **Real ArXiv API integration** with proper search functionality
- ✅ **LaTeX-to-Markdown conversion pipeline** (FileSaver, LaTeXToMarkdownConverter)
- ✅ **Enhanced error handling** with custom exception hierarchy
- ✅ **Optional dependencies framework** with graceful fallbacks
- ✅ **MCP tools integration** (10 functional tools)
- ✅ **Citation parsing system** with multiple format support

### v2.0.0 Foundation

- ✅ **Modular architecture** (core/, processors/, clients/, utils/)
- ✅ **Configuration management** with YAML/JSON support
- ✅ **Async processing pipeline** with resource management
- ✅ **Logging and metrics** with structured output

---

## 🚫 Deliberately Excluded (Scope Management)

### ❌ Machine Learning Features

- Automatic classification, semantic analysis, AI summarization
- **Reason**: Adds complexity, maintenance burden, external dependencies
- **Alternative**: Focus on reliable document processing

### ❌ Multi-User Features  

- Collaboration, shared workspaces, user management
- **Reason**: Simple tool should remain simple
- **Alternative**: Individual user focus

### ❌ Advanced Analytics

- Complex trending analysis, social features
- **Reason**: Core mission is document fetching, not analytics platform
- **Alternative**: Basic usage tracking only

---

## 📋 Success Metrics

### Core Functionality (MUST HAVE)

- [ ] Papers successfully saved to output directory: 95%+
- [ ] LaTeX→Markdown conversion success: 85%+
- [ ] API search reliability: 99%+
- [ ] Test suite passing: 100%

### Quality Targets (SHOULD HAVE)

- [ ] Type hint coverage: 90%+
- [ ] Documentation coverage: 100% of public APIs
- [ ] Error handling: <5% unhandled exceptions
- [ ] Performance: <30s per paper processing

### User Experience (NICE TO HAVE)

- [ ] Clear error messages for all failure modes
- [ ] Progress indication for long operations
- [ ] Simple configuration with validation

---

## 🗓️ Timeline Estimates

### Sprint 1 (1-2 weeks) - Critical Fixes

- Fix file saving issues (URGENT)
- Resolve test failures
- **Deliverable**: Working core functionality

### Sprint 2 (2-3 weeks) - Quality & Features  

- Output organization improvements
- Enhanced LaTeX processing
- **Deliverable**: Production-ready v2.2.0

### Sprint 3 (3-4 weeks) - Polish & Performance

- Code quality improvements
- Performance optimizations
- **Deliverable**: Stable v2.3.0

---

## 📝 Definition of Done

### Feature Complete

- [ ] Implementation finished
- [ ] Tests written and passing
- [ ] Documentation updated
- [ ] No regressions introduced

### Quality Gates

- [ ] Type hints added
- [ ] Error handling implemented
- [ ] Performance acceptable (<30s per paper)
- [ ] User feedback incorporated

---

*Last updated: January 2025*
*Focus: Simple, reliable ArXiv paper fetching with LaTeX-to-Markdown conversion*
