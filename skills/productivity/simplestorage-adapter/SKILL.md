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

# SimpleMem Multi-Backend Storage Adapter

## A2 — 触发场景 (Trigger) ★

### 何时激活

1. **HuggingFace SSL 阻断** — LanceDB 依赖 HuggingFace embedding 模型，国内服务器报错
2. **想用 PostgreSQL** — 已有云端 PostgreSQL，想复用而不是新装 LanceDB
3. **Docker Compose 部署** — 习惯用 docker-compose 管理所有服务
4. **存储后端切换** — 用户说"换存储"、"试试 pgvector"

### 语言信号

- "换存储"
- "postgresql"
- "pgvector"
- "安装报错"
- "docker compose"
- "存储后端"

### Anti-Trigger

- 已在用 LanceDB 且正常
- 只是信息查询

---

## R — Reference（参考）

### 现有架构（SimpleMem v3.3.2）

```
SimpleMem/
├── config.py                    配置（STORAGE_ADAPTER 可在此添加）
├── core/
│   ├── memory_builder.py         MemoryEntry 构建
│   └── hybrid_retriever.py      混合检索（语义 + 关键词 + 结构化）
├── database/
│   └── vector_store.py          LanceDB vector_store ← 核心存储类
├── utils/
│   ├── embedding.py             SiliconFlow 嵌入（已验证）
│   └── llm_client.py            MiniMax LLM 客户端
└── lancedb_data/                LanceDB 数据目录
```

**核心：database/vector_store.py**
- VectorStore 类负责 add / search / delete
- 切换存储需替换此类，或新增适配器

### 当前可用存储路径

| 存储 | 状态 | 依赖 |
|------|------|------|
| LanceDB（SiliconFlow embedding） | ✅ 已验证 | `lancedb` |
| PostgreSQL + pgvector | 🔧 需安装 | `psycopg2-binary`, `pgvector` |
| SQLite | 🔧 需开发 | 内置，无需额外包 |

### PostgreSQL + pgvector 优势

| 维度 | LanceDB | PostgreSQL + pgvector |
|------|---------|----------------------|
| 部署 | 嵌入式文件 | Docker 一行 |
| 向量维度 | 1024d | 1024d（pgvector） |
| 全文检索 | FTS（弱） | PostgreSQL FTS（强） |
| 多租户 | 差 | 原生 RLS |
| 生态 | 新兴 | 成熟稳定 |

---

## E — Execution（执行步骤）★

### 方案 A：Docker Compose 部署 PostgreSQL + pgvector

```bash
# 1. 创建 docker-compose.yaml
cat > ~/simplemem-postgres/docker-compose.yaml << 'YAML'
version: "3.8"
services:
  postgres:
    image: pgvector/pgvector:pg16
    container_name: simplemem-pg
    environment:
      POSTGRES_DB: simplemem
      POSTGRES_USER: simplemem
      POSTGRES_PASSWORD: your_password_here
    ports:
      - "5432:5432"
    volumes:
      - pgdata:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U simplemem"]
      interval: 10s
      timeout: 5s
      retries: 5

volumes:
  pgdata:
YAML

# 2. 启动
cd ~/simplemem-postgres
docker compose up -d

# 3. 等待就绪，启用 pgvector 扩展
docker exec simplemem-pg psql -U simplemem -d simplemem -c "CREATE EXTENSION IF NOT EXISTS vector;"
```

### 方案 B：已有 PostgreSQL，直接启用 pgvector

```bash
# 在 PostgreSQL 服务器上执行
psql -U postgres -d simplemem -c "CREATE EXTENSION IF NOT EXISTS vector;"

# 验证
psql -U postgres -d simplemem -c "\\dx pgvector"
```

### 配置 SimpleMem 使用 PostgreSQL

```python
# ~/SimpleMem/config.py 新增配置

# 存储后端选择：lancedb / postgresql / sqlite
STORAGE_ADAPTER = "postgresql"

# PostgreSQL 连接信息
POSTGRES_HOST = "localhost"
POSTGRES_PORT = 5432
POSTGRES_DB = "simplemem"
POSTGRES_USER = "simplemem"
POSTGRES_PASSWORD = "your_password_here"

# pgvector 表名
VECTOR_TABLE_NAME = "memory_entries"
EMBEDDING_DIMENSION = 1024   # 必须与 SiliconFlow bge-large-zh-v1.5 一致
```

### PostgreSQL Adapter 实现（database/vector_store_postgres.py）

```python
# ~/SimpleMem/database/vector_store_postgres.py
# 替换 LanceDB 的存储实现

import psycopg2
import psycopg2.extras
import numpy as np
from typing import List, Optional

class PostgresVectorStore:
    """
    PostgreSQL + pgvector 实现。
    使用 SiliconFlow embedding (1024d)，向量存于 pgvector 列。
    """

    def __init__(self, connection_params: dict, table_name: str = "memory_entries", dimension: int = 1024):
        self.conn = psycopg2.connect(**connection_params)
        self.table_name = table_name
        self.dimension = dimension
        self._ensure_table()

    def _ensure_table(self):
        with self.conn.cursor() as cur:
            cur.execute(f"""
                CREATE TABLE IF NOT EXISTS {self.table_name} (
                    id SERIAL PRIMARY KEY,
                    content TEXT NOT NULL,
                    keywords TEXT[],
                    vector vector({self.dimension}),
                    metadata JSONB,
                    created_at TIMESTAMP DEFAULT NOW()
                )
            """)
            # HNSW 索引（比 IVFFlat 更快）
            cur.execute(f"""
                CREATE INDEX IF NOT EXISTS idx_vector_hnsw
                ON {self.table_name} USING hnsw (vector vector_cosine_ops)
                WITH (m = 16, ef_construction = 64)
            """)
            self.conn.commit()

    def add(self, content: str, vector: List[float], metadata: dict = None):
        with self.conn.cursor() as cur:
            cur.execute(f"""
                INSERT INTO {self.table_name} (content, vector, metadata)
                VALUES (%s, %s, %s)
            """, (content, vector, psycopg2.extras.Json(metadata or {})))
            self.conn.commit()

    def search(self, query_vector: List[float], top_k: int = 5) -> List[dict]:
        with self.conn.cursor() as cur:
            cur.execute(f"""
                SELECT content, metadata,
                       1 - (vector <=> %s::vector) AS similarity
                FROM {self.table_name}
                ORDER BY vector <=> %s::vector
                LIMIT %s
            """, (query_vector, query_vector, top_k))
            return [
                {
                    "content": row[0],
                    "metadata": row[1],
                    "score": float(row[2])
                }
                for row in cur.fetchall()
            ]

    def delete(self, content: str):
        with self.conn.cursor() as cur:
            cur.execute(
                f"DELETE FROM {self.table_name} WHERE content = %s",
                (content,)
            )
            self.conn.commit()

    def count(self) -> int:
        with self.conn.cursor() as cur:
            cur.execute(f"SELECT COUNT(*) FROM {self.table_name}")
            return cur.fetchone()[0]
```

### 修改 database/vector_store.py 路由到适配器

```python
# ~/SimpleMem/database/vector_store.py 顶部修改

from config import STORAGE_ADAPTER

if STORAGE_ADAPTER == "postgresql":
    from .vector_store_postgres import PostgresVectorStore as VectorStore
elif STORAGE_ADAPTER == "sqlite":
    from .vector_store_sqlite import SQLiteVectorStore as VectorStore
else:
    from .vector_store_lancedb import LanceDBVectorStore as VectorStore

# 以下代码保持原有接口不变
```

### Docker Compose 完整部署（含 SimpleMem）

```yaml
# ~/simplemem-postgres/docker-compose-full.yaml
version: "3.8"
services:
  postgres:
    image: pgvector/pgvector:pg16
    container_name: simplemem-pg
    environment:
      POSTGRES_DB: simplemem
      POSTGRES_USER: simplemem
      POSTGRES_PASSWORD: change_me
    ports:
      - "5432:5432"
    volumes:
      - pgdata:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U simplemem -d simplemem"]
      interval: 10s
      timeout: 5s
      retries: 5

  simplemem:
    image: python:3.12-slim
    container_name: simplemem-app
    working_dir: /app
    volumes:
      - ~/SimpleMem:/app
    environment:
      STORAGE_ADAPTER: "postgresql"
      POSTGRES_HOST: "postgres"
      POSTGRES_PORT: 5432
      POSTGRES_DB: "simplemem"
      POSTGRES_USER: "simplemem"
      POSTGRES_PASSWORD: "change_me"
      OPENAI_API_KEY: "${OPENAI_API_KEY}"
    depends_on:
      postgres:
        condition: service_healthy
    command: >
      bash -c "pip install uv && uv pip install -r requirements.txt && python main.py"

volumes:
  pgdata:
```

---

## B — Boundary（边界条件）

### 已知限制

| 限制 | 说明 | 规避方案 |
|------|------|---------|
| pgvector 维度 | pgvector 最大 2000d，bge-large-zh-v1.5 的 1024d 没问题 | — |
| HNSW 内存 | HNSW 索引会占用额外内存 | 生产环境给 PostgreSQL 2GB+ RAM |
| Docker 网络 | 容器间通信需要 depends_on + service_healthy | 如上配置 |
| 迁移 | 从 LanceDB 迁移到 PostgreSQL 需要数据导出/导入 | 见下方迁移脚本 |

### 数据迁移（LanceDB → PostgreSQL）

```python
# ~/SimpleMem/scripts/migrate_lancedb_to_pg.py
"""一次性迁移脚本：从 LanceDB 迁移到 PostgreSQL"""

def migrate_lancedb_to_pg():
    from database.vector_store_lancedb import LanceDBVectorStore
    from database.vector_store_postgres import PostgresVectorStore

    lancedb_store = LanceDBVectorStore("./lancedb_data")
    pg_store = PostgresVectorStore(
        connection_params={
            "host": "localhost",
            "port": 5432,
            "dbname": "simplemem",
            "user": "simplemem",
            "password": "change_me",
        },
        dimension=1024,
    )

    # 读取 LanceDB 所有数据（需要先实现 get_all 方法）
    entries = lancedb_store.get_all() if hasattr(lancedb_store, "get_all") else []
    for entry in entries:
        pg_store.add(
            content=entry["content"],
            vector=entry["vector"],
            metadata=entry.get("metadata", {})
        )

    print(f"Migrated {len(entries)} entries to PostgreSQL")
```

### 安全边界

- **生产环境**：PostgreSQL 密码必须通过环境变量注入，绝不写死在 docker-compose.yaml
- **网络**：生产环境 PostgreSQL 端口不对公网暴露
- **备份**：PostgreSQL 数据通过 `pg_dump` 定期备份

---

## I — Interoperability（互操作性）

### 与现有 SimpleMem 组件兼容

| 组件 | 兼容性 | 说明 |
|------|--------|------|
| `hybrid_retriever.py` | ✅ | 只调用 `.search()` 接口，存储无关 |
| `memory_builder.py` | ✅ | 只调用 `.add()` 接口，存储无关 |
| `utils/embedding.py` | ✅ | SiliconFlow embedding 不变 |
| `utils/llm_client.py` | ✅ | MiniMax LLM 客户端不变 |
| `utils/privacy_tags.py` | ✅ | 隐私标签 stripping 不变 |

### 部署检查清单

```
□ PostgreSQL 16 + pgvector 扩展已安装
□ STORAGE_ADAPTER = "postgresql" 已写入 config.py
□ POSTGRES_* 连接参数正确
□ 连接测试: psql -h localhost -U simplemem -d simplemem -c "\dx pgvector"
□ SimpleMem 启动验证: python main.py 后无存储相关错误
□ 写入测试: 发送一条消息，检索能否返回结果
```
