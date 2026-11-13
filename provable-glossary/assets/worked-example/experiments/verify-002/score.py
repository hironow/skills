"""対照の答えを機械で採点する。使い方: python3 -I score.py"""
import json
import pathlib
import re
import subprocess

HERE = pathlib.Path(__file__).parent
GEN = HERE / "gen"
MODELS = ["fable", "opus", "sonnet"]
SWITCHES = ["GUARD_ISSUE", "FREEZE_HOLD", "REFUND", "FAIL_RELEASES", "DRAIN_WAITS",
            "RESERVE_CHECKS_TICKET"]
STEP = re.compile(
    r'^(?:(?:reserve|startPayment|paymentSucceeds|paymentFails|issueTicket|holdExpires|refund)'
    r'\("c[12]"\)|startPlannedMaintenance|completeDrain|vulnerabilityDetected|applyCutoff|recover)$')


def parse(text):
    blocks = re.findall(r"```json\s*(\{.*?\})\s*```", text, re.S)
    if not blocks:
        return None
    try:
        return json.loads(blocks[-1])
    except json.JSONDecodeError:
        return None


def trace_breaks(variant, prop, trace, tag):
    """操作の列を実行し、最後の状態で性質が偽なら True。"""
    if not trace or not all(isinstance(s, str) and STEP.match(s.strip()) for s in trace):
        return False
    args = ", ".join(f"{n} = {'true' if b == '1' else 'false'}" for n, b in zip(SWITCHES, variant))
    chain = "".join(f"\n      .then({s.strip()})" for s in trace)
    body = (HERE / "ticket_sale.qnt").read_text()
    path = GEN / f"check_{tag}.qnt"
    path.write_text(
        f"{body}\nmodule check {{\n  import ticket_sale({args}).*\n"
        f"  run replayTest =\n    init{chain}\n      .expect(not({prop}))\n}}\n")
    res = subprocess.run(["quint", "test", "--main=check", "--max-samples=1", str(path)],
                         capture_output=True, text=True)
    return res.returncode == 0 and "ok replayTest" in res.stdout


def main():
    GEN.mkdir(exist_ok=True)
    items = [l.split("\t") for l in (HERE / "items.tsv").read_text().splitlines()[1:]]
    lines = ["item\tvariant\tproperty\ttruth\t" + "\t".join(MODELS)]
    totals = {m: 0 for m in MODELS}
    for item, variant, prop, truth in items:
        cells = []
        for m in MODELS:
            path = HERE / "answers" / m / f"{item}.md"
            ans = parse(path.read_text()) if path.exists() else None
            if ans is None:
                cells.append("no-answer")
                continue
            verdict = ans.get("verdict")
            if truth == "holds":
                ok = verdict == "holds"
                cells.append("correct" if ok else "false-alarm")
            elif verdict != "violated":
                ok = False
                cells.append("missed")
            else:
                ok = trace_breaks(variant, prop, ans.get("trace"), f"{m}_{item}")
                cells.append("correct" if ok else "bad-trace")
            totals[m] += ok
        lines.append("\t".join([item, variant, prop, truth] + cells))
    lines.append("total\t\t\t\t" + "\t".join(f"{totals[m]}/{len(items)}" for m in MODELS))
    (HERE / "scores.tsv").write_text("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
