# RSS Source Health Checker — SPEC

## Feature: 安全资讯 RSS 源健康检查预检脚本

**Trigger**: Cron job `5bed6f2e3557` (安全资讯日报) 执行前，prerun script 调用
**Goal**: 在 cron 执行前快速检查6个RSS源可用性，返回结构化JSON供上游决策

---

## Background Problem

- `security_news.py` 依赖 `feedparser`（未安装），导致 `ModuleNotFoundError`
- 3/6 源偶发超时（curl exit=28），上游无法区分"源坏"还是"网络抖动"
- cron prerun 机制支持 script_path → stdout JSON 注入 prompt

---

## Architecture

```
rss_health_checker.py          ← prerun script (standalone)
├── check_all_sources()        ← 并发 httpx 请求，httpx 内置 XML 解析
├── SourceHealthChecker         ← 单源检查：HTTP状态 / 超时 / 内容有效性
└── 输出: JSON {sources:[{name,url,status,http_code,size,response_time_ms,error}], summary}
```

**不引入 feedparser / lxml**：用 `httpx` (已安装) + `xml.etree.ElementTree` (stdlib)

---

## Functionality Specification

### 1. `SourceHealthChecker.check(url, timeout=15) -> dict`

**Input**: RSS URL, timeout (default 15s)
**Output**:
```json
{
  "name": "FreeBuf",
  "url": "https://www.freebuf.com/feed",
  "status": "healthy" | "degraded" | "unreachable" | "timeout" | "http_error" | "parse_error",
  "http_code": 200,
  "size_bytes": 16892,
  "response_time_ms": 340,
  "error": null,
  "entries_count": 8
}
```

**Status classification**:
- `healthy`: HTTP 200, size > 500, valid XML with entries
- `degraded`: HTTP 200 but size tiny or XML malformed
- `http_error`: HTTP 4xx/5xx
- `timeout`: request timed out
- `unreachable`: connection error / DNS fail
- `parse_error`: HTTP 200 but XML has no entries

### 2. `check_all_sources(sources, concurrency=6, timeout=15) -> (results, summary)`

**Input**: List of {name, url, tag} dicts
**Concurrency**: 6 parallel requests (one per source)
**Output**: (list of per-source dicts, summary string)

**Summary format**: `"✅ 4/6 源正常：FreeBuf、4hou、安全派、Paper Seebug；❌ 2/6 失败：Dark Reading(timeout)、The Register(http_error)"`

### 3. `main()` — Prerun Script Entry

- Reads sources from `FEEDS` constant (inline, same as security_news.py)
- Calls `check_all_sources()`
- Prints JSON to stdout
- Returns exit 0 (always — even all-fail is informative)

### 4. `FEEDS` Constant

Exact same sources as `security_news.py`:
```python
FEEDS = [
    {"name": "FreeBuf",      "url": "https://www.freebuf.com/feed",               "tag": "技术社区"},
    {"name": "4hou",         "url": "https://www.4hou.com/feed",                  "tag": "技术社区"},
    {"name": "安全派",         "url": "https://www.secpulse.com/feed",              "tag": "技术社区"},
    {"name": "Paper Seebug", "url": "https://paper.seebug.org/rss/",              "tag": "漏洞预警"},
    {"name": "Dark Reading", "url": "https://www.darkreading.com/rss.xml",        "tag": "国际媒体"},
    {"name": "The Register", "url": "https://www.theregister.com/security/headlines.atom", "tag": "国际媒体"},
]
```

---

## Acceptance Criteria

- [x] `python3 rss_health_checker.py` 输出有效 JSON
- [x] 6个源并发检查，15s超时，总耗时 < 5s
- [x] HTTP 200 + valid XML + entries → `healthy`
- [x] HTTP 200 + empty XML → `parse_error`
- [x] HTTP 4xx/5xx → `http_error`
- [x] curl timeout (exit 28) → `timeout`
- [x] Connection error → `unreachable`
- [x] Summary string正确反映 healthy/degraded/unhealthy 源
- [x] 单元测试覆盖所有 status 类型 (mock httpx)
- [x] 集成测试用真实源 (real HTTP, can fail fast)
- [x] No feedparser import — only httpx + stdlib

---

## File Structure

```
cron/
  rss_health_checker.py    ← 主脚本（prerun script）
  tests/
    test_rss_health_checker.py  ← 单元测试（mock）+ 集成测试（real）
```

---

## Integration with Cron Scheduler

`scheduler.py` 的 prerun script 机制：
- `_run_job_script()` 执行 `bash script_path`
- stdout 注入 prompt 作为 `{output}` placeholder
- 安全资讯 job 添加 `script_path: ~/.hermes/scripts/rss_health_checker.py`

**但**：prerun script 的 stdout 作为 prompt 注入，但 JSON 不是有效的 prompt。
**决策**：prerun script 输出 human-readable 摘要文本（print(summary)），同时输出完整 JSON 到 stderr 或第二通道。
**替代方案**：prerun script 只负责修复 `feedparser` 问题 —— 将 `security_news.py` 改写为不依赖 feedparser，同时保留原有逻辑。

---

## Revised Integration Plan

由于 prerun stdout 会混入 prompt，rss_health_checker 作为**独立诊断工具**运行：
1. 用户手动 / 定时调用 `rss_health_checker.py` 诊断源健康
2. 如果发现问题，修复 `security_news.py` 的 feedparser 依赖

**更彻底的修复**：改写 `security_news.py` 使用 httpx + xml.etree，消除 feedparser 依赖。

---

## Test Scenarios

### Unit Tests (mock httpx)

| Scenario | Mock response | Expected status |
|---|---|---|
| All healthy | HTTP 200, valid RSS XML | `healthy` |
| HTTP 404 | HTTP 404 | `http_error` |
| Timeout | timeout | `timeout` |
| Connection error | ConnectionError | `unreachable` |
| Empty XML | HTTP 200, 0 entries | `parse_error` |
| Tiny response | HTTP 200, < 100 bytes | `degraded` |

### Integration Tests (real HTTP)

| Test | Expected |
|---|---|
| All 6 real sources | ≥ 4/6 `healthy` |
| Concurrent 6 requests | total time < 10s |
| JSON output is valid | `json.loads()` succeeds |
