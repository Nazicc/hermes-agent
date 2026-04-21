#!/usr/bin/env python3
"""
hermes-eval — Hermes Agent Skill Evaluation Harness
===================================================
自动化评测 Hermes skills 的工具。

用法:
  python3 harness.py                           # 跑全部 suite
  python3 harness.py --skill systematic-debugging  # 跑单个 skill
  python3 harness.py --suite software-development  # 跑整个 suite
  python3 harness.py --list                       # 列出所有可用 suites

输出:
  results/{timestamp}_{skill}.json   # 详细结果
  stdout: 表格化摘要
"""

import argparse
import json
import os
import sys
import time
import yaml
from dataclasses import dataclass, asdict, field
from datetime import datetime
from pathlib import Path
from typing import Optional

# ─── 配置 ────────────────────────────────────────────────────────────────────

SKILL_EVAL_DIR = Path(__file__).parent
SUITES_DIR = SKILL_EVAL_DIR / "suites"
RESULTS_DIR = SKILL_EVAL_DIR / "results"

# MiniMax LLM 评测
LLM_MODEL = "MiniMax-M2.7"
LLM_BASE_URL = "https://api.minimaxi.com/v1"
LLM_API_KEY = os.environ.get("OPENAI_API_KEY", "")

SKILLS_BASE = Path.home() / ".hermes" / "skills"


# ─── 数据模型 ────────────────────────────────────────────────────────────────

@dataclass
class TestCase:
    id: str
    description: str
    type: str           # reasoning | command | file_edit | output_match
    input: str
    expected: str
    timeout: int = 60


@dataclass
class SuiteResult:
    skill: str
    version: str
    total: int
    passed: int
    failed: int
    skipped: int
    score: float       # 0.0–1.0
    duration_ms: int
    cases: list[dict]
    timestamp: str


@dataclass
class EvalReport:
    report_version: str = "1.0.0"
    hermes_version: str = ""
    eval_timestamp: str = ""
    total_suites: int = 0
    total_skills: int = 0
    total_cases: int = 0
    total_passed: int = 0
    total_failed: int = 0
    overall_score: float = 0.0
    suites: list[SuiteResult] = field(default_factory=list)


# ─── LLM Judge ──────────────────────────────────────────────────────────────

def llm_judge(prompt: str, expected: str, actual: str) -> tuple[bool, str]:
    """
    用 MiniMax 作为 judge 评判 LLM 输出是否符合预期。
    返回 (pass: bool, reason: str)
    """
    if not LLM_API_KEY:
        return _keyword_judge(actual, expected)

    try:
        import openai
        client = openai.OpenAI(api_key=LLM_API_KEY, base_url=LLM_BASE_URL)
        response = client.chat.completions.create(
            model=LLM_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are an impartial judge evaluating an AI agent's response.\n"
                        "Judge PASS (return true) only if the response substantively addresses "
                        "the expected behavior. Partial answers score PASS.\n"
                        "Judge FAIL (return false) only if the response is completely wrong, "
                        "off-topic, or missing the core requirement.\n"
                        "Respond ONLY with valid JSON: {\"pass\": true/false, \"reason\": \"...\"}"
                    ),
                },
                {
                    "role": "user",
                    "content": (
                        f"Expected behavior: {expected}\n\n"
                        f"Actual response: {actual}\n\n"
                        f"Input: {prompt}\n\n"
                        "Respond with JSON only."
                    ),
                },
            ],
            temperature=0.1,
            max_tokens=256,
        )
        raw = response.choices[0].message.content or "{}"
        # 去除 markdown fence
        raw = raw.strip().strip("```json").strip("```").strip()
        result = json.loads(raw)
        return bool(result.get("pass", False)), result.get("reason", "")
    except Exception as e:
        return _keyword_judge(actual, expected)


def _keyword_judge(actual: str, expected: str) -> tuple[bool, str]:
    """关键词回退裁判 — 无 API key 时使用"""
    exp_keywords = set(expected.lower().split())
    act_lower = actual.lower()
    matched = sum(1 for kw in exp_keywords if kw in act_lower)
    ratio = matched / len(exp_keywords) if exp_keywords else 0
    return ratio >= 0.4, f"keyword match {matched}/{len(exp_keywords)}"


# ─── Case 执行 ───────────────────────────────────────────────────────────────

def execute_reasoning(case: TestCase, skill_path: Path) -> tuple[bool, str]:
    """推理类测试：读 SKILL.md，让 LLM 模拟 skill 执行，judge 输出"""
    skill_md = skill_path / "SKILL.md"
    if not skill_md.exists():
        return False, f"SKILL.md not found: {skill_md}"

    content = skill_md.read_text()
    truncated = content[: 12_000]  # 防止 context 溢出

    prompt = (
        f"You are executing the skill: {case.id}\n\n"
        f"## Skill Content (truncated)\n{truncated}\n\n"
        f"## Task\n{case.input}\n\n"
        f"## Expected\n{case.expected}"
    )

    if not LLM_API_KEY:
        return False, "SKIP: no OPENAI_API_KEY"

    try:
        import openai
        client = openai.OpenAI(api_key=LLM_API_KEY, base_url=LLM_BASE_URL)
        response = client.chat.completions.create(
            model=LLM_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=512,
        )
        actual = response.choices[0].message.content or ""
    except Exception as e:
        return False, f"LLM error: {e}"

    passed, reason = llm_judge(case.input, case.expected, actual)
    return passed, reason


def execute_command(case: TestCase, skill_path: Path) -> tuple[bool, str]:
    """命令类测试：在 skill 目录执行命令，检查 exit code 和输出"""
    import subprocess

    skill_md = skill_path / "SKILL.md"
    if not skill_md.exists():
        return False, f"SKILL.md not found"

    # 从 case.expected 解析 "exit:0 keyword:XXX"
    parts = case.expected.split("|")
    expected_exit = 0
    expected_kw = ""
    for p in parts:
        p = p.strip()
        if p.startswith("exit:"):
            expected_exit = int(p.split(":")[1])
        elif p.startswith("keyword:"):
            expected_kw = p.split(":", 1)[1].strip()

    try:
        result = subprocess.run(
            case.input,
            shell=True,
            cwd=str(skill_path),
            capture_output=True,
            text=True,
            timeout=case.timeout,
        )
        exit_ok = result.returncode == expected_exit
        kw_ok = expected_kw in result.stdout or expected_kw in result.stderr
        passed = exit_ok and (not expected_kw or kw_ok)
        reason = f"exit={result.returncode} expected={expected_exit}"
        if expected_kw:
            reason += f", keyword={expected_kw} {'found' if kw_ok else 'NOT found'}"
        return passed, reason
    except subprocess.TimeoutExpired:
        return False, f"TIMEOUT after {case.timeout}s"
    except Exception as e:
        return False, f"Error: {e}"


def execute_file_edit(case: TestCase, skill_path: Path) -> tuple[bool, str]:
    """文件编辑类测试：检查文件是否存在或包含特定内容"""
    parts = case.expected.split("|")
    expected_file = parts[0].strip()
    expected_content = parts[1].strip() if len(parts) > 1 else ""

    target = skill_path / expected_file
    if not target.exists():
        return False, f"File not found: {expected_file}"

    if expected_content:
        content = target.read_text()
        found = expected_content in content
        return found, f"content {'found' if found else 'NOT found'}: {expected_content[:60]}"
    return True, "file exists"


def execute_output_match(case: TestCase, _: Path) -> tuple[bool, str]:
    """输出匹配类测试：检查输出是否包含预期字符串"""
    passed = case.expected in case.input
    reason = f"{'matched' if passed else 'NOT matched'}: {case.expected[:60]}"
    return passed, reason


# ─── Suite 执行 ──────────────────────────────────────────────────────────────

def load_suite(suite_path: Path) -> dict:
    with open(suite_path, encoding="utf-8") as f:
        return yaml.safe_load(f)


def run_suite(suite_path: Path) -> SuiteResult:
    """运行一个 YAML suite，返回 SuiteResult"""
    data = load_suite(suite_path)
    skill_name = data["skill"]
    version = data.get("version", "unknown")
    cases: list[dict] = data.get("cases", [])

    skill_base = SKILLS_BASE
    # skill 可能在两层目录 (category/skill-name)
    skill_path = skill_base / data.get("category", "software-development") / skill_name
    if not skill_path.exists():
        # 尝试直接搜索
        found = next(skill_path.parent.glob(skill_name), None)
        if found:
            skill_path = found

    total = len(cases)
    passed = failed = skipped = 0
    case_results = []
    start = time.time()

    for case_data in cases:
        case = TestCase(
            id=case_data["id"],
            description=case_data.get("description", ""),
            type=case_data.get("type", "reasoning"),
            input=case_data["input"],
            expected=case_data["expected"],
            timeout=case_data.get("timeout", 60),
        )

        t0 = time.time()
        try:
            if case.type == "reasoning":
                ok, reason = execute_reasoning(case, skill_path)
            elif case.type == "command":
                ok, reason = execute_command(case, skill_path)
            elif case.type == "file_edit":
                ok, reason = execute_file_edit(case, skill_path)
            elif case.type == "output_match":
                ok, reason = execute_output_match(case, skill_path)
            else:
                ok, reason = False, f"Unknown type: {case.type}"
        except Exception as e:
            ok, reason = False, f"Exception: {e}"
        duration_ms = int((time.time() - t0) * 1000)

        status = "PASS" if ok else "FAIL"
        if reason.startswith("SKIP"):
            status = "SKIP"
            skipped += 1
        elif ok:
            passed += 1
        else:
            failed += 1

        case_results.append({
            "id": case.id,
            "type": case.type,
            "status": status,
            "reason": reason,
            "duration_ms": duration_ms,
        })

    duration_ms = int((time.time() - start) * 1000)
    score = passed / total if total > 0 else 0.0

    return SuiteResult(
        skill=skill_name,
        version=version,
        total=total,
        passed=passed,
        failed=failed,
        skipped=skipped,
        score=score,
        duration_ms=duration_ms,
        cases=case_results,
        timestamp=datetime.now().isoformat(),
    )


def save_result(result: SuiteResult):
    ts = datetime.now().strftime("%Y%m%d-%H%M%S")
    path = RESULTS_DIR / f"{ts}_{result.skill}.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(asdict(result), f, ensure_ascii=False, indent=2)


# ─── 主程序 ─────────────────────────────────────────────────────────────────

def print_table(results: list[SuiteResult]):
    header = f"{'Skill':<40} {'Ver':<10} {'Pass':>5} {'Fail':>5} {'Skip':>5} {'Score':>7} {'Time':>7}"
    sep = "-" * len(header)
    print()
    print(header)
    print(sep)
    for r in results:
        bar = "█" * int(r.score * 10) + "░" * (10 - int(r.score * 10))
        print(f"{r.skill:<40} {r.version:<10} {r.passed:>5} {r.failed:>5} {r.skipped:>5} {bar} {r.duration_ms:>6}ms")
    print(sep)
    total_pass = sum(r.passed for r in results)
    total_fail = sum(r.failed for r in results)
    total_skip = sum(r.skipped for r in results)
    total_cases = sum(r.total for r in results)
    overall = total_pass / total_cases if total_cases > 0 else 0
    print(f"{'OVERALL':<40} {'':<10} {total_pass:>5} {total_fail:>5} {total_skip:>5} {overall:>7.1%}")
    print()


def main():
    parser = argparse.ArgumentParser(description="Hermes Skill Evaluation Harness")
    parser.add_argument("--skill", help="Run specific skill only")
    parser.add_argument("--suite", help="Run all skills in a suite YAML")
    parser.add_argument("--list", action="store_true", help="List available suites")
    parser.add_argument("--output", help="Output JSON report path")
    args = parser.parse_args()

    RESULTS_DIR.mkdir(exist_ok=True)

    if args.list:
        print("Available suites:")
        for p in sorted(SUITES_DIR.glob("*.yaml")):
            print(f"  {p.stem}")
        return

    # 发现 suites
    if args.skill:
        # 查找单个 skill 的 suite
        matches = list(SUITES_DIR.glob(f"*_{args.skill}.yaml"))
        if not matches:
            print(f"ERROR: No suite found for skill '{args.skill}'")
            sys.exit(1)
        suite_paths = matches
    elif args.suite:
        suite_paths = [SUITES_DIR / f"{args.suite}.yaml"]
        if not suite_paths[0].exists():
            print(f"ERROR: Suite not found: {args.suite}")
            sys.exit(1)
    else:
        suite_paths = sorted(SUITES_DIR.glob("*.yaml"))

    print(f"[hermes-eval] {len(suite_paths)} suite(s) found")
    print(f"[hermes-eval] Results dir: {RESULTS_DIR}")

    results: list[SuiteResult] = []
    for sp in suite_paths:
        print(f"\n▶  Running: {sp.stem}")
        try:
            result = run_suite(sp)
            save_result(result)
            results.append(result)
            status = "✅" if result.score >= 0.8 else "⚠️ " if result.score >= 0.5 else "❌"
            print(f"   {status} {result.skill}: {result.passed}/{result.total} passed ({result.score:.0%})")
        except Exception as e:
            print(f"   ❌ ERROR: {e}")

    if results:
        print_table(results)

        # 写汇总报告
        ts = datetime.now().strftime("%Y%m%d-%H%M%S")
        summary = {
            "report_version": "1.0.0",
            "eval_timestamp": datetime.now().isoformat(),
            "total_suites": len(results),
            "total_cases": sum(r.total for r in results),
            "total_passed": sum(r.passed for r in results),
            "total_failed": sum(r.failed for r in results),
            "overall_score": sum(r.passed for r in results) / sum(r.total for r in results),
            "results": [asdict(r) for r in results],
        }
        summary_path = RESULTS_DIR / f"summary_{ts}.json"
        with open(summary_path, "w", encoding="utf-8") as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)
        print(f"[hermes-eval] Summary: {summary_path}")

        if args.output:
            with open(args.output, "w", encoding="utf-8") as f:
                json.dump(summary, f, ensure_ascii=False, indent=2)

        # Exit code: 0 if all pass, 1 if any fail
        all_pass = all(r.failed == 0 for r in results)
        sys.exit(0 if all_pass else 1)
    else:
        print("No suites run.")


if __name__ == "__main__":
    main()
