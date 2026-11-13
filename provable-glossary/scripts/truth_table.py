"""Build the truth table of an experiment: for each module and each property, does it hold?

Every cell is decided by TLC exploring all reachable states (`quint verify --backend tlc`), never
by the simulator, which can miss counterexamples. Cells run one after another; a run that hits
Apalache's busy port is retried.

usage: python3 truth_table.py <project-root> --spec Spec/x.qnt --modules a,b,c --properties P,Q --out truth.tsv

Output columns: module, property, verdict (holds | violated), distinct_states.
Rows are written as they are decided. Run the same command again to continue after an interruption.
A cell that gives no verdict in three attempts (a type error, a timeout) stops the script with the log.
"""
import argparse
import pathlib
import re
import sys

from quint_tools import run_quint


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("project")
    parser.add_argument("--spec", required=True)
    parser.add_argument("--modules", required=True, help="comma-separated module names")
    parser.add_argument("--properties", required=True, help="comma-separated invariant names")
    parser.add_argument("--out", required=True)
    parser.add_argument("--timeout", type=int, default=900, help="seconds per cell; a check that never ends means an infinite state space")
    args = parser.parse_args()
    project = pathlib.Path(args.project).resolve()
    out = pathlib.Path(args.out)
    header = "module\tproperty\tverdict\tdistinct_states"
    done = {}
    if out.exists():  # resume: keep the cells already decided
        for line in out.read_text().splitlines()[1:]:
            cells = line.split("\t")
            if len(cells) == 4:
                done[(cells[0], cells[1])] = line
    out.write_text("\n".join([header, *done.values()]) + "\n")
    for module in args.modules.split(","):
        for prop in args.properties.split(","):
            if (module, prop) in done:
                continue
            verdict, text = None, ""
            for attempt in range(3):  # a run can fail for a passing reason; ask again before giving up
                code, text = run_quint(project, ["verify", "--backend", "tlc", f"--main={module}",
                                                 f"--invariant={prop}", args.spec], args.timeout)
                if code == 0 and re.search(r"^\[ok\]", text, re.M):
                    verdict = "holds"
                elif re.search(r"^\[violation\]", text, re.M):
                    verdict = "violated"
                if verdict:
                    break
            if verdict is None:
                print(f"{module}.{prop}: TLC gave no verdict in three attempts. The cells decided so far are "
                      f"in {out}; run the same command again to continue.\n{text[-1500:]}", file=sys.stderr)
                return 1
            states = (re.findall(r"(\d+) distinct states found", text) or [""])[-1]
            row = f"{module}\t{prop}\t{verdict}\t{states}"
            with out.open("a") as handle:  # written as it goes, so an interruption loses nothing
                handle.write(row + "\n")
            print(row, flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
