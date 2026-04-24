#!/usr/bin/env python3
"""
skills_quality_mcp — FastMCP server for Hermes Skills Quality Framework.

Exposes 7 tools:
1. quality_validate_skill    — Validate single skill structure
2. quality_score_skill       — Score pedagogic depth
3. quality_check_references  — Validate cross-references
4. quality_report_all        — Generate full quality report
5. quality_find_stubs        — List all stub skills
6. quality_suggest_improvements — Get improvement suggestions
7. quality_check_trigger     — Validate triggers/anti-triggers

Usage:
    python skills_quality_mcp.py                    # starts server
    hermes mcp add skills-quality --command python --args skills_quality_mcp.py
"""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Optional

# Add skills_quality to path
# skills_quality_mcp.py is at skills_quality/skills_quality_mcp.py
# the package is at skills_quality/skills_quality/ (one level up from skills_quality/)
_module_dir = Path(__file__).parent  # skills_quality/ directory
_package_dir = _module_dir.parent  # parent of skills_quality/ directory
sys.path.insert(0, str(_package_dir))

from skills_quality.core import (
    SkillParser,
    PedagogicScorer,
    DependencyGraph,
    TriggerValidator,
    QualityReport,
    validate_structure,
    classify_skill_type,
    extract_references,
    validate_references,
    PedagogicScore,
    ReportResult,
)

# ---------------------------------------------------------------------------
# FastMCP server setup
# ---------------------------------------------------------------------------

try:
    from mcp.server.fastmcp import FastMCP
    HAS_FASTMCP = True
except ImportError:
    HAS_FASTMCP = False


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

HERMES_SKILLS_DIR = os.environ.get(
    "HERMES_SKILLS_DIR",
    str(Path.home() / ".hermes" / "skills")
)


def _get_skills_dir() -> str:
    """Get the skills directory, validate it exists."""
    d = HERMES_SKILLS_DIR
    if not Path(d).exists():
        raise FileNotFoundError(f"Skills directory not found: {d}")
    return d


def _format_pedagogic(score: PedagogicScore) -> str:
    """Format pedagogic score as readable string."""
    emoji_map = {"stub": "🗼", "developing": "📈", "good": "✅", "excellent": "⭐"}
    emoji = emoji_map.get(score.tier, "?")

    lines = [
        f"📊 Pedagogic Depth Score: {score.total}/10 — {score.tier.capitalize()}",
        "",
        f"  Teaching (Why This Works):     {score.teaching}/2 {'⭐⭐' if score.teaching == 2 else '⭐' if score.teaching else '✗'}",
        f"  Anti-Patterns:                {score.anti_patterns}/2 {'⭐⭐' if score.anti_patterns == 2 else '⭐' if score.anti_patterns else '✗'}",
    ]
    if score.named_failures:
        failures = ", ".join(score.named_failures[:3])
        lines.append(f"    Named: {failures}")
    lines.extend([
        f"  Examples:                     {score.examples}/2 {'⭐⭐' if score.examples == 2 else '⭐' if score.examples else '✗'}",
        f"  When NOT to Use:             {score.when_not_to_use}/2 {'⭐⭐' if score.when_not_to_use == 2 else '⭐' if score.when_not_to_use else '✗'}",
        f"  Cross-References:             {score.cross_references}/2 {'⭐⭐' if score.cross_references == 2 else '⭐' if score.cross_references else '✗'}",
        "",
        "  PM-Skills standard (7/10 minimum): " +
        ("✅ PASS" if score.total >= 7 else f"❌ GAP (need {7 - score.total} more)"),
    ])
    return "\n".join(lines)


def _format_struct_validation(skill_name: str, skill, struct_result) -> str:
    """Format structure validation result."""
    lines = [f"{'✅' if not struct_result.errors else '⚠️'} {skill_name} ({classify_skill_type(skill)}, {skill.line_count} lines, {struct_result.profile} profile)"]

    if struct_result.errors:
        lines.append("")
        lines.append("Structural Errors:")
        for err in struct_result.errors:
            lines.append(f"  ❌ {err}")
    else:
        lines.append("Structural Checks:")
        for sec in ["Purpose", "Key Concepts", "Examples", "Anti-Patterns"]:
            if sec.lower() in [s.lower() for s in skill.sections]:
                lines.append(f"  ✅ Has ## {sec} section")
            elif sec.lower() in ["purpose"]:
                lines.append(f"  ❌ MISSING: ## {sec}")
        if not struct_result.errors:
            lines.append("  ✅ All structural checks passed")

    if struct_result.warnings:
        lines.append("")
        lines.append("Warnings:")
        for w in struct_result.warnings:
            lines.append(f"  ⚠️ {w}")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# MCP Tools
# ---------------------------------------------------------------------------

if HAS_FASTMCP:
    mcp = FastMCP("skills-quality")

    @mcp.tool()
    def quality_validate_skill(skill_name: str) -> str:
        """
        Validate a single skill's structure.

        Returns a human-readable validation report including:
        - Profile classification (stub/partial/full)
        - Missing required sections
        - Pedagogic score breakdown
        - Trigger status
        """
        skills_dir = _get_skills_dir()
        parser = SkillParser(skills_dir=skills_dir)
        scorer = PedagogicScorer()
        trigger_validator = TriggerValidator()

        skill = parser.parse_skill_by_name(skill_name)
        if not skill:
            # Fuzzy suggest similar names
            from difflib import get_close_matches
            all_skills = []
            for item in Path(skills_dir).rglob("SKILL.md"):
                s = parser.parse(item)
                if s.name:
                    all_skills.append(s.name)
            suggestions = get_close_matches(skill_name, all_skills, n=3, cutoff=0.4)
            suggestion_text = ""
            if suggestions:
                suggestion_text = f"\n\nDid you mean one of: {', '.join(suggestions)}?"
            return f"❌ Skill '{skill_name}' not found.{suggestion_text}"

        struct = validate_structure(skill)
        score = scorer.score(skill)
        trigger_result = trigger_validator.validate(skill)

        lines = [
            _format_struct_validation(skill_name, skill, struct),
            "",
            _format_pedagogic(score),
        ]

        # Trigger info
        lines.append("")
        lines.append("🎯 Trigger Check:")
        if trigger_result.has_triggers:
            lines.append(f"  ✅ Has {len(trigger_result.triggers)} triggers")
            if len(trigger_result.triggers) <= 5:
                lines.append(f"  Triggers: {', '.join(trigger_result.triggers[:5])}")
        else:
            lines.append(f"  ⚠️ NO triggers (coverage: {trigger_result.coverage_score}/4)")
        if trigger_result.warnings:
            for w in trigger_result.warnings:
                lines.append(f"  ⚠️ {w}")

        # PM-Skills standard note
        if score.total < 7:
            lines.append("")
            lines.append(f"💡 Tip: Add ## Why This Works, ## Anti-Patterns (3+ named failures), and ## Examples to reach Good (7/10)")

        return "\n".join(lines)

    @mcp.tool()
    def quality_score_skill(skill_name: str) -> str:
        """
        Score a skill's pedagogic depth (0-10 across 5 dimensions).

        Dimensions: Teaching, Anti-Patterns, Examples, When NOT to Use, Cross-References
        Tiers: Stub (0-3), Developing (4-6), Good (7-8), Excellent (9-10)
        """
        skills_dir = _get_skills_dir()
        parser = SkillParser(skills_dir=skills_dir)
        scorer = PedagogicScorer()

        skill = parser.parse_skill_by_name(skill_name)
        if not skill:
            return f"❌ Skill '{skill_name}' not found."

        score = scorer.score(skill)
        return _format_pedagogic(score)

    @mcp.tool()
    def quality_check_references(skill_name: str) -> str:
        """
        Check cross-references for a skill.

        Returns valid/broken references and graph position.
        """
        skills_dir = _get_skills_dir()
        parser = SkillParser(skills_dir=skills_dir)

        skill = parser.parse_skill_by_name(skill_name)
        if not skill:
            return f"❌ Skill '{skill_name}' not found."

        refs = extract_references(skill)
        ref_result = validate_references(skill, skills_dir=skills_dir)

        lines = [f"🔗 Reference Check: {skill_name}", ""]

        if refs:
            lines.append("Referenced skills:")
            for ref in refs:
                status = "✅" if ref not in ref_result.broken_refs else "❌"
                lines.append(f"  {status} {ref}")
        else:
            lines.append("  (no references)")

        if ref_result.broken_refs:
            lines.append("")
            lines.append("⚠️ Broken references:")
            for br in ref_result.broken_refs:
                lines.append(f"  ❌ skills/{br}/SKILL.md — NOT FOUND")

        # Graph position
        graph = DependencyGraph(skills_dir=skills_dir)
        graph.build()
        node = graph.nodes.get(skill_name, {})
        refs_in = node.get("referenced_by", [])
        refs_out = node.get("references", [])

        if refs_in or refs_out:
            lines.append("")
            lines.append("Graph position:")
            lines.append(f"  Referenced by: {len(refs_in)} skill(s)")
            lines.append(f"  References: {len(refs_out)} skill(s)")
            if len(refs_in) == 0:
                lines.append("  🌿 Leaf node (not referenced by others)")
        else:
            lines.append("")
            lines.append("🌿 Orphan (no references, not referenced)")

        return "\n".join(lines)

    @mcp.tool()
    def quality_report_all(
        limit: int = 10,
        tier: str = "all",
        sort: str = "score"
    ) -> str:
        """
        Generate full quality report for all skills.

        Args:
            limit: Max skills to return (default 10)
            tier: Filter by stub|developing|good|excellent|all (default all)
            sort: Sort by score|lines|name|improvement (default score)
        """
        skills_dir = _get_skills_dir()
        report = QualityReport(skills_dir=skills_dir)

        try:
            result = report.generate(tier=tier, sort=sort, limit=limit)
        except Exception as e:
            return f"❌ Error generating report: {e}"

        summary = result.summary
        tier_emoji = {"stub": "🗼", "developing": "📈", "good": "✅", "excellent": "⭐"}
        tier_map = {"stub": summary["stubs"], "developing": summary["developing"], "good": summary["good"], "excellent": summary["excellent"]}

        lines = [
            f"📋 Hermes Skills Quality Report",
            f"",
            f"Total: {summary['total_skills']} skills",
            f"",
        ]

        # Tier distribution bar
        total = summary['total_skills'] or 1
        for tier_name in ["stub", "developing", "good", "excellent"]:
            count = tier_map.get(tier_name, 0)
            pct = count / total * 100
            bar_len = int(pct / 5)
            emoji = tier_emoji.get(tier_name, "?")
            lines.append(f"{emoji} {tier_name.capitalize():12s}: {count:3d} skills  {'█' * bar_len}{'░' * (20 - bar_len)} {pct:.1f}%")

        lines.extend(["", f"Top {len(result.skills)} by score:"])
        for i, s in enumerate(result.skills, 1):
            tier_char = {"stub": "🗼", "developing": "📈", "good": "✅", "excellent": "⭐"}.get(s["type"], "?")
            errors = len(s.get("errors", []))
            error_marker = f" ⚠️{errors}" if errors else ""
            lines.append(f"  {i}. {tier_char} {s['name']}: {s['pedagogic_score']}/10{error_marker}")

        if summary.get("broken_references"):
            lines.append("")
            lines.append(f"⚠️  {len(summary['broken_references'])} broken references detected")

        if summary.get("circular_references"):
            lines.append(f"🔄  {len(summary['circular_references'])} circular reference(s)")

        return "\n".join(lines)

    @mcp.tool()
    def quality_find_stubs() -> str:
        """
        List all stub skills (pedagogic score ≤ 3).

        These skills have only frontmatter — no Purpose, no Application, no Examples.
        Run quality_suggest_improvements on any skill below for specific upgrade path.
        """
        skills_dir = _get_skills_dir()
        report = QualityReport(skills_dir=skills_dir)

        result = report.generate(tier="stub", sort="score", limit=50)

        if not result.skills:
            return "✅ No stub skills found!"

        lines = [
            f"🚨 Stub Skills ({len(result.skills)} found — need major work):",
            ""
        ]
        for i, s in enumerate(result.skills, 1):
            lines.append(f"  {i}. **{s['name']}** ({s['line_count']} lines, {s['pedagogic_score']}/10)")

        lines.extend([
            "",
            "Run `quality_suggest_improvements` on any skill above for specific upgrade path."
        ])
        return "\n".join(lines)

    @mcp.tool()
    def quality_suggest_improvements(skill_name: str) -> str:
        """
        Get improvement suggestions for a specific skill.

        Shows current score, target tier, gap analysis, and prioritized action items.
        """
        skills_dir = _get_skills_dir()
        parser = SkillParser(skills_dir=skills_dir)
        scorer = PedagogicScorer()

        skill = parser.parse_skill_by_name(skill_name)
        if not skill:
            return f"❌ Skill '{skill_name}' not found."

        score = scorer.score(skill)
        current = score.total
        target = 7  # Good tier minimum

        lines = [
            f"💡 Improvement Path: {skill_name}",
            "",
            f"Current State: {score.tier.capitalize()} ({current}/10)",
            f"Target: Good (7/10 minimum)",
            f"GAP: +{target - current} points needed",
            "",
        ]

        gaps = []
        if score.teaching < 2:
            gaps.append(f"  ❌ Teaching (Why This Works): {score.teaching}→2 — Add a dedicated section explaining *why* this approach works")
        if score.anti_patterns < 2:
            gaps.append(f"  ❌ Anti-Patterns: {score.anti_patterns}→2 — Add 3+ named failure modes (e.g., **Feature Factory**, **Gold Plating**)")
        if score.examples < 2:
            gaps.append(f"  ❌ Examples: {score.examples}→2 — Add 2-3 concrete examples (good/bad/edge cases)")
        if score.when_not_to_use < 2:
            gaps.append(f"  ⚠️  When NOT to Use: {score.when_not_to_use}→2 — Add explicit boundary conditions")
        if score.cross_references < 2:
            gaps.append(f"  ⚠️  Cross-References: {score.cross_references}→2 — Link 3+ related skills")

        if gaps:
            lines.append("Gap Analysis:")
            lines.extend(gaps)

        lines.extend([
            "",
            "Priority Order:",
            "  1. Add ## Purpose section (quickest win, +1-2 pts)",
            "  2. Add ## Anti-Patterns with 3 named failure modes (+1-2 pts)",
            "  3. Add 2 examples with real-world traces (+1 pt)",
            "  4. Add ## When NOT to Use boundary (+1 pt)",
            "  5. Add ## References linking related skills (+1 pt)",
        ])

        estimated_lines = 0
        if score.teaching < 2:
            estimated_lines += 30
        if score.anti_patterns < 2:
            estimated_lines += 40
        if score.examples < 2:
            estimated_lines += 50
        if score.when_not_to_use < 2:
            estimated_lines += 15
        if score.cross_references < 2:
            estimated_lines += 10

        if estimated_lines:
            lines.append(f"\nEstimated: ~{estimated_lines} lines to reach Good (7/10)")

        return "\n".join(lines)

    @mcp.tool()
    def quality_check_trigger(skill_name: str) -> str:
        """
        Validate trigger and anti-trigger configuration for a skill.

        Checks trigger count, Chinese triggers, anti-triggers, and intent field.
        """
        skills_dir = _get_skills_dir()
        parser = SkillParser(skills_dir=skills_dir)
        trigger_validator = TriggerValidator()

        skill = parser.parse_skill_by_name(skill_name)
        if not skill:
            return f"❌ Skill '{skill_name}' not found."

        result = trigger_validator.validate(skill)

        lines = [
            f"🎯 Trigger Check: {skill_name}",
            f"",
            f"Trigger Coverage: {result.coverage_score}/4",
            "",
        ]

        components = [
            ("Has ≥3 triggers", bool(result.triggers_bonus), f"{len(result.triggers)} triggers"),
            ("Has Chinese triggers", bool(result.chinese_bonus), "中文关键词" if result.has_chinese else "none"),
            ("Has anti-triggers", bool(result.anti_trigger_bonus), f"{len(result.anti_triggers)} anti-triggers"),
            ("Has intent field", bool(result.intent_bonus), "✅" if result.has_intent else "❌"),
        ]

        for label, passed, detail in components:
            emoji = "✅" if passed else "⚠️"
            lines.append(f"  {emoji} {label}: {detail}")

        if result.triggers:
            lines.append("")
            lines.append("Trigger Keywords:")
            for t in result.triggers[:8]:
                lines.append(f"  - \"{t}\"")

        if result.anti_triggers:
            lines.append("")
            lines.append("Anti-Trigger Keywords:")
            for at in result.anti_triggers:
                lines.append(f"  - \"{at}\"")

        if result.warnings:
            lines.append("")
            lines.append("Warnings:")
            for w in result.warnings:
                lines.append(f"  ⚠️ {w}")
            if "NO_TRIGGERS" in result.warnings:
                lines.append("")
                lines.append("💡 Tip: Add 3+ trigger keywords and anti-triggers to frontmatter to improve discovery")

        return "\n".join(lines)

    @mcp.tool()
    def quality_list_skills(tier: str = "all", limit: int = 20) -> str:
        """
        List skills filtered by quality tier.

        Args:
            tier: Filter by stub|developing|good|excellent|all (default all)
            limit: Max skills to return (default 20)
        """
        skills_dir = _get_skills_dir()
        report = QualityReport(skills_dir=skills_dir)

        result = report.generate(tier=tier, sort="score", limit=limit)

        tier_emoji = {"stub": "🗼", "developing": "📈", "good": "✅", "excellent": "⭐"}

        lines = [f"📋 Skills ({tier}): {len(result.skills)} shown"]
        for s in result.skills:
            emoji = tier_emoji.get(s["type"], "?")
            lines.append(f"  {emoji} {s['name']}: {s['pedagogic_score']}/10 ({s['line_count']} lines)")

        return "\n".join(lines)

    def main():
        """Start the MCP server."""
        if not HAS_FASTMCP:
            print("ERROR: fastmcp not installed. Install with: pip install fastmcp", file=sys.stderr)
            sys.exit(1)
        mcp.run()

else:
    # Fallback: run as standalone CLI
    def main():
        print("FastMCP not installed. Run: pip install fastmcp", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
