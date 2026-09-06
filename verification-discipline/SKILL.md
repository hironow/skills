---
name: verification-discipline
description: >-
  How to not fool yourself (or be fooled) when verifying work — yours, a
  reviewer's, a subagent's, or a checker's. Use whenever accepting review
  findings, grading/judging another agent's output, verifying checksums or
  pinned versions, interpreting a failing (or suspiciously passing) test or
  gate, or writing any report that claims something is "done", "green", or
  "verified". Especially load-bearing when the author and the verifier are
  the same context — the situation this skill exists to break.
license: MIT
metadata:
  provenance: original
---

# Verification discipline: trust nothing ("何も信用しない"), including yourself

Capability is cheap; calibrated trust is what fails. These rules turn "I
believe it works" into "here is what was proven, by what, and what wasn't."
Each rule carries the real incident that earned it.

## 1. Every claim is a hypothesis until executed

Reading code tells you what it says; only running it tells you what it does.
Before reporting a state ("gate is green", "tests pass", "the pin is
current"), execute the command that proves it, in the final state of the
tree. A claim someone else made — reviewer, subagent, tool output you
half-remember — gets re-executed, not quoted.

*Incident:* a plan reviewer (another model) produced 4 findings; each was
checked against the actual repo before adoption. All 4 held — but only the
checking made them adoptable. The reviewer had no repo context guarantees;
"plausible" and "true" diverge exactly there.

## 2. Verify the verifier

When a checker fails something, read the checker before demanding the fix.
When it passes something suspiciously easily, ask what it cannot see.
Checkers are code; code has bugs.

*Incident:* an eval grader FAILed an agent for "proposing to pin an
unpinnable tool". The agent's actual sentence said the tool **cannot** be
pinned — the grader's regex matched the word "pin" inside a do-not-pin
statement. The agent was right; the grader was wrong. The fix was to the
grader, and the lesson is symmetric: when checker and checked disagree,
suspect both until one is proven.

## 3. Two independent paths for security-critical values

Checksums, pinned SHAs, release artifacts: one source of truth is one spoof
(or one typo) away from wrong. Confirm via two paths that do not share a
failure mode: the published checksum file AND a local hash of the actually
downloaded artifact; the release API's digest AND the bytes. If the two
paths disagree, stop — that disagreement is the most important signal you
will get all day.

*Incident:* every checksum bump in the pipeline was double-sourced
(SHASUMS256.txt + hashing the real tarball). Cost: seconds. It also
converts "I copied a hash" into "I verified an artifact".

## 4. Report in three grades, never two

Every claim in a report is **proven** (you executed it, evidence attached),
**reasoned** (you read/derived it, could be wrong), or **unverified** (out
of reach from here). Say which, per claim. The failure mode is laundering:
one honest "tests pass" makes the neighboring unverified claims look proven.
"Not verifiable locally: smoke on the real runner pool — needs the PR CI
run" is a *stronger* report than silence, because the reader now knows the
exact residual risk.

## 5. Independence is structural, not attitudinal

You cannot adversarially review what you authored in the same context —
your reasons look like facts from inside. Independence means a mechanically
separate examiner: a different model, a fresh subagent with no memory of
authoring, a gate that runs regardless of anyone's opinion. Order of
preference for making judgment survive people (and models):
**mechanized gate > checklist run by a fresh context > prose advice.**
When you find a real bug, ask what CLASS it belongs to and whether the
class can be mechanized — one gate quietly outperforms a hundred future
acts of vigilance.

*Incident:* with conventions wired into a repo's gate (manifest
consistency, sync checks, an unmapped-pin heuristic), baseline agents with
NO skill files matched skill-equipped ones 23/23 on mechanical assertions.
The gate carried the judgment. That result is this rule's proof.
