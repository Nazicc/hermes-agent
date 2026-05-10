---
name: codebase-inspection
description: "Inspect and analyze codebases — LOC counting with pygount, language composition, code-vs-comment ratios, and systematic strategies for exploring repository structure via GitHub raw content or local files. Use when asked to check lines of code, repo size, language breakdown, or to deeply understand a repository's architecture. NOT for: analyzing GitHub repos to understand architecture (use github-deep-research instead), deep architectural inspection of Rust monorepos (use rust-monorepo-deep-dive), or understanding tool implementation patterns — those require reading source files directly, not LOC counting."
category: general
---

## LOC Counting with pygount

pygount is a statistics generator for source code. It recurses directories, detects languages by extension, and counts lines of code vs comments vs blank lines.

bash
cd /path/to/codebase && python -m pygount --format=summary .


For a CSV export with per-file breakdown:

bash
python -m pygount --format=csv --outfile=/tmp/loc_results.csv .


For language-specific filtering:

bash
python -m pygount --format=summary --pattern='*.py' .  # Python only
python -m pygount --format=summary --pattern='*.rs' .  # Rust only


For quick stats on a cloned repo:

bash
git clone --depth 1 <repo-url> /tmp/quick-clone && cd /tmp/quick-clone && python -m pygount . --format=summary


## Systematic GitHub Repo Analysis

When asked to deeply analyze a GitHub repository (not just get LOC stats), follow this priority order via raw GitHub content — **do not clone the repo first**. Use `execute_code` with Python `urllib` to fetch files directly:

python
import urllib.request

def fetch_github_raw(owner, repo, path, branch="main"):
    url = f"https://raw.githubusercontent.com/{owner}/{repo}/{branch}/{path}"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=15) as r:
        return r.read().decode("utf-8")


### Priority File Order

Fetch files in this order based on project type:

**For any project:**
1. `README.md` — scope, purpose, key features
2. Dependency manifest (`Cargo.toml`, `package.json`, `pyproject.toml`, `go.mod`, `Gemfile`) — architecture hints, key packages

**For Rust projects:**
3. `src/main.rs` — entry point, module structure
4. `src/bin/` or `src/daemon.rs` — daemon/main logic
5. `src/connection.rs` or `src/ipc.rs` — IPC patterns (Unix Domain Sockets, JSON-RPC)
6. `src/skills.rs` or `src/{domain}/mod.rs` — plugin/skill architecture

**For Node.js/TypeScript projects:**
3. `src/index.ts` / `src/main.ts` — entry point
4. `src/{lib,core,shared}/` — shared logic
5. `src/tools/` or `src/handlers/` — tool/action definitions

**For Python projects:**
3. `src/__main__.py` or main module — entry point
4. `src/{core,handlers,tools}/` — functional modules
5. `tests/` structure — testing patterns

### What to Extract from Each File

| File | What to look for |
|------|-------------------|
| `README.md` | Project type, architecture overview, key commands |
| `Cargo.toml` | Workspace structure (members), critical dependencies (tokio, serde, CDP), binary targets |
| `package.json` | Scripts, dependencies, monorepo workspace members |
| `main.rs` | Module imports, binary/daemon branching, CLI argument parsing |
| `daemon.rs` | Daemon lifecycle (start/shutdown), connection handling, Unix socket setup |
| `connection.rs` | IPC protocol (JSON-RPC, CDP, custom), message format, error handling |

### Architecture Pattern Recognition

Common patterns to identify quickly:

- **Daemon + CLI**: Daemon binary (long-running) + CLI binary (connects via Unix socket, sends command, exits). Look for `tokio::spawn`, `unix::SocketAddr`, `std::os::unix`.
- **CDP-based browser automation**: `cdp` crate, Chrome DevTools Protocol messages, `Page.navigate`, `Runtime.evaluate`.
- **Plugin/skill system**: `skills.rs` or `plugins.rs` with trait objects, `Box<dyn ...>`, registry/map of handlers.
- **Monorepo workspace**: `members` in Cargo.toml or `packages` in package.json — list all crates/packages first.

### Multi-Language Monorepo Navigation

For polyglot repos (Rust + TypeScript + Python):

1. Identify the root orchestrator (Makefile, justfile, turbo.json, Cargo workspace)
2. Identify each language's manifest (Cargo.toml, package.json, pyproject.toml)
3. Map the integration point (IPC protocol, HTTP API, shared schemas)

## Qualitative Analysis (Secondary)

For tasks that need more than metrics — understanding architecture, design patterns, or code organization:

### File Structure

bash
find /path/to/codebase -type f \( -name "*.py" -o -name "*.rs" -o -name "*.ts" -o -name "*.go" \) | head -50


### Entry Points by Language

| Language | Entry Point(s) |
|----------|----------------|
| Python   | `main.py`, `__main__.py`, `cli.py`, `__init__.py` |
| Rust     | `src/main.rs`, `src/bin/*.rs`, `Cargo.toml` workspace members |
| TypeScript | `src/index.ts`, `src/cli.ts`, `package.json` bin field |
| Go       | `cmd/*.go`, `main.go` |

### Dependencies by Language

| Language | Dependency File |
|----------|----------------|
| Python   | `requirements.txt`, `pyproject.toml`, `setup.py` |
| Rust     | `Cargo.toml` (workspace + per-crate) |
| TypeScript | `package.json` |
| Go       | `go.mod` |

## Skill Selection Guide

| Task | Skill |
|------|-------|
| Count lines of code / language breakdown | `codebase-inspection` (this skill) |
| Deep Rust monorepo architectural analysis | `rust-monorepo-deep-dive` |
| Analyze GitHub repo structure + plugin manifests | `github-deep-research` |
| Code simplification / refactoring | `code-simplification` |
| Systematic debugging | `systematic-debugging` |
| Test-driven development | `test-driven-development` |

## Common Pitfalls

- **Don't use pygount on SKILL.md files** — they inflate counts with markdown content, not code. Use `--exclude='**/SKILL.md'`
- **pygount may misdetect languages** for uncommon extensions — use `--pattern` to override
- **For very large repos**, limit scope: `pygount src/ src_bin/ --outfile=summary.csv`
- **Hermes Agent venv**: use `~/.hermes/hermes-agent/venv/bin/python -m pygount` to ensure the right Python environment
- **For repos with >1000 files**, consider `github-deep-research` skill instead of cloning
