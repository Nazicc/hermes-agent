---
version: 1.0.0
description: When sensitive data (API keys, real business data) is accidentally pushed to a public GitHub repo — trace ancestry, cherry-pick clean commits, force-push to erase history.
name: git-history-security-response
tags: [git, security, incident-response]
---

# Git History Security Incident Response

## Purpose
When sensitive data (API keys, credentials, real business data like bank APK audit reports) is accidentally pushed to a public GitHub repository, systematically remove it from history while preserving clean commits.

## Core Principle
> A sensitive commit being an **ancestor** of a pushed commit means the ENTIRE history from that point is contaminated — not just "a few bad commits at the tip."

## Critical First Step: Verify Remote Tracking

```bash
# BEFORE ANYTHING — understand what origin points to
git remote -v
git config --get remote.origin.url
```

After changing a remote URL from upstream (NousResearch) to a fork (Nazicc), `origin/main` tracks the **fork's** remote history — including all commits pushed to that fork. The "diverged" message in `git status` is misleading because the 85 "remote" commits are from the original upstream, while the sensitive commits are mixed into the local 22.

## Workflow

### Step 1: Verify Scope with merge-base --is-ancestor
```bash
# Check if sensitive commit is in remote's ancestry
git merge-base --is-ancestor <sensitive_sha> <remote_sha>
# Exit code 0 = YES (sensitive IS in ancestry — contaminated)
# Exit code 1 = NO  (sensitive NOT in ancestry — only local)

# ALWAYS check this before assuming you can just drop new commits
```

### Step 2: Identify ALL Contaminated Commits
```bash
# List ALL commits in the contaminated range
git log --reverse --format="%H %s" <clean_base>..<dirty_tip>

# Find by content or message
git log --all --format="%H %s" | grep -i "工商银行|ICBC|apikey|password"
```

### Step 3: Find the Clean Base
```bash
# Find the commit BEFORE contamination started
# Last known clean commit + 1 = first contaminated
git log --oneline
# or
git reflog | head -20
```

### Step 4: Create Clean Branch from Clean Base
```bash
git checkout -b clean-main <clean_base_sha>
```

### Step 5: Cherry-Pick Only Clean Commits
```bash
SENSITIVE_SHAS="f6c4c4e5 a3aa3351"  # space-separated

for sha in $(git log --reverse --format="%H" <clean_base>..<dirty_tip>); do
  if [[ " $SENSITIVE_SHAS " =~ " $sha " ]]; then
    echo "🔒 SKIP $sha (sensitive)"
  else
    git cherry-pick $sha --no-commit
    git commit -m "$(git log -1 --format=%B $sha)"
    echo "✅ $sha"
  fi
done
```

### Step 6: Verify Clean State Before Pushing
```bash
# Confirm sensitive commits are gone
git log --oneline | grep -E "f6c4c4e5|a3aa3351" | wc -l
# Must return 0

# Check ancestry — should return exit code 1 (NOT an ancestor)
git merge-base --is-ancestor <sensitive_sha> HEAD
```

### Step 7: Force Push
```bash
git push https://<TOKEN>@github.com/<user>/<repo>.git clean-branch:refs/heads/main --force
```

### Step 8: Post-Push Verification
```bash
git fetch origin main
git log --oneline origin/main | grep -E "sensitive1|sensitive2" | wc -l  # must be 0
git merge-base --is-ancestor <sensitive_sha> origin/main  # must exit 1
```

## Key Pitfalls Discovered

### Pitfall 1: Remote Tracking Confusion
After changing `remote.origin.url` from upstream to fork, `origin/main` tracks the **fork's** remote, not the upstream. "Diverged" in `git status` means the local branch and the fork's remote have both moved — it does NOT tell you whether sensitive commits are in the remote's history.

**Verification**: `git merge-base --is-ancestor <sensitive> origin/main` — exit code 0 means contaminated.

### Pitfall 2: "Diverged" ≠ Just New Tips
`git status` showing "22 local commits, 85 remote commits" is MISLEADING. The 85 remote commits are from the original upstream repo. The 22 local commits include sensitive ones that WERE pushed to the fork when `origin` pointed there.

**Lesson**: Always use `git merge-base --is-ancestor`, not `git log --oneline | grep`.

### Pitfall 3: Cherry-Pick Creates New SHAs
Cherry-picking creates NEW commits with DIFFERENT SHAs. The new SHA ≠ old SHA is expected and correct.

### Pitfall 4: GitHub Keeps All Objects
Even after force-push, GitHub retains all objects unless GC'd. A commit remains accessible via direct SHA URL until GitHub runs garbage collection (which they do periodically but not on demand).

**Mitigation**: After force-push, the commit is no longer reachable via any branch or tag — it becomes a dangling object. It's still in the Git object store but not linked from any ref.

## When NOT to Force Push
- If collaborators may have pulled the contaminated history
- If contaminated commits are tagged in a release
- If CI/CD uses the contaminated commit SHA as an artifact ID

**Alternative**: Archive the old repo, create a NEW clean repository, push the clean branch there.

## Verification Checklist
- [ ] `git merge-base --is-ancestor <sensitive_sha> origin/main` returns exit code 1
- [ ] `git log --oneline origin/main | grep <sensitive>` returns nothing
- [ ] `git ls-remote origin refs/heads/main` returns clean tip SHA
- [ ] `git fetch origin main && git log --oneline origin/main -n 3` shows clean history
