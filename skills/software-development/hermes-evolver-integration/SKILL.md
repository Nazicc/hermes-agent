---
name: hermes-evolver-integration
description: >
  Integrate Hermes Agent with Evolver (NousResearch/hermes-agent-self-evolution) via
  lightweight bridge — sync Hermes session logs to Evolver's scan directory, run GEPA
  optimization dry-run to validate setup, and optionally trigger full evolution runs.
  ⚠️ CRITICAL: SkillClaw's `_configure_hermes` (claw_adapter.py) OVERWRITES `~/.hermes/config.yaml`
  to route ALL LLM traffic through the SkillClaw proxy. This overrides existing MiniMax
  (or any other) LLM config. A backup is saved to `~/.skillclaw/backups/hermes/` before overwrite.
  Only activate SkillClaw proxy integration explicitly after understanding this impact.
trigger:
  - "evolver"
  - "evolution"
  - "gep"
  - "self-evolution"
  - "进化"
  - "gene"
  - "信号"
  - "process sessions with evolver"
  - "触发evolution"
anti_trigger:
  - "不需要evolver"  # 不需要集成evolver
  - "don't need evolution"  # 不需要evolution功能
  - "不需要SkillClaw"  # 不需要SkillClaw代理
source: hermes-agent
version: 3.0.0
license: MIT
metadata:
  sources: []
  hermes:
    tags: [evolver, self-evolution, skill-evolution, GEPA, DSPy]
    related_skills: [skills-evolution-from-research]
    quality_redlines:
      - MUST have E (Execution) section
      - MUST have B (Boundary) section
      - MUST have A2 (Trigger) section
---

## ⚠️ SkillClaw Adapter Warning

SkillClaw (AMAP-ML/SkillClaw) includes `claw_adapter.py` with `_configure_hermes()` that
**overwrites `~/.hermes/config.yaml`**, setting:
- `provider: custom`
- `base_url: http://127.0.0.1:<proxy_port>/v1`
- `api_key: skillclaw`

This ROUTES ALL Hermes LLM traffic through the SkillClaw proxy, **overriding existing MiniMax
or any other LLM config**. A backup is saved to `~/.skillclaw/backups/hermes/` before overwrite.

To inspect current Hermes config integration status:
```bash
python3 -c "from skillclaw.claw_adapter import inspect_hermes_config; \
  from skillclaw.config import SkillClawConfig; \
  cfg = SkillClawConfig(claw_type='hermes'); \
  print(inspect_hermes_config(cfg))"
```

To restore from backup:
```bash
python3 -c "from skillclaw.claw_adapter import restore_hermes_config; restore_hermes_config()"
```

## Environment Setup

Required packages (install into hermes-agent venv via pip target):
```bash
# Install SkillClaw
pip install --upgrade --force-reinstall -e "/tmp/SkillClaw[evolve,sharing]" \
  -t ~/.hermes/hermes-agent/venv/lib/python3.11/site-packages/

# Install DSPy (evolver dependency)
pip install --upgrade --force-reinstall dspy \
  -t ~/.hermes/hermes-agent/venv/lib/python3.11/site-packages/

# Install evolver dev deps
cd ~/.hermes/hermes-agent/hermes-agent-self-evolution && \
  pip install -q -e ".[dev]" -t ~/.hermes/hermes-agent/venv/lib/python3.11/site-packages/
```

## Execution

### Step 1 — Validate bridge (dry-run, no writes):
```bash
cd ~/.hermes/hermes-agent && \
  python3 scripts/hermes_to_evolver_bridge.py --dry-run
```

Expected output: lists N sessions found from `~/.hermes/state.db`, shows what would be written to
`~/.openclaw/agents/hermes-agent/sessions/`. No files written.

### Step 2 — Run bridge (writes session JSONL + RTK metrics):
```bash
cd ~/.hermes/hermes-agent && \
  python3 scripts/hermes_to_evolver_bridge.py
```

Output: confirms N session files written to Evolver scan dir; RTK metrics appended to
`~/.hermes/hermes-agent/hermes-agent-self-evolution/assets/gep/rtk_metrics.jsonl`.

### Step 3 — Validate evolver setup (dry-run):
```bash
cd ~/.hermes/hermes-agent/hermes-agent-self-evolution && \
  HERMES_AGENT_REPO=~/.hermes/hermes-agent \
  ~/.hermes/hermes-agent/venv/bin/python3 \
  -m evolution.skills.evolve_skill --skill <skill-name> --dry-run
```

Expected: "DRY RUN — setup validated successfully." — confirms DSPy + GEPA load correctly.

### Step 4 — Full evolver run (optional, costs ~$2-10):
```bash
cd ~/.hermes/hermes-agent/hermes-agent-self-evolution && \
  HERMES_AGENT_REPO=~/.hermes/hermes-agent \
  ~/.hermes/hermes-agent/venv/bin/python3 \
  -m evolution.skills.evolve_skill \
  --skill <skill-name> \
  --iterations 10 \
  --eval-source synthetic \
  --run-tests
```

## SkillClaw Hermes Adapter — Advanced

Only use if you want Hermes to route ALL LLM calls through SkillClaw's proxy network
( SkillClaw acts as a multi-agent skill-sharing infrastructure layer):

```bash
# Initialize SkillClaw with Hermes adapter (OVERWRITES ~/.hermes/config.yaml)
skillclaw init --claw-type=hermes --proxy-port 8080

# Inspect integration status
skillclaw inspect hermes

# Restore original config from backup
skillclaw restore hermes
```

**When NOT to use**: If Hermes is your primary agent with MiniMax or Anthropic as the LLM
backend — the adapter overwrites that config and routes everything through SkillClaw proxy.

## SkillClaw 共享 Group 搭建（hermes-team）

### 现状（2026-04-23）

| 项目 | 值 |
|------|-----|
| Group ID | `hermes-team` |
| 存储后端 | 本地目录 `~/.skillclaw/shared/` |
| Skill 数量 | 143 个（全部 Hermes skills 已 push） |
| Evolve Server | launchd 服务，每 300s 一个 cycle |

### 本地服务管理
```bash
# 查看服务状态
launchctl print gui/$(id -u)/ai.hermes.skillclaw-evolve

# 查看日志
tail -f ~/.skillclaw/logs/evolve-server.out.log
tail -f ~/.skillclaw/logs/evolve-server.err.log

# 停止服务
launchctl unload ~/Library/LaunchAgents/ai.hermes.skillclaw-evolve.plist

# 重启服务
launchctl load ~/Library/LaunchAgents/ai.hermes.skillclaw-evolve.plist

# 手动触发一个 evolution cycle
~/.openharness-venv/bin/skillclaw-evolve-server \
  --use-skillclaw-config --engine workflow \
  --publish-mode direct --once --verbose
```

### Plist 文件
`~/Library/LaunchAgents/ai.hermes.skillclaw-evolve.plist`

### 新成员加入 Group
```bash
skillclaw config sharing.enabled true
skillclaw config sharing.backend local
skillclaw config sharing.local_root /path/to/shared-dir   # NFS/网盘挂载点
skillclaw config sharing.group_id hermes-team
skillclaw config sharing.user_alias <成员名>
skillclaw skills pull
```

### 切换到 OSS 跨互联网共享
```bash
skillclaw config sharing.backend oss
skillclaw config sharing.endpoint https://oss-cn-hangzhou.aliyuncs.com
skillclaw config sharing.bucket <bucket-name>
skillclaw config sharing.access_key_id <key>
skillclaw config sharing.secret_access_key <secret>
skillclaw config sharing.group_id hermes-team

# 重启服务使配置生效
launchctl unload ~/Library/LaunchAgents/ai.hermes.skillclaw-evolve.plist
launchctl load ~/Library/LaunchAgents/ai.hermes.skillclaw-evolve.plist
```

## Regression Testing

After any change, always run the full skill validation:
```bash
python3 /tmp/validate_skills.py --path ~/.hermes/skills/
```

Expected: "All checks passed." — 0 errors, 0 warnings across all 143 skills.
