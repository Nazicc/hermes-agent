#!/usr/bin/env python3
r"""
RSS Source Health Checker — cron/rss_health_checker.py

安全资讯日报 cron job 的预检脚本：
  - 并发检查6个RSS源可用性（httpx + stdlib xml，无 feedparser）
  - 分类：healthy / degraded / http_error / timeout / unreachable / parse_error
  - 输出结构化 JSON 摘要供诊断 / 上游决策

用法:
  python3 rss_health_checker.py              # 打印 summary + JSON
  python3 rss_health_checker.py --json        # 仅输出 JSON
  python3 rss_health_checker.py --sources 4hou,Dark\ Reading  # 仅检查指定源
"""

from __future__ import annotations

import argparse
import json
import sys
import time
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

import httpx


# =============================================================================
# RSS 订阅源配置（与 security_news.py 保持一致）
# =============================================================================

FEEDS: List[Dict[str, str]] = [
    {"name": "FreeBuf",      "url": "https://www.freebuf.com/feed",                "tag": "技术社区"},
    {"name": "4hou",         "url": "https://www.4hou.com/feed",                  "tag": "技术社区"},
    {"name": "安全派",        "url": "https://www.secpulse.com/feed",               "tag": "技术社区"},
    {"name": "Paper Seebug", "url": "https://paper.seebug.org/rss/",              "tag": "漏洞预警"},
    {"name": "Dark Reading", "url": "https://www.darkreading.com/rss.xml",         "tag": "国际媒体"},
    {"name": "The Register", "url": "https://www.theregister.com/security/headlines.atom", "tag": "国际媒体"},
]

HEALTHY_SOURCE_MIN_SIZE = 500  # bytes — less than this → degraded


# =============================================================================
# XML Parsing (stdlib only — no feedparser)
# =============================================================================

def _strip_cdata(text: Optional[str]) -> Optional[str]:
    """Remove CDATA wrapper if present, return clean text."""
    if text is None:
        return None
    stripped = text.strip()
    if stripped.startswith("<![CDATA[") and stripped.endswith("]]>"):
        return stripped[9:-3].strip()
    return stripped


def _element_text(el: "ET.Element") -> Optional[str]:
    """Get all text content of an element (including CDATA), joined."""
    parts = []
    if el.text:
        parts.append(el.text)
    for child in el:
        if child.tag == "NAK" or (hasattr(child, "tag") and child.tag.endswith("}CDATA")):
            if child.text:
                parts.append(child.text)
        parts.append(_element_text(child))
        if child.tail:
            parts.append(child.tail)
    result = "".join(parts)
    return result if result else None


def _parse_rss_xml(raw_bytes: bytes) -> Tuple[int, List[str]]:
    """
    Parse RSS 2.0 or Atom 1.0 XML, return (entry_count, list_of_titles).
    Uses xml.etree.ElementTree (stdlib) — no feedparser needed.
    Handles CDATA sections in RSS feeds.
    """
    try:
        root = ET.fromstring(raw_bytes)
    except ET.ParseError:
        return 0, []

    # Detect feed type
    tag = root.tag.lower()

    if "feed" in tag:  # Atom: <feed>
        entries = root.findall(".//{http://www.w3.org/2005/Atom}entry")
        if not entries:
            entries = root.findall(".//entry")  # non-namespaced
        titles = []
        for e in entries:
            t = e.find("{http://www.w3.org/2005/Atom}title")
            if t is None:
                t = e.find("title")
            if t is not None:
                raw = _element_text(t) or t.text
                clean = _strip_cdata(raw)
                if clean:
                    titles.append(clean)
        return len(entries), titles

    else:  # RSS 2.0 / other: <rss> or <rdf>
        # RSS items can be direct or inside <channel>
        items = root.findall(".//item")
        if not items:
            channel = root.find("channel")
            if channel is not None:
                items = channel.findall("item")

        titles = []
        for item in items:
            t = item.find("title")
            if t is not None:
                raw = _element_text(t) or t.text
                clean = _strip_cdata(raw)
                if clean:
                    titles.append(clean)
        return len(items), titles


# =============================================================================
# Source Health Checker
# =============================================================================

class SourceHealthChecker:
    """检查单个 RSS 源的健康状态"""

    def __init__(self, timeout: int = 15):
        self.timeout = timeout
        self._client: Optional[httpx.Client] = None

    def _client_(self) -> httpx.Client:
        if self._client is None:
            self._client = httpx.Client(
                timeout=httpx.Timeout(self.timeout, connect=10.0),
                follow_redirects=True,
                headers={
                    "User-Agent": (
                        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                        "AppleWebKit/537.36 (KHTML, like Gecko) "
                        "Chrome/120.0.0.0 Safari/537.36"
                    ),
                },
            )
        return self._client

    def close(self):
        if self._client:
            self._client.close()
            self._client = None

    def check(self, url: str, name: str = "", tag: str = "") -> Dict[str, Any]:
        """
        检查单个 RSS 源，返回结构化诊断 dict。

        Status 分类:
          healthy     — HTTP 200, size >= 500, XML 有条目
          degraded    — HTTP 200, size < 500, 条目正常
          http_error  — HTTP 4xx / 5xx
          timeout     — httpx TimeoutException
          unreachable — 连接错误（DNS / Refused / etc）
          parse_error — HTTP 200 但 XML 无条目
        """
        start = time.time()
        result: Dict[str, Any] = {
            "name": name,
            "url": url,
            "tag": tag,
            "status": "unreachable",
            "http_code": None,
            "size_bytes": 0,
            "response_time_ms": 0,
            "error": None,
            "entries_count": 0,
        }

        try:
            client = self._client_()
            response = client.get(url)
            elapsed_ms = int((time.time() - start) * 1000)
            result["response_time_ms"] = elapsed_ms
            result["http_code"] = response.status_code
            result["size_bytes"] = len(response.content)

            # HTTP 错误
            if response.status_code >= 400:
                result["status"] = "http_error"
                result["error"] = "HTTP %d" % response.status_code
                return result

            # 检测 WAF / JS 挑战页（content-type 是 text/html 而非 XML）
            content_type = response.headers.get("content-type", "").lower()
            if "text/html" in content_type:
                result["status"] = "waf_blocked"
                result["error"] = "WAF/JS challenge (content-type=text/html, not RSS)"
                return result

            # 解析 XML
            count, _ = _parse_rss_xml(response.content)
            result["entries_count"] = count

            if count == 0:
                result["status"] = "parse_error"
                result["error"] = "XML无条目或格式异常"
            elif result["size_bytes"] < HEALTHY_SOURCE_MIN_SIZE:
                result["status"] = "degraded"
            else:
                result["status"] = "healthy"

        except httpx.TimeoutException:
            elapsed_ms = int((time.time() - start) * 1000)
            result["response_time_ms"] = elapsed_ms
            result["status"] = "timeout"
            result["error"] = "timeout"

        except httpx.ConnectError as exc:
            elapsed_ms = int((time.time() - start) * 1000)
            result["response_time_ms"] = elapsed_ms
            result["status"] = "unreachable"
            result["error"] = str(exc)[:100]

        except Exception as exc:
            elapsed_ms = int((time.time() - start) * 1000)
            result["response_time_ms"] = elapsed_ms
            result["status"] = "unreachable"
            result["error"] = str(exc)[:100]

        return result


# =============================================================================
# Batch Check
# =============================================================================

def check_all_sources(
    sources: List[Dict[str, str]],
    concurrency: int = 6,
    timeout: int = 15,
) -> Tuple[List[Dict[str, Any]], str]:
    """
    并发检查所有 RSS 源，返回 (results, summary)。

    summary 格式:
      "✅ 4/6 源正常：FreeBuf、4hou、安全派、Paper Seebug；
       ❌ 2/6 失败：Dark Reading(timeout)、The Register(http_error)"
    """
    results: List[Dict[str, Any]] = []
    checker = SourceHealthChecker(timeout=timeout)

    with ThreadPoolExecutor(max_workers=concurrency) as pool:
        futures = {
            pool.submit(checker.check, src["url"], src["name"], src.get("tag", "")): src
            for src in sources
        }
        for future in as_completed(futures):
            src = futures[future]
            try:
                result = future.result()
            except Exception as exc:
                result = {
                    "name": src["name"],
                    "url": src["url"],
                    "tag": src.get("tag", ""),
                    "status": "unreachable",
                    "http_code": None,
                    "size_bytes": 0,
                    "response_time_ms": 0,
                    "error": str(exc)[:100],
                    "entries_count": 0,
                }
            results.append(result)

    checker.close()

    # Sort to match input order
    order = {src["name"]: i for i, src in enumerate(sources)}
    results.sort(key=lambda r: order.get(r["name"], 99))

    # Build summary
    summary = _build_summary(results)

    return results, summary


def _build_summary(results: List[Dict[str, Any]]) -> str:
    """生成人类可读摘要字符串"""
    healthy = [r for r in results if r["status"] == "healthy"]
    degraded = [r for r in results if r["status"] == "degraded"]
    failed = [r for r in results if r["status"] not in ("healthy", "degraded")]

    total = len(results)
    ok_count = len(healthy) + len(degraded)
    sep = "\uff0c"  # full-width comma

    parts = []
    if healthy or degraded:
        ok_names = [r["name"] for r in (healthy + degraded)]
        parts.append("\u2705 %d/%d 源正常：%s" % (ok_count, total, sep.join(ok_names)))
    if failed:
        fail_parts = []
        for r in failed:
            err = r["error"] or r["status"]
            fail_parts.append("%s(%s)" % (r["name"], err))
        parts.append("\u274c %d/%d 源失败：%s" % (len(failed), total, sep.join(fail_parts)))

    return "\uff1b".join(parts) if parts else "\u26a0 0/%d 源可用" % total


# =============================================================================
# CLI
# =============================================================================

def main():
    parser = argparse.ArgumentParser(description="RSS 源健康检查")
    parser.add_argument("--json", action="store_true", help="仅输出 JSON")
    parser.add_argument(
        "--sources",
        default=None,
        help="仅检查指定源（逗号分隔），如 --sources 4hou,Dark\\ Reading",
    )
    parser.add_argument(
        "--timeout", type=int, default=15, help="单源超时秒数（默认15）"
    )
    args = parser.parse_args()

    # Filter sources if requested
    feeds = FEEDS
    if args.sources:
        wanted = {n.strip() for n in args.sources.split(",")}
        feeds = [f for f in FEEDS if f["name"] in wanted]
        if not feeds:
            print(f"错误：未找到匹配的源，可用源：{[f['name'] for f in FEEDS]}", file=sys.stderr)
            sys.exit(1)

    results, summary = check_all_sources(feeds, concurrency=len(feeds), timeout=args.timeout)

    output = {
        "checked_at": datetime.now().isoformat(),
        "sources": results,
        "summary": summary,
    }

    if args.json:
        print(json.dumps(output, ensure_ascii=False, indent=2))
    else:
        # Human-readable: print summary then compact JSON
        print(f"\n{'='*50}")
        print(f"RSS 源健康检查 — {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*50}")
        print(f"\n📡 {summary}\n")
        print("详细结果：")
        for r in results:
            status_icon = {"healthy": "✅", "degraded": "⚠️", "http_error": "❌",
                           "timeout": "⏱️", "unreachable": "🚫", "parse_error": "📭"}.get(r["status"], "?")
            print(f"  {status_icon} {r['name']}: {r['status']} "
                  f"(HTTP {r['http_code']}, {r['size_bytes']}B, "
                  f"{r['response_time_ms']}ms, {r['entries_count']}条)"
                  + (f" — {r['error']}" if r['error'] else ""))
        print(f"\n完整 JSON：")
        print(json.dumps(output, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
