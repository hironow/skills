---
name: "yeet"
description: "Use only when the user explicitly asks to stage, commit, push, and open a GitHub pull request in one flow using the GitHub CLI (`gh`)."
---

## Prerequisites

- Require GitHub CLI `gh`. Check `gh --version`. If missing, ask the user to install `gh` and stop.
- Require authenticated `gh` session. Run `gh auth status`. If not authenticated, ask the user to run `gh auth login` (and re-run `gh auth status`) before continuing.

## Naming conventions

- Branch: `{agent}/{description}` (e.g. `codex/…`, `claude/…`) when starting from the default branch.
- Commit: `{description}` (terse).
- PR title: `{description}` summarizing the full diff.

## Workflow

- If on main/master/default, create a branch: `git checkout -b "{agent}/{description}"`
- Otherwise stay on the current branch.
- Confirm status, then stage everything: `git status -sb` then `git add -A`.
- Commit tersely with the description: `git commit -m "{description}"`
- Run checks if not already. If checks fail due to missing deps/tools, install dependencies and rerun once.
- Push with tracking: `git push -u origin $(git branch --show-current)`
- If the push is rejected for a missing `workflow` scope, run `gh auth refresh -s workflow` and retry.
- Write the PR body to a temp file with real newlines (heredoc → `pr-body.md`), then: `GH_PROMPT_DISABLED=1 GIT_TERMINAL_PROMPT=0 gh pr create --draft --title "{description}" --body-file pr-body.md --head "$(git branch --show-current)"`
- PR description (markdown) must be detailed prose covering the issue, the cause and effect on users, the root cause, the fix, and any tests or checks used to validate.
