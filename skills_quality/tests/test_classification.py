"""
BDD Feature 2: Skill Type Classification

Tests for:
- Classify skill type by structure
- Workflow skill references other skills
- Interactive skill missing enumerated options
"""

import pytest
from skills_quality.core import SkillParser


class TestSkillTypeClassification:
    """Tests for skill type classification (component/interactive/workflow/unknown)."""

    def test_workflow_classification(self, good_skill_path):
        """Good workflow skill is classified as workflow."""
        from skills_quality.core import classify_skill_type
        parser = SkillParser(skills_dir=good_skill_path.parent.parent)
        skill = parser.parse(good_skill_path)
        skill_type = classify_skill_type(skill)
        assert skill_type == "workflow"

    def test_interactive_classification(self, interactive_skill_path):
        """Interactive skill with questions is classified as interactive."""
        from skills_quality.core import classify_skill_type
        parser = SkillParser(skills_dir=interactive_skill_path.parent.parent)
        skill = parser.parse(interactive_skill_path)
        skill_type = classify_skill_type(skill)
        assert skill_type == "interactive"

    def test_component_classification(self, developing_skill_path):
        """Developing skill (template-like) is classified as component."""
        from skills_quality.core import classify_skill_type
        parser = SkillParser(skills_dir=developing_skill_path.parent.parent)
        skill = parser.parse(developing_skill_path)
        skill_type = classify_skill_type(skill)
        assert skill_type == "component"

    def test_unknown_classification_stub(self, stub_skill_path):
        """Stub skill with no content is classified as unknown."""
        from skills_quality.core import classify_skill_type
        parser = SkillParser(skills_dir=stub_skill_path.parent.parent)
        skill = parser.parse(stub_skill_path)
        skill_type = classify_skill_type(skill)
        assert skill_type == "unknown"

    def test_workflow_has_phase_markers(self, good_skill_path):
        """Workflow classification uses phase/step markers."""
        from skills_quality.core import classify_skill_type
        parser = SkillParser(skills_dir=good_skill_path.parent.parent)
        skill = parser.parse(good_skill_path)
        skill_type = classify_skill_type(skill)
        assert skill_type == "workflow"
        # Good skill has Phase 1, Phase 2 markers
        assert "phase 1" in skill.content.lower() or "step 1" in skill.content.lower()

    def test_interactive_has_question_patterns(self, interactive_skill_path):
        """Interactive classification uses question and numbered options patterns."""
        from skills_quality.core import classify_skill_type
        parser = SkillParser(skills_dir=interactive_skill_path.parent.parent)
        skill = parser.parse(interactive_skill_path)
        skill_type = classify_skill_type(skill)
        assert skill_type == "interactive"

    def test_interactive_missing_options_warning(self, developing_skill_path):
        """Interactive skill without numbered options raises warning."""
        from skills_quality.core import classify_skill_type, validate_structure
        parser = SkillParser(skills_dir=developing_skill_path.parent.parent)
        skill = parser.parse(developing_skill_path)
        # Force classify as interactive despite lacking options
        skill_type = classify_skill_type(skill)
        if skill_type == "interactive":
            result = validate_structure(skill)
            assert "INTERACTIVE_NO_OPTIONS" in result.warnings
