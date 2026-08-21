---
name: intent-guard
description: Prevents code collisions and AI overwrites by checking team intent and uncommitted local changes before modifying files.
---

# AI Intent Guard

Use this skill BEFORE executing any file-modifying actions (`Write`, `Edit`, `Replace`, `Patch`) or making multi-file structural changes to ensure no teammates are currently editing the same modules.

## When to Activate

* Automatically before modifying, refactoring, or creating any code file in the repository.
* When executing multi-file refactoring tasks or complex feature updates.

## Execution Workflow

1. Identify the primary file path being targeted for changes.
2. Formulate a 1-sentence summary of the intended code modification.
3. Run the interceptor script via CLI before calling any file-writing tools:

```bash
python intent_interceptor.py --dev-id "$DEV_ID" --prompt "DESCRIPTION_OF_CHANGE" --target "PATH_TO_FILE"

Response Handling
 * If Execution is ALLOWED: Proceed immediately with the code generation and file modifications.
 * If Execution is BLOCKED: Halt file-writing tools immediately. Inform the user that another teammate is currently working on the target file, display the conflicting developer's ID, and request manual confirmation before proceeding.

