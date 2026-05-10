---
name: github-code-review
description: "Use when reviewing code changes by analyzing git diffs, leaving inline comments on PRs, and performing thorough pre-push review. Works with gh CLI or falls back to git + GitHub REST API via curl. NOT for: non-GitHub code review, automated testing, or when GitHub CLI is not available."
category: general
triggers: [review PR, review code, analyze diff, git diff review, code review, PR comments,
  pre-push review]
anti_triggers: [create repository, manage issues, run tests, deploy code]
version: 1.1.0
...
author: Hermes Agent
...
license: MIT
...
---

## A2 — 触发场景 (Trigger)

Load this skill when the user asks to review a PR, analyze git diffs, leave inline comments on a pull request, or perform any code review activity.

## R — 知识溯源 (Reading)

- Git diff parsing: `git diff <ref>` for changed lines, `git log` for commit history
- GitHub PR API: `GET /repos/{owner}/{repo}/pulls/{pull_number}` for PR details
- Inline comments: `POST /repos/{owner}/{repo}/pulls/{pull_number}/comments`
- gh CLI: `gh pr diff`, `gh pr review`

## I — 方法论骨架 (Interpretation)

1. Fetch the PR diff using gh CLI or git + GitHub REST API
2. Parse the diff to identify changed files, hunks, and line-level changes
3. Analyze each changed file for: logic errors, security issues, style violations, test coverage gaps
4. Generate a structured review report with file-by-file findings
5. Post inline comments for specific line-level issues using the GitHub API
6. Submit the overall review (approve/request-changes/comment)

## A1 — Application

### Step 1: Fetch PR metadata

bash
# Using gh CLI (preferred)
gh pr view <pr-number> --repo <owner>/<repo> --json title,body,state,author

# Using GitHub REST API
curl -H "Authorization: token $GITHUB_TOKEN" \
  https://api.github.com/repos/<owner>/<repo>/pulls/<pr-number>


### Step 2: Get the diff

bash
gh pr diff <pr-number> --repo <owner>/<repo>

# Or via API
curl -H "Authorization: token $GITHUB_TOKEN" \
  https://api.github.com/repos/<owner>/<repo>/pulls/<pr-number> \
  | jq -r '.diff_url' | xargs curl -H "Authorization: token $GITHUB_TOKEN"


### Step 3: Leave inline comments

bash
gh api repos/<owner>/<repo>/pulls/<pr-number>/comments \
  -f body='<comment-body>' \
  -f commit_id='<commit-sha>' \
  -f path='<file-path>' \
  -f line=<line-number>


### Step 4: Submit review

bash
gh pr review <pr-number> --repo <owner>/<repo> --approve  # or --request-changes

# Via API
curl -X POST -H "Authorization: token $GITHUB_TOKEN" \
  -d '{"event": "APPROVE", "body": "LGTM"}' \
  https://api.github.com/repos/<owner>/<repo>/pulls/<pr-number>/reviews


## E — Edge Cases

- **Large diffs**: Paginate using `per_page` and `page` parameters; process in chunks
- **Binary files**: Skip binary file diffs — they cannot be reviewed via text diff
- **Renamed files**: Use `git diff --name-status` to detect renames before reviewing
- **Merge commits**: Exclude merge commits from diff review (`--no-merges`)
- **Unrelated commits in PR**: Filter by commits belonging to the PR vs. base branch history
- **gh not installed**: Fall back to `git fetch` + `git diff origin/<branch>` + `curl` to GitHub REST API
- **Authentication**: Set `GITHUB_TOKEN` environment variable for API calls; gh CLI uses stored credentials

## B — Background

GitHub's code review workflow involves fetching the diff between two branches (typically `main` and the PR branch), analyzing changes at the file and line level, and posting feedback via the GitHub API or gh CLI. The review should cover correctness, security, test coverage, performance, and maintainability. Always distinguish between blocking issues (bugs, security) and non-blocking suggestions (style, naming).
