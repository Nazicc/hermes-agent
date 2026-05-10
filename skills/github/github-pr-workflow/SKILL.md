---
name: github-pr-workflow
description: "Full pull request lifecycle — create branches, commit changes, open PRs, monitor CI status, auto-fix failures, and merge. Works with gh CLI or falls back to git + GitHub REST API via curl. Trigger signals: user asks to create a PR, open a pull request, merge code, check CI status, fix CI failures, sync branches. NOT for: GitHub authentication setup (use github-auth), repository creation/forking/management (use github-repo-management), code review without PR context (use github-code-review)."
category: general
---

## GitHub PR Workflow

### Prerequisites

**gh CLI (preferred):** `brew install gh` or `npm install -g gh`
**Fallback:** `git`, `curl`, `jq`, and `GH_TOKEN` env var set to a GitHub Personal Access Token

### Detection Flow


if gh is installed and gh auth status succeeds:
    use gh CLI for all operations
else:
    use git + GitHub REST API via curl
    require GH_TOKEN env var
    require REPO_OWNER and REPO_NAME env vars (or extract from git remote)


## Branch & Commit Workflow

### Via gh CLI

bash
# Create a branch and commit
BRANCH="feat/$(date +%Y%m%d%H%M%S)"
git checkout -b $BRANCH
git add . && git commit -m "..."
git push -u origin $BRANCH

# Create PR
gh pr create --title "<title>" --body "<description>" --base <target-branch>
gh pr view --web  # open in browser


### Via curl fallback

bash
# Detect repo from git remote
REPO=$(git remote get-url origin | sed 's|.*github.com/||' | sed 's|\.git$||')
OWNER=$(echo $REPO | cut -d/ -f1)
REPO_NAME=$(echo $REPO | cut -d/ -f2)

# Create branch
BRANCH="feat/$(date +%Y%m%d%H%M%S)"
git checkout -b $BRANCH
git add . && git commit -m "..."
git push -u origin $BRANCH

# Create PR via REST API
curl -s -X POST \
  -H "Authorization: token $GH_TOKEN" \
  -H "Accept: application/vnd.github+json" \
  https://api.github.com/repos/$OWNER/$REPO_NAME/pulls \
  -d '{"title":"<title>","body":"<description>","head":"'$BRANCH'","base":"<target>"}'


## CI Monitoring & Auto-Fix

### Check CI status

bash
# gh
gh pr status
gh pr checks <pr-number>

# curl fallback
curl -s -H "Authorization: token $GH_TOKEN" \
  "https://api.github.com/repos/$OWNER/$REPO_NAME/commits/$BRANCH/status"


### Auto-fix CI failures

bash
# Checkout PR branch
gh pr checkout <pr-number>
# Fix failures locally, amend or create new commit
git commit --amend --no-edit
git push --force-with-lease


## Merge

bash
# gh
gh pr merge <pr-number> --squash --delete-branch

# curl fallback
curl -s -X PUT \
  -H "Authorization: token $GH_TOKEN" \
  -H "Accept: application/vnd.github+json" \
  "https://api.github.com/repos/$OWNER/$REPO_NAME/pulls/<pr-number>/merge" \
  -d '{"merge_method":"squash"}'


## Quality Guidelines

- Check gh availability first, then fall back to git+curl. Do NOT assume gh is installed.
- PR descriptions and branch names must be validated before creation to avoid silent failures.
- CI status polling should include a timeout to prevent infinite loops.
- Auto-fix logic must identify the specific failing step before attempting remediation.
- API rate limiting: 5000 req/hr for authenticated requests
