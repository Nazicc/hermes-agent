---
name: hermes-agent-git-workflow
description: "Safe git operations for hermes-agent skill development. Covers staged-file safety, destructive command guards, nested repo awareness, write-to-commit patterns, and recovery from accidents."
category: general
---

# Git Workflow for Hermes Skill Development

Safe, repeatable workflow for creating, editing, and committing skill files in the hermes repository. Follow this workflow to avoid data loss from destructive git operations.

## Pre-Destruction Checks (MANDATORY)

Before running any destructive git command (`reset --hard`, `rebase -i`, `checkout --force`, `clean -fd`), execute ALL of the following:

bash
# 1. Check working directory — unstaged changes will be LOST
git status

# 2. Check staged files — staged changes will ALSO be LOST under reset --hard
git diff --cached --name-only

# 3. Check staged-but-not-committed files in particular
# These look "safe" in the index but will be wiped by reset --hard
# If any exist, commit them FIRST

# 4. Check reflog for recent HEAD movements
git reflog -10

# 5. Check stash list
git stash list


## Staged Files Are NOT Safe From reset --hard

**Critical**: `git reset --hard` moves HEAD AND resets the working tree AND resets the staging area. Any file staged with `git add` but not yet committed will be DELETED from the working tree.

Symptoms of this failure:
- You created a skill with skill_manage, it was staged, but not committed
- You ran `git reset --hard` thinking you were cleaning up
- The skill file is gone from the working tree
- `git status` shows a clean working directory but the file is missing

## Safe File Operations

**Preferred method: use `execute_code` with Python's `open()`**.

python
import os

# Ensure parent directory exists
skill_dir = os.path.expanduser("~/.hermes/skills/hermes-agent/<skill-name>")
os.makedirs(skill_dir, exist_ok=True)

# Write the skill file
skill_path = os.path.join(skill_dir, "SKILL.md")
with open(skill_path, "w") as f:
    f.write("# Skill content here\n")


**Why `execute_code` instead of `write_file`?**

`write_file` silently fails — returning success without creating the file — when the parent directory does not exist. Python's `open()` creates parent directories and raises a clear exception on failure.

**Always verify** the file was written before proceeding:

python
import os
assert os.path.exists(skill_path), f"File not created: {skill_path}"
print(f"Verified: {skill_path}")


## Immediate Commit After Skill Creation

After creating or majorly updating a skill, commit immediately:

bash
git add skills/hermes-agent/<skill-name>/SKILL.md
git commit -m "feat(skills): add <skill-name> — brief description"


**Rule: commit before staging, not after staging**. The safest pattern is to write the file, then immediately commit it.

Do NOT leave skill files staged but uncommitted. "I'll commit after I verify it works" leads to losing the file under a stray reset.

## Staging Safety and Unstaging

If you accidentally stage a file and need to unstage it, use:

bash
git reset HEAD -- <path>


This removes the file from the staging area without modifying the working directory or losing any content.

| Command | Staging area | Working directory | Risk |
|---|---|---|---|
| `git reset HEAD -- <path>` | ✓ Removed | ✓ Intact | Safe |
| `git reset --soft` | ✓ Reset | ✓ Intact | Safe |
| `git reset --hard` | ✗ Wiped | ✗ Wiped | **Destructive** |
| `git checkout -- <path>` | ✓ Intact | ✗ Overwritten | Overwrites uncommitted work |

**Never use `git reset --hard`** to unstage files. It deletes all staged and unstaged changes permanently.

## Stashing Changes

**Before running `git stash`, check the scope of what will be stashed.**

bash
git stash list
git status   # Shows all files that would be stashed


In the hermes repository, there may be many untracked or modified files outside the skill you're working on. Stashing everything creates a bloated stash entry.

**To stash only specific files:**

bash
git stash push -m "wip: ctf-master skill" -- skills/hermes-agent/hermes-ctf-master/


**Drop stashes promptly** after pushing to avoid confusion about which stash corresponds to which work.

## Nested Repo Awareness

The hermes agent may have multiple git repos inside `~/.hermes` at the same time (e.g., ctf-skills, ctf-wiki, awesome-ctf cloned as subdirectories). Before running git commands:

bash
# Confirm you are in the intended repo
pwd && git rev-parse --show-toplevel

# If cloning repos for exploration, clone them OUTSIDE ~/.hermes
# to avoid git-context confusion and accidental resets


Common mistake: running `git reset --hard` in `~/.hermes` when you meant to run it in a subdirectory repo. This will wipe staged files in `~/.hermes` itself.

## Recovery Procedures

### After accidental reset --hard

bash
# Find the commit hash before the reset
git reflog
# Output looks like:
# abc1234 HEAD@{0}: reset: moving to HEAD~1
# def5678 HEAD@{1}: commit: feat: add my skill
#
# Restore by creating a new branch at the lost commit:
git branch recovery-branch <commit-hash>

# Or directly checkout the lost commit:
git checkout <commit-hash>


### Recovering from a cluttered stash

bash
# View stash list with context
git stash list

# Show files in a specific stash entry
git stash show -p stash@{N}

# Apply only specific files from a stash
# (use git checkout to restore individual files rather than applying whole stash)

# Drop a single stash entry
git stash drop stash@{N}


## Remote Operations

**Primary remote for skill pushes: `home`**

bash
git remote -v
# home   git@github.com:user/hermes.git (fetch)
# origin git@github.com:other/repo.git (fetch)

# Push to home:
git push home main


The `origin` remote may contain unrelated force-pushed history. Always confirm the correct remote before pushing.

Before force-pushing:

bash
git fetch origin
git log origin/main..HEAD  # review unpushed commits


Avoid `git push --force` on main branches. Use `git push --force-with-lease` as a safer alternative.

## Summary Checklist

- [ ] Use `execute_code` (Python `open()`) to create skill files — verifies parent directories exist
- [ ] Verify file exists immediately after writing
- [ ] Run pre-destruction checks before any destructive git command
- [ ] Commit immediately after `git add`
- [ ] Never use `git reset --hard` to unstage — use `git reset HEAD -- <path>` instead
- [ ] Use `git stash push -m "message" -- <specific-paths>` for targeted stashes
- [ ] Verify `pwd` and repo context before running git commands in nested repos
- [ ] Push to `home` remote, not `origin`

