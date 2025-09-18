# ArXiv MCP Server Documentation

Welcome to the documentation for the ArXiv MCP Server. This documentation is organized using the Diátaxis framework, which separates content into four distinct categories:

- **[Tutorials](./tutorials/)**: Learning-oriented lessons for beginners.
- **[How-To Guides](./how-to-guides/)**: Goal-oriented steps to solve a specific problem.
- **[Reference](./reference/)**: Technical descriptions of the machinery.
- **[Explanation](./explanation/)**: Big-picture understanding and concepts.

## Getting Started

If you are new to the project, we recommend starting with the [Getting Started](./tutorials/1_getting_started.md) tutorial.

## Legacy Documentation

Archived and outdated documentation can be found in the [legacy](./legacy/) directory.

# Documentation

This directory contains all project documentation, organized by audience and purpose.

## 📁 Documentation Structure

```text
docs/
├── api/                    # API documentation and references
├── archive/                # Historical documentation and decisions
├── guides/                 # User and developer guides
├── examples/               # Usage examples and tutorials
├── specifications/         # Technical specifications
├── README.md              # This file
└── *.md                   # Top-level documentation files
```text

## 📚 Documentation Categories

### Current Files

- **`LATEX_MARKDOWN_PROCESSING.md`**: LaTeX to Markdown conversion guide
- **`WORKSPACE_CLEANUP_SUMMARY.md`**: Workspace organization history
- **`WORKSPACE_ENFORCEMENT_GUIDE.md`**: Organization compliance guide
- **`directory-analysis-2025-09-11.md`**: Directory structure analysis
- **`workspace-analysis-2025-09-11.md`**: Comprehensive workspace analysis
- **`workspace-reorganization-plan.md`**: Reorganization implementation plan

### Planned Structure

#### `api/` - API Documentation

- OpenAPI specifications
- Tool function references
- Integration guides
- Response schemas

#### `guides/` - User Documentation

- Getting started guide
- Configuration guide
- Troubleshooting guide
- Best practices

#### `examples/` - Usage Examples

- Common use cases
- Integration examples
- Code samples
- Tutorials

#### `specifications/` - Technical Specs

- Architecture decisions
- Protocol specifications
- Data formats
- Performance requirements

## 🎯 Documentation Standards

### Writing Guidelines

- **Audience-first**: Write for the intended reader
- **Clarity**: Use clear, concise language
- **Examples**: Include practical examples
- **Maintenance**: Keep documentation current with code

### File Naming

- Use descriptive, lowercase names with hyphens
- Include purpose: `user-guide.md`, `api-reference.md`
- Version when needed: `migration-v2-to-v3.md`

### Content Structure

```markdown
# Title

Brief description of purpose and scope.

## Overview

High-level explanation...

## Sections

Detailed content...

## Examples

Practical usage examples...

## References

Links to related documentation...
```text

## 🔧 Maintenance

### Regular Updates

- Review documentation quarterly
- Update examples with code changes
- Archive outdated information
- Validate external links

### Review Process

1. **Technical accuracy**: Verify with code
1. **Clarity**: Get feedback from users
1. **Completeness**: Check all scenarios covered
1. **Currency**: Ensure information is up-to-date

---

_Good documentation is code. It should be versioned, reviewed, and maintained with the same rigor as source code._
