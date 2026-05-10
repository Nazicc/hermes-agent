---
name: codex
description: "Use when delegating coding tasks to OpenAI Codex CLI — building features, refactoring, PR reviews, and batch issue fixing. NOT for: when codex CLI is not installed (use opencode instead), non-git repositories, or when opencode is preferred."
category: general
---

# Codex Skill

Delegate coding tasks to OpenAI Codex CLI agent for feature implementation, refactoring, PR reviews, and long-running autonomous sessions.

## Environment Status

| Component | Status |
|-----------|--------|
| Codex CLI (OpenAI) | ❌ Not installed — `which codex` → not found |
| OpenCode CLI | ✅ Installed v1.4.3 — use for autonomous coding on this machine |
| Git repository | Required — Codex uses git history for context |
| deepcode-hku | Separate pip package — research paper-to-code engine, NOT a codex replacement |

**Current environment**: OpenAI Codex CLI is not installed. Use the **`opencode`** skill instead for CLI-based autonomous coding tasks.

## Prerequisites

- OpenAI Codex CLI installed (`brew install openai-codex` or `npm install -g @openai/codex`)
- Codex CLI authenticated (`codex --auth`)
- Git repository (codex requires a git repo to track changes)
- OpenAI API key configured in environment

## Usage

### Feature Implementation

bash
# Start a new coding session
codex --prompt "Implement the user authentication feature"

# With specific context
codex --prompt "Add rate limiting to the API endpoints" --context "backend/api/v1/"


### Refactoring

bash
codex --prompt "Refactor the data layer to use the repository pattern" --context "src/models/"


### PR Reviews

bash
# Review a pull request
codex --review "https://github.com/owner/repo/pull/123"

# Or use the review command directly
codex --review


### Batch Issue Fixes

bash
# Process multiple issues from a GitHub project
codex --issues "--label=bug --state=open" --auto-commit

# Batch fix all instances of a pattern
codex --batch "fix all instances of pattern X"


### Model Selection

bash
# Specify a different model
codex --model claude "fix the login bug"


## Output

Codex will:
1. Analyze the codebase context
2. Make changes with git tracking
3. Create commits per logical change
4. Report summary of all changes made

## Exit Codes

| Code | Meaning |
|------|---------|
| `0` | All tasks completed successfully |
| `1` | Partial completion (some tasks failed) |
| `2` | CLI error (not installed, not authenticated) |

## Distinction from Related Skills

| Skill | What it is | When to use |
|-------|------------|-------------|
| `codex` | OpenAI Codex CLI (NOT installed on this machine) | Only if Codex CLI is available in target environment |
| `opencode` | OpenCode CLI agent v1.4.3 (INSTALLED) | Primary choice for autonomous coding on this machine |
| `deepcode-hku` | DeepCode Research Engine (pip package) | Research paper to code workflows, not general coding delegation |

## Key Differences: Codex vs OpenCode

| Feature | Codex | OpenCode |
|---------|-------|----------|
| Provider | OpenAI | Various (SambaNova, etc.) |
| Context window | Limited | Extended (200K+ tokens) |
| Multi-file projects | Basic | Advanced |
| This machine | NOT INSTALLED | AVAILABLE |

## Important Notes

- **Requires git repository** — Codex uses git history for context
- **Requires OpenAI API key** configured in environment
- Use `--model` flag to specify model (e.g., `--model claude`)
- For research paper implementation, use `deepcode-hku` directly — it is an HKU research paper-to-code engine with its own FastAPI backend, NOT a codex replacement
- Since codex is not installed on this machine, this skill serves as documentation only
