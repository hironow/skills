---
name: update-submodule-changelog
description: |
  Update docs/changelogs.md after submodules under protocols/*, payments/*, or gcloud/* change.
  Applies automatically on keywords such as "サブモジュール更新", "changelog更新", "プロトコル変更まとめ",
  after git submodule update, or whenever dependency changes need to be documented.
argument-hint: [submodule name (all when omitted)]
allowed-tools: Read, Write, Bash(git:*), Grep, Glob, Agent
license: MIT
metadata:
  provenance: original
---

# Submodule Changelog Update Skill

The workflow for updating `docs/changelogs.md` after submodules change.

## Overview

This skill:
1. Detects which submodules changed
2. Collects the changes from each submodule's CHANGELOG.md or git log
3. Updates `docs/changelogs.md` in the agreed format

**Important**: this changelog records **each project's latest release**, not the submodule's checked-out state. Look up each repository's latest tag or release rather than trusting `git submodule status`.

## Workflow

### Step 1: Detect changed submodules

```bash
# Which submodules changed
git status

# Latest commit of each submodule
git submodule status
```

### Step 2: Collect the changes

For each submodule:

```bash
# Enter the submodule and look at recent commits
cd <submodule-path>
git log --oneline -10

# Read CHANGELOG.md if there is one
cat CHANGELOG.md | head -100
```

**Scope**: the submodules listed by `git submodule status` that are external libraries or specifications. Exclude the self-authored, non-library ones: `skills` / `knowledge-work-plugins` / `guardrails/**` / `tools/**`. Use `git submodule status` **only to enumerate** the targets; the version you record is each repository's latest tag or release (see "Important" above). Current layout: `protocols/` (protocol specifications), `payments/` (payment protocols), `gcloud/` (Google Cloud / ADK).

### Step 3: Update changelogs.md

Update `docs/changelogs.md` with this structure (the document is written in Japanese; keep the headings as they are):

```markdown
# プロトコル変更ログ

最終更新: YYYY-MM-DD

---

## プロトコル (Protocols)

### <プロトコル名>

**現行バージョン**: <version>

#### 主要な変更点
- **機能名**: 説明

#### 破壊的変更（あれば）
| 変更 | 影響 |
|------|------|
| 変更内容 | 影響範囲 |

#### 参考リンク
- [リンク名](URL)

---

## Google Cloud / ADK

### <コンポーネント名>

**現行バージョン**: <version>

#### 主要な変更点
- **機能名**: 説明

---

## 注目ポイント

### 破壊的変更一覧
| 対象 | 変更内容 | 対応優先度 |
|------|---------|-----------|

### 新規追加プロトコル
1. **名前** - 説明 (管理元)

### セキュリティ更新
- **対象**: 説明
```

## Format conventions

### Version notation
- semver: `v1.2.3`
- date-based: `YYYY-MM-DD`
- first release: `初期リリース`
- tracking the tip: `latest`

### Writing a change entry
- Feature name in **bold**
- A colon `:` followed by the description
- Code references in backticks
- PR and issue numbers as `(#123)`

### Breaking changes
- Always listed under the breaking-changes section
- State the affected area
- Include the migration path if there is one

## Research tips

### Finding the latest release
```bash
# Latest tags of the repository (may differ from the checked-out state)
cd <submodule-path>
git fetch --tags
git tag -l --sort=-v:refname | head -5

# Latest release from CHANGELOG.md
cat CHANGELOG.md | head -100
```

**Note**: `git submodule status` shows the checked-out state. Use `git tag` or CHANGELOG.md to find the latest release.

### When there is no CHANGELOG.md
```bash
# Infer the changes from recent commits
git log --oneline -20
git log --pretty=format:"%s" -10

# Latest version from tags
git describe --tags --abbrev=0
git tag -l | tail -5
```

## Checklist

Before declaring the update done:

- [ ] `最終更新` shows today's date
- [ ] **Versions reflect each repository's latest release** (not the checked-out state)
- [ ] Newly added protocols appear under `注目ポイント`
- [ ] Breaking changes are collected in the summary table
- [ ] Every reference link in each section resolves
- [ ] The Japanese reads naturally
- [ ] Stale information is removed (except backward-compatibility notes that still matter)

## Do not commit

Leave reviewing the change to the user. Wait for the user's instruction before committing.
