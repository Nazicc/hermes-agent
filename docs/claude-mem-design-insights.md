# claude-mem 设计洞察 — 融入 Hermes Agent

## 来源

`thedotmack/claude-mem` — 65k stars, AGPL-3.0, TypeScript, v12.3.8

## 三大核心设计

### 1. 隐私标签 `<private>`

**最简单有效的隐私控制。** 用户在任意内容外包裹 `<private>...</private>`，钩子层直接 strip 掉，不入库。

```html
Bob，我们明天下午2点在<span class="private"><</span>private>星巴克旁边的招商银行ATM机<private>见面吧</span>
```

**融入 Hermes：** 在 `SimpleMem` 的 `add_dialogue()` 前加 strip 层：
```python
import re
PRIVATE_TAG_REGEX = re.compile(r'<private>[\s\S]*?</private>')

def strip_private_tags(text: str) -> str:
    return PRIVATE_TAG_REGEX.sub('[已隐藏敏感内容]', text)
```

**优势：** 用户无需配置权限、学习 ACL，天然、直觉、零成本。

---

### 2. 三层查询工作流（节省 10x tokens）

```
Step 1: search  → 返回索引（ID + 时间 + 标题，~50-100 tokens/条）
Step 2: timeline → 获取围绕锚点的上下文（按需）
Step 3: fetch    → 仅对过滤后的 ID 取完整详情（~500-1000 tokens/条）
```

**为什么不直接 fetch？** 全量 fetch 浪费巨大。三层过滤确保只取真正相关的内容。

**融入 Hermes：** 给 SimpleMem/MemPalace 实现相同模式：
- `memory_search(query)` → 返回 {id, time, type, title} 列表
- `memory_timeline(anchor_id, depth)` → 返回上下文片段
- `memory_fetch(ids)` → 返回完整条目

---

### 3. 渐进式上下文注入（Progressive Disclosure）

不是把所有记忆一股脑塞进 context，而是**分层注入**：

```
Layer 0 (始终注入):  高优先级事实 - 工作目录、当前项目、用户偏好
Layer 1 (按需注入):  近期相关会话 - 通过 search 发现
Layer 2 (手动触发):  历史深度上下文 - 通过 timeline 展开
Layer 3 (never):     被 <private> 排除的内容
```

**融入 Hermes：** 在 `HermesCLI` 的 context 注入逻辑中实现分层：
- `system_info` = Layer 0（始终有）
- `memory_search_results` = Layer 1（query 时注入）
- `timeline_expansion` = Layer 2（显式请求时注入）

---

## 其他可借鉴设计

### Citation 引用

claude-mem 用 ID 引用历史观察：`#11131`。Hermes 可以给每条 SimpleMem 记忆分配稳定 ID，支持 `memory[id]` 直接读取。

### Observation 类型标签

记忆条目打标签：`bugfix | feature | decision | discovery | change`。搜索时按类型过滤，减少噪音。

### Skill-Based Search

claude-mem 的 `mem-search` skill 实际上是一个 MCP 工具封装。Hermes 的 skill 系统可以给 SimpleMem/MemPalace 做同样封装，通过 MCP 协议暴露。

---

## 已融入的内容

1. **`~/SimpleMem/utils/embedding.py`** — SiliconFlow API 嵌入（HuggingFace 被墙方案）
2. **`~/SimpleMem/config.py`** — MiniMax Token Plan + SiliconFlow 配置
3. **`~/.hermes/skills/productivity/simplerag-siliconflow/`** — 安装 skill
4. **`~/.hermes/memory`** — 更新了 SiliconFlow 嵌入模型速查

## 待融入

- [ ] `strip_private_tags()` 工具函数
- [ ] `SimpleMem` 的 `add_dialogue()` 集成隐私 strip
- [ ] `mem-search` skill (三层查询协议)
- [ ] Memory 条目 ID + citation 支持
- [ ] Observation 类型标签 (bugfix/feature/decision/discovery/change)
- [ ] 渐进式上下文注入层（Layer 0/1/2）
