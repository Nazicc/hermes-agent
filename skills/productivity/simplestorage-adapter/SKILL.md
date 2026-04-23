---
name: simplestorage-adapter
description: |
  SimpleMem Multi-Backend Storage Adapter — 扩展 SimpleMem 支持 PostgreSQL/pgvector 向量存储。
  适用场景：HuggingFace SSL 阻断 / 国内服务器 / 想用云 PostgreSQL / Docker Compose 部署。
  Trigger: 用户想换存储后端、安装报 LanceDB 错、国内服务器部署、想用 pgvector。
  Anti-trigger: 已在用 LanceDB 且正常、只需要本地轻量存储。
trigger:
  - "换存储"
  - "postgresql"
  - "pgvector"
  - "安装 LanceDB 报错"
  - "国内服务器部署"
  - "docker compose"
  - "HuggingFace SSL"
  - "存储后端"
anti_trigger:
  - "只是问问"
  - "怎么用"
version: 2.0.0
license: MIT
metadata:
  sources: []
  hermes:
    tags: [storage, postgresql, pgvector, lancedb, simplemem, deployment]
    related_skills: [simplerag-siliconflow]
    quality_redlines:
      - MUST have R (Reference) section documenting current architecture
      - MUST have E (Execution) section with step-by-step PostgreSQL setup
      - MUST have A2 (Trigger) section with activation signals
      - MUST have B (Boundary) section with known limitations
---