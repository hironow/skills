"""Check a claimed counterexample by replaying it in Quint.

A control (or anyone) claims that after `init` and a list of actions, a property is false.
This script inserts a scripted run into the named module and executes it. The run passes only if
every action is enabled in turn and the property is false in the final state.

usage: python3 replay_trace.py <project-root> --spec Spec/x.qnt --module variant --property P \
           --trace '["reserve(\"c1\")", "tick", "settle(\"c1\")"]'

Exit code 0: the trace is a real counterexample. Exit code 1: it is not (a step was not enabled,
the property still holds at the end, or the trace is empty or malformed).

The run is inserted inside the module itself. Importing a variant module from a new module does
not work when the variant was built with `import base(...).*`: Quint reports QNT404 for its names.

--self-test runs three sanity checks on the given trace, which must be a real counterexample:
the trace itself must pass, the trace without its last step must fail, and the trace with its
first step repeated must fail (the repeated step is not enabled, or the state differs).
"""
import argparse
import json
import pathlib
import re
import sys
import tempfile

from quint_tools import module_span, run_quint

STEP = re.compile(r'^[A-Za-z_]\w*(\((\s*("[^"\\]*"|-?\d+|true|false)\s*(,\s*("[^"\\]*"|-?\d+|true|false)\s*)*)?\))?$')


def replays(project: pathlib.Path, spec: str, module: str, prop: str, trace: list) -> bool:
    if not trace or not all(isinstance(s, str) and STEP.match(s.strip()) for s in trace):
        return False
    source = (project / spec).read_text()
    _, close = module_span(source, module)
    chain = "".join(f"\n      .then({s.strip()})" for s in trace)
    run = f"\n  run replayedTraceTest =\n    init{chain}\n      .expect(not({prop}))\n"
    with tempfile.TemporaryDirectory(dir=project / pathlib.Path(spec).parent) as tmp:
        path = pathlib.Path(tmp) / "replay.qnt"
        path.write_text(source[:close] + run + source[close:])
        code, text = run_quint(project, ["test", "--max-samples=1", f"--main={module}",
                                         "--match=replayedTraceTest", str(path)], 300)
    return code == 0 and "ok replayedTraceTest" in text


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("project")
    parser.add_argument("--spec", required=True)
    parser.add_argument("--module", required=True)
    parser.add_argument("--property", required=True)
    parser.add_argument("--trace", required=True, help="JSON list of action calls")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    project = pathlib.Path(args.project).resolve()
    try:
        trace = json.loads(args.trace)
    except json.JSONDecodeError:
        trace = None
    if not isinstance(trace, list):
        print("replay: the trace is not a JSON list", file=sys.stderr)
        return 1
    check = lambda t: replays(project, args.spec, args.module, args.property, t)
    if args.self_test:
        results = {"the trace is a counterexample": check(trace),
                   "without its last step it is rejected": not check(trace[:-1]),
                   "with its first step repeated it is rejected": not check(trace[:1] + trace)}
        for name, ok in results.items():
            print(("ok  " if ok else "NG  ") + name)
        return 0 if all(results.values()) else 1
    ok = check(trace)
    print("counterexample confirmed" if ok else "not a counterexample")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
