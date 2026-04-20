#!/usr/bin/env python3
"""
Bridge Integration Tests
验证 hermes_to_evolver_bridge.py 的完整数据流
"""
import json
import subprocess
import sys
from pathlib import Path

HERMES_BRIDGE = Path.home() / ".hermes/hermes-agent/scripts/hermes_to_evolver_bridge.py"
OUTPUT_DIR = Path.home() / ".openclaw/agents/hermes-agent/sessions"
RTK_METRICS = Path.home() / ".hermes/hermes-agent/evolver/assets/gep/rtk_metrics.jsonl"
AGENT_NAME = "hermes-agent"


def test_bridge_runs_successfully():
    """1. Bridge 脚本能正常运行不报错"""
    result = subprocess.run(
        [sys.executable, str(HERMES_BRIDGE)],
        capture_output=True, text=True, timeout=30,
        env={**subprocess.os.environ, "AGENT_NAME": AGENT_NAME}
    )
    assert result.returncode == 0, f"Bridge failed: {result.stderr}"
    print("✓ Bridge runs successfully")


def test_session_files_are_valid_jsonl():
    """2. Session 文件是合法的 JSONL，每行都是有效 JSON"""
    files = list(OUTPUT_DIR.glob("session_*.jsonl"))
    assert len(files) > 0, f"No session files in {OUTPUT_DIR}"

    total_records = 0
    for f in sorted(files, key=lambda x: -x.stat().st_mtime)[:5]:  # 最近5个
        with open(f) as fh:
            for i, line in enumerate(fh):
                line = line.strip()
                assert line, f"{f.name} line {i+1} is empty"
                try:
                    rec = json.loads(line)
                except json.JSONDecodeError as e:
                    raise AssertionError(f"{f.name} line {i+1} is not valid JSON: {e}\nContent: {line[:200]}")
                # 验证必要字段
                assert "type" in rec, f"{f.name} line {i+1} missing 'type' field"
                assert "timestamp" in rec, f"{f.name} line {i+1} missing 'timestamp' field"
                assert "content" in rec, f"{f.name} line {i+1} missing 'content' field"
                assert rec["type"] in ("system", "assistant", "tool_use", "user"), \
                    f"{f.name} line {i+1} has invalid type: {rec['type']}"
                total_records += 1

    print(f"✓ {total_records} session records valid across recent files")
    return total_records


def test_session_files_not_huge():
    """3. Session 文件不过大（每条记录 content 不超过 2000 chars）"""
    files = list(OUTPUT_DIR.glob("session_*.jsonl"))
    for f in sorted(files, key=lambda x: -x.stat().st_mtime)[:3]:
        with open(f) as fh:
            for i, line in enumerate(fh):
                rec = json.loads(line.strip())
                if rec["type"] in ("assistant", "tool_use", "user"):
                    content_len = len(rec.get("content", ""))
                    assert content_len <= 2010, \
                        f"{f.name} line {i+1} content too long ({content_len} chars): {rec['content'][:100]}"
    print("✓ Session content sizes OK")


def test_rtk_metrics_file_valid():
    """4. RTK metrics 文件是合法的 JSONL"""
    if not RTK_METRICS.exists():
        print(f"⚠ RTK metrics file not found at {RTK_METRICS} (may be created on next bridge run)")
        return

    with open(RTK_METRICS) as fh:
        lines = fh.readlines()

    assert len(lines) >= 1, "RTK metrics file is empty"
    for i, line in enumerate(lines):
        rec = json.loads(line.strip())
        assert "timestamp" in rec, f"rtk_metrics line {i+1} missing timestamp"
        assert "total_commands" in rec, f"rtk_metrics line {i+1} missing total_commands"
        assert "savings_pct" in rec, f"rtk_metrics line {i+1} missing savings_pct"
        # 验证合理范围
        assert 0 <= rec["savings_pct"] <= 100, f"rtk_metrics savings_pct out of range: {rec['savings_pct']}"
        assert rec["total_commands"] >= 0, f"rtk_metrics total_commands negative: {rec['total_commands']}"

    print(f"✓ RTK metrics file valid ({len(lines)} records)")


def test_no_double_escaped_json():
    """5. Session 内容不包含双转义的 JSON（tool call JSON 不被嵌入为字符串）"""
    files = list(OUTPUT_DIR.glob("session_*.jsonl"))
    for f in sorted(files, key=lambda x: -x.stat().st_mtime)[:3]:
        with open(f) as fh:
            for i, line in enumerate(fh):
                rec = json.loads(line.strip())
                content = rec.get("content", "")
                # 检查是否包含双重转义序列（如 \\" 而不是 \"）
                if "tool_use" in rec["type"] or "assistant" in rec["type"]:
                    # 不应该有 \"command\": 这样的内嵌 JSON
                    assert '\\"command\\":' not in content and '\\"command\\":"' not in content, \
                        f"{f.name} line {i+1} appears to have embedded JSON in content: {content[:150]}"
    print("✓ No embedded JSON in session content")


def test_rtk_binary_accessible():
    """6. rtk 二进制在 PATH 中可访问"""
    result = subprocess.run(
        ["rtk", "gain"],
        capture_output=True, text=True, timeout=10,
        env={**subprocess.os.environ, "PATH": subprocess.os.environ.get("PATH", "") + ":/Users/can/.local/bin"}
    )
    assert result.returncode == 0, f"rtk gain failed: {result.stderr}"
    print(f"✓ rtk binary accessible, output:\n{result.stdout.strip()}")


def main():
    tests = [
        test_bridge_runs_successfully,
        test_session_files_are_valid_jsonl,
        test_session_files_not_huge,
        test_no_double_escaped_json,
        test_rtk_metrics_file_valid,
        test_rtk_binary_accessible,
    ]

    passed = 0
    failed = 0
    for t in tests:
        try:
            t()
            passed += 1
        except AssertionError as e:
            print(f"✗ {t.__name__}: {e}")
            failed += 1
        except Exception as e:
            print(f"✗ {t.__name__}: Unexpected error: {e}")
            failed += 1

    print(f"\n{'='*50}")
    print(f"Results: {passed} passed, {failed} failed")
    if failed:
        sys.exit(1)
    print("All tests passed!")


if __name__ == "__main__":
    main()
