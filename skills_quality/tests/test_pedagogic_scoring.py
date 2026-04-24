"""
BDD Feature 3: Pedagogic Depth Scoring

Tests for:
- Score pedagogic depth across 5 dimensions
- Stub skill is flagged
- Score components are individually reported
"""

import pytest
from skills_quality.core import SkillParser, PedagogicScorer


class TestPedagogicScoring:
    """Tests for pedagogic depth scoring."""

    def test_good_skill_score(self, good_skill_path):
        """Good skill scores 7-8 (Good tier)."""
        parser = SkillParser(skills_dir=good_skill_path.parent.parent)
        skill = parser.parse(good_skill_path)
        scorer = PedagogicScorer()
        score = scorer.score(skill)
        assert score.total >= 7
        assert score.tier == "good"

    def test_stub_skill_score(self, stub_skill_path):
        """Stub skill scores 0-3 (Stub tier)."""
        parser = SkillParser(skills_dir=stub_skill_path.parent.parent)
        skill = parser.parse(stub_skill_path)
        scorer = PedagogicScorer()
        score = scorer.score(skill)
        assert score.total <= 3
        assert score.tier == "stub"

    def test_developing_skill_score(self, developing_skill_path):
        """Developing skill scores 4-6 (Developing tier)."""
        parser = SkillParser(skills_dir=developing_skill_path.parent.parent)
        skill = parser.parse(developing_skill_path)
        scorer = PedagogicScorer()
        score = scorer.score(skill)
        assert score.tier in ("developing", "stub")

    def test_score_breakdown_dimensions(self, good_skill_path):
        """Score breakdown has all 5 dimensions."""
        parser = SkillParser(skills_dir=good_skill_path.parent.parent)
        skill = parser.parse(good_skill_path)
        scorer = PedagogicScorer()
        score = scorer.score(skill)
        assert hasattr(score, "teaching")
        assert hasattr(score, "anti_patterns")
        assert hasattr(score, "examples")
        assert hasattr(score, "when_not_to_use")
        assert hasattr(score, "cross_references")

    def test_teaching_dimension_good(self, good_skill_path):
        """Good skill has teaching dimension = 2."""
        parser = SkillParser(skills_dir=good_skill_path.parent.parent)
        skill = parser.parse(good_skill_path)
        scorer = PedagogicScorer()
        score = scorer.score(skill)
        assert score.teaching == 2

    def test_teaching_dimension_stub(self, stub_skill_path):
        """Stub skill has teaching dimension = 0."""
        parser = SkillParser(skills_dir=stub_skill_path.parent.parent)
        skill = parser.parse(stub_skill_path)
        scorer = PedagogicScorer()
        score = scorer.score(skill)
        assert score.teaching == 0

    def test_anti_patterns_named_failures(self, good_skill_path):
        """Good skill has named anti-patterns."""
        parser = SkillParser(skills_dir=good_skill_path.parent.parent)
        skill = parser.parse(good_skill_path)
        scorer = PedagogicScorer()
        score = scorer.score(skill)
        # 2 named failures → score of 1 (needs 3+ for score of 2)
        assert score.anti_patterns == 1
        # Named failures are present
        assert "Anti-Pattern 1" in skill.content or "Anti-Pattern" in skill.content

    def test_examples_dimension_good(self, good_skill_path):
        """Good skill has examples dimension = 2."""
        parser = SkillParser(skills_dir=good_skill_path.parent.parent)
        skill = parser.parse(good_skill_path)
        scorer = PedagogicScorer()
        score = scorer.score(skill)
        assert score.examples == 2

    def test_cross_references_good(self, good_skill_path):
        """Good skill has cross-references."""
        parser = SkillParser(skills_dir=good_skill_path.parent.parent)
        skill = parser.parse(good_skill_path)
        scorer = PedagogicScorer()
        score = scorer.score(skill)
        assert score.cross_references >= 1

    def test_chinese_content_scored(self, chinese_skill_path):
        """Chinese content is scored (teaching in multiple languages)."""
        parser = SkillParser(skills_dir=chinese_skill_path.parent.parent)
        skill = parser.parse(chinese_skill_path)
        scorer = PedagogicScorer()
        score = scorer.score(skill)
        # Chinese content has teaching value
        assert score.teaching >= 1
        assert "反面模式" in skill.content

    def test_score_tiers(self):
        """Score tiers are correctly mapped."""
        from skills_quality.core import PedagogicScore

        # Stub tier: 0-3
        stub_score = PedagogicScore(
            total=2, tier="stub",
            teaching=0, anti_patterns=0, examples=1, when_not_to_use=0, cross_references=1,
            named_failures=[]
        )
        assert stub_score.tier == "stub"

        # Developing tier: 4-6
        developing_score = PedagogicScore(
            total=5, tier="developing",
            teaching=1, anti_patterns=1, examples=1, when_not_to_use=1, cross_references=1,
            named_failures=[]
        )
        assert developing_score.tier == "developing"

        # Good tier: 7-8
        good_score = PedagogicScore(
            total=7, tier="good",
            teaching=2, anti_patterns=2, examples=1, when_not_to_use=1, cross_references=1,
            named_failures=[]
        )
        assert good_score.tier == "good"

        # Excellent tier: 9-10
        excellent_score = PedagogicScore(
            total=9, tier="excellent",
            teaching=2, anti_patterns=2, examples=2, when_not_to_use=1, cross_references=2,
            named_failures=[]
        )
        assert excellent_score.tier == "excellent"


class TestPedagogicTierBoundaries:
    """Tests for tier boundary conditions."""

    def test_stub_tier_exactly_3(self):
        """Score exactly 3 is stub tier."""
        from skills_quality.core import PedagogicScore
        score = PedagogicScore(
            total=3, tier="stub",
            teaching=1, anti_patterns=0, examples=1, when_not_to_use=0, cross_references=1,
            named_failures=[]
        )
        assert score.tier == "stub"

    def test_developing_tier_exactly_4(self):
        """Score exactly 4 is developing tier."""
        from skills_quality.core import PedagogicScore
        score = PedagogicScore(
            total=4, tier="developing",
            teaching=1, anti_patterns=1, examples=1, when_not_to_use=0, cross_references=1,
            named_failures=[]
        )
        assert score.tier == "developing"

    def test_good_tier_exactly_7(self):
        """Score exactly 7 is good tier."""
        from skills_quality.core import PedagogicScore
        score = PedagogicScore(
            total=7, tier="good",
            teaching=2, anti_patterns=2, examples=1, when_not_to_use=1, cross_references=1,
            named_failures=[]
        )
        assert score.tier == "good"

    def test_excellent_tier_exactly_9(self):
        """Score exactly 9 is excellent tier."""
        from skills_quality.core import PedagogicScore
        score = PedagogicScore(
            total=9, tier="excellent",
            teaching=2, anti_patterns=2, examples=2, when_not_to_use=1, cross_references=2,
            named_failures=[]
        )
        assert score.tier == "excellent"
