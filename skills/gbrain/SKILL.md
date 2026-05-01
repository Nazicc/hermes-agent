---
name: gbrain
description: 查询 hermes-agent 个人知识库（gbrain 知识图谱）。当用户询问「你记得...」「查一下...」「知识库里有...」时使用。53 pages, 1241 embedded chunks。
triggers:
  - gbrain
  - 知识库
  - 知识图谱
  - 查一下
  - 你记得
  - brain
  - recall
  - 记得吗
anti_triggers:
  - gbrain embed
  - gbrain 嵌入
  - gbrain init
purpose: 查询本地 gbrain 知识库的内容，补充 agent 记忆
when_not_to_use: 实时信息、新闻、天气、当天会议（这些查飞书/API更好）；需要精确事实的代码调试（直接搜对应文件）
---

# gbrain 知识库

## 快速查询

```bash
# 1. 混合搜索（嵌入向量 + 关键词），最常用
cd ~/gbrain && bun run src/cli.ts query "<问题>"

# 2. 纯关键词搜索（tsvector，无需嵌入）
cd ~/gbrain && bun run src/cli.ts search "<关键词>"

# 3. 知识库统计
cd ~/gbrain && bun run src/cli.ts stats

# 4. 读取单个页面
cd ~/gbrain && bun run src/cli.ts get <slug>

# 5. 列出所有页面
cd ~/gbrain && bun run src/cli.ts list -n 20
```

## 输出格式

```
[0.9991] slug -- 标题

正文片段...
[0.8855] slug -- 标题
...
```

## 当前状态

- **Pages**: 53
- **Chunks**: 1309（1241 已嵌入，68 未嵌入因 400 错误）
- **类型**: concept
- **数据库**: `/Users/can/.gbrain/brain.pglite`

## 嵌入向量模型

- **Embedding**: SiliconFlow BAAI/bge-large-zh-v1.5（1024 维）
- **API Key**: 存储于 `~/gbrain/.env`（**不要 push 到 git**）
- **MAX_CHARS**: 450（中文安全阈值，450 chars ≈ 450 tokens）
- **BATCH_SIZE**: 30（SiliconFlow per-request 上限 32 items）

## 重新嵌入（需要 API key）

如果新增/修改了页面需要重新嵌入：

```bash
source ~/gbrain/.env
cd ~/gbrain && bun run src/cli.ts embed <slug>   # 单页
cd ~/gbrain && bun run src/cli.ts embed --all    # 全部（注意：68 chunks 会失败，属已知问题）
```

## 注意事项

1. `query` 命令使用已有嵌入，无需 API key
2. `embed` 命令需要先 `source ~/gbrain/.env` 加载 API key
3. 2 个页面嵌入失败（slug 含时间戳如 `20260420_205435_ac9efe`，内容为空/只有标题）
4. `.env` 和 `brain.pglite` 已在 `.gitignore`，不要 push
