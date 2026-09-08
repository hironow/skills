# Maintenance tasks for this skills repository. Every top-level directory
# with a SKILL.md is a skill; `scripts/` holds the stdlib-only tooling that
# keeps them consistent. Conventions: README.md ("Maintaining").

set shell := ["bash", "-eu", "-o", "pipefail", "-c"]
# Native Windows: WSL's System32 bash.exe shadows Git Bash for a bare `bash`,
# while `sh` resolves to Git Bash; the prelude puts /usr/bin first so the
# recipe's own commands resolve there too. Copied from the dotfiles justfile
# (its comment explains the mechanism in full) because just settings do not
# carry over into a nested `just --justfile` invocation.
set windows-shell := ["sh", "-eu", "-o", "pipefail", "-c", 'PATH="/usr/bin:$PATH"; exec /usr/bin/sh -eu -o pipefail -c "$0"']

# List recipes
default:
    @just --list --unsorted

# Structural audit: frontmatter, links and anchors, code fences, emoji
# markers, language rule, provenance contract.
audit:
    uv run scripts/audit.py

# The same audit plus a byte comparison against every agent home that
# receives a copy (dotfiles' additive sync never refreshes them) and
# dangling-symlink detection. Depends on the machine, so not part of `check`.
audit-consumers:
    uv run scripts/audit.py --consumers

# Regenerate the generated README tables (index + credits) from frontmatter.
# Run after adding, removing, or re-sourcing a skill, then commit README.md.
readme-index:
    uv run scripts/readme_index.py

# The README tables must match the frontmatter.
readme-check:
    uv run scripts/readme_index.py --check

# Quantitative comparison of skill versions (fork first, then the upstream
# copies): sizes, description length, tooling violations, body diff.
# Usage: just compare review /path/to/upstream/code-review
compare +versions:
    uv run scripts/compare.py {{ versions }}

# Unit tests of the tooling
test:
    uv run pytest -q -ra

# ruff format
fmt:
    uv run ruff format

# ruff (format check + lint) and ty (type check; warnings fail, see pyproject)
lint:
    uv run ruff format --check
    uv run ruff check
    uv run ty check

# The full local gate; CI runs the same thing.
check: lint test audit readme-check
