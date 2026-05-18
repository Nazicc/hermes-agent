# Changelog

All notable changes to this fork are documented here.

> **Base version:** v0.13.0 (forked from [NousResearch/hermes-agent](https://github.com/NousResearch/hermes-agent))  
> **Format:** Commits on `main` branch — custom patches layered on upstream

---

## [Unreleased] — CMA-inspired Evolution

### Added
- `agent/tool_result.py` — standardized `ToolResult` abstraction (CMA `execute()` pattern)
- `agent/session_event_log.py` — append-only session event log (CMA harness-ready architecture)
- ARCH-001/ARCH-002 architecture decision records (session externality, tool result standardization)
- CMA-inspired harness readiness (decoupled brain from hands, traceable tool calls)

### Changed
- README.md — full rewrite reflecting actual deployment state (Feishu-native, macOS, GLM-5.1)
- docs/diagrams/hermes-architecture.html — updated platforms, tools count, Honcho L4, footer
- docs/diagrams/hermes-memory-flow.html — updated embedding provider (硅基流动), footer

---

## [2025-05-19] Multi-Agent Team — Phase 3 Complete

### Added
- Mailbox v2: security hardening, encrypted delivery, HMAC verification
- Full collaboration infrastructure verified across [Alice, Bob, Charlie, Dave] agents
- Beads MCP: task dependency graph, blocked issue detection, automated workflow
- Honcho L4: multi-agent coordination on :8889 with SINK protocol

### Changed
- Mailbox security: TLS enforcement, key rotation support, audit logging
- Agent profiles (SOUL.md) for each team member with independent .env/state.db

---

## [2025-05-12] Multi-Agent Team — Architecture & Profile System

### Added
- Multi-agent architecture plan: docs/multi-agent-team-v2.md (18KB, 4-layer: L0 Lead → L1 Profile → L2 delegate_task → L3 cron)
- Profile as first-class citizen: independent SOUL.md, .env, state.db, Gateway per agent
- Beads task board integration for inter-agent coordination
- Git worktree isolation for agent workspaces

---

## [2025-05-10] OpenWolf Context Manager

### Added
- OpenWolf: external session context manager on port 1933
- wolf:// URI namespace for externalized session state
- Dual-path: context push/pull via wolf tool
- Cron-based context health check

### Changed
- README.md — updated architecture with OpenWolf reference
- Architecture/Memory-flow SVGs — initial SVG diagrams created

---

## [2025-05-08] Constitution Governance System — Phase 1

### Added
- Constitution governance: principle-based agent self-regulation
- Constitution evaluator: score agent actions against defined principles
- Enforcement hooks: pre-action evaluation, post-action audit
- Principles: accuracy, helpfulness, safety, efficiency, transparency
- Durable storage of governance records

---

## [2025-05-05] Security Hardening

### Changed
- .gitignore updated to exclude hermes_memory_data/, .hermes/, .wolf/ runtime files
- config.py: environment variable support for sensitive config
- Removed hardcoded credentials from source files
- Security audit tooling (git grep + automated scanning)

---

## [2025-05-01] Upstream Upgrade — v0.10.0 → v0.13.0

### Upstream changes merged
- v0.11.0: Skills system (skill_manage/skill_view/skills_list), MCP support
- v0.12.0: Multi-platform Gateway (Feishu, Telegram, Discord, etc.), cron system
- v0.13.0: Progressive Disclosure (AGENTS.md/CLAUDE.md/.cursorrules), context compression

### Custom patches re-applied (on top of v0.13)
- memory tool dual-write (L0 + L2 sync)
- context compression custom thresholds
- OpenViking integration

---

## [2025-04-20] Evolver & Self-Improvement Foundation

### Added
- Evolver bridge: skill auto-creation from complex tasks
- DSPy skill generation: programmatic skill creation
- GEP metrics tracking: rtk_metrics.jsonl for evolution telemetry
- RTK metrics dashboard foundation

### Changed
- evolver/ directory with full DSPy-based self-evolution pipeline

---

## [2025-04-15] OpenViking Knowledge Base

### Added
- OpenViking KB integration (Docker, port 1933)
- viking_search/read/remember/browse/add_resource tools
- L2 memory layer: semantic embedding storage
- L0→L2 dual-write: memory tool → viking_remember sync

---

## [2025-04-10] Initial Custom Deployment

### Added
- Feishu (Lark) platform integration
- Volcengine/GLM-5.1 provider configuration
- User profile: r00tcc, TopSec (天融信) cloud/regional security service team
- Chinese language support
- BLOOM methodology adoption for complex tasks
- skills/ directory with custom skills (security, CTF, etc.)

### Changed
- Base config from upstream NousResearch/hermes-agent v0.10.0
- Platform focus: Feishu-native with additional platforms

---

## [v0.2.0 — v0.10.0] Upstream Releases

See respective RELEASE_*.md files for upstream changelog:
- RELEASE_v0.2.0.md through RELEASE_v0.10.0.md
