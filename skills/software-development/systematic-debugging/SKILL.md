---
name: systematic-debugging
description: "Use when encountering any bug, test failure, or unexpected behavior. 4-phase root cause investigation: Observe → Hypothesize → Test → Iterate. CRITICAL: No fixes without understanding the problem first. Premature fixes create technical debt. Covers shell scripts, Python, and general debugging. Shell-specific: use `bash -x` traces and understand `set -e` + `[ $? -eq 0 ]` anti-patterns."
category: general
---

# Systematic Debugging

4-phase root cause investigation. **No fixes without understanding the problem first.** Apply the scientific method to code.

## When to Use

Activate when:
- A test fails (unit, integration, e2e)
- A tool call returns an error or unexpected output
- The agent produces incorrect or incomplete results
- Any `Error:`, `Exception:`, `Traceback:`, or non-zero exit code appears
- Behavior diverges from the spec or user's intent
- Before writing any fix, hotpatch, or workaround
- When the agent is about to guess at a solution

---

## Phase 1: Observe

**Collect facts, not assumptions.** Do NOT guess, do NOT fix.

**What to collect:**
- The exact error message or unexpected output
- The command/context that triggered it
- Relevant log entries (`~/.skillclaw/health.log`, stderr, stdout)
- What changed recently (dependency updates, config changes, new commits)
- Exit codes and stack traces
- What was the last working state? What changed?

**Commands:**
bash
# Check recent logs
tail -50 ~/.skillclaw/health.log

# Check git diff for recent changes
git -C ~/.hermes/hermes-agent log --oneline -5
git -C ~/.hermes/hermes-agent diff HEAD~1

# For shell scripts: use bash -x for maximum verbosity
bash -x script.sh 2>&1 | grep -v "^++"

# Check exit codes explicitly after critical commands
cmd; echo "exit: $?"


**Shell-specific checks:**
- Check file permissions, symlinks, path variables
- For shell scripts: check `set -e` behavior — script may exit early without error message
- **CRITICAL shell anti-pattern**: `set -e` + `[ $? -eq 0 ]` always exits because `$?` is the exit code of `[`, which is always 0 or 1 (the equality check itself can fail → `[` exits 1 → `set -e` catches it → script exits). Use a sentinel variable instead: `SKIP=0; python3 ...; [ $? -eq 0 ] && SKIP=1; [ $SKIP -eq 1 ] && exit 0`

**Output of Phase 1:** A concise list of facts (not interpretations).

---

## Phase 2: Hypothesize

**State the root cause as a testable claim.** Each hypothesis must be falsifiable.

**Rules:**
- List ALL plausible hypotheses before choosing one
- Prefer the simplest explanation that fits all facts
- Distinguish symptoms from root causes
- **Never say "I'll try X and see"** — first understand why X would work
- For shell: Is it `set -e`? Wrong path? Permission? Stale state?

**Hypothesis template:**

H1: <cause> → <effect>
  Evidence supporting: ...
  Evidence against: ...

H2: <alternative cause> → <effect>
  Evidence supporting: ...
  Evidence against: ...


**Common root causes (check in order):**
1. Environment mismatch (wrong port, missing env var, network)
2. API/contract change (endpoint, payload schema, auth)
3. Race condition or ordering dependency
4. Missing resource or dependency not installed
5. Configuration error (typo, wrong path)
6. Logic error in the code itself

---

## Phase 3: Test

**Verify the hypothesis with a targeted test.** One variable at a time.

**Test patterns:**
bash
# Test a specific tool/function
hermes test --tool <name> --case <case-name>

# Verify environment state
echo $PORT && curl http://127.0.0.1:$PORT/healthz

# Check if resource exists
ls -la ~/.hermes/<path>

# Run the minimal reproduction
python3 -c "import <module>; <module>.<func>()"

# For shell: syntax check before running
bash -n script.sh


**Principles:**
- Test the specific hypothesis, not multiple things
- If the test passes → hypothesis likely correct, move to Fix
- If the test fails → hypothesis wrong, return to Phase 2
- Verify fix doesn't break other paths
- Run with dry-run flags if available

---

## Phase 4: Iterate

**Refine based on test results.** Once root cause is confirmed, fix it and verify.

**Fixing rules:**
- Fix the root cause, not the symptom
- Write a regression test to prevent recurrence
- If the fix is non-trivial, use incremental-implementation skill
- After fix: re-run the original failing case, then run full test suite

**Verification checklist:**
- [ ] Original error is gone
- [ ] Related functionality still works
- [ ] Regression test passes
- [ ] No new errors in health.log

**If hypothesis was wrong:** Return to Phase 2 with new evidence.

**Cleanup:** Document what you learned. Clean up any test/temporary files.

---

## Shell Script Checklist

Before declaring a shell bug fixed, verify:
- [ ] `bash -n` (syntax check) passes
- [ ] Script runs to completion without `set -e` early exit
- [ ] Exit codes are checked explicitly after critical commands
- [ ] No `[ $? -eq 0 ]` pattern after `set -e` (use sentinel variable)
- [ ] Paths are absolute, not relative to current directory

---

## Anti-Patterns

1. **Don't fix without understanding** — You WILL create bugs
2. **`set -e` + `[ $? -eq 0 ]`** — `$?` is the exit code of `[`, not the previous command. Use sentinel variable instead.
3. **Silent failure** — commands that fail without error messages under `set -e`
4. **Don't restart services blindly** — Observe first, then restart as a targeted test
5. **Don't assume API stability** — APIs change. Check the actual contract
6. **Stale state** — script reads cached files or environment from previous runs
7. **Path dependency** — assumes current working directory is correct

---

## Debugging the Hermes System Specifically

### SkillClaw proxy issues
bash
# Check SkillClaw health
curl -s http://127.0.0.1:30000/healthz
# Expected: {"status":"ok"} or {"healthy":true}

# Restart if unhealthy
kill $(cat ~/.skillclaw/gateway.pid 2>/dev/null) 2>/dev/null
# Then restart the gateway


### Hermes routing issues
bash
# Check hermes config
cat ~/.hermes/hermes-agent/config.yaml 2>/dev/null | grep -A5 "hermes:"

# Verify provider settings
# Correct: provider=custom, base_url=http://127.0.0.1:30000/v1


### MCP tool errors
bash
# Check MCP server logs
tail -30 ~/.hermes/logs/mcp.log

# Test MCP connection
python3 -c "from mcp.client import Client; c = Client('http://127.0.0.1:3001'); print(c.ping())"


### Skill injection failures
bash
# Check skills index
ls ~/.hermes/skills/skills/

# Rebuild index
rm -f ~/.hermes/.skills_prompt_snapshot.json

# Verify skill file exists
cat ~/.hermes/skills/skills/<skill-name>/SKILL.md | head -20


---

## Related Skills

- `test-driven-development` — Write tests BEFORE fixing (Phase 3 companion)
- `incremental-implementation` — For complex fixes, break them down
- `spec-driven-development` — If bug reveals missing spec, use this first
