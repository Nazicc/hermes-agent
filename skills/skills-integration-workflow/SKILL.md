---
name: skills-integration-workflow
description: >-
  Systematic approach for upgrading Hermes skills against a higher-quality reference.
  Decides between full replacement vs. merge, then validates with regression testing.
  Use when analyzing external skill repositories (e.g., addyosmani/agent-skills) and
  integrating their content into Hermes.
trigger:
  - integrate skills
  - upgrade skill
  - skill comparison
  - skill replacement
  - merge skill
license: MIT
metadata.hermes.tags: [skills, workflow, integration]
related_skills: [spec-driven-development, code-simplification]
---

# Skills Integration Workflow

## When to Use

Upgrading an existing Hermes skill by comparing it against a higher-quality reference (e.g., addyosmani/agent-skills, or a richer skill from another source). Use this before blindly replacing content — some skills are already advanced and should be merged, not clobbered.

## Process

### 1. Compare scope
For each overlapping skill, count lines of content:
- **Reference skill ≥ 2x the size of Hermes skill** → likely a **full replacement candidate**
- **Both are similar size/complexity** → likely a **merge candidate**
- **Hermes is already advanced** (e.g., has pipeline phases, defined sections) → **merge**, keep existing architecture

### 2. Full replacement (stub → full)
When Hermes skill is a stub (<300 lines) and reference has 400-800+ lines with anti-rationalization tables:
- Replace the entire SKILL.md with reference content
- Preserve Hermes-specific frontmatter (`name`, `description`, `trigger`, `license`, `metadata.hermes.tags`, `related_skills`)
- Append any Hermes-specific conventions if reference omits them

### 3. Merge (advanced → enhanced)
When Hermes skill already has meaningful structure (e.g., 8-phase pipeline, defined sections):
- Keep existing content
- Append reference's **AntiRationalizations** section if Hermes lacks one
- Append reference's **RedFlags** section if applicable
- Merge **Verification** checklists
- Update version semver (e.g., v3.0 → v3.1)

### 4. Regression test
Always run after any skill changes:
```bash
python3 /tmp/validate_skills.py --path ~/.hermes/skills/
```
Expect: 0 errors, 0 warnings. If failures, inspect and fix before proceeding.

### 5. Commit and push
```bash
git add -A
git commit -m "feat(skills): integrate <source> production-grade content"
git push origin main
```

## AntiRationalizations (why you might skip this)

- **"I'll just read the reference directly next time"** → Without integration, the reference content isn't available to Hermes at decision time. Integration makes it actionable.
- **"Merge is too complex, full replace is faster"** → Full replace loses any advanced Hermes-specific content that took work to develop (pipelines, conventions, user preferences).
- **"I tested one skill, the others are probably fine"** → Regression test is fast (seconds) and catches syntax/frontmatter errors that silently break skills.

## Red Flags

- Reference skill has a very different problem domain than Hermes (don't merge e.g. a Solidity smart contract skill over a Python one)
- Frontmatter `license` field gets accidentally deleted during replacement
- Regression test shows new errors that weren't there before
- Commit message doesn't reference the source (hard to trace later)

## Verification

1. `validate_skills.py` passes with 0 errors, 0 warnings
2. `git log --oneline -1` shows commit referencing the source
3. New skills appear in `~/.hermes/skills/` with correct frontmatter
4. Skills that were merged still retain their original architecture/pipeline phases
