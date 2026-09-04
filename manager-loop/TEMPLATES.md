# Manager Loop templates

Copy, fill the `<...>` slots, keep the wording about "extremely well" and the
stall rule intact. `<skill-dir>` is the directory containing SKILL.md.

## 1. Interview questions (manager -> user)

Ask until each has a concrete answer; stop when you can write the finish line
as one paragraph.

- What does "done" look like? What could I open, run, or watch to know it is done?
- What is explicitly out of scope, even if it seems adjacent?
- What is the scariest or least-known part? We will put it in an early phase.
- What quality bar per phase? (Default: "extremely well", demonstrable, gate green.)
- Which existing repo gates apply (`just check`, tests, lint)? Anything the implementer may not touch?
- Budget: how many hours or phases may this run? Stall threshold (default 30 min)?
- May the manager respawn a dead implementer without asking?

## 2. Seed format (`manager-loop/plan.md`, read once by `init`)

`init --from plan.md` turns this into `dashboard.html`, which is the checklist
from then on. Shape: one `#` title, `## Phase N: title` headers numbered
consecutively from 1 (`init` rejects gaps), `- [ ]` / `- [x]` items. Item ids
become `<phase>.<position>`.

```markdown
# Simulated civilization in Three.js

## Phase 1: World that renders
- [ ] Terrain, water and sky render at 60 fps on the dev machine
- [ ] Camera orbits and zooms with the mouse
- [ ] `just check` green

## Phase 2: Animals with plausible behaviour
- [ ] Ten animals spawn on land, never in water
- [ ] Animals wander, avoid water, and rest
- [ ] Regression test pins the "no animal in water after 60 s" rule

## Phase 3: Verification
- [ ] Every earlier phase's demo still works from a clean checkout
- [ ] README explains how to run it
- [ ] Unchecked items from earlier phases are listed with reasons
```

Guidelines: many small verifiable items beat few big ones; each phase ends in
something demonstrable; put a gate item (`just check` or the repo's own) in
every phase (tick it by id, or by substring while that phase is current); the
last phase is always verification.

## 3. Implementer briefing (manager -> `Agent`, `name: "implementer"`, background)

```
You are the implementer in a Manager Loop. A manager agent will send you one
phase at a time; you finish each phase completely and extremely well, then
report back. You do not stop mid-phase to ask questions.

Project goal (agreed with the user):
<one-paragraph finish line>

Out of scope: <list>

Working files:
- The checklist is the page: <abs path>/manager-loop/dashboard.html. Every
  box, its state and the time you ticked it live there. Never edit it by hand;
  use the script, which also draws the counter and the progress chart.
- Tick a box the moment an item is verifiably done (records the time):
    python3 <skill-dir>/scripts/manager_loop_dashboard.py --dir <abs path>/manager-loop tick <id|substring>
- Only you tick boxes. Sub-agents report to you; you verify, then tick.
- Do not `skip` items yourself; leave them open and explain in the report.
  The manager decides what is accepted.
- Reports go to <abs path>/manager-loop/reports/phase-<N>.md (format below)

Rules:
- Work only on the phase you were given. Ideas outside it go into a
  "Suggested items" section of your report, not into the code.
- "Extremely well" means demonstrable and gate-green, not perfect. Move on
  once an item is good enough.
- Stall rule: if you have not ticked a box in <stall-minutes, same value as
  the page> minutes, stop polishing, leave the item open with a one-line
  reason in the report, and move to the next item. Finishing the phase
  matters more than any single item.
- Decide and record rather than ask. When something is ambiguous, pick the
  option that keeps the finish line reachable, note the assumption in the
  report, and continue.
- Repo conventions still apply: <TDD / just check / commit discipline / never
  weaken gates>. Commit at sensible points with Conventional Commit messages.
- Parallelise: when items in the phase are independent, spawn sub-agents
  (Agent tool) for them and integrate their results. Prefer several small
  focused sub-agents over one large one.

Report format (write the file, then end your turn with a 5-line summary):
# Phase <N>: <title>
## Done
- <item id> <item> - evidence: <command + key output, file, screenshot path>
## Not done
- <item id> <item> - reason, what was tried, what would unblock it
## Assumptions made
## Suggested items for later phases
## Gate
<exact command run and result>

Wait for the manager's first phase message before starting.
```

## 4. Phase kick-off (manager -> implementer via `SendMessage`)

```
Complete Phase <N> completely, extremely well.

Phase <N>: <title>
<paste the phase's checklist items>

Finish line: <one sentence a stranger could verify>.
Tick each box as you verify it. Stall rule: <stall-minutes> minutes without a
tick means move on and note why. Do not stop until every item is ticked or
noted, then write reports/phase-<N>.md and end your turn.
```

## 5. Stall nudge (manager -> implementer)

```
No box has been ticked for <M> minutes. Stop polishing the current item, leave
it open with a one-line reason, and move to the next open item in Phase <N>.
The finish line is unchanged: <finish line>.
```

## 6. Supervision prompt (for the `loop` skill, ~15 min cadence)

```
Manager Loop supervision tick. Run
  python3 <skill-dir>/scripts/manager_loop_dashboard.py --dir <abs path>/manager-loop status
(the stall threshold is stored in the page). If `stalled` is true and the
implementer is still running, send the stall nudge (TEMPLATES.md section 5)
via SendMessage to "implementer". If ListAgents shows no implementer and
`all_done` is false, respawn one with the handoff briefing (section 7). If
`all_done` is true, stop the loop and report to the user. Otherwise do
nothing and say "no change".
```

## 7. Handoff briefing (respawning a lost implementer)

Use the briefing in section 3 with this paragraph prepended:

```
You are replacing a previous implementer that stopped. Before doing anything,
run the dashboard script's `status`, read <abs path>/manager-loop/log.md and
the newest file in reports/. Treat ticked and skipped boxes as settled.
Continue from the first open item of Phase <N>; do not redo finished work.
Wait for the manager's phase message.
```

## 8. Manager log entry (`manager-loop/log.md`)

Append one block per decision so a compacted manager can rebuild its state.

```
## <ISO timestamp> Phase <N> <started|accepted|re-run|skipped>
- Budget: <hours or phases remaining>
- Evidence checked: <what you ran or opened>
- Open items settled by `skip`: <ids and one-line reasons>
- Open items carried forward: <ids and target phase>
- Decision: <next phase / narrowed re-run items / stop>
```

## 9. `/goal` line for the manager session (user types it; you cannot)

Print this filled in, then end your turn. The evaluator only sees the
conversation, so the condition names things you will surface in it: the
`status` JSON and the outcome file.

```
/goal Manager Loop for "<goal title>" is finished: running
`python3 <skill-dir>/scripts/manager_loop_dashboard.py --dir <abs path>/manager-loop status`
prints all_done true, every skipped item has a reason recorded in log.md, and
<abs path>/manager-loop/OUTCOME.md summarises what shipped, what was skipped
and where the evidence lives. Or stop after <N> hours / <M> phases and report.
```

Keep the condition under 4,000 characters. The time or phase clause is the
budget from step 0; without it the run has no ceiling.
