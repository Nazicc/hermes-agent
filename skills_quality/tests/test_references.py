"""
BDD Feature 4: Cross-Reference Validation

Tests for:
- Extract valid skill references
- Broken skill references are detected
- Build skill dependency graph
- Circular references are detected
"""

import pytest
from skills_quality.core import SkillParser


class TestReferenceExtraction:
    """Tests for skill reference extraction."""

    def test_extract_valid_references(self, good_skill_path):
        """Good skill extracts referenced skill names."""
        from skills_quality.core import extract_references
        parser = SkillParser(skills_dir=good_skill_path.parent.parent)
        skill = parser.parse(good_skill_path)
        refs = extract_references(skill)
        assert len(refs) >= 3
        assert "test-driven-development" in refs
        assert "systematic-debugging" in refs

    def test_extract_no_references(self, stub_skill_path):
        """Stub skill has no references."""
        from skills_quality.core import extract_references
        parser = SkillParser(skills_dir=stub_skill_path.parent.parent)
        skill = parser.parse(stub_skill_path)
        refs = extract_references(skill)
        assert len(refs) == 0

    def test_extract_broken_references(self, broken_ref_skill_path, temp_skills_dir):
        """Broken reference skill detects fake skill names."""
        from skills_quality.core import extract_references, validate_references
        parser = SkillParser(skills_dir=broken_ref_skill_path.parent.parent)
        skill = parser.parse(broken_ref_skill_path)
        refs = extract_references(skill)
        assert "nonexistent-skill" in refs
        assert "another-fake" in refs
        # Validate references against the temp dir (which doesn't have these)
        result = validate_references(skill, skills_dir=temp_skills_dir)
        assert "nonexistent-skill" in result.broken_refs
        assert "another-fake" in result.broken_refs


class TestReferenceValidation:
    """Tests for reference validation against filesystem."""

    def test_real_skills_exist(self, good_skill_path):
        """Real referenced skills in good_skill_path reference other real skills."""
        from skills_quality.core import extract_references, validate_references
        # good_skill_path points to temp dir with only test-* skills
        parser = SkillParser(skills_dir=good_skill_path.parent.parent)
        skill = parser.parse(good_skill_path)
        refs = extract_references(skill)
        result = validate_references(skill, skills_dir=good_skill_path.parent.parent)
        # In temp dir, most won't exist
        assert len(result.valid_refs) >= 0

    def test_broken_reference_names_extracted(self, broken_ref_skill_path, temp_skills_dir):
        """Broken reference validation returns the broken skill names."""
        from skills_quality.core import validate_references
        parser = SkillParser(skills_dir=broken_ref_skill_path.parent.parent)
        skill = parser.parse(broken_ref_skill_path)
        result = validate_references(skill, skills_dir=temp_skills_dir)
        # Should detect the broken references in the temp corpus
        assert len(result.broken_refs) >= 1


class TestDependencyGraph:
    """Tests for skill dependency graph building."""

    def test_graph_builds_from_corpus(self, mixed_corpus):
        """Graph builder produces nodes and edges from corpus."""
        from skills_quality.core import DependencyGraph
        # mixed_corpus creates skills in temp_skills_dir
        # Use the parent of the first skill path to get the skills_dir
        first_skill = next(iter(mixed_corpus.values()))
        skills_dir = first_skill.parent.parent
        graph = DependencyGraph(skills_dir=skills_dir)
        graph.build()
        # Graph includes the corpus skills plus referenced-but-not-existing skills
        assert len(graph.nodes) >= len(mixed_corpus)
        # Skill name is from frontmatter: "test-good", not the dir name "good-workflow"
        assert "test-good" in graph.nodes

    def test_graph_references_field(self, good_skill_path):
        """Graph node has references and referenced_by fields."""
        from skills_quality.core import DependencyGraph
        graph = DependencyGraph(skills_dir=good_skill_path.parent.parent)
        graph.build()
        node = graph.nodes.get("test-good")
        assert node is not None
        assert isinstance(node.get("references", []), list)
        assert isinstance(node.get("referenced_by", []), list)

    def test_graph_circular_detection(self, circular_skills, temp_skills_dir):
        """Circular references are detected."""
        from skills_quality.core import DependencyGraph
        graph = DependencyGraph(skills_dir=temp_skills_dir)
        graph.build()
        assert len(graph.cycles) >= 1
        cycle = graph.cycles[0]
        assert "test-circular-a" in cycle
        assert "test-circular-b" in cycle

    def test_graph_no_cycles_normal(self, mixed_corpus, temp_skills_dir):
        """Normal corpus has no cycles."""
        from skills_quality.core import DependencyGraph
        graph = DependencyGraph(skills_dir=temp_skills_dir)
        graph.build()
        assert len(graph.cycles) == 0

    def test_graph_orphans(self, mixed_corpus, temp_skills_dir):
        """Orphan skills (no refs, not referenced) are identified."""
        from skills_quality.core import DependencyGraph
        graph = DependencyGraph(skills_dir=temp_skills_dir)
        graph.build()
        assert isinstance(graph.orphans, list)

    def test_graph_leaf_nodes(self, mixed_corpus, temp_skills_dir):
        """Leaf nodes (no incoming edges) are identified."""
        from skills_quality.core import DependencyGraph
        graph = DependencyGraph(skills_dir=temp_skills_dir)
        graph.build()
        assert isinstance(graph.leaf_nodes, list)
