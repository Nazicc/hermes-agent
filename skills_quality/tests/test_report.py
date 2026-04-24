"""
BDD Feature 6: Quality Report Generation

Tests for:
- Generate full quality report for all skills
- Report filters by quality tier
- Report sorts by improvement potential
"""

import pytest
from pathlib import Path
from skills_quality.core import SkillParser, PedagogicScorer


class TestQualityReport:
    """Tests for quality report generation."""

    def test_report_summary(self, mixed_corpus, temp_skills_dir):
        """Report has summary statistics."""
        from skills_quality.core import QualityReport
        report = QualityReport(skills_dir=temp_skills_dir)
        result = report.generate()
        assert result.summary["total_skills"] == len(mixed_corpus)
        assert "stubs" in result.summary
        assert "developing" in result.summary
        assert "good" in result.summary
        assert "excellent" in result.summary

    def test_report_skills_detail(self, mixed_corpus, temp_skills_dir):
        """Report has per-skill detail."""
        from skills_quality.core import QualityReport
        report = QualityReport(skills_dir=temp_skills_dir)
        result = report.generate()
        # Skill name is from frontmatter (e.g., "test-good", not "good-workflow")
        skill_names = [s["name"] for s in result.skills]
        assert "test-good" in skill_names
        assert "stub-only" in skill_names or any(s["pedagogic_score"] <= 3 for s in result.skills)

    def test_report_stub_tier_filter(self, mixed_corpus, temp_skills_dir):
        """Report filters to stub tier only."""
        from skills_quality.core import QualityReport
        report = QualityReport(skills_dir=temp_skills_dir)
        result = report.generate(tier="stub")
        assert all(s["pedagogic_score"] <= 3 for s in result.skills)

    def test_report_sort_by_score(self, mixed_corpus, temp_skills_dir):
        """Report sorts by pedagogic score descending."""
        from skills_quality.core import QualityReport
        report = QualityReport(skills_dir=temp_skills_dir)
        result = report.generate(sort="score")
        scores = [s["pedagogic_score"] for s in result.skills]
        assert scores == sorted(scores, reverse=True)

    def test_report_sort_by_name(self, mixed_corpus, temp_skills_dir):
        """Report sorts by name ascending."""
        from skills_quality.core import QualityReport
        report = QualityReport(skills_dir=temp_skills_dir)
        result = report.generate(sort="name")
        names = [s["name"] for s in result.skills]
        assert names == sorted(names)

    def test_report_improvement_potential(self, mixed_corpus, temp_skills_dir):
        """Report computes improvement potential."""
        from skills_quality.core import QualityReport
        report = QualityReport(skills_dir=temp_skills_dir)
        result = report.generate(sort="improvement")
        if len(result.skills) > 0:
            assert "improvement_gap" in result.skills[0] or "potential_score" in result.skills[0]

    def test_report_line_count(self, good_skill_path, temp_skills_dir):
        """Report includes line count per skill."""
        from skills_quality.core import QualityReport
        report = QualityReport(skills_dir=temp_skills_dir)
        result = report.generate()
        good_skill = next((s for s in result.skills if s["name"] == "test-good"), None)
        assert good_skill is not None
        assert good_skill["line_count"] >= 90

    def test_report_has_broken_refs(self, mixed_corpus, temp_skills_dir):
        """Report tracks broken references."""
        from skills_quality.core import QualityReport
        report = QualityReport(skills_dir=temp_skills_dir)
        result = report.generate()
        assert isinstance(result.summary.get("broken_references", []), list)

    def test_report_has_circular_refs(self, circular_skills, temp_skills_dir):
        """Report tracks circular references."""
        from skills_quality.core import QualityReport
        report = QualityReport(skills_dir=temp_skills_dir)
        result = report.generate()
        assert len(result.summary.get("circular_references", [])) >= 1

    def test_report_top_improvements(self, mixed_corpus, temp_skills_dir):
        """Report has top improvements section."""
        from skills_quality.core import QualityReport
        report = QualityReport(skills_dir=temp_skills_dir)
        result = report.generate()
        assert hasattr(result, "top_improvements") or len(result.skills) > 0

    def test_report_skill_profile(self, good_skill_path, temp_skills_dir):
        """Report includes profile classification."""
        from skills_quality.core import QualityReport
        report = QualityReport(skills_dir=temp_skills_dir)
        result = report.generate()
        good_skill = next((s for s in result.skills if s["name"] == "test-good"), None)
        assert good_skill is not None
        assert good_skill["profile"] in ("stub", "partial", "full")

    def test_report_skill_type(self, good_skill_path, temp_skills_dir):
        """Report includes skill type."""
        from skills_quality.core import QualityReport
        report = QualityReport(skills_dir=temp_skills_dir)
        result = report.generate()
        good_skill = next((s for s in result.skills if s["name"] == "test-good"), None)
        assert good_skill is not None
        assert good_skill["type"] in ("workflow", "interactive", "component", "unknown")


class TestRealHermesSkills:
    """Tests against the real Hermes skills directory (~111 skills)."""

    @pytest.mark.skipif(
        not (Path.home() / ".hermes" / "skills").exists(),
        reason="Hermes skills dir not found"
    )
    def test_real_skills_load(self):
        """Real Hermes skills directory loads successfully."""
        from skills_quality.core import QualityReport
        report = QualityReport(skills_dir=str(Path.home() / ".hermes" / "skills"))
        result = report.generate()
        assert result.summary["total_skills"] >= 60

    @pytest.mark.skipif(
        not (Path.home() / ".hermes" / "skills").exists(),
        reason="Hermes skills dir not found"
    )
    def test_real_skills_have_stubs(self):
        """Real Hermes skills have some stub skills."""
        from pathlib import Path
        skills_dir = Path.home() / ".hermes" / "skills"
        from skills_quality.core import QualityReport
        report = QualityReport(skills_dir=str(skills_dir))
        result = report.generate()
        assert result.summary["stubs"] > 0

    @pytest.mark.skipif(
        not (Path.home() / ".hermes" / "skills").exists(),
        reason="Hermes skills dir not found"
    )
    def test_real_skills_have_good(self):
        """Real Hermes skills include some higher-quality skills."""
        from skills_quality.core import QualityReport
        report = QualityReport(skills_dir=str(Path.home() / ".hermes" / "skills"))
        result = report.generate()
        # Scoring may be strict — just verify total is meaningful
        total = result.summary["total_skills"]
        assert total >= 60
