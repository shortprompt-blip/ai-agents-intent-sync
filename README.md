# 🛡️ AI Agents Intent Sync (V2)

**Agent Coordination Protocol for Multi-Agent Workflows**

`ai-agents-intent-sync` is a coordination layer that lets autonomous coding agents (Claude Code, Cursor, Windsurf, Codex) safely work in parallel on the same codebase without stepping on each other's toes.

Unlike traditional git-conflict tools that act *after* the code is written, this system uses an **Intent Lease Engine** to coordinate agents *before* they generate or overwrite local files.

## 🧠 The Concept: Intent Leases

Agents do not talk to each other directly. They talk to a central coordination server.
Before starting a task, an agent registers an *intent* (a lease):

1. **Acquire:** Agent requests to modify `src/auth.py`.
2. **Evaluate:** Server's Conflict Engine determines if overlapping operations exist based on a deterministic policy matrix and directory hierarchy.
3. **Lock/TTL:** If allowed, the lease is granted with a Time-To-Live (TTL). If the agent crashes, the lease naturally expires, preventing deadlocks.
4. **Release:** Agent commits the changes and releases the lease.

## 📦 Architecture

- **Coordination Server:** FastAPI backend with an SQLite lease manager and deterministic conflict engine.
- **Universal CLI:** A dependency-free Python CLI used by agents to acquire/release leases.
- **Agent Adapters:** Easy integration via custom instructions or skills (e.g., Claude Code `.claude/skills`).

## 🚀 Quick Start

### 1. Start the Server
Run the FastAPI server locally or on a shared team machine:
```bash
pip install -r requirements.txt
python -m server.api

2. Agent Usage (CLI)
Agents (or developers) interact with the server via the CLI tool:
Acquire a lease before modifying:
python -m cli.main acquire --files "src/auth.py,src/session.py" --intent "Refactor JWT authentication" --agent "claude-dev"
# Output: ✅ ALLOWED: Lease acquisita. ID: intent_8f4a1...

If another agent tries to touch overlapping files:
python -m cli.main acquire --files "src/auth.py" --intent "Add logging" --agent "cursor-dev"
# Output: ❌ CONFLICT: Conflitto rilevato... Agente [claude-dev] sta eseguendo 'modify'

Release the lease when done:
python -m cli.main release intent_8f4a1...

3. Check Status
Verify server health and active intents across your repository:
python -m cli.main status
python -m cli.main doctor

🛠️ Claude Code Integration
Simply copy the provided skill to your local workspace to make Claude natively aware of the coordination protocol:
mkdir -p .claude/skills/intent-sync
cp SKILL.md .claude/skills/intent-sync/SKILL.md

📄 License
MIT License.

