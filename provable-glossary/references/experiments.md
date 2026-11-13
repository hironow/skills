# Comparing with a control

Find out what the formal work added by giving the same material to tool-less models (the control). The example's records are in `assets/worked-example/experiments/`. Copy the scripts as a starting point and adapt them to the domain.

## Why

In the cinema example the control scored full marks or close to it in all six comparisons. Run the comparison anyway, for two reasons.

- "The formal model found X" is unsupported until compared. Comparisons made the example retract a claim.
- A different domain or a larger model may give a different result. If it does, that is the finding.

## Scripts that come with the skill

Use these instead of writing your own. They read the project's pinned Quint version and work for any model.

| Script | What it does |
|---|---|
| `scripts/truth_table.py` | For each module and property, asks TLC whether it holds. Writes a TSV. Retries when Apalache's port is busy |
| `scripts/replay_trace.py` | Replays a claimed counterexample inside the named module. Exit 0 only if every step is enabled and the property is false at the end. `--self-test` checks the scorer on a known counterexample |
| `scripts/run_control.py` | Asks one tool-less model one question in an empty directory and saves the answer |

What stays specific to an experiment, and is yours to write: the prompt, the sampling of items, and the loop that calls these scripts and tallies the results. Keep that loop short.

## Rules for every experiment

1. **Write first, commit, then run.** `experiments/<name>/protocol.md` states the question, the method, the scoring, your prediction, the decision rule, and the known limits.
2. **Isolate the control.** `scripts/run_control.py` runs it in an empty directory with no tools:

```sh
claude -p --model <model> --effort high --tools "" --strict-mcp-config --setting-sources ""
```

   The question goes in on standard input. Use several models (strongest to weakest). `claude --help` lists the flags if a version differs.
3. **Score by machine.** Ask for a final JSON block. For a "violated" answer, replay the trace with `scripts/replay_trace.py`; the property must be false in the last state. The run has to be inserted inside the variant module, which the script does; importing the variant from a new module fails with QNT404.
4. **Test the scorer.** Run `replay_trace.py --self-test` on one known counterexample: the trace must pass, the trace without its last step must fail, and a trace with a step that is not enabled must fail. Also confirm that a trace aimed at a module where the property holds is rejected.
5. **Record changes made before the run** (a model bug fixed, a property dropped). After the control has run, do not change the models, the items, or the scoring. Replaying a trace is not a change: `replay_trace.py` works on a temporary copy and leaves the spec untouched.
6. **`result.md`** gives the conclusion, the numbers, predictions against outcomes, what can be said, and what cannot.

## When the control gets everything right

Expect this; it happened in every comparison so far. It is a result, not a failed experiment. Write it down as it is, withdraw any claim that the formal work "found" something, and describe the formal contribution as assurance. If time allows, run one harder round (items near a boundary, a larger model) and report that too. Do not keep making items harder until the control fails; the documents should describe the system, not the search for a weakness.

## Kinds of experiment

| Kind | Question | Example | Use it when |
|---|---|---|---|
| Discovery | From the business description and the draft alone, does the control list the same gaps? | `control-001` | You want to claim a discovery |
| Verification | Can the control tell, by reading, whether a variant satisfies a property? | `verify-002`, `scale-003` | First choice |
| Notation | Does accuracy change when the same content is given in natural language? | `formal-004` | You want to claim value for the formal notation |
| Forward | From a rough brief, does writing a spec leave fewer decisions open than writing a design document? | `forward-005` | You want to claim that formalizing forces decisions |
| Derivation | Can the control write the closed-form condition itself? | `derive-006` | Before writing that the model "produced" a condition |

### Building a verification experiment

1. Give the model switches or parameters and generate a few hundred variants.
2. Tabulate variant × property with TLC alone (`scripts/truth_table.py`). The simulator can miss counterexamples.
3. Draw the items at random with a fixed seed (`sample.py`). Balance holds and violated. Separating items near a boundary (one step of one parameter flips the result) from far ones shows where errors cluster.
4. Run the control (`scripts/run_control.py`) and score by machine (`scripts/replay_trace.py` for every "violated" answer).

### Tool notes

- To run TLC in parallel, start an Apalache server first; without it parallel runs fail silently. Stop it when done.

```sh
~/.quint/apalache-dist-*/apalache/bin/apalache-mc server --port=8822
```

- Generate one file per variant under `gen/` and add `gen/` to `.gitignore`.
- Give every check a timeout. A check that never ends means an infinite state space.
- Keep the control's answers under `answers/` and commit them. Never rewrite them.
- A counterexample length reported by multi-threaded TLC is an upper bound, not the minimum.
