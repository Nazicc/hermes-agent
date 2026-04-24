"""
skills_quality.core — Core quality validation engine.

Classes:
- SkillParser       — Parse SKILL.md into structured SkillFile
- PedagogicScorer   — Score pedagogic depth (teaching/anti-patterns/examples)
- DependencyGraph   — Build and analyze skill reference graph
- TriggerValidator  — Validate trigger/anti-trigger configuration
- QualityReport     — Generate full corpus quality report

Result dataclasses:
- SkillFile         — Parsed SKILL.md
- ValidationResult  — Structure validation result
- PedagogicScore    — Pedagogic depth score
- TriggerResult    — Trigger validation result
- ReferenceResult  — Reference validation result
- ReportResult     — Full quality report result
"""

from __future__ import annotations

import os
import re
import yaml
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


# ---------------------------------------------------------------------------
# Global caches (reset per test via reset_singletons fixture)
# ---------------------------------------------------------------------------

_CACHE: dict = {}
_GRAPH_CACHE: dict = {}
_parsed_skills: dict = {}


# ---------------------------------------------------------------------------
# Dataclasses
# ---------------------------------------------------------------------------

@dataclass
class SkillFile:
    """Parsed SKILL.md file."""
    name: Optional[str]
    description: Optional[str]
    intent: Optional[str]
    skill_type: Optional[str]
    frontmatter: dict
    content: str
    raw_content: str
    sections: dict  # section_name -> section_content
    line_count: int
    path: Path
    errors: list = field(default_factory=list)
    warnings: list = field(default_factory=list)


@dataclass
class ValidationResult:
    """Structure validation result."""
    errors: list
    warnings: list
    profile: str  # stub | partial | full
    missing_sections: list


@dataclass
class StructValidationResult(ValidationResult):
    """Alias for structure validation result."""
    pass


@dataclass
class PedagogicScore:
    """Pedagogic depth score breakdown."""
    total: int
    tier: str  # stub | developing | good | excellent
    teaching: int        # 0-2
    anti_patterns: int   # 0-2
    examples: int        # 0-2
    when_not_to_use: int # 0-2
    cross_references: int # 0-2
    named_failures: list[str]


@dataclass
class TriggerResult:
    """Trigger validation result."""
    has_triggers: bool
    triggers: list[str]
    anti_triggers: list[str]
    warnings: list
    has_chinese: bool
    has_intent: bool
    has_anti_triggers: bool  # whether anti_triggers field is non-empty
    coverage_score: int
    triggers_bonus: int
    chinese_bonus: int
    anti_trigger_bonus: int
    intent_bonus: int


@dataclass
class ReferenceResult:
    """Reference validation result."""
    valid_refs: list
    broken_refs: list
    warnings: list


@dataclass
class ReportResult:
    """Full quality report result."""
    summary: dict
    skills: list
    top_improvements: list


# ---------------------------------------------------------------------------
# SkillParser
# ---------------------------------------------------------------------------

class SkillParser:
    """
    Parse a SKILL.md file into a SkillFile dataclass.

    Usage:
        parser = SkillParser(skills_dir="/path/to/skills")
        skill = parser.parse(Path("/path/to/skills/my-skill/SKILL.md"))
    """

    FRONTMATTER_RE = re.compile(r'^---\s*\n(.*?)\n---\s*\n', re.DOTALL)
    SECTION_RE = re.compile(r'^##\s+(.+)\s*\n', re.MULTILINE)

    def __init__(self, skills_dir: str | Path):
        self.skills_dir = Path(skills_dir)

    def parse(self, skill_path: str | Path) -> SkillFile:
        """Parse a SKILL.md file."""
        path = Path(skill_path)
        try:
            raw = path.read_text(encoding="utf-8")
        except Exception as e:
            return SkillFile(
                name=None, description=None, intent=None, skill_type=None,
                frontmatter={}, content="", raw_content="", sections={},
                line_count=0, path=path,
                errors=[f"PARSE_ERROR: {e}"]
            )

        lines = raw.splitlines()
        line_count = len(lines)
        content = raw.strip()

        # Parse frontmatter
        fm_match = self.FRONTMATTER_RE.match(raw)
        frontmatter = {}
        if fm_match:
            try:
                frontmatter = yaml.safe_load(fm_match.group(1)) or {}
            except yaml.YAMLError:
                frontmatter = {}
                raw_errors = ["PARSE_ERROR: YAML frontmatter invalid"]
        else:
            raw_errors = ["PARSE_ERROR: No frontmatter"]

        name = frontmatter.get("name")
        description = frontmatter.get("description", "")
        intent = frontmatter.get("intent", "")
        skill_type = frontmatter.get("type", "")

        errors = []
        if name is None:
            errors.append("MISSING_NAME")
        if description and len(description) > 200:
            errors.append("DESCRIPTION_TOO_LONG")

        # Parse sections
        sections = {}
        section_matches = list(self.SECTION_RE.finditer(raw))
        for i, match in enumerate(section_matches):
            title = match.group(1).strip().lower()
            start = match.end()
            end = section_matches[i + 1].start() if i + 1 < len(section_matches) else len(raw)
            sections[title] = raw[start:end].strip()

        return SkillFile(
            name=name,
            description=description,
            intent=intent,
            skill_type=skill_type,
            frontmatter=frontmatter,
            content=content,
            raw_content=raw,
            sections=sections,
            line_count=line_count,
            path=path,
            errors=errors
        )

    def parse_skill_by_name(self, skill_name: str) -> Optional[SkillFile]:
        """Parse a skill by its name (looks for skills_dir/<name>/SKILL.md)."""
        path = self.skills_dir / skill_name / "SKILL.md"
        if not path.exists():
            # Try subdirs
            for item in self.skills_dir.rglob("SKILL.md"):
                if item.parent.name == skill_name:
                    path = item
                    break
        if not path.exists():
            return None
        return self.parse(path)


# ---------------------------------------------------------------------------
# Structure Validation
# ---------------------------------------------------------------------------

def validate_structure(skill: SkillFile) -> StructValidationResult:
    """Validate skill structure against required sections."""
    errors = list(skill.errors)
    warnings = []
    missing_sections = []

    # Determine profile
    if skill.line_count < 10:
        profile = "stub"
        if len(skill.sections) == 0:
            errors.append("NO_SECTIONS")
        return StructValidationResult(
            errors=errors, warnings=warnings,
            profile=profile, missing_sections=missing_sections
        )

    if skill.line_count < 50:
        profile = "partial"
        # Partial: just need name + description
        return StructValidationResult(
            errors=errors, warnings=warnings,
            profile=profile, missing_sections=missing_sections
        )

    # Full profile (≥50 lines)
    profile = "full"
    required = ["purpose"]
    optional_key = ["key concepts", "application"]

    for req in required:
        if req not in skill.sections:
            errors.append(f"MISSING_REQUIRED_SECTION: ## {req.title()}")
            missing_sections.append(req)

    # Check for cross-references in References section
    has_references = any("reference" in s.lower() for s in skill.sections)
    if not has_references:
        warnings.append("NO_REFERENCES_SECTION")

    # Classify as interactive if it has question patterns
    has_options = bool(re.search(r'^\d+\.\s', skill.content, re.MULTILINE))
    if skill.skill_type == "interactive" and not has_options:
        warnings.append("INTERACTIVE_NO_OPTIONS")

    return StructValidationResult(
        errors=errors, warnings=warnings,
        profile=profile, missing_sections=missing_sections
    )


# ---------------------------------------------------------------------------
# Skill Type Classification
# ---------------------------------------------------------------------------

def classify_skill_type(skill: SkillFile) -> str:
    """Classify skill type: workflow | interactive | component | unknown."""
    content_lower = skill.content.lower()

    # Explicit type from frontmatter
    explicit = (skill.skill_type or "").lower()
    if explicit in ("workflow", "interactive", "component"):
        return explicit

    # Heuristics from content
    # Workflow: phase markers, step markers, orchestrates other skills
    phase_markers = re.findall(r'\b(phase|step|stage)\s*\d+', content_lower)
    workflow_refs = re.findall(r'orchestrates?|references?|invokes?|calls?\s+skills?', content_lower)
    if len(phase_markers) >= 2 or len(workflow_refs) >= 1:
        return "workflow"

    # Interactive: question patterns and numbered options
    questions = re.findall(r'\?\s*$', content_lower, re.MULTILINE)
    options = re.findall(r'^\d+\.\s+\*\*', content_lower, re.MULTILINE)
    if len(questions) >= 2 and len(options) >= 1:
        return "interactive"

    # Component: has template/artifact sections but not workflow phases
    template_markers = re.findall(r'(template|example|artifact|canvas)', content_lower)
    if len(template_markers) >= 1:
        return "component"

    # Unknown
    if len(skill.sections) == 0:
        return "unknown"

    return "component"


# ---------------------------------------------------------------------------
# Pedagogic Scorer
# ---------------------------------------------------------------------------

class PedagogicScorer:
    """
    Score pedagogic depth across 5 dimensions (0-2 each, total 0-10).

    Inspired by PM-Skills "ABC: Always Be Coaching" principle.
    """

    def score(self, skill: SkillFile) -> PedagogicScore:
        """Score a skill's pedagogic depth."""
        teaching = self._score_teaching(skill)
        anti_patterns = self._score_anti_patterns(skill)
        examples = self._score_examples(skill)
        when_not = self._score_when_not_to_use(skill)
        cross_refs = self._score_cross_references(skill)

        total = teaching + anti_patterns + examples + when_not + cross_refs
        tier = self._tier(total)
        named_failures = self._extract_named_failures(skill)

        return PedagogicScore(
            total=total,
            tier=tier,
            teaching=teaching,
            anti_patterns=anti_patterns,
            examples=examples,
            when_not_to_use=when_not,
            cross_references=cross_refs,
            named_failures=named_failures
        )

    def _score_teaching(self, skill: SkillFile) -> int:
        """Score teaching dimension (Why This Works)."""
        content = skill.content
        # Check for "Why This Works" or similar section
        why_patterns = [
            r'why this works',
            r'why it works',
            r'why do we',
            r'reasoning',
            r'principle',
        ]
        has_why = any(re.search(p, content, re.IGNORECASE) for p in why_patterns)
        if has_why:
            # Check depth: at least 2 sentences or 1 paragraph
            why_section = re.search(r'(why this works.*?)(\n##|\Z)', content, re.IGNORECASE | re.DOTALL)
            if why_section:
                text = why_section.group(1)
                sentences = re.findall(r'[.!?]+', text)
                if len(sentences) >= 2:
                    return 2
                return 1
            return 1
        return 0

    def _teaching_tier(self, text: str) -> int:
        """Helper: tier teaching based on text length."""
        sentences = re.findall(r'[.!?]+', text)
        if len(sentences) >= 3:
            return 2
        if len(sentences) >= 1:
            return 1
        return 0

    def _score_anti_patterns(self, skill: SkillFile) -> int:
        """Score anti-patterns dimension."""
        content = skill.content
        # Check for anti-patterns section or named failures
        anti_patterns_section = re.search(
            r'(anti-?patterns?|common pitfalls|what this is not|反面模式)',
            content, re.IGNORECASE
        )
        named_failures = self._extract_named_failures(skill)

        if not anti_patterns_section and not named_failures:
            return 0

        if len(named_failures) >= 3:
            return 2
        if len(named_failures) >= 1:
            return 1
        if anti_patterns_section:
            return 1
        return 0

    def _extract_named_failures(self, skill: SkillFile) -> list:
        """Extract named failure modes from content."""
        content = skill.content
        # Pattern: **Name** — description or *Consequence*
        named = re.findall(r'\*\*(.+?)\*\*\s*[-—]', content)
        # Also: "Failure Mode: Name" pattern
        failure_names = re.findall(r'(?:failure mode|anti-?pattern)[:\s]+([A-Z][\w\s]+)', content, re.IGNORECASE)
        return list(set(named + failure_names))

    def _score_examples(self, skill: SkillFile) -> int:
        """Score examples dimension."""
        content = skill.content
        # Count code blocks or labeled examples
        code_blocks = len(re.findall(r'```', content))
        example_sections = len(re.findall(r'##\s+examples?', content, re.IGNORECASE))
        labeled_examples = len(re.findall(r'(?:good|bad|example)[:\s]+\*\*', content, re.IGNORECASE))

        example_count = example_sections + labeled_examples
        if example_sections >= 2 or labeled_examples >= 3:
            return 2
        if example_sections >= 1 or labeled_examples >= 1:
            return 1
        return 0

    def _score_when_not_to_use(self, skill: SkillFile) -> int:
        """Score When NOT to Use dimension."""
        content = skill.content
        # Check for "When NOT to Use" or "When not to use"
        patterns = [
            r'when not to use',
            r'when\s+not\s+use',
            r'not\s+for\s+',
            r'do\s+not\s+use\s+when',
            r'avoid\s+when',
        ]
        has_boundary = any(re.search(p, content, re.IGNORECASE) for p in patterns)
        if not has_boundary:
            return 0
        # Check depth: at least 2 distinct boundary conditions
        boundaries = re.findall(r"(?:not for|avoid|don.t|when not)", content, re.IGNORECASE)
        if len(boundaries) >= 3:
            return 2
        return 1

    def _score_cross_references(self, skill: SkillFile) -> int:
        """Score cross-references dimension."""
        from skills_quality.core import extract_references
        refs = extract_references(skill)
        if len(refs) >= 5:
            return 2
        if len(refs) >= 2:
            return 1
        if len(refs) >= 1:
            return 0
        return 0

    def _tier(self, total: int) -> str:
        """Map total score to tier."""
        if total <= 3:
            return "stub"
        if total <= 6:
            return "developing"
        if total <= 8:
            return "good"
        return "excellent"


# ---------------------------------------------------------------------------
# Reference Extraction
# ---------------------------------------------------------------------------

def extract_references(skill: SkillFile) -> list[str]:
    """Extract referenced skill names from content."""
    content = skill.content
    # Match skills/SKILL.md or skills/skill-name/SKILL.md patterns
    pattern = r'skills/([a-z0-9_-]+)/SKILL\.md'
    matches = re.findall(pattern, content, re.IGNORECASE)
    return list(set(matches))


def validate_references(skill: SkillFile, skills_dir: str | Path) -> ReferenceResult:
    """Validate skill references against the filesystem."""
    skills_dir = Path(skills_dir)
    refs = extract_references(skill)
    valid = []
    broken = []

    for ref in refs:
        ref_path = skills_dir / ref / "SKILL.md"
        if not ref_path.exists():
            # Try recursive search
            found = False
            for item in skills_dir.rglob("SKILL.md"):
                if item.parent.name == ref:
                    found = True
                    break
            if not found:
                broken.append(ref)
            else:
                valid.append(ref)
        else:
            valid.append(ref)

    warnings = []
    if broken:
        warnings.append(f"BROKEN_REFERENCE: {', '.join(broken)}")

    return ReferenceResult(valid_refs=valid, broken_refs=broken, warnings=warnings)


# ---------------------------------------------------------------------------
# Dependency Graph
# ---------------------------------------------------------------------------

class DependencyGraph:
    """
    Build and analyze skill dependency graph.

    Usage:
        graph = DependencyGraph(skills_dir="/path/to/skills")
        graph.build()
        print(graph.cycles)   # list of circular reference paths
        print(graph.orphans)  # skills with no edges
    """

    def __init__(self, skills_dir: str | Path):
        self.skills_dir = Path(skills_dir)
        self.nodes: dict = {}
        self.edges: dict = {}
        self.cycles: list = []
        self.orphans: list = []
        self.leaf_nodes: list = []

    def build(self) -> None:
        """Build the dependency graph from all SKILL.md files."""
        parser = SkillParser(self.skills_dir)

        # Collect all skills
        skill_files = {}
        for item in self.skills_dir.rglob("SKILL.md"):
            skill = parser.parse(item)
            if skill.name:
                skill_files[skill.name] = skill

        # Build edges
        for name, skill in skill_files.items():
            refs = extract_references(skill)
            self.nodes[name] = {
                "references": refs,
                "referenced_by": [],
                "path": str(skill.path),
            }
            for ref in refs:
                if ref not in self.nodes:
                    # Reference to non-existent skill
                    self.nodes[ref] = {"references": [], "referenced_by": [], "path": ""}
                if name not in self.nodes[ref]["referenced_by"]:
                    self.nodes[ref]["referenced_by"].append(name)

        # Detect orphans (no refs out, no refs in)
        self.orphans = [
            name for name, node in self.nodes.items()
            if len(node["references"]) == 0 and len(node["referenced_by"]) == 0
        ]

        # Leaf nodes (no incoming edges)
        self.leaf_nodes = [
            name for name, node in self.nodes.items()
            if len(node["referenced_by"]) == 0 and len(node["references"]) > 0
        ]

        # Detect cycles using DFS
        self._detect_cycles()

    def _detect_cycles(self) -> None:
        """Detect all cycles using DFS."""
        visited = set()
        rec_stack = set()
        path = []

        def dfs(node: str) -> list:
            cycles_found = []
            visited.add(node)
            rec_stack.add(node)
            path.append(node)

            for neighbor in self.nodes.get(node, {}).get("references", []):
                if neighbor not in visited:
                    result = dfs(neighbor)
                    cycles_found.extend(result)
                elif neighbor in rec_stack:
                    # Found cycle
                    cycle_start = path.index(neighbor)
                    cycle = path[cycle_start:] + [neighbor]
                    cycles_found.append(cycle)

            path.pop()
            rec_stack.remove(node)
            return cycles_found

        for node in self.nodes:
            if node not in visited:
                found = dfs(node)
                for cycle in found:
                    if cycle not in self.cycles:
                        self.cycles.append(cycle)


# ---------------------------------------------------------------------------
# Trigger Validator
# ---------------------------------------------------------------------------

class TriggerValidator:
    """
    Validate trigger and anti-trigger configuration.
    """

    def validate(self, skill: SkillFile) -> TriggerResult:
        """Validate trigger configuration."""
        fm = skill.frontmatter
        triggers = fm.get("trigger", [])
        if isinstance(triggers, str):
            triggers = [triggers]
        anti_triggers = fm.get("anti_trigger", [])
        if isinstance(anti_triggers, str):
            anti_triggers = [anti_triggers]

        has_triggers = len(triggers) > 0
        has_anti_triggers = len(anti_triggers) > 0
        has_intent = bool(skill.intent)
        has_chinese = bool(
            re.search(r'[\u4e00-\u9fff]', skill.description or "") or
            re.search(r'[\u4e00-\u9fff]', " ".join(triggers))
        )

        warnings = []
        if has_triggers and len(triggers) < 3:
            warnings.append("FEW_TRIGGERS")
        if has_triggers and has_anti_triggers:
            # Check for overlap (anti-trigger is negation of trigger)
            for t in triggers:
                for at in anti_triggers:
                    if t.lower().strip() in at.lower().replace("don't ", "").replace("not ", ""):
                        warnings.append("TRIGGER_ANTITRIGGER_OVERLAP")
                        break

        # Coverage score components
        triggers_bonus = 1 if len(triggers) >= 3 else 0
        chinese_bonus = 1 if has_chinese else 0
        anti_trigger_bonus = 1 if has_anti_triggers else 0
        intent_bonus = 1 if has_intent else 0
        coverage_score = triggers_bonus + chinese_bonus + anti_trigger_bonus + intent_bonus

        return TriggerResult(
            has_triggers=has_triggers,
            triggers=triggers,
            anti_triggers=anti_triggers,
            warnings=warnings,
            has_chinese=has_chinese,
            has_intent=has_intent,
            has_anti_triggers=has_anti_triggers,
            coverage_score=coverage_score,
            triggers_bonus=triggers_bonus,
            chinese_bonus=chinese_bonus,
            anti_trigger_bonus=anti_trigger_bonus,
            intent_bonus=intent_bonus,
        )


# ---------------------------------------------------------------------------
# Quality Report
# ---------------------------------------------------------------------------

class QualityReport:
    """
    Generate full quality report for all skills in a directory.

    Usage:
        report = QualityReport(skills_dir="/path/to/skills")
        result = report.generate(tier="stub", sort="score")
    """

    def __init__(self, skills_dir: str | Path):
        self.skills_dir = Path(skills_dir)
        self.parser = SkillParser(self.skills_dir)
        self.scorer = PedagogicScorer()
        self.trigger_validator = TriggerValidator()

    def generate(
        self,
        tier: str = "all",
        sort: str = "score",
        limit: int = 10
    ) -> ReportResult:
        """Generate quality report."""
        # Build graph
        graph = DependencyGraph(self.skills_dir)
        graph.build()

        skills_data = []
        tier_counts = {"stub": 0, "developing": 0, "good": 0, "excellent": 0}

        for item in self.skills_dir.rglob("SKILL.md"):
            skill = self.parser.parse(item)
            if not skill.name:
                continue

            pscore = self.scorer.score(skill)
            tier_counts[pscore.tier] += 1

            # Classify type
            skill_type = classify_skill_type(skill)

            # Validate structure
            struct = validate_structure(skill)

            # Validate references
            ref_result = validate_references(skill, self.skills_dir)

            # Trigger validation
            trigger_result = self.trigger_validator.validate(skill)

            # Compute improvement potential
            potential = 10 - pscore.total

            skill_dict = {
                "name": skill.name,
                "path": str(skill.path),
                "line_count": skill.line_count,
                "profile": struct.profile,
                "type": skill_type,
                "pedagogic_score": pscore.total,
                "pedagogic_breakdown": {
                    "teaching": pscore.teaching,
                    "anti_patterns": pscore.anti_patterns,
                    "examples": pscore.examples,
                    "when_not_to_use": pscore.when_not_to_use,
                    "cross_references": pscore.cross_references,
                },
                "named_failures": pscore.named_failures,
                "errors": struct.errors + ref_result.warnings,
                "warnings": struct.warnings + trigger_result.warnings,
                "references": extract_references(skill),
                "referenced_by": graph.nodes.get(skill.name, {}).get("referenced_by", []),
                "potential_score": potential,
                "improvement_gap": potential,
            }
            skills_data.append(skill_dict)

        # Filter
        if tier != "all":
            skills_data = [s for s in skills_data if s["pedagogic_score"] <= 3]  # stub
            if tier == "developing":
                skills_data = [s for s in skills_data if 4 <= s["pedagogic_score"] <= 6]
            elif tier == "good":
                skills_data = [s for s in skills_data if 7 <= s["pedagogic_score"] <= 8]
            elif tier == "excellent":
                skills_data = [s for s in skills_data if s["pedagogic_score"] >= 9]

        # Sort
        if sort == "score":
            skills_data.sort(key=lambda s: s["pedagogic_score"], reverse=True)
        elif sort == "name":
            skills_data.sort(key=lambda s: s["name"])
        elif sort == "lines":
            skills_data.sort(key=lambda s: s["line_count"], reverse=True)
        elif sort == "improvement":
            skills_data.sort(key=lambda s: s["improvement_gap"], reverse=True)

        # Top improvements (stubs sorted by potential)
        top_improvements = sorted(
            [s for s in skills_data if s["pedagogic_score"] <= 6],
            key=lambda s: s["improvement_gap"],
            reverse=True
        )[:5]

        summary = {
            "total_skills": len(skills_data),
            "stubs": tier_counts["stub"],
            "developing": tier_counts["developing"],
            "good": tier_counts["good"],
            "excellent": tier_counts["excellent"],
            "broken_references": list(set(
                ref
                for s in skills_data
                for ref in s.get("references", [])
                if ref not in graph.nodes
            )),
            "circular_references": graph.cycles,
        }

        return ReportResult(
            summary=summary,
            skills=skills_data[:limit],
            top_improvements=top_improvements,
        )
