---
name: manager-loop
description: Run very long-horizon, multi-hour autonomous builds in Claude Code by splitting roles - a manager session that interviews the user, writes a phased checklist and steers, and a separate implementer agent that finishes one phase at a time "extremely well" while ticking a progress dashboard. Use whenever the user asks for an ambitious end-to-end build, a large migration or rewrite, a "build the whole thing" request, or anything a human team would need days for; also when the user says "manager loop", "run this to completion", "keep going until it's done", "long-running", "autonomous build", or complains that a long agent run stalled in minutiae, plateaued, or asymptoted. Not for ordinary single-task coding.
license: MIT
metadata:
  provenance: original
  inspired-by: "https://x.com/mattshumer_/status/2095723177389232540; https://somethingbig.ai/astra-review"
---

# Manager Loop

Two agents, two jobs. A **manager** keeps the project moving through a phased
plan. A separate **implementer** does the work, one phase at a time. The manager
automates the steering a human would otherwise do by hand.

## Why this works

Over a long horizon a single agent asymptotes: it gets far, then progress
against the goal slows while it polishes small details. Forcing the work into
closed phases, each with a concrete finish line, resets that curve every
phase. The manager never touches implementation, so its context stays lean
enough to keep judging progress after hours of work. The dashboard makes
"I have not made progress in a while" visible to the implementer itself.

## Roles in Claude Code

```
+---------------------+   Agent(name=implementer, background)   +---------------------+
|  MANAGER            | --------------------------------------> |  IMPLEMENTER        |
|  (this session)     |   SendMessage: "Phase N, extremely well" |  (separate agent,   |
|  interview -> plan  | <-------------------------------------- |   own context)      |
|  phases -> steer    |   completion notification + report      |  ticks checklist    |
|  never implements   |                                         |  may spawn Agents   |
+---------------------+                                         +----------+----------+
          |                                                                |
          |  /goal check-in or loop skill: status (stall?)                 v
          +------------------------->  manager-loop/  <------------  sub-agents
                                        dashboard.html  (the checklist,
                                        log.md           ticks + times + chart)
```

| Concept | Claude Code primitive |
| --- | --- |
| Manager | The foreground session that loaded this skill |
| Implementer | `Agent` (general-purpose) with `name: "implementer"`, run in the background. Its tool output never enters the manager's context |
| Manager -> implementer message | `SendMessage({to: "implementer", ...})`. Continues the same agent with its context intact |
| Implementer -> manager | The task-completion notification plus the report the implementer writes to disk |
| Goal mode (manager) | `/goal <run-level condition>` typed by the user on the manager session. Only a human (or `claude -p "/goal ..."`) can set it; a skill or the model cannot. While the implementer runs in the background the evaluator waits and delivers a check-in every 30 min (`CLAUDE_CODE_GOAL_CHECKIN_MINUTES`), which doubles as stall supervision |
| Goal mode (implementer) | Cannot be set on an `Agent` subagent. The phase kick-off message carries it instead: explicit finish line, "do not stop until", stall rule (TEMPLATES.md). Variant: run the implementer as a separate `claude -p "/goal <phase condition>"` process and coordinate through the page and reports, giving up `SendMessage` |
| Sub-agents | The implementer's own `Agent` calls. Tell it explicitly to parallelise independent items; raising a limit alone does not make it fan out |
| Supervision | Completion notifications for phase ends; `/goal` check-ins (30 min, backing off) between them; the `loop` skill when a tighter or fixed cadence is needed |
| Shared state | `manager-loop/dashboard.html`. The page is the checklist: every box, its state and the time it was ticked live in that one file, so compaction of either agent loses nothing |

Prerequisites: this session must expose `Agent` (with `name`), `SendMessage`
and `ListAgents`. Check the tool list before promising the user an autonomous
run; without messaging, fall back to one fresh implementer per phase.

## Workflow

### 0. Budget and stop conditions

Long runs consume an enormous number of tokens. Before anything else, agree
with the user on: how many hours or phases the run may take, the stall
threshold (default 30 minutes without a tick), and whether the manager may
respawn a dead implementer without asking. Write these into `log.md`.

### 1. Interview until the goal is agreed

Interview the user about the goal until you can state, in one paragraph, what
"done" looks like and what is explicitly out of scope. Push on unknowns and
the scariest part first. `grilling:grit-grill` is a good fit for this step
when available. Do not start writing the checklist before this converges;
a vague finish line is the main cause of asymptoting runs.

### 2. Build the massive checklist, then phase it, then seed the page

Draft `manager-loop/plan.md` in the seed format (see TEMPLATES.md). Aim for
many small, verifiable items, then group them into phases. Each phase should
be a coherent deliverable that can be demonstrated on its own, ordered so that
earlier phases de-risk later ones. Include a final verification phase. Show it
to the user and get a nod. Then turn it into the page, once:

```sh
python3 <skill-dir>/scripts/manager_loop_dashboard.py init --from manager-loop/plan.md --stall-minutes 30
open manager-loop/dashboard.html          # auto-refreshes every 60 s
```

From here on `dashboard.html` is the checklist. `plan.md` is a draft you no
longer read; do not edit it to change scope, add items on the page instead
(or reseed with `--force` before the implementer starts). The stall threshold
is stored in the page so implementer and supervisor use the same number.

### 3. Spawn the implementer, then hand the user the `/goal` line

Spawn one `Agent` with `name: "implementer"`, background, using the
implementer briefing in TEMPLATES.md. The briefing gives it the page path,
the tick command, the stall rule, the report format, and the standing
instruction to make assumptions and record them rather than ask. Repo
conventions (tests, gates, commit discipline) still apply to the implementer;
say so in the briefing.

Then print the exact `/goal` line for the user to type (TEMPLATES.md section
9) and stop your turn. You cannot set the goal yourself; the user types it
once and from then on the session keeps cycling turns until the condition is
met, judged impossible, or cleared. Auto mode is what removes per-tool
prompts; `/goal` is what removes per-turn prompts. Both are needed for a
hands-off run.

### 4. Run the phase loop

For each phase:

1. `SendMessage` the phase kick-off: "Complete Phase N completely, extremely
   well." with the phase's items pasted in and the finish line restated.
2. Wait for the completion notification. Do not poll the implementer; the
   notification arrives on its own.
3. Read `manager-loop/reports/phase-N.md`, not the implementer's raw output.
   Spot-check the evidence: run the cheap gate yourself (`just check`, the
   test suite, opening the page). If an item was left open with a reason,
   decide: accept it (then `skip` it with the reason so the phase closes and
   supervision stops nudging), fold it into a later phase, or send a narrowed
   re-run.
4. Record the decision in `log.md` and start the next phase.

Keep phases closed. New ideas go into a later phase or a new item, never into
the running phase; scope creep inside a phase is how the asymptote returns.

### 5. Supervise for stalls between notifications

With `/goal` active, Claude Code delivers a check-in while the implementer is
still running: first after 30 minutes, then 1 h, then every 2 h. Treat every
check-in as a supervision tick and run:

```sh
python3 <skill-dir>/scripts/manager_loop_dashboard.py status     # threshold comes from the page
```

If `stalled` is true, send the stall nudge: move on, leave the item open with
a one-line note, keep the phase's finish line. If `ListAgents` shows no
implementer, respawn one with the handoff briefing; it reads the page,
`log.md`, and the last report to pick up where the previous one stopped.

The check-in cadence backs off, and idle check-ins pause after three until the
user sends a prompt. When the stall threshold is tighter than that, or the run
is unattended for many hours, add the `loop` skill with the supervision prompt
from TEMPLATES.md at a fixed interval (about 15 minutes).

### 6. Finish

After the verification phase, write `manager-loop/OUTCOME.md` and surface it
in the conversation: what shipped, what was skipped and why, and where the
evidence lives. Run `status` one last time so the evaluator sees `all_done`
and the goal clears. `grilling:handover` is a good closing step when the
project continues later.

## Wording that matters

- Ask for each phase to be done **"extremely well"**, not "perfectly".
  "Perfect" sends the model back into the minutiae; "extremely well" implies
  it may move on once the result is good enough.
- Put the stall rule in the implementer's own prompt: "if you have not ticked
  a box in <stall-minutes> minutes, move on and note why". Being told this
  beats being nudged. Use the same number you passed to `init`.
- Tell the implementer to **decide and record** rather than ask. Every
  question back to the manager is a stall; the manager cannot answer faster
  than a well-documented assumption.
- Always give a **finish line**, not a direction. "Phase 2 done means the two
  people talk to each other audibly" beats "work on the people".

## Manager rules of thumb

- Never do implementer work yourself, even a small fix. Your value is a
  clean context that can still judge progress at hour six.
- Read reports and status JSON, not transcripts. If you need detail, ask the
  implementer for a paragraph.
- Everything that matters is on disk: `dashboard.html` (state and timeline),
  `log.md` (your decisions), `reports/` (evidence). After a compaction, run
  `status` and re-read `log.md` before acting.
- Only the implementer ticks boxes; sub-agents report back to it. One writer
  keeps the page coherent (the script also takes a lock, but do not rely on it
  to arbitrate scope).
- Open items and skipped items are different things. Open means work remains;
  skipped means the manager accepted the omission. Leaving accepted omissions
  open is how a finished run keeps looking stalled.
- The boxes are not equal and that is fine. The chart exists to make a flat
  line visible, not to measure value.

## Dashboard commands

```sh
S=<skill-dir>/scripts/manager_loop_dashboard.py       # --dir defaults to ./manager-loop
python3 $S init --from manager-loop/plan.md --stall-minutes 30   # once; --force to reseed
python3 $S tick 2.3                                   # mark done, time recorded in the page
python3 $S tick "voices play"                         # substring; current phase wins on ties
python3 $S skip 2.4 --note "needs a GPU we lack"      # settle without doing; reason shown on page
python3 $S status                                     # JSON: done/skipped/total, current_phase, stalled
python3 $S render                                     # re-render the page from its own data
```

Each item is an `<li data-id data-state data-at data-note>` in the page; the
counter, per-phase bars and the inline SVG chart are drawn from those
attributes. Single file, no network, 60 s auto-refresh. Substring matching is
case-insensitive and prefers the current phase, so a gate item repeated in
every phase resolves to the right one.

## Failure modes

| Symptom | Response |
| --- | --- |
| Implementer returns early asking a question | Answer with a decision in one message, restate the finish line, resend the phase |
| Ticks stop but the agent is busy | Stall nudge: move on, note the blocker, finish the phase |
| Phase report claims done but the gate fails | Send a narrowed re-run listing only the failing items; do not fix it yourself |
| Implementer keeps expanding scope | Remind it phases are closed; add its ideas as items in a later phase |
| Phase accepted but `status` still reports it incomplete | `skip` the accepted-open items with the reason; open items keep the phase (and the stall clock) alive |
| `ListAgents` shows no implementer | Respawn with the handoff briefing; the page carries the state |
| Session prints `Goal cleared after an unrecoverable error` | Fix the named cause (auth, credits, context overflow, model), then ask the user to type the `/goal` line again; the page and `log.md` are intact |
| Evaluator stops the loop for "no progress" | You answered several turns without tool use. Run `status`, act on it (nudge, respawn, next phase), and the goal resumes on the next prompt |
| Manager context was compacted | Run `status`, re-read `log.md` and the latest report, then continue the loop |

## Files

- `TEMPLATES.md` - interview questions, seed format, implementer briefing,
  phase kick-off, stall nudge, supervision prompt, handoff, log entry, and the
  `/goal` line for the manager session.
- `scripts/manager_loop_dashboard.py` - the page as checklist: seed, tick,
  skip, status, render. Stdlib only.
  Tests: `python3 -m unittest discover -s scripts -p 'test_*.py'`.
