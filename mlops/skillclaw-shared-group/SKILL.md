---
name: skillclaw-shared-group
description: >
  Set up and operate a SkillClaw shared skill group — operator initializes the group and
  uploads skills, members join via config. Covers local backend (zero cost) and OSS/S3
  backend (cross-internet team sharing). Includes evolve server deployment.
trigger:
  - "skillclaw shared group"
  - "skillclaw group"
  - "skillclaw sharing"
  - "共享 group"
  - "skillclaw sync"
  - "skillclaw push"
  - "skillclaw pull"
  - "skillclaw oss"
  - "skillclaw s3"
  - "skillclaw evolve server"
anti_trigger:
  - "不需要共享"
source: hermes-agent
version: 1.0.0
license: MIT
metadata:
  sources: []
  hermes:
    tags: [skillclaw, skill-sharing, multi-agent, shared-group, evolver]
    related_skills: [hermes-evolver-integration, skills-evolution-from-research]
---

## Overview

SkillClaw shared groups let multiple AI agents (Hermes, Codex, Claude Code, etc.) share evolved
skills via a shared storage backend. No hosted service — everything is self-hosted.

```
[Client A] ──┐                     ┌── [Client B]
             ├──→ [Shared Storage] ←─┤
[Client C] ──┘         ↑            └── [Client D]
                        │
              [Evolve Server] ← optional, writes evolved skills back
```

**Two roles:**
- **Operator**: Initializes the group, uploads skills, optionally runs evolve server
- **Member**: Configures the shared storage endpoint, pulls skills

## Storage Backends

| Backend | Value | Cost | Use Case |
|---------|-------|------|----------|
| Local directory | `local` | Free | Single machine / NFS / rsync / Syncthing |
| Alibaba Cloud OSS | `oss` | ~¥3/mo | Cross-internet team sharing |
| AWS S3 / compatible | `s3` | ~$0.02/GB | Cross-internet team sharing |

## Step 1 — Operator: Initialize Group

### 1a. Install SkillClaw (if not already)

```bash
pip install -e "/tmp/SkillClaw[evolve,sharing]" \
  -t ~/.hermes/hermes-agent/venv/lib/python3.11/site-packages/
# CLI: ~/.openharness-venv/bin/skillclaw
```

### 1b. Configure sharing (local backend example)

```bash
SKILLCLAW=~/.openharness-venv/bin/skillclaw

$SKILLCLAW config sharing.enabled true
$SKILLCLAW config sharing.backend local
$SKILLCLAW config sharing.local_root ~/.skillclaw/shared
$SKILLCLAW config sharing.group_id hermes-team
$SKILLCLAW config sharing.user_alias hermes-operator
```

**⚠️ Critical: `skills.dir` must point directly to the skills directory**, not a parent.
SkillClaw scans `skills.dir` recursively — symlinks inside it do NOT work:

```bash
# WRONG — symlink inside skills.dir:
#   ~/.skillclaw/skills/ → ~/.hermes/skills/  ❌ push sees 0 skills
$SKILLCLAW config skills.dir ~/.skillclaw/skills  # empty dir, 0 skills pushed

# RIGHT — point directly to the skills directory:
$SKILLCLAW config skills.dir ~/.hermes/skills
```

### 1c. Verify config

```bash
cat ~/.skillclaw/config.yaml
# Key sections to check:
#   sharing.enabled: true
#   sharing.backend: local
#   sharing.local_root: ~/.skillclaw/shared
#   sharing.group_id: hermes-team
#   skills.dir: ~/.hermes/skills        # must be actual dir, not symlink parent
```

### 1d. Run evolve server once (validates storage connection)

```bash
~/.openharness-venv/bin/skillclaw-evolve-server \
  --use-skillclaw-config \
  --engine workflow \
  --publish-mode direct \
  --once \
  --verbose
```

Expected output:
```
INFO [SkillIDRegistry] no existing registry in storage — starting fresh
INFO [EvolveServer] === starting evolution cycle ===
INFO [EvolveServer] === cycle done: 0 sessions ... ===
{"skills_evolved": 0, "uploaded_skills": 0, ...}
```

Check that storage was created:
```bash
ls ~/.skillclaw/shared/hermes-team/
# Should contain: manifest.jsonl, evolve_skill_registry.json, skills/
```

### 1e. Push skills to the group

```bash
~/.openharness-venv/bin/skillclaw skills push --no-filter
# Output: Done: N uploaded, 0 unchanged, 0 filtered, N total local skills.
```

The `--no-filter` flag skips the effectiveness quality gate (skills need injection
history before they pass the default `push_min_injections=5` threshold).

Check push results:
```bash
wc -l ~/.skillclaw/shared/hermes-team/manifest.jsonl
# Should be ~143 (one skill per line)
```

## Step 2 — Member: Join the Group

On each member machine, configure sharing to point to the same storage:

### For local/NFS/rsync sharing:

```bash
SKILLCLAW=~/.openharness-venv/bin/skillclaw

$SKILLCLAW config sharing.enabled true
$SKILLCLAW config sharing.backend local
$SKILLCLAW config sharing.local_root /path/to/shared-dir   # NFS mount / Syncthing folder
$SKILLCLAW config sharing.group_id hermes-team
$SKILLCLAW config sharing.user_alias alice

$SKILLCLAW config skills.dir ~/.hermes/skills   # local skills dir

# Pull shared skills
$SKILLCLAW skills pull
```

### For OSS sharing:

```bash
SKILLCLAW=~/.openharness-venv/bin/skillclaw

$SKILLCLAW config sharing.enabled true
$SKILLCLAW config sharing.backend oss
$SKILLCLAW config sharing.endpoint https://oss-cn-hangzhou.aliyuncs.com
$SKILLCLAW config sharing.bucket your-bucket-name
$SKILLCLAW config sharing.access_key_id "$OSS_ACCESS_KEY_ID"
$SKILLCLAW config sharing.secret_access_key "$OSS_ACCESS_KEY_SECRET"
$SKILLCLAW config sharing.group_id hermes-team
$SKILLCLAW config sharing.user_alias alice

$SKILLCLAW skills pull
```

## Step 3 — Operate Evolve Server (Optional)

The evolve server reads session data from shared storage and automatically evolves skills.
It does NOT directly communicate with clients — only reads/writes the shared storage.

### Deploy as background service (local backend, single machine):

```bash
# Run in background with launchd (macOS) or systemd (Linux)
nohup skillclaw-evolve-server \
  --use-skillclaw-config \
  --engine workflow \
  --publish-mode direct \
  --interval 300 \
  --verbose \
  > ~/.skillclaw/evolve-server.log 2>&1 &
```

### Deploy with OSS backend (can run on any machine with bucket access):

```bash
skillclaw-evolve-server \
  --use-skillclaw-config \
  --storage-backend oss \
  --oss-endpoint https://oss-cn-hangzhou.aliyuncs.com \
  --oss-bucket your-bucket-name \
  --group-id hermes-team \
  --engine workflow \
  --publish-mode direct \
  --interval 300 \
  --port 8787 &
```

### Key server options:

| Flag | Description |
|------|-------------|
| `--engine workflow` | Fixed LLM pipeline (Summarize → Aggregate → Execute) |
| `--engine agent` | OpenClaw-driven agent workspace (requires `openclaw` npm) |
| `--publish-mode direct` | Immediately publish evolved skills |
| `--publish-mode validated` | Stage candidates, require client-side validation before publish |
| `--interval 300` | Run evolution cycle every 5 minutes |
| `--once` | Single run and exit (useful for testing) |
| `--skill-verifier` | Enable pre-upload skill quality verification (workflow engine only) |

### Check server status:

```bash
# View logs
tail -f ~/.skillclaw/evolve-server.log

# Check if running
~/.openharness-venv/bin/skillclaw-evolve-server --help > /dev/null 2>&1 && echo "CLI available"
ps aux | grep skillclaw-evolve-server | grep -v grep
```

## Sharing Skills Between Groups

Each group has its own `group_id` namespace. To share skills between two groups:

1. Group A operator: `skillclaw skills push` (uploads to group A storage)
2. Group B operator: mount Group A's storage as a local dir, or copy skill bundles manually
3. Group B members: `skillclaw skills pull`

There is no cross-group federation built in — skill sharing between groups requires
manual transfer or shared storage arrangement.

## Common Issues

### Push reports "0 skills"

Cause: `skills.dir` points to an empty directory or a symlink to a directory.
Fix: Point `skills.dir` directly to the actual skills directory:
```bash
skillclaw config skills.dir ~/.hermes/skills   # actual path, not ~/.skillclaw/skills/
skillclaw skills push --no-filter
```

### Evolve server reports "queue empty"

Cause: No session data in shared storage. Clients must route LLM traffic through
SkillClaw proxy (`skillclaw start`) to generate session artifacts.
Fix: Run `skillclaw start --daemon` on client machines first.

### OSS push fails with auth error

Cause: Wrong `access_key_id`/`secret_access_key` or bucket not accessible from this region.
Fix: Test with `ossutil` or `aws s3 ls` directly before configuring SkillClaw.

### Skill quality gate filtering all skills

New skills with no injection history have `effectiveness=0` and are filtered by default
(`push_min_effectiveness=0.3`, `push_min_injections=5`).
Fix: Use `--no-filter` for initial push to bypass quality gates.

## Storage Structure

```
{local_root_or_bucket}/
└── {group_id}/
    ├── manifest.jsonl              ← global skill index (one JSON per line)
    ├── evolve_skill_registry.json   ← skill ID registry with history
    └── skills/
        ├── {skill-name}/
        │   ├── SKILL.md             ← current version
        │   ├── files/               ← references/, scripts/, etc.
        │   └── versions/
        │       └── v1/
        │           ├── SKILL.md
        │           └── bundle.json
        └── {another-skill}/
            └── ...
```

## Security Notes

- **OSS/S3 credentials = group membership**. Anyone with valid credentials can read/write
  skills to the group. Use bucket IAM policies to restrict access if needed.
- **No per-skill ACLs**. All members can see and overwrite all skills.
- The evolve server does not authenticate clients — it trusts anyone who can write to storage.
- Local backend sharing relies on filesystem permissions (NFS exports, Syncthing device trust).
