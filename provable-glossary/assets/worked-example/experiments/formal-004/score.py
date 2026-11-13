"""対照の答えを機械で採点する。採点器は 003 のものを使う。使い方: python3 -I score.py"""
import pathlib
import sys

HERE = pathlib.Path(__file__).parent
SCALE = HERE.parent / "scale-003"
sys.path.insert(0, str(SCALE))
import score as scale  # noqa: E402

ARMS = ["precise", "design"]


def main():
    scale.GEN.mkdir(exist_ok=True)
    items = [l.split("\t") for l in (SCALE / "items.tsv").read_text().splitlines()[1:]]
    cols = [(a, m) for a in ARMS for m in scale.MODELS]
    lines = ["item\tvariant\tproperty\ttruth\tboundary\t" + "\t".join(f"{a}/{m}" for a, m in cols)]
    totals = {c: 0 for c in cols}
    for item, variant, prop, truth, boundary, *_ in items:
        cells = []
        for a, m in cols:
            path = HERE / "answers" / a / m / f"{item}.md"
            ans = scale.parse(path.read_text()) if path.exists() else None
            if ans is None:
                cell = "no-answer"
            elif truth == "holds":
                cell = "correct" if ans.get("verdict") == "holds" else "false-alarm"
            elif ans.get("verdict") != "violated":
                cell = "missed"
            elif scale.trace_breaks(variant, prop, ans.get("trace"), f"{a}_{m}_{item}"):
                cell = "correct"
            else:
                cell = "bad-trace"
            totals[a, m] += cell == "correct"
            cells.append(cell)
        lines.append("\t".join([item, variant, prop, truth, boundary] + cells))
    lines.append("total\t\t\t\t\t" + "\t".join(f"{totals[c]}/{len(items)}" for c in cols))
    (HERE / "scores.tsv").write_text("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
