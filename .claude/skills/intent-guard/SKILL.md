---
name: intent-sync
description: Agent Coordination Protocol - Acquires a file lease before modifying code to prevent conflicts with other autonomous agents or developers.
---

# Intent Sync Coordination

You are operating in a multi-agent environment. BEFORE executing any file-modifying actions (`Write`, `Edit`, `Replace`, `Patch`, `Delete`), you MUST acquire a lease from the coordination server.

## Workflow

1. **Identify Target Files**: Determine exactly which files you need to modify.
2. **Formulate Intent**: Create a concise, 1-sentence description of your task (e.g., "Refactor JWT auth middleware").
3. **Acquire Lease**: Run the CLI tool to acquire the lock:
   ```bash
   python -m cli.main acquire --files "file1.py,file2.py" --intent "Description of task"

 * Evaluate Response:
   * If ALLOWED: Note the intent_id provided in the output. Proceed with your file modifications.
   * If CONFLICT: Stop immediately. Read the CLI output to see which agent is working on the files. Ask the user how to proceed or wait.
 * Release Lease: Once your code generation or refactoring is COMPLETE and saved (or committed), you MUST release the lock using the ID you received:
   python -m cli.main release <intent_id>

Do not bypass this process. It guarantees codebase integrity.

