---
mode: [agent, ask]
description: Help fix the code in the current commit based on the context searched.
---
For every next task, you'll break them down into smaller steps, and for each step, you shall make a preselection of the agent tools you'll use.

# Rules

- #think you MUST prefer to use search speciaized tools (#websearch, githubRepo, deepwiki) rather than your own fix when you have a bug to fix. **This rule is ABSOLUTELY MANDATORY**.

# Tasks

- #think you shall guarantee every tool of the mcp in this repo works, while adhering to best softeares best practices and patterns.
- #think you shall not introduce any new feature, only fix the existing code.
- #think you shall not break any existing functionality.
- #think you shall read our `pyproject`
- #think you shall only fix the existing code.
- #think you shall update docs and changelog
- #think you shall remove any unused code, docs and other artefacts.
- #think you shall fix any broken tests.
- #think you shall fix any broken linter or type checker issues.
