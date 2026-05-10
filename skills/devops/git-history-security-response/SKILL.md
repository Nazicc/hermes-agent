---
name: git-history-security-response
description: "Use when responding to sensitive data exposure in git history — API keys, tokens, credentials, or business data accidentally pushed to a public repository. Also use for proactive security audits of git history to detect leaked secrets before incidents occur. Covers tracing commit ancestry with `git log --all -S`, BFG Repo-Cleaner, git-filter-repo, cherry-picking clean commits, and force-pushing to erase history. NOT for: routine commits, normal git workflows, or when the repository has no sensitive data history."
category: devops
---

## When to Load This Skill

- A secret, API key, token, credential, or business data is found (or suspected) in a public repository
- Proactive security audit of a repository's git history
- Responding to a reported leak or 'found secret' alert
- Auditing a freshly cloned or inherited repository before publishing

## Quick Reference

When sensitive data is accidentally pushed:

1. **Identify** the sensitive content and the commit(s) that introduced it
2. **Assess** the exposure scope (public repo? forks? clones?)
3. **Contain** by revoking exposed credentials immediately
4. **Remediate** by rewriting history and force-pushing clean commits
5. **Notify** affected parties if data is truly public

## Proactive Security Audit

Run these checks regularly or before any public repo push to catch leaked secrets before they are found by others.

### Audit entire history for common secret patterns

bash
# AWS keys
git log --all -S "AKIA" --oneline

# GitHub tokens
git log --all -S "ghp_" --oneline
git log --all -S "github.com" --oneline | grep -i "token\|key\|secret"

# OpenAI keys
git log --all -S "sk-" --oneline

# Database passwords
git log --all -S "password=" --oneline

# JWT/Bearer tokens
git log --all -S "eyJ" --oneline

# Private keys
git log --all -S "-----BEGIN" --oneline

# Check for .env committed
git log --all --oneline -- ".env"

# Scan all branches
git log --all --oneline | head -20

# Check remote URLs for embedded credentials
git remote -v


### .gitignore coverage check

bash
grep -i "\.bak" .gitignore || echo "WARNING: .bak not in .gitignore"
grep -i "\.env" .gitignore || echo "WARNING: .env not in .gitignore"
grep -i "secrets" .gitignore || echo "WARNING: secrets/ not in .gitignore"


### Commit hygiene checks

bash
git log origin/main..HEAD --oneline
git log origin/main..HEAD --oneline -- "skills/" | head -20


## Incident Response

### Find secrets in history

bash
# Trace a specific string through all history
git log --all -p -S "YOUR_SECRET_VALUE" --source --all

# Case-insensitive search
git log --all -p -S "your_secret" --source --all -i

# Search for API key patterns across all commits
git log --all -p --pattern "sk-[0-9a-zA-Z]" | head -100
git log --all -p --pattern "ghp_[0-9a-zA-Z]" | head -100
git log --all -p --pattern "AKIA[0-9A-Z]" | head -100

# Grep all commits for secret keyword
grep -r "secret" --all-commit -- . 2>/dev/null


### Remove a secret from all history

**WARNING: These operations rewrite git history. Coordinate with your team before proceeding.**

**Option A: BFG Repo-Cleaner (recommended, 10-1000x faster than filter-branch)**

Download from https://rtyley.github.io/bfg-repo-cleaner/

bash
# Create passwords.txt with lines like "SECRET_KEY###" (appends ### to replacement)
echo "THE_SECRET_VALUE###" > passwords.txt

# Clean the repository
java -jar bfg.jar --replace-text passwords.txt --no-blob-protection repo.git

# Force push to overwrite remote
git push origin --force --all
git push origin --force --tags


**Option B: git-filter-repo (requires pip install)**

bash
pip install git-filter-repo
git filter-repo --path-glob '*.env' --invert-paths
git filter-repo --path secret.txt --invert-paths


**Option C: Cherry-pick clean commits**

bash
git checkout --orphan clean-history
git cherry-pick <clean-commit-hash>
# Repeat for all clean commits, then force push


**Option D: git filter-branch (legacy, slower)**

bash
git filter-branch --force --index-filter \
  'git rm --cached --ignore-unmatch filename_with_secret' \
  --prune-empty --tag-name-template '' -- --all


### Verify cleanup

bash
git log --all -S "YOUR_SECRET" --oneline  # Should return empty
grep -r "YOUR_SECRET" --all-commit -- . 2>/dev/null  # Should return empty


### Check exposure scope

bash
# GitHub: check if repository was public
gh api repos/OWNER/REPO --jq '.visibility'

# Check recent activity
gh api repos/OWNER/REPO/events --jq '.[].type'


### After force-push to GitHub

GitHub shows commit remediation status. Check **Settings → Code security and analysis → Secret scanning** for alert details.

## Notify Affected Parties

- If a GitHub PAT was exposed: revoke immediately at https://github.com/settings/tokens
- If an AWS key was exposed: rotate in IAM console and check CloudTrail for misuse
- If a database password was exposed: rotate and audit access logs

**Notification Template:**

**Subject:** [Security Incident] Repository {name} - Sensitive Data Exposure

**Details:**
- What was exposed:
- When it was exposed:
- Exposure scope (public forks, downloads):
- Action taken:
- Credentials revoked: Yes/No

## Prevention

### Pre-push hook

bash
# .git/hooks/pre-push
#!/bin/bash
git diff --staged -S "sk-" -- . && echo "BLOCKED: potential secret in staged changes" && exit 1
git diff --staged -S "ghp_" -- . && echo "BLOCKED: potential GitHub token in staged changes" && exit 1
git diff --staged -S "AKIA" -- . && echo "BLOCKED: potential AWS key in staged changes" && exit 1


### Additional measures

- Use git-secret, blackbox, or similar tools for encrypting sensitive files in repos
- Enable secret scanning on GitHub: **Settings → Code security and analysis → Secret scanning**
- Enable push protection: **Settings → Code security and analysis → Push protection**
