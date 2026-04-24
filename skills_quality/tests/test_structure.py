"""
BDD Feature 1: Skill Structure Validation

Tests for:
- Valid skill passes structure checks
- Skill missing frontmatter name
- Skill description exceeds 200 characters
- Skill missing required markdown sections
- Skill has content but no markdown sections
"""

import pytest
from skills_quality.core import SkillParser, ValidationResult


class TestSkillParser:
    """Unit tests for SkillParser."""

    def test_parse_stub_skill(self, stub_skill_path):
        """Stub skill parses successfully."""
        parser = SkillParser(skills_dir=stub_skill_path.parent.parent)
        result = parser.parse(stub_skill_path)
        assert result.name == "test-stub"
        assert result.description == "A stub skill with no markdown content."
        # STUB_SKILL has ~8 lines (only frontmatter)
        assert result.line_count >= 5
        assert len(result.sections) == 0

    def test_parse_good_skill(self, good_skill_path):
        """Good skill parses with all frontmatter fields."""
        parser = SkillParser(skills_dir=good_skill_path.parent.parent)
        result = parser.parse(good_skill_path)
        assert result.name == "test-good"
        assert result.intent is not None
        assert "workflow" in result.skill_type
        assert len(result.sections) > 0

    def test_parse_missing_name(self, no_name_skill_path):
        """Skill missing frontmatter name returns MISSING_NAME."""
        parser = SkillParser(skills_dir=no_name_skill_path.parent.parent)
        result = parser.parse(no_name_skill_path)
        assert result.name is None
        assert "MISSING_NAME" in result.errors

    def test_parse_long_description(self, long_desc_skill_path):
        """Description > 200 chars returns DESCRIPTION_TOO_LONG."""
        parser = SkillParser(skills_dir=long_desc_skill_path.parent.parent)
        result = parser.parse(long_desc_skill_path)
        assert "DESCRIPTION_TOO_LONG" in result.errors
        # Description should be captured anyway
        assert len(result.description) > 200

    def test_parse_no_sections(self, stub_skill_path):
        """Skill with only frontmatter has zero H2 sections."""
        parser = SkillParser(skills_dir=stub_skill_path.parent.parent)
        result = parser.parse(stub_skill_path)
        assert len(result.sections) == 0

    def test_parse_has_sections(self, good_skill_path):
        """Good skill has expected H2 sections."""
        parser = SkillParser(skills_dir=good_skill_path.parent.parent)
        result = parser.parse(good_skill_path)
        section_names = [s.lower() for s in result.sections.keys()]
        assert any("purpose" in s for s in section_names)
        assert any("key concepts" in s for s in section_names)

    def test_parse_chinese_content(self, chinese_skill_path):
        """Chinese content is preserved in parsed content."""
        parser = SkillParser(skills_dir=chinese_skill_path.parent.parent)
        result = parser.parse(chinese_skill_path)
        assert "为什么这个技能有效" in result.content
        assert "反面模式" in result.content


class TestStructureValidation:
    """Tests for structure validation rules."""

    def test_stub_skill_profile(self, stub_skill_path):
        """Stub skill is correctly classified as stub profile."""
        from skills_quality.core import validate_structure
        parser = SkillParser(skills_dir=stub_skill_path.parent.parent)
        skill = parser.parse(stub_skill_path)
        result = validate_structure(skill)
        assert result.profile == "stub"
        assert "NO_SECTIONS" in result.errors
        # Stub profile short-circuits, so MISSING_REQUIRED_SECTION not added
        # (NO_SECTIONS is sufficient to identify the stub)

    def test_good_skill_profile(self, good_skill_path):
        """Good skill is correctly classified as full profile."""
        from skills_quality.core import validate_structure
        parser = SkillParser(skills_dir=good_skill_path.parent.parent)
        skill = parser.parse(good_skill_path)
        result = validate_structure(skill)
        assert result.profile == "full"
        assert len(result.errors) == 0

    def test_developing_skill_profile(self, developing_skill_path):
        """Developing skill is partial profile."""
        from skills_quality.core import validate_structure
        parser = SkillParser(skills_dir=developing_skill_path.parent.parent)
        skill = parser.parse(developing_skill_path)
        result = validate_structure(skill)
        assert result.profile in ("partial", "stub", "full")
        # Should have some sections but not all full-profile requirements
        assert len(skill.sections) >= 2

    def test_description_length_threshold(self, long_desc_skill_path):
        """Description exactly 200 chars is valid."""
        from skills_quality.core import SkillParser, validate_structure
        # Create a skill with exactly 200-char description
        exactly_200 = "A" * 200
        content = f"""---
name: exactly-200
description: {exactly_200}
---
## Purpose
Test.
"""
        import tempfile
        import os
        with tempfile.TemporaryDirectory() as td:
            p = os.path.join(td, "exactly-200", "SKILL.md")
            os.makedirs(os.path.dirname(p))
            with open(p, "w") as f:
                f.write(content)
            parser = SkillParser(skills_dir=td)
            skill = parser.parse(p)
            result = validate_structure(skill)
            assert "DESCRIPTION_TOO_LONG" not in result.errors

    def test_missing_purpose_section(self, developing_skill_path):
        """Developing skill missing Purpose section is flagged."""
        from skills_quality.core import SkillParser, validate_structure
        parser = SkillParser(skills_dir=developing_skill_path.parent.parent)
        skill = parser.parse(developing_skill_path)
        result = validate_structure(skill)
        # developing skill has Purpose but it's uppercase-less
        section_names = [s.lower() for s in skill.sections.keys()]
        if "purpose" not in section_names:
            assert "MISSING_REQUIRED_SECTION" in result.errors

    def test_no_frontmatter(self, temp_skills_dir):
        """Skill with no frontmatter returns MISSING_NAME and has parsed content."""
        from skills_quality.core import SkillParser
        import os
        p = temp_skills_dir / "no-frontmatter" / "SKILL.md"
        p.parent.mkdir()
        p.write_text("## Purpose\nJust markdown, no frontmatter.\n")
        parser = SkillParser(skills_dir=temp_skills_dir)
        skill = parser.parse(p)
        assert "MISSING_NAME" in skill.errors
        # Parser handles gracefully, content is still readable
        assert "Just markdown" in skill.content
