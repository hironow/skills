---
name: obsidian-vault
description: Search, create, and manage notes in the Obsidian vault with wikilinks and index notes. Use when user wants to find, create, or organize notes in Obsidian.
license: MIT
metadata:
  provenance: derived
  upstream: mattpocock/skills@f958fa1:skills/personal/obsidian-vault
  upstream-license: MIT
  changes: "the vault root comes from $OBSIDIAN_VAULT (asked once if unset) instead of the hardcoded /mnt/d/Obsidian Vault/AI Research/ path"
---

# Obsidian Vault

## Vault location

Read the vault root from `$OBSIDIAN_VAULT`; if unset, ask the user once and export it for the session. Mostly flat at root level.

## Naming conventions

- **Index notes**: aggregate related topics (e.g., `Ralph Wiggum Index.md`, `Skills Index.md`, `RAG Index.md`)
- **Title case** for all note names
- No folders for organization - use links and index notes instead

## Linking

- Use Obsidian `[[wikilinks]]` syntax: `[[Note Title]]`
- Notes link to dependencies/related notes at the bottom
- Index notes are just lists of `[[wikilinks]]`

## Workflows

### Search for notes

```bash
# Search by filename
find "$OBSIDIAN_VAULT" -name "*.md" | grep -i "keyword"

# Search by content
grep -rl "keyword" "$OBSIDIAN_VAULT" --include="*.md"
```

Or use Grep/Glob tools directly on the vault path.

### Create a new note

1. Use **Title Case** for filename
2. Write content as a unit of learning (per vault rules)
3. Add `[[wikilinks]]` to related notes at the bottom
4. If part of a numbered sequence, use the hierarchical numbering scheme

### Find related notes

Search for `[[Note Title]]` across the vault to find backlinks:

```bash
grep -rl "\\[\\[Note Title\\]\\]" "$OBSIDIAN_VAULT"
```

### Find index notes

```bash
find "$OBSIDIAN_VAULT" -name "*Index*"
```
