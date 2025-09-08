# LaTeX and Markdown Processing Documentation

## Current Capabilities & Planned Features

### ✅ Currently Available
- **LaTeX Processing**: Extract and process LaTeX source files from ArXiv papers
- **Text Extraction**: Basic text extraction from LaTeX files 
- **PDF Compilation**: Compile LaTeX to PDF (optional)
- **Configurable Output**: Output directory configuration (`./output` by default)

### ❌ Currently Missing (Will Implement)
- **File Saving**: Papers are processed in memory but not saved to files
- **LaTeX to Markdown Conversion**: No conversion capability exists
- **YAML Frontmatter**: No metadata extraction to YAML headers
- **Unified Download+Convert**: No tool combining download with format conversion

## Questions & Answers

### 1. Where are the LaTeX papers being outputted?

**Current State**: LaTeX papers are **NOT currently saved to files**. They are only processed in memory and returned as results.

**Configuration**: Output directory is configurable via:
- Config file: `output_directory: "./output"`
- Environment variable: `ARXIV_MCP_OUTPUT_DIRECTORY`
- Default: `./output`

**Implementation Needed**: File saving functionality to actually use the configured output directory.

### 2. What about markdown conversion? Is it reliable/better than pandoc?

**Current State**: **No LaTeX to Markdown conversion exists**.

The current system only has:
- Basic text extraction from LaTeX (removes commands, math environments)
- Markdown generation for API documentation (not paper conversion)

**Implementation Plan**: 
- Create LaTeX to Markdown converter with pandoc integration
- Provide fallback for when pandoc unavailable
- Compare quality with pandoc as reference standard

### 3. Can I get YAML preamble in every markdown output?

**Current State**: **No YAML frontmatter generation**.

**Implementation Plan**: Extract paper metadata and generate YAML frontmatter:
```yaml
---
title: "Paper Title"
authors: ["Author 1", "Author 2"]
arxiv_id: "2301.00001"
categories: ["cs.AI", "cs.LG"]
submitted: "2023-01-01"
abstract: "Paper abstract..."
keywords: ["keyword1", "keyword2"]
---
```

### 4. Is there a download+convert tool outputting to latex and markdown folders?

**Current State**: **No unified download+convert tool exists**.

**Implementation Plan**: Create unified tool that:
- Downloads ArXiv paper
- Extracts LaTeX files → saves to `output/latex/{arxiv_id}/`
- Converts to Markdown → saves to `output/markdown/{arxiv_id}/`
- Generates YAML frontmatter for markdown files
- Provides both formats in organized folder structure

## Implementation Roadmap

### Phase 1: File Saving Infrastructure
- [ ] Implement file saving in pipeline
- [ ] Create output directory structure
- [ ] Save LaTeX files to `latex/` subdirectory

### Phase 2: Markdown Conversion
- [ ] Create LaTeX to Markdown converter
- [ ] Integrate pandoc (optional dependency)
- [ ] Implement fallback conversion
- [ ] Quality comparison with pandoc

### Phase 3: YAML Frontmatter
- [ ] Extract paper metadata (title, authors, categories, etc.)
- [ ] Generate YAML frontmatter
- [ ] Integrate with markdown output

### Phase 4: Unified Download+Convert Tool
- [ ] Create new MCP tool: `download_and_convert`
- [ ] Implement dual output (latex + markdown folders)
- [ ] Add configuration options
- [ ] Comprehensive testing

### Phase 5: Documentation & Examples
- [ ] Update main README.md
- [ ] Create usage examples
- [ ] Document configuration options
- [ ] Add troubleshooting guide

## Future Enhancements
- **Multiple Markdown Flavors**: GitHub, CommonMark, etc.
- **Citation Processing**: Convert LaTeX citations to markdown format
- **Math Rendering**: Handle LaTeX math in markdown (MathJax, KaTeX)
- **Image Handling**: Convert and reference figures appropriately
- **Batch Processing**: Process multiple papers simultaneously
