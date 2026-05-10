---
name: github-issues
description: "Create, manage, triage, and close GitHub issues. Search existing issues, add labels, assign people, and link to PRs. Works with gh CLI or falls back to git + GitHub REST API via curl."
category: general
---

## R — 知识溯源 (Reference)

- GitHub REST API v3: `https://api.github.com/repos/{owner}/{repo}/issues`
- gh CLI docs: `gh issue --help`
- Authentication: `gh auth login` or `export GITHUB_TOKEN=<PAT>`

## I — 方法论骨架 (Interpretation)

**Issue workflow:**
1. Detect auth method (gh CLI or token-based curl)
2. Map user intent → API action (create / search / label / assign / close)
3. Execute with gh or curl fallback
4. Parse response and confirm to user

**Tool selection:**
- gh CLI preferred (interactive, handles pagination)
- curl fallback for headless environments or custom hosts

## A1 — Application (gh CLI path)

bash
# Auth check
gh auth status

# List issues
gh issue list --repo owner/repo --state open --limit 20

# Search issues
gh issue search "bug in auth" --repo owner/repo

# Create issue
gh issue create --repo owner/repo --title "Bug: login fails" --body "..." --label bug

# Add labels
gh issue edit 123 --repo owner/repo --add-label "priority:high"

# Assign
gh issue edit 123 --repo owner/repo --add-assignee username

# Close
gh issue close 123 --repo owner/repo

# Link PR to issue
gh pr close 456 --delete-branch && gh issue close 123


## A2 — Application (curl fallback path)

bash
# Set token
export GITHUB_TOKEN=ghp_...
BASE="https://api.github.com/repos/owner/repo"

# List
grep 'total_count\|title\|state' <<<$(curl -sH "Authorization: token $GITHUB_TOKEN" "$BASE/issues?state=open")

# Search
grep 'total_count\|title' <<<$(curl -sH "Authorization: token $GITHUB_TOKEN" "https://api.github.com/search/issues&q=repo:owner/repo+bug")

# Create
curl -s -X POST -H "Authorization: token $GITHUB_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"title":"Bug: login fails","body":"...","labels":["bug"]}' \
  "$BASE/issues"

# Edit (label/assign)
curl -s -X PATCH -H "Authorization: token $GITHUB_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"labels":["priority:high"],"assignees":["username"]}' \
  "$BASE/issues/123"

# Close
curl -s -X PATCH -H "Authorization: token $GITHUB_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"state":"closed"}' \
  "$BASE/issues/123"


## E — Edge Cases

- **No GITHUB_TOKEN**: Prompt user or fall back to gh CLI interactive auth (`gh auth login`)
- **Rate limiting**: Check `X-RateLimit-Remaining` header; wait 1 hour if exhausted
- **Private repos**: gh CLI handles auth automatically; curl needs explicit token
- **Issue vs PR**: Issues and PRs share the same API endpoint but have different `pull_request` field in response
- **Labels with spaces**: Use URL-encoded or JSON-array format; gh CLI handles this automatically

## B — Boundary Conditions

- **Pagination**: Use `--page` flag (gh) or `?page=N&per_page=100` (curl) for >30 items
- **State filters**: `--state all|open|closed` (gh) / `?state=all` (curl)
- **Milestone**: `--milestone "v2.0"` (gh) / `?milestone=N` (curl)
- **Comments**: Separate endpoint `GET /repos/{owner}/{repo}/issues/{issue_number}/comments`
- **Reactions**: `POST /repos/{owner}/{repo}/issues/{issue_number}/reactions` (requires specific accept header)
