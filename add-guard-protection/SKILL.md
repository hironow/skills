---
name: add-guard-protection
license: Apache-2.0
description: Protect code paths that have no incoming HTTP request — AI agent tool calls, agent loops, MCP tool handlers, background jobs, queue workers — with Arcjet Guard (`@arcjet/guard` for JS/TS, `arcjet.guard` for Python), covering rate limiting, prompt injection detection, sensitive information blocking, and custom rules. Use when the user says "rate limit my tool calls", "block prompt injection in my agent", "add security to my MCP server", or "protect my queue worker", even without mentioning Arcjet or Guard. Not for HTTP routes, endpoints, forms, or webhooks — that is add-request-protection. Uses the Arcjet CLI (`bunx @arcjet/cli` or `brew install arcjet`) for authentication and site/key setup.
metadata:
  author: arcjet
---

# Add Arcjet Guard Protection

Arcjet Guard provides rate limiting, prompt injection detection, sensitive information blocking, and custom rules for code paths that don't have an HTTP request — AI agent tool calls, MCP tool handlers, background job processors, queue workers, and similar.

## Step 0: Set Up the Arcjet CLI

The Arcjet CLI is the primary tool for authenticating, managing sites, configuring remote rules, and monitoring traffic. Install it if not already available:

```bash
# Via bunx (no install required)
bunx @arcjet/cli --help

# Or install globally via bun
bun add -g @arcjet/cli

# Or via Homebrew
brew install arcjet
```

### Authenticate

```bash
arcjet auth login
```

Opens the browser for authentication. Check status with `arcjet auth status`.

### Site & Key Setup

```bash
# List your teams
arcjet teams list

# List sites for a team
arcjet sites list --team-id <team-id>

# Create a new site
arcjet sites create --team-id <team-id> --name "My Guard App" --confirm

# Get the SDK key for a site
arcjet sites get-key --site-id <site-id>
```

Add the key to your environment file (`.env`, `.env.local`, etc.) as `ARCJET_KEY`.

## Step 1: Detect the Language and Install

Check the project for language indicators:

- `package.json` → JavaScript/TypeScript → `bun add @arcjet/guard` (requires `@arcjet/guard` >= 1.4.0)
- `requirements.txt` / `pyproject.toml` → Python → `uv add arcjet` (requires `arcjet` >= 0.7.0; Guard is included)
- `go.mod`, `Cargo.toml`, `pom.xml`, or other languages → **Guard is not available**. Tell the user that Arcjet Guard currently only supports JavaScript/TypeScript and Python. Do not create a hand-rolled imitation or hallucinate a package that doesn't exist. Suggest they reach out to Arcjet with their use case.

## Step 2: Read the Language Reference

**You must read the reference file for the detected language before writing any code.** The references contain the exact imports, constructor signatures, rule configuration syntax, and guard() call patterns for that language.

- JavaScript/TypeScript: [references/javascript.md](references/javascript.md)
- Python: [references/python.md](references/python.md)

Do not guess at the API. The reference files are the source of truth for all code patterns.

## Step 3: Create the Guard Client (Once, at Module Scope)

The client holds a persistent connection. Create it once at module scope and reuse it — never inside a function or per-call. Name the variable `arcjet`.

Check if `ARCJET_KEY` is set in the environment file (`.env`, `.env.local`, etc.). If not, obtain the key in this priority order:
1. **CLI (preferred):** Run `arcjet sites get-key --site-id <site-id>` (requires `arcjet auth login` first — see Step 0)
2. **MCP:** If the Arcjet MCP server is connected, use it to list sites and retrieve the key
3. **Manual (last resort):** Add a placeholder and tell the user to get a key from https://app.arcjet.com

## Step 4: Configure Rules at Module Scope

Rules are configured once as reusable factories, then called with per-invocation input. This two-phase pattern matters — the rule config carries a stable ID used for server-side aggregation, while the per-call input varies.

When configuring rate limit rules, set `bucket` to a descriptive name (e.g. `"tool-calls"`, `"session-api"`) for semantic clarity and fewer collisions.

### Choosing Rules by Use Case

| Use case | Recommended rules |
| -------- | ----------------- |
| AI agent tool calls | `tokenBucket` + `detectPromptInjection` |
| MCP tool handlers | `slidingWindow` or `tokenBucket` + `detectPromptInjection` |
| Background AI task processor | `tokenBucket` + `localDetectSensitiveInfo` |
| Queue worker with user input | `tokenBucket` + `detectPromptInjection` + `localDetectSensitiveInfo` |
| Scanning tool results for injection | `detectPromptInjection` (scan the returned content) |

## Step 5: Call guard() Inline Before Each Operation

Call `guard()` directly where each operation happens — inline in each tool handler, task processor, or function that needs protection. Do not wrap guard in a shared helper function.

Each `guard()` call takes:
- **label**: descriptive string for the dashboard (e.g. `"tools.search_web"`, `"tasks.generate"`)
- **rules**: array of bound rule invocations
- **metadata** (optional): key-value pairs for analytics/auditing (e.g. `{ userId }`)

Rate limit rules take an explicit **key** string — use a user ID, session ID, API key, or any stable identifier.

Wire `guard()` into the actual handlers; adding the dependency alone protects nothing.

## Step 6: Handle Decisions

Always check `decision.conclusion`:
- `"DENY"` → block the operation. Use per-rule result accessors (see reference) for specific error messages like retry-after times.
- `"ALLOW"` → safe to proceed

See the language reference for the exact decision-checking pattern and per-rule result accessors.

## Common Mistakes to Avoid

- **Using the HTTP SDK when there's no request** — use `@arcjet/guard` / `arcjet.guard`, not `@arcjet/node`, `@arcjet/next`, or `arcjet()`.
- **Generic DENY messages** — use per-rule result accessors to give users specific feedback like retry-after times.

## Step 7: Verify

Once the `arcjet guards` CLI subcommand ships, use `arcjet guards watch --site-id <site-id>` to stream decisions and `arcjet guards details` to inspect one; until then verify in the dashboard at https://app.arcjet.com.

## CLI Quick Reference

| Task | Command |
| ---- | ------- |
| Install/run CLI | `bunx @arcjet/cli` or `brew install arcjet` |
| Authenticate | `arcjet auth login` |
| Check auth status | `arcjet auth status` |
| List teams | `arcjet teams list` |
| List sites | `arcjet sites list --team-id <id>` |
| Create site | `arcjet sites create --team-id <id> --name "Name" --confirm` |
| Get SDK key | `arcjet sites get-key --site-id <id>` |

### Global Flags

All commands support:
- `--output text|json` — output format (default: text on TTY, json otherwise)
- `--fields <list>` — comma-separated fields to include in JSON output
- `--no-color` — disable ANSI colors (also honors `NO_COLOR` env var)
- `--timeout <duration>` — max execution time (e.g. `30s`, `5m`; 0 disables)

### Exit Codes

| Code | Meaning |
| ---- | ------- |
| 0 | Success |
| 1 | General error (unknown command, API failure, network error) |
| 2 | Authentication error (not logged in, token expired) |
| 3 | Input validation error (invalid ID, value out of range) |
| 4 | Confirmation required (mutation needs `--confirm`) |
