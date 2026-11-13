"""読み手の答えを集計する。使い方: python3 -I score.py"""
import json
import pathlib
import re

HERE = pathlib.Path(__file__).parent
READERS = ["fable", "opus", "sonnet"]
IDS = [f"S{i:02d}" for i in range(1, 15)]


def parse(path):
    blocks = re.findall(r"```json\s*(\{.*?\})\s*```", path.read_text(), re.S)
    return json.loads(blocks[-1])


def main():
    lines = ["artifact\tdetermined\tall_Z\tsplit\t" + "\t".join(IDS)]
    for art in sorted((HERE / "artifacts").glob("*.md")):
        answers = [parse(HERE / "readings" / art.stem / f"{r}.md") for r in READERS]
        cells, det, allz, split = [], 0, 0, 0
        for s in IDS:
            got = [a.get(s, "?") for a in answers]
            if len(set(got)) == 1 and got[0] != "Z":
                det += 1
            elif set(got) == {"Z"}:
                allz += 1
            else:
                split += 1
            cells.append("".join(got))
        lines.append("\t".join([art.stem, str(det), str(allz), str(split)] + cells))
    (HERE / "scores.tsv").write_text("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
