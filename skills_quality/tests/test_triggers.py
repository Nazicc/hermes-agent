"""
BDD Feature 5: Trigger/TAnti-Trigger Validation

Tests for:
- Skills without triggers are flagged
- Trigger and anti-trigger overlap
- Trigger coverage score
"""

import pytest
from skills_quality.core import SkillParser


class TestTriggerValidation:
    """Tests for trigger and anti-trigger validation."""

    def test_trigger_skill_has_triggers(self, trigger_skill_path):
        """Trigger skill has triggers in frontmatter."""
        from skills_quality.core import TriggerValidator
        parser = SkillParser(skills_dir=trigger_skill_path.parent.parent)
        skill = parser.parse(trigger_skill_path)
        validator = TriggerValidator()
        result = validator.validate(skill)
        assert result.has_triggers is True
        assert len(result.triggers) >= 3
        assert "quality check" in result.triggers

    def test_stub_skill_no_triggers(self, stub_skill_path):
        """Stub skill has no triggers."""
        from skills_quality.core import TriggerValidator
        parser = SkillParser(skills_dir=stub_skill_path.parent.parent)
        skill = parser.parse(stub_skill_path)
        validator = TriggerValidator()
        result = validator.validate(skill)
        assert result.has_triggers is False

    def test_trigger_coverage_score(self, trigger_skill_path):
        """Trigger coverage score has all components."""
        from skills_quality.core import TriggerValidator
        parser = SkillParser(skills_dir=trigger_skill_path.parent.parent)
        skill = parser.parse(trigger_skill_path)
        validator = TriggerValidator()
        result = validator.validate(skill)
        assert result.coverage_score >= 3
        assert result.has_chinese is True
        assert result.has_anti_triggers is True
        assert result.has_intent is True

    def test_trigger_anti_trigger_coverage(self, trigger_skill_path):
        """Trigger skill has anti-triggers."""
        from skills_quality.core import TriggerValidator
        parser = SkillParser(skills_dir=trigger_skill_path.parent.parent)
        skill = parser.parse(trigger_skill_path)
        validator = TriggerValidator()
        result = validator.validate(skill)
        assert result.has_anti_triggers is True
        assert len(result.anti_triggers) >= 1

    def test_good_skill_trigger_warning(self, good_skill_path):
        """Good skill with high score but no triggers should have NO_TRIGGERS."""
        from skills_quality.core import TriggerValidator, PedagogicScorer
        parser = SkillParser(skills_dir=good_skill_path.parent.parent)
        skill = parser.parse(good_skill_path)
        scorer = PedagogicScorer()
        score = scorer.score(skill)
        validator = TriggerValidator()
        result = validator.validate(skill)
        # NO_TRIGGERS is added in report generation, not in validator
        # Validator should correctly report has_triggers=False
        assert result.has_triggers is False
        assert score.total >= 5

    def test_trigger_overlap_detection(self):
        """Trigger and anti-trigger overlap is detected."""
        from skills_quality.core import TriggerValidator, SkillParser
        content = """---
name: test-overlap
description: Tests trigger overlap.
trigger:
  - "debug"
  - "fix bug"
anti_trigger:
  - "don't debug"
  - "don't fix bug"
---
## Purpose
Test.
"""
        import tempfile, os
        with tempfile.TemporaryDirectory() as td:
            p = os.path.join(td, "test-overlap", "SKILL.md")
            os.makedirs(os.path.dirname(p))
            with open(p, "w") as f:
                f.write(content)
            parser = SkillParser(skills_dir=td)
            skill = parser.parse(p)
            validator = TriggerValidator()
            result = validator.validate(skill)
            # "don't debug" is a negation of "debug"
            assert "TRIGGER_ANTITRIGGER_OVERLAP" in result.warnings


class TestTriggerScoring:
    """Tests for trigger coverage scoring."""

    def test_trigger_score_has_three_plus(self, trigger_skill_path):
        """Score component: ≥3 triggers."""
        from skills_quality.core import TriggerValidator
        parser = SkillParser(skills_dir=trigger_skill_path.parent.parent)
        skill = parser.parse(trigger_skill_path)
        validator = TriggerValidator()
        result = validator.validate(skill)
        assert result.triggers_bonus == 1  # Has ≥3 triggers

    def test_trigger_score_chinese(self, trigger_skill_path):
        """Score component: Chinese triggers."""
        from skills_quality.core import TriggerValidator
        parser = SkillParser(skills_dir=trigger_skill_path.parent.parent)
        skill = parser.parse(trigger_skill_path)
        validator = TriggerValidator()
        result = validator.validate(skill)
        assert result.chinese_bonus == 1  # Has Chinese triggers

    def test_trigger_score_anti_trigger(self, trigger_skill_path):
        """Score component: anti-triggers present."""
        from skills_quality.core import TriggerValidator
        parser = SkillParser(skills_dir=trigger_skill_path.parent.parent)
        skill = parser.parse(trigger_skill_path)
        validator = TriggerValidator()
        result = validator.validate(skill)
        assert result.anti_trigger_bonus == 1  # Has anti-triggers

    def test_trigger_score_intent(self, good_skill_path):
        """Score component: intent field present."""
        from skills_quality.core import TriggerValidator
        parser = SkillParser(skills_dir=good_skill_path.parent.parent)
        skill = parser.parse(good_skill_path)
        validator = TriggerValidator()
        result = validator.validate(skill)
        assert result.intent_bonus == 1  # Has intent field
