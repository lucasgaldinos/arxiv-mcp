---
description: "This instruction file contains absolute rules that must always be followed for testing in this workspace."
applyTo: '**/{test,tests,__tests__}/**/*test*.*'
---

# Absolute Rules

**[ABSOLUTE] You shall ALWAYS provide clear and concise instructions.**
**[ABSOLUTE] You shall ALWAYS validate generated code with tests.**
**[ABSOLUTE] You shall ALWAYS handle errors gracefully.**

# Production Testing Requirements

**[ABSOLUTE] You shall ALWAYS ensure production testing before deployment.**
**[ABSOLUTE] You shall ALWAYS test MCP server functionality with inline chat integration.**
**[ABSOLUTE] You shall ALWAYS create development branches for production-like testing.**
**[ABSOLUTE] You shall ALWAYS validate MCP tool functionality in realistic client environments.**

## Production Testing Checklist

### MCP Server Integration Testing
- **[MANDATORY] Test all MCP tools with actual MCP client (e.g., Claude Desktop, VS Code with MCP)**
- **[MANDATORY] Validate inline chat functionality and tool responses**
- **[MANDATORY] Test error handling in client-server communication**
- **[MANDATORY] Verify tool parameter validation and response formatting**

### Development Branch Testing Protocol
- **[MANDATORY] Create dedicated development branch for production testing**
- **[MANDATORY] Test with real ArXiv paper IDs and actual network requests**
- **[MANDATORY] Validate full workflow from search to download to conversion**
- **[MANDATORY] Test concurrent operations and rate limiting**

### Client Environment Validation
- **[MANDATORY] Test MCP server startup and tool registration**
- **[MANDATORY] Validate tool descriptions and parameter schemas**
- **[MANDATORY] Test error scenarios and graceful degradation**
- **[MANDATORY] Verify performance under realistic load conditions**

## Production Testing Infrastructure

### Required Test Suites
1. **Unit Tests**: Core functionality validation (must pass 100%)
2. **MCP Server Integration Tests**: Tool registration and direct invocation
3. **Inline Chat Integration Tests**: Client-like interaction simulation
4. **End-to-End Production Tests**: Complete workflow validation

### Test Environment Setup
- **[MANDATORY] Use `.dev/production_tests/` directory for production test infrastructure**
- **[MANDATORY] Maintain separate test results and reports**
- **[MANDATORY] Include performance benchmarks and success rate tracking**
- **[MANDATORY] Document test scenarios covering normal and edge cases**

### Production Readiness Criteria
- **[MANDATORY] 100% unit test pass rate**
- **[MANDATORY] 100% MCP server integration test pass rate**
- **[MANDATORY] 100% inline chat integration test pass rate**
- **[MANDATORY] All production workflows complete successfully**
- **[MANDATORY] Error handling validated for all failure modes**
- **[MANDATORY] Performance benchmarks within acceptable limits**

### Pre-Deployment Validation
- **[MANDATORY] Run comprehensive production test suite**
- **[MANDATORY] Generate production readiness report**
- **[MANDATORY] Validate with actual MCP client environment**
- **[MANDATORY] Test with development branch configuration**

**[ABSOLUTE] NO CODE SHALL BE CONSIDERED PRODUCTION-READY WITHOUT PASSING ALL PRODUCTION TESTS.**

## Branch-Specific Testing Requirements

### Development Branch Testing (arxiv-dev-mcp)
- **[MANDATORY] Test MCP server configuration in development environment**
- **[MANDATORY] Validate tool functionality with development-specific settings**
- **[MANDATORY] Test integration with actual MCP clients (Claude Desktop, VS Code)**
- **[MANDATORY] Verify inline chat functionality works seamlessly**
- **[MANDATORY] Test error recovery and graceful degradation**

### Production Branch Testing
- **[MANDATORY] Full regression test suite before merge**
- **[MANDATORY] Performance validation under production load**
- **[MANDATORY] Security and stability validation**
- **[MANDATORY] Documentation and configuration validation**
