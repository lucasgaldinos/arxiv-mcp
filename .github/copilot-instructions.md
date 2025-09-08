---
applyTo: '**'
---
# Absolute Rules

**[ABSOLUTE] You shall ALWAYS follow these rules in `copilot_instructions.md`, no matter what. If you find any contradictions, you must ALWAYS follow these rules.**
**[ABSOLUTE] ALWAYS incorporate the rules into the steps you break down.**
**[ABSOLUTE] You shall ALWAYS ALWAYS ALWAYS GUARANTEE THE TOOL IS RUNNING IN PRODUCTION**

- **[MANDATORY-CHECK] You shall ALWAYS use #think tool before executing any complex task requiring multiple steps**
- **[MANDATORY-CHECK] When asked to follow instructions step by step, break down the task into clear steps, selecting the appropriate tools and fallbacks (multiple if needed) from your tool list for each step.**
  - [MANDATORY-READ] **The available tools are in `/home/lucas_galdino/repositories/mcp_servers/arxiv-mcp-improved/.github/.knowledge_base/0-tool_usage/1-simple_tool_list.md`[folder](../.knowledge_base/0-tool_usage).**
  - [MANDATORY-READ] **You will also find more information about each tool in `/home/lucas_galdino/repositories/mcp_servers/arxiv-mcp-improved/.github/.knowledge_base/0-tool_usage/tools_and_mcps.md`[folder](.knowledge_base/0-tool_usage).**
- **[MANDATORY] ALWAYS prefer tools that are specialized for the task at hand, rather tha general-purpose tools.**
- **[MANDATORY] You are obliged to #think and `optimize tool selection`[^1] before executing any task where tools are not explictly set.**
- **[MANDATORY] ALWAYS break the task down into clear steps, selecting the appropriate tools and fallbacks (multiple if needed) from your tool list for each step before executing.**
- **[MANDATORY] When there are steps already broken, you must follow them, unless:
  - **[MANDATORY-CHECK] absurd ordering.**
  - **[MANDATORY-CHECK] user didn't organized**
    - in a logical way (e.g. `<ol>`).
    - explictly said "Follow these exact steps" `<ul>` or semantical ordering from prompt.
- NEVER use keep files with `fixed` or `final` as names. There's no such thing. Substitute the old ones with `_backup_v{n}`.
- [MANDATORY] You shall set appropriate timeouts when testing or other fallback mechanism.
- [MANDATORY] You shall ALWAYS validate your outputs, specially when generating code or documentation. NEVER assume your first output is correct.
- [MANDATORY] You shall ALWAYS follow best practices for code and documentation generation.
- [MANDATORY] You shall update or create `CHANGELOG.md` or `UPDATE.md` files with a summary of changes made.
- [MANDATORY] You shall update or create `TODO.md` or `IMPROVEMENTS.md` files with a summary of planned improvements.
- [MANDATORY] You shall ALWAYS follow the knowledge base organization principles when creating or updating documentation inside `./.github/.knowledge_base/`.
- **[MANDATORY-CHECK] WHEN necessary, recall your prompts, summarize conversations.**
- **[MANDATORY] ALWAYS optimize tool selection (and it's fallback) after thinking and initializing a task.**
- **[MANDATORY] ALWAYS update docs over changes made.**
  - **[MANDATORY-CHECK] ALWAYS update docs with accurate information.**
  - **[MANDATORY] ALWAYS analyze the contents hierarchy and structure.**
- **[MANDATORY-CHECK] ALWAYS check #memory after a few iterations**
  - **[MANDATORY] ALWAYS create proper observations.**
  - **[MANDATORY] ALWAYS create proper relations.**
  - **[MANDATORY] ALWAYS create proper entities where due.**
  - **[MANDATORY] WHEN necessary, recall your memories (read_graph).**
- **[MANDATORY] look for informations on the internet when necessary.**
- **[MANDATORY] You shall NEVER make "tests to pass" without proper validation. TESTS ARE MADE TO FAIL, not to pass, unless specific for the methodology. But test should really cover what they're supposed to cover.**

  With "proper" meaning you have to analyze, specially your current conversation.
- **[MANDATORY-CHECK] follow good design patterns and principles.**
- **[MANDATORY-CHECK] follow good architectural styles WHEN they are NEEDED.**
- **[MANDATORY-CHECK] follow good system design principles.**
- **[MANDATORY] Always output your step-by-step reasoning in the chat or create #memory entities for it and add observation from then on, while creating relations as well.**
  - **[MANDATORY-CHECK] You shall ALWAYS preselect tools and their fallbacks inside this reasoning.**
- **[MANDATORY] Remember to test using appropriate test suites and automated tests.**
  - [MANDATORY-VHECK] #pylanceRunCodeSnippet or #runTests
  - [MANDATORY-VHECK] pylance_mcp and built in has bunch of test suites.
  - [MANDATORY-VHECK] the usage of tasks is also welcome.

# Conditional rules

- When analyzing code, ALWAYS check for:
  - [MANDATORY-CHECK] If there are any `UPDATE.md`, `CHANGELOG.md`, or similar files in the repository, you must update them with a summary of changes made. If there aren't, create one. NEVER keep creating new changelogs.
  - If there is any `TODO.md`, `IMPROVEMENTS.MD` or similar containing the specs, phase or anything like it, Update them.If there aren't, create one. NEVER keep creating new changelogs.
- [MANDATORY] python should always be used with uv
- [MANDATORY] use typescript instead of javascript when possible
- [MANDATORY] use async/await (aiohttp/httpx in python) when possible
