---
name: hermes-agent-git-workflow
description: hermes-agent 工作目录的安全 git + 文件操作规范。创建 skill 后立即 commit；文件写入优先 write_file，失败时用 execute_code；reset hard 会清工作区，永远不要对未 commit 的内容执行。
triggers:
  - 创建新的 skill 文件
  - git 操作后文件丢失
  - write_file 疑似静默失败
---

# hermes-agent Git Workflow & File Operation Safety

## 核心规范

### 1. 创建 Skill 后立即 Commit（最重要）

永远不要让新建的 skill 文件停留在 staged 或 working directory。
**正确流程：**

```bash
# 方案 A：write_file 后立刻 git add + commit
write_file(path="~/.hermes/skills/my-new-skill/SKILL.md", content="...")
git add skills/my-new-skill/SKILL.md && git commit -m "feat(skills): add my-new-skill"
git push home main
```

### 2. write_file 静默失败的 Workaround

`write_file` 对**不存在的父目录静默失败**。如果文件创建后 `ls` 验证为空，说明目录不存在。

**Workaround：使用 execute_code + Python open()**

```python
from hermes_tools import terminal, write_file

# 确保目录存在
terminal(command="mkdir -p ~/.hermes/skills/my-new-skill")

# 写入文件（execute_code 会抛出异常，不会静默失败）
content = """---
name: my-new-skill
description: ...
---

# Skill Content
"""
with open("/Users/can/.hermes/skills/my-new-skill/SKILL.md", "w") as f:
    f.write(content)

# 验证
terminal(command="ls -la ~/.hermes/skills/my-new-skill/SKILL.md")
```

### 3. git reset 的危险等级（按破坏力排序）

| 命令 | 影响 | 恢复方式 |
|------|------|----------|
| `git reset HEAD file` | 仅取消 stage | `git add file` |
| `git reset HEAD -- .` | 取消所有 stage | 重新 `git add` |
| `git reset --soft HEAD^` | 删除 last commit，保留文件在 staged | `git log` 可查 |
| `git reset --hard HEAD^` | **删除 last commit + 工作区文件** | `git reflog` + 重建 |
| `git reset --hard`（无参数） | **清空整个工作区**，所有未 commit 改动丢失 | 只能从 reflog 恢复 commit |

**规则：永远不要对未 commit 的内容执行 `reset --hard`。**

文件级 unstaging 正确方式：
```bash
git checkout HEAD -- skills/my-skill/SKILL.md   # 从 HEAD 恢复文件
# 或
git restore --source=HEAD --staged --worktree skills/my-skill/SKILL.md
```

### 4. hermes-agent 的 Remote 架构

```
home  remote  →  https://github.com/Nazicc/hermes-agent.git（当前活跃）
origin remote →  https://github.com/nazicc/hermes-home.git（已 force-push，历史无关）
```

**push 前务必确认目标 remote：**
```bash
git remote -v   # 查看所有 remote
git status      # 确认当前 branch
```

日常 push 用 `git push home main`，不要默认推 origin。

### 5. Stash 管理

```bash
# 查看 stash
git stash list

# 选择性 stash（仅相关文件）
git stash push -m "wip: my changes" -- skills/my-skill/

# 清理无关 stash
git stash drop stash@{N}
```

## 防踩坑检查清单

创建 skill 前后：
- [ ] 父目录存在？不存在则先 `mkdir -p`
- [ ] `write_file` 后立即 `ls` 验证
- [ ] `git add` 后立即 `git commit`
- [ ] `git commit` 后立即 `git push home main`
- [ ] 确认没有 `reset --hard` 的风险

## 相关记忆

- `execute_code` 写入文件比 `write_file` 更可靠（异常可见）
- `git reflog` 是误操作后的救命命令
