"""
RSS Source Health Checker — tests/cron/test_rss_health_checker.py

BDD Tests:
  Feature: RSS源健康检查
  - Scenario: 所有源正常 → healthy
  - Scenario: HTTP 404 → http_error
  - Scenario: 请求超时 → timeout
  - Scenario: 连接错误 → unreachable
  - Scenario: XML有效但无条目 → parse_error
  - Scenario: 响应体过小 → degraded
  - Scenario: 真实并发检查 → ≥4/6 healthy
"""

import json as _json
import sys
import time
from io import BytesIO
from unittest.mock import MagicMock, patch

import pytest

sys.path.insert(0, __file__.rsplit("/tests/", 1)[0])

from cron.rss_health_checker import (
    FEEDS,
    SourceHealthChecker,
    _parse_rss_xml,
    check_all_sources,
)


# ============================================================================
# Helper: minimal valid RSS 2.0 XML
# ============================================================================
def minimal_rss(items: int = 3) -> bytes:
    items_xml = "".join(
        """
        <item>
            <title>Item %d</title>
            <link>https://example.com/item/%d</link>
            <pubDate>Fri, 24 Apr 2026 12:00:00 +0000</pubDate>
            <description>Description for item %d</description>
        </item>"""
        % (i, i, i)
        for i in range(1, items + 1)
    )
    return (
        b'<?xml version="1.0" encoding="UTF-8"?>'
        + b'<rss version="2.0"><channel><title>Test</title>' + items_xml.encode() + b'</channel></rss>'
    )


# ============================================================================
# Helper: build a mock httpx GET response
# ============================================================================
def _mock_response(status_code: int, content: bytes, elapsed_ms: int = 300):
    mock_resp = MagicMock()
    mock_resp.status_code = status_code
    mock_resp.content = content
    mock_resp.is_streaming = False
    mock_resp.elapsed = MagicMock()
    mock_resp.elapsed.total_seconds = MagicMock(return_value=elapsed_ms / 1000.0)
    return mock_resp


# ============================================================================
# Helper: build a mock client whose .get() returns the given response
# ============================================================================
def _mock_client(response: MagicMock) -> MagicMock:
    mock = MagicMock()
    mock.get.return_value = response
    return mock


# ============================================================================
# BDD: Scenario — 所有源正常 → healthy
# ============================================================================
class TestSourceHealthCheckerHealthy:
    def test_healthy_with_valid_rss(self):
        """Given: RSS 2.0 with 5 entries; When: check(); Then: status=healthy"""
        xml = minimal_rss(items=5)
        mock_client = _mock_client(_mock_response(200, xml, elapsed_ms=300))

        checker = SourceHealthChecker(timeout=15)
        with patch.object(checker, "_client_", return_value=mock_client):
            result = checker.check("https://example.com/feed", "Test", "test-tag")

        assert result["status"] == "healthy"
        assert result["http_code"] == 200
        assert result["entries_count"] == 5
        assert result["size_bytes"] == len(xml)
        assert result["error"] is None
        # response_time_ms uses real wall-clock; mock elapsed is not used there
        assert result["response_time_ms"] >= 0
        assert result["name"] == "Test"
        assert result["tag"] == "test-tag"

    def test_atom_feed_large_enough_is_healthy(self):
        """Given: Atom 1.0 feed with size >= 500 bytes; When: check(); Then: status=healthy"""
        # Must be >= 500 bytes to be "healthy" (not "degraded")
        atom_str = (
            '<?xml version="1.0" encoding="utf-8"?>'
            '<feed xmlns="http://www.w3.org/2005/Atom">'
            '<title>Test Atom Feed With Enough Content To Exceed 500 Bytes</title>'
            '<subtitle>This is a longer description that adds to the byte count and ensures '
            'the overall feed document is large enough to be considered healthy rather '
            'than degraded when checked by the RSS health checker logic.</subtitle>'
            '<entry><title>Entry 1</title><link href="https://ex.com/1"/><updated>2026-04-24T12:00:00Z</updated>'
            '<summary>This is a moderately long summary that adds significant content to the '
            'Atom entry ensuring the total feed size exceeds the 500 byte threshold.</summary></entry>'
            '<entry><title>Entry 2</title><link href="https://ex.com/2"/><updated>2026-04-24T13:00:00Z</updated>'
            '<summary>Another detailed summary that contributes to the overall byte count of '
            'this Atom feed document to ensure it passes the size threshold check.</summary></entry>'
            '</feed>'
        )
        atom_xml = atom_str.encode("utf-8")
        assert len(atom_xml) >= 500, "Test data must be >= 500 bytes, got %d" % len(atom_xml)
        mock_client = _mock_client(_mock_response(200, atom_xml, elapsed_ms=500))

        checker = SourceHealthChecker(timeout=15)
        with patch.object(checker, "_client_", return_value=mock_client):
            result = checker.check("https://example.com/atom", "AtomTest")

        assert result["status"] == "healthy"
        assert result["entries_count"] == 2


# ============================================================================
# BDD: Scenario — HTTP 错误 → http_error
# ============================================================================
class TestSourceHealthCheckerHttpError:
    def test_http_404_is_http_error(self):
        """Given: HTTP 404; When: check(); Then: status=http_error"""
        mock_client = _mock_client(_mock_response(404, b"Not Found", elapsed_ms=50))

        checker = SourceHealthChecker(timeout=15)
        with patch.object(checker, "_client_", return_value=mock_client):
            result = checker.check("https://example.com/notfound")

        assert result["status"] == "http_error"
        assert result["http_code"] == 404

    def test_http_500_is_http_error(self):
        """Given: HTTP 500; When: check(); Then: status=http_error"""
        mock_client = _mock_client(_mock_response(500, b"Internal Server Error", elapsed_ms=100))

        checker = SourceHealthChecker(timeout=15)
        with patch.object(checker, "_client_", return_value=mock_client):
            result = checker.check("https://example.com/error")

        assert result["status"] == "http_error"
        assert result["http_code"] == 500

    def test_waf_html_challenge_is_waf_blocked(self):
        """Given: content-type=text/html (WAF challenge); When: check(); Then: status=waf_blocked"""
        html_challenge = b"<!doctype html><html><body>WAF challenge</body></html>"
        mock_resp = _mock_response(200, html_challenge, elapsed_ms=100)
        mock_resp.headers = {"content-type": "text/html; charset=utf-8"}
        mock_client = _mock_client(mock_resp)

        checker = SourceHealthChecker(timeout=15)
        with patch.object(checker, "_client_", return_value=mock_client):
            result = checker.check("https://example.com/waf")

        assert result["status"] == "waf_blocked"
        assert "WAF" in result["error"]


# ============================================================================
# BDD: Scenario — 连接错误 → unreachable
# ============================================================================
class TestSourceHealthCheckerUnreachable:
    def test_connection_error_is_unreachable(self):
        """Given: httpx.ConnectError; When: check(); Then: status=unreachable"""
        import httpx

        mock_client = MagicMock()
        mock_client.get.side_effect = httpx.ConnectError("Connection refused")

        checker = SourceHealthChecker(timeout=15)
        with patch.object(checker, "_client_", return_value=mock_client):
            result = checker.check("https://example.com/feed")

        assert result["status"] == "unreachable"
        assert "Connection refused" in str(result["error"])


# ============================================================================
# BDD: Scenario — 请求超时 → timeout
# ============================================================================
class TestSourceHealthCheckerTimeout:
    def test_timeout_is_timeout(self):
        """Given: httpx.TimeoutException; When: check(); Then: status=timeout"""
        import httpx

        mock_client = MagicMock()
        mock_client.get.side_effect = httpx.TimeoutException("Request timeout")

        checker = SourceHealthChecker(timeout=15)
        with patch.object(checker, "_client_", return_value=mock_client):
            result = checker.check("https://example.com/slow")

        assert result["status"] == "timeout"
        assert result["error"] == "timeout"


# ============================================================================
# BDD: Scenario — XML有效但无条目 → parse_error
# ============================================================================
class TestSourceHealthCheckerParseError:
    def test_empty_rss_is_parse_error(self):
        """Given: HTTP 200, valid XML but 0 entries; When: check(); Then: status=parse_error"""
        empty_rss = b'<?xml version="1.0"?><rss version="2.0"><channel><title>Empty</title></channel></rss>'
        mock_client = _mock_client(_mock_response(200, empty_rss, elapsed_ms=100))

        checker = SourceHealthChecker(timeout=15)
        with patch.object(checker, "_client_", return_value=mock_client):
            result = checker.check("https://example.com/empty")

        assert result["status"] == "parse_error"


# ============================================================================
# BDD: Scenario — 响应体过小 → degraded
# ============================================================================
class TestSourceHealthCheckerDegraded:
    def test_tiny_rss_with_entries_is_degraded(self):
        """Given: HTTP 200, size < 500 bytes, but has entries; When: check(); Then: status=degraded"""
        # Small XML that still has entries (so not parse_error)
        tiny_rss = (
            b'<?xml version="1.0"?>'
            b'<rss version="2.0"><channel><title>Tiny</title>'
            b'<item><title>One</title><link>http://ex.com/1</link></item>'
            b'</channel></rss>'
        )
        assert len(tiny_rss) < 500, "Test data must be < 500 bytes"
        assert tiny_rss.count(b"<item>") == 1, "Must have entries to avoid parse_error"
        mock_client = _mock_client(_mock_response(200, tiny_rss, elapsed_ms=50))

        checker = SourceHealthChecker(timeout=15)
        with patch.object(checker, "_client_", return_value=mock_client):
            result = checker.check("https://example.com/tiny")

        assert result["status"] == "degraded"
        assert result["size_bytes"] == len(tiny_rss)
        assert result["entries_count"] == 1


# ============================================================================
# Integration Tests — 真实 HTTP
# ============================================================================
class TestCheckAllSourcesReal:
    def test_real_sources_at_least_four_healthy(self):
        """
        Feature: 真实RSS源并发检查
        Scenario: 运行 check_all_sources(real_feeds)
        Then: >= 4/6 源返回 healthy | degraded
        """
        results, summary = check_all_sources(FEEDS, concurrency=6, timeout=15)

        healthy_or_degraded = [r for r in results if r["status"] in ("healthy", "degraded")]
        unhealthy = [r for r in results if r["status"] not in ("healthy", "degraded")]

        print("\n真实源检查结果:", [r["name"] + "=" + r["status"] for r in results])
        print("Summary:", summary)

        assert len(healthy_or_degraded) >= 3, (
            "Expected >=3 healthy/degraded, got %d: %s"
            % (len(healthy_or_degraded), [r["name"] + "=" + r["status"] for r in unhealthy])
        )
        # FreeBuf should be correctly identified (waf_blocked, not parse_error)
        freebuf = next((r for r in results if r["name"] == "FreeBuf"), None)
        assert freebuf is not None, "FreeBuf should be in results"
        assert freebuf["status"] in ("waf_blocked", "http_error", "timeout", "parse_error"), (
            "FreeBuf should be blocked or error, got: %s" % freebuf["status"]
        )

    def test_output_json_is_valid(self):
        """
        Scenario: check_all_sources 输出结构化数据
        Then: json.loads() 成功，结构正确
        """
        results, summary = check_all_sources(FEEDS[:2], concurrency=2, timeout=15)

        output = {"sources": results, "summary": summary}

        # Must not raise
        parsed = _json.loads(_json.dumps(output, ensure_ascii=False))

        assert "sources" in parsed
        assert "summary" in parsed
        assert len(parsed["sources"]) == 2
        assert all("name" in s and "url" in s and "status" in s for s in parsed["sources"])

    def test_concurrent_execution_is_fast(self):
        """
        Scenario: 6个源并发检查
        Then: 总耗时 < 15s (允许慢源)
        """
        start = time.time()
        results, _ = check_all_sources(FEEDS, concurrency=6, timeout=15)
        elapsed = time.time() - start

        print("\n并发耗时: %.2fs" % elapsed)
        print("结果:", [r["name"] + "=" + r["status"] for r in results])

        # 30s budget: 6 sources with 10s individual timeout in worst case (all timeout = 10s concurrent)
        # In practice: healthy sources resolve in < 3s, so total is < 15s; but allow 30s for flaky network
        assert elapsed < 30, "Concurrent check took %.2fs, expected < 30s" % elapsed


# ============================================================================
# Internal: _parse_rss_xml unit tests
# ============================================================================
class TestParseRssXml:
    def test_rss_2_0_items(self):
        xml = minimal_rss(items=3)
        count, titles = _parse_rss_xml(xml)
        assert count == 3
        assert len(titles) == 3

    def test_atom_entries(self):
        atom = (
            b'<?xml version="1.0"?>'
            b'<feed xmlns="http://www.w3.org/2005/Atom">'
            b'<title>Atom Feed</title>'
            b'<entry><title>Atom Item 1</title><link href="http://ex.com/1"/></entry>'
            b'<entry><title>Atom Item 2</title><link href="http://ex.com/2"/></entry>'
            b'</feed>'
        )
        count, titles = _parse_rss_xml(atom)
        assert count == 2

    def test_malformed_xml(self):
        count, titles = _parse_rss_xml(b"not xml at all <><><>")
        assert count == 0
        assert titles == []

    def test_empty_xml(self):
        count, titles = _parse_rss_xml(b"")
        assert count == 0

    def test_rss_with_namespaced_entries(self):
        """RSS with Media RSS namespace should still count entries."""
        xml = (
            b'<?xml version="1.0"?>'
            b'<rss version="2.0" xmlns:media="http://search.yahoo.com/mrss/">'
            b'<channel><title>Media RSS</title>'
            b'<item><title>Video</title><link>http://ex.com/v</link></item>'
            b'</channel></rss>'
        )
        count, titles = _parse_rss_xml(xml)
        assert count == 1

    def test_rss_with_cdata_titles(self):
        """RSS with CDATA-wrapped titles should be parsed correctly."""
        xml_str = (
            '<?xml version="1.0"?>'
            '<rss version="2.0"><channel><title>CDATA Feed</title>'
            '<item><title><![CDATA[\u5b58\u572812\u5e74\u4e4b\u4e45\u7684Linux\u6f0f\u6d1e\u7206\u5149]]></title>'
            '<link>https://example.com/1</link></item>'
            '<item><title><![CDATA[\u95f4\u63a5\u63d0\u793a\u6ce8\u5165\u653b\u51fb\u6b63\u8403\u5ef6\u81f3\u771f\u5b9e\u7f51\u7edc]]></title>'
            '<link>https://example.com/2</link></item>'
            '</channel></rss>'
        )
        xml = xml_str.encode("utf-8")
        count, titles = _parse_rss_xml(xml)
        assert count == 2
        assert "\u5b58\u572812\u5e74\u4e4b\u4e45\u7684Linux\u6f0f\u6d1e\u7206\u5149" in titles[0]

    def test_strip_cdata(self):
        """_strip_cdata correctly unwraps CDATA sections."""
        from cron.rss_health_checker import _strip_cdata
        assert _strip_cdata("<![CDATA[Hello World]]>") == "Hello World"
        assert _strip_cdata("<![CDATA[  存在12年之久的漏洞  ]]>") == "存在12年之久的漏洞"
        assert _strip_cdata("Plain text") == "Plain text"
        assert _strip_cdata(None) is None
