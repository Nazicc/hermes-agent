"""
Fixtures and test utilities for skills_quality tests.
"""

import os
import sys
import tempfile
from pathlib import Path
from typing import Dict

import pytest

# Ensure skills_quality is importable
sys.path.insert(0, str(Path(__file__).parent.parent))


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

HERMES_SKILLS_DIR = Path.home() / ".hermes" / "skills"


# ---------------------------------------------------------------------------
# Singleton reset fixture
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def reset_singletons():
    """Reset any global caches between tests for isolation."""
    import skills_quality.core as sq_core
    if hasattr(sq_core, '_CACHE'):
        sq_core._CACHE.clear()
    if hasattr(sq_core, '_GRAPH_CACHE'):
        sq_core._GRAPH_CACHE.clear()
    if hasattr(sq_core, '_parsed_skills'):
        sq_core._parsed_skills.clear()
    yield


# ---------------------------------------------------------------------------
# Minimal stub skill (8 lines — only YAML frontmatter)
# ---------------------------------------------------------------------------

STUB_SKILL = """---
name: test-stub
description: A stub skill with no markdown content.
version: 1.0.0
license: MIT
---

"""

# ---------------------------------------------------------------------------
# Developing skill (partial sections)
# ---------------------------------------------------------------------------

DEVELOPING_SKILL = """---
name: test-developing
description: A developing skill with some sections. Use when testing quality scoring.
intent: >-
  This skill teaches the basics but lacks depth in anti-patterns and examples.
type: component
version: 1.0.0
license: MIT
---

## Purpose

This skill does something useful.

## Application

1. Step one
2. Step two
3. Step three
"""

# ---------------------------------------------------------------------------
# Good skill (PM-Skills standard)
# ---------------------------------------------------------------------------

GOOD_SKILL = """---
name: test-good
description: A good skill with full PM-Skills structure. Use when validating quality standards.
intent: >-
  This skill exemplifies the PM-Skills quality standard with teaching, anti-patterns,
  examples, and cross-references.
type: workflow
best_for:
  - "Testing quality frameworks"
scenarios:
  - "I want to verify my skill meets quality standards"
version: 1.0.0
license: MIT
---

## Purpose

This skill demonstrates what a high-quality Hermes skill looks like.
It serves both human learning and AI execution — neither goal is optional.

## Key Concepts

### Why This Works

Teaching both the *why* and the *how* builds judgment, not just rote execution.
When humans understand why a framework works, they can adapt it to novel situations.
When agents get *why*, they make better context-dependent choices.

### Anti-Patterns

**Anti-Pattern 1: Stub Skill** — A skill with only YAML frontmatter and no markdown content.
*Consequence*: Agents cannot learn the reasoning behind the framework.
*Fix*: Add ## Purpose, ## Key Concepts, and at least one example.

**Anti-Pattern 2: Fluff Layer** — Excessive explanation that doesn't teach.
*Consequence*: Users skim and miss the actual guidance.
*Fix*: Every paragraph should earn its place. Cut filler.

## When to Use

- When building a new Hermes skill
- When auditing existing skills for quality
- When teaching others about skill authoring

## When NOT to Use

- For simple skills that don't need teaching depth
- For one-off tasks that won't be reused

## Application

### Phase 1: Structure

1. Write the ## Purpose section first
2. Add ## Key Concepts with Why This Works
3. Add ## Anti-Patterns with named failure modes
4. Add ## Examples showing reasoning

### Phase 2: Refine

5. Check for cross-references
6. Add ## References section
7. Validate YAML frontmatter completeness

## Examples

### Good Example

```markdown
## Purpose

The Opportunity Solution Tree aligns teams around customer outcomes...

### Why This Works

By mapping opportunities to solutions to hypotheses...
```

### Bad Example

```markdown
## Purpose

This skill helps you use OST. Use it when doing discovery.
```

## Common Pitfalls

1. Skipping ## Why This Works — agents get *what* without *why*
2. Naming anti-patterns generically — "don't do X" not "X (failure mode)"
3. No ## Examples — teaching without illustration is incomplete

## References

- skills/spec-driven-development/SKILL.md
- skills/test-driven-development/SKILL.md
- skills/systematic-debugging/SKILL.md
"""


# ---------------------------------------------------------------------------
# Interactive skill (question/answer patterns)
# ---------------------------------------------------------------------------

INTERACTIVE_SKILL = """---
name: test-interactive
description: An interactive skill with question sequences and numbered options.
intent: >-
  Tests interactive skill detection via question patterns and enumerated recommendations.
type: interactive
version: 1.0.0
license: MIT
---

## Purpose

Guide the user through a structured choice process with adaptive questions.

## Key Concepts

### How Interactive Skills Work

Interactive skills ask questions one at a time, then offer numbered recommendations.

## Application

Step 1: Ask opening question.

**What is your primary goal?**

Options:
1. Maximize revenue
2. Minimize churn
3. Improve NPS

Step 2: Based on answer, ask follow-up.

**What is your timeframe?**

Options:
1. This quarter
2. This year
3. Multi-year

Step 3: Synthesize and recommend.

Based on your answers, recommended approach:

1. **Revenue Focus (short-term)** — Use when goal=revenue and timeframe=quarter
2. **Retention Focus** — Use when goal=churn and timeframe=year
3. **Strategic Overhaul** — Use when goal=NPS and timeframe=multi-year
"""


# ---------------------------------------------------------------------------
# Skill with broken references
# ---------------------------------------------------------------------------

BROKEN_REF_SKILL = """---
name: test-broken-ref
description: A skill with broken cross-references.
intent: Tests broken reference detection.
type: component
version: 1.0.0
license: MIT
---

## Purpose

This skill references skills that don't exist.

## References

- skills/real-skill/SKILL.md
- skills/nonexistent-skill/SKILL.md
- skills/another-fake/SKILL.md
"""


# ---------------------------------------------------------------------------
# Skill with circular references (setup in temp dir)
# ---------------------------------------------------------------------------

CIRCULAR_A_SKILL = """---
name: test-circular-a
description: Circular ref skill A.
intent: Tests circular reference detection.
type: workflow
version: 1.0.0
license: MIT
---

## Purpose

A workflow that references B.

## References

- skills/test-circular-b/SKILL.md
"""

CIRCULAR_B_SKILL = """---
name: test-circular-b
description: Circular ref skill B.
intent: Tests circular reference detection.
type: workflow
version: 1.0.0
license: MIT
---

## Purpose

A workflow that references A back.

## References

- skills/test-circular-a/SKILL.md
"""


# ---------------------------------------------------------------------------
# Skill with triggers
# ---------------------------------------------------------------------------

TRIGGER_SKILL = """---
name: test-trigger
description: A skill with full trigger configuration.
intent: Tests trigger detection.
trigger:
  - "quality check"
  - "validate skill"
  - "质量检查"
anti_trigger:
  - "don't validate"
  - "no quality check"
version: 1.0.0
license: MIT
---

## Purpose

Tests trigger validation.
"""


# ---------------------------------------------------------------------------
# Skill with description too long (> 200 chars)
# ---------------------------------------------------------------------------

LONG_DESC_SKILL = """---
name: test-long-desc
description: This skill has a description that is way too long and exceeds the two hundred character limit that is typically considered the maximum for a good trigger-oriented description. This description should fail validation.
intent: Tests long description detection.
version: 1.0.0
license: MIT
---

## Purpose

A test skill.
"""


# ---------------------------------------------------------------------------
# Skill missing name in frontmatter
# ---------------------------------------------------------------------------

NO_NAME_SKILL = """---
description: Missing the name field.
version: 1.0.0
---

## Purpose

This skill is missing its name.
"""


# ---------------------------------------------------------------------------
# Skill with Chinese content (for pedagogic depth)
# ---------------------------------------------------------------------------

CHINESE_TEACHING_SKILL = """---
name: test-chinese
description: Tests Chinese content detection in pedagogic scoring.
intent: 测试中文内容检测。
version: 1.0.0
license: MIT
---

## Purpose

This skill has Chinese content for teaching variety.

## Key Concepts

### Why This Works

为什么这个技能有效 — teaching in multiple languages reinforces concepts.

### 反面模式

**反面模式: Stub Skill** — 仅有 YAML frontmatter 的技能。
*后果*: Agents cannot learn the reasoning.
*修复*: Add teaching sections.

## Examples

### Good Example

好的例子展示了如何正确使用本技能。

## When NOT to Use

- 当任务是简单的一次性工作时
- 当不需要教学深度时
"""


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def temp_skills_dir(tmp_path):
    """Create a temporary skills directory structure."""
    skills_dir = tmp_path / "skills"
    skills_dir.mkdir()
    return skills_dir


@pytest.fixture
def stub_skill_path(temp_skills_dir):
    """Create a stub SKILL.md."""
    p = temp_skills_dir / "test-stub" / "SKILL.md"
    p.parent.mkdir()
    p.write_text(STUB_SKILL)
    return p


@pytest.fixture
def developing_skill_path(temp_skills_dir):
    """Create a developing SKILL.md."""
    p = temp_skills_dir / "test-developing" / "SKILL.md"
    p.parent.mkdir()
    p.write_text(DEVELOPING_SKILL)
    return p


@pytest.fixture
def good_skill_path(temp_skills_dir):
    """Create a good quality SKILL.md."""
    p = temp_skills_dir / "test-good" / "SKILL.md"
    p.parent.mkdir()
    p.write_text(GOOD_SKILL)
    return p


@pytest.fixture
def interactive_skill_path(temp_skills_dir):
    """Create an interactive SKILL.md."""
    p = temp_skills_dir / "test-interactive" / "SKILL.md"
    p.parent.mkdir()
    p.write_text(INTERACTIVE_SKILL)
    return p


@pytest.fixture
def broken_ref_skill_path(temp_skills_dir):
    """Create a SKILL.md with broken references."""
    p = temp_skills_dir / "test-broken-ref" / "SKILL.md"
    p.parent.mkdir()
    p.write_text(BROKEN_REF_SKILL)
    return p


@pytest.fixture
def circular_skills(temp_skills_dir):
    """Create two skills with circular references."""
    p_a = temp_skills_dir / "test-circular-a" / "SKILL.md"
    p_b = temp_skills_dir / "test-circular-b" / "SKILL.md"
    p_a.parent.mkdir()
    p_b.parent.mkdir()
    p_a.write_text(CIRCULAR_A_SKILL)
    p_b.write_text(CIRCULAR_B_SKILL)
    return p_a, p_b


@pytest.fixture
def trigger_skill_path(temp_skills_dir):
    """Create a SKILL.md with triggers."""
    p = temp_skills_dir / "test-trigger" / "SKILL.md"
    p.parent.mkdir()
    p.write_text(TRIGGER_SKILL)
    return p


@pytest.fixture
def long_desc_skill_path(temp_skills_dir):
    """Create a SKILL.md with description > 200 chars."""
    p = temp_skills_dir / "test-long-desc" / "SKILL.md"
    p.parent.mkdir()
    p.write_text(LONG_DESC_SKILL)
    return p


@pytest.fixture
def no_name_skill_path(temp_skills_dir):
    """Create a SKILL.md missing name field."""
    p = temp_skills_dir / "test-no-name" / "SKILL.md"
    p.parent.mkdir()
    p.write_text(NO_NAME_SKILL)
    return p


@pytest.fixture
def chinese_skill_path(temp_skills_dir):
    """Create a SKILL.md with Chinese content."""
    p = temp_skills_dir / "test-chinese" / "SKILL.md"
    p.parent.mkdir()
    p.write_text(CHINESE_TEACHING_SKILL)
    return p


# ---------------------------------------------------------------------------
# Shared skill corpus for full-report tests
# ---------------------------------------------------------------------------

@pytest.fixture
def mixed_corpus(temp_skills_dir):
    """
    Create a mixed corpus of skills across quality tiers.
    Returns a dict mapping skill_name -> path.
    """
    skills = {
        "stub-only": STUB_SKILL,
        "developing-basic": DEVELOPING_SKILL,
        "good-workflow": GOOD_SKILL,
        "interactive-flow": INTERACTIVE_SKILL,
        "broken-ref": BROKEN_REF_SKILL,
        "trigger-rich": TRIGGER_SKILL,
        "long-description": LONG_DESC_SKILL,
        "chinese-content": CHINESE_TEACHING_SKILL,
    }
    paths = {}
    for name, content in skills.items():
        p = temp_skills_dir / name / "SKILL.md"
        p.parent.mkdir()
        p.write_text(content)
        paths[name] = p
    return paths
