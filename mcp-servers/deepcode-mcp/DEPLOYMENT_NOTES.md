# DeepCode + DeepTutor MCP Server Config

## Status: ✅ Deployed (2026-04-27)

## config.yaml additions (MCP servers section)

Add after `deerflow:` entry (around line 389):

```yaml
  deepcode:
    command: /Users/can/.openharness-venv/bin/python
    args:
    - /Users/can/.hermes/deepcode-mcp/deepcode_mcp.py
    env:
      DEEPCODE_BASE_URL: http://127.0.0.1:8000
    enabled: true
  deeptutor:
    command: /Users/can/.openharness-venv/bin/python
    args:
    - /Users/can/.hermes/deeptutor-mcp/deeptutor_mcp.py
    env:
      DEEPTUTOR_BASE_URL: http://127.0.0.1:8001
    enabled: true
```

## Tool Summary

### DeepCode (9 tools)
- `deepcode_chat_planning` — submit task for AI planning
- `deepcode_paper_to_code` — generate code from paper
- `deepcode_workflow_status` — get task status
- `deepcode_workflow_respond` — send follow-up to workflow
- `deepcode_requirements_questions` — analyze requirements
- `deepcode_requirements_summarize` — summarize requirements
- `deepcode_active_workflows` — list active tasks
- `deepcode_recent_workflows` — list recent tasks
- `deepcode_health` — health check

### DeepTutor (23 tools)
- Knowledge: health, list, create, upload, sync
- TutorBot: list, create, chat, recent
- Co-Writer: edit, edit_react (streaming)
- Book: list, deep_dive, supplement
- Notebook: create, add, add_with_summary, list
- Q&A: lookup, upsert
- Session: get
