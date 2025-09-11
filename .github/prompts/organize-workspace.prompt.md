---
mode: agent
name: organize-workspace
description: Organize the workspace following best practices.
---

#think You must break this process step by step, explictly preselecting tools use [#file:0-tool_usage](../../infrastructure/0-tool_usage).

1. Familiarize yourself with this codebase (`tree -a`).
   - look for loose files, misplaced files, inconsistent naming conventions, etc.
2. Read [#file:workspace-organization-best-practices.md](../../infrastructure/folder-organization/workspace-organization-best-practices.md)
3. create 3 Tree of thoughts (ToT) and for each of them a Chain of thought.
   - Identify the specific folders that deviate from the best practices outlined in the document.
   - Create a plan to refactor these folders to align with the best practices.
   - Implement the changes and reensure it is correct as expected.
4. **Ask me which one I prefer BEFORE PROCEEDING**.
5. Define the ultimate folder structure and naming conventions to be used. Define it in the README.md file. from the main repo.
6. Apply them to all folders.

   You must:
   - rename folders
   - move files if necessary
   - define a main instruction (as in `/home/lucas_galdino/Documents/StudiesVault_v2/AI-knowledge-base/main-knowledge-base/.github/instructions`) for each folder.
