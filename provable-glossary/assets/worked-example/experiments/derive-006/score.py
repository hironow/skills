"""式を 288 通りに当てはめ、正解表と比べる。使い方: python3 -I score.py"""
import ast
import csv
import json
import pathlib
import re

HERE = pathlib.Path(__file__).parent
NAMES = ["TTL", "EXT", "LAT", "MAINT", "FREEZE", "REACQUIRE"]
ALLOWED = (ast.Expression, ast.BoolOp, ast.And, ast.Or, ast.UnaryOp, ast.Not, ast.USub, ast.Compare,
           ast.Eq, ast.NotEq, ast.Lt, ast.LtE, ast.Gt, ast.GtE, ast.BinOp, ast.Add, ast.Sub, ast.Mult,
           ast.Name, ast.Load, ast.Constant, ast.IfExp)


def compile_condition(text):
    """許した構文だけでできた式なら、コードにして返す。"""
    tree = ast.parse(text, mode="eval")
    for node in ast.walk(tree):
        if not isinstance(node, ALLOWED):
            raise ValueError(f"許していない構文: {type(node).__name__}")
        if isinstance(node, ast.Name) and node.id not in NAMES:
            raise ValueError(f"許していない名前: {node.id}")
        if isinstance(node, ast.Constant) and not isinstance(node.value, (int, bool)):
            raise ValueError("許していない定数")
    return compile(tree, "<condition>", "eval")


def main():
    truth = {(r["variant"], r["property"]): r["verdict"] == "holds"
             for r in csv.DictReader(open(HERE.parent / "scale-003" / "truth.tsv"), delimiter="\t")}
    variants = sorted({v for v, _ in truth})
    lines = ["answer\tproperty\tmatches\tcondition"]
    for path in sorted((HERE / "answers").glob("*.md")):
        prop = path.stem.split("-")[1]
        blocks = re.findall(r"```json\s*(\{.*?\})\s*```", path.read_text(), re.S)
        try:
            cond = json.loads(blocks[-1])["condition"]
            code = compile_condition(cond)
            hits = 0
            for v in variants:
                env = {n: (bool(int(d)) if n in ("FREEZE", "REACQUIRE") else int(d))
                       for n, d in zip(NAMES, v)}
                hits += bool(eval(code, {"__builtins__": {}}, env)) == truth[v, prop]
            lines.append(f"{path.stem}\t{prop}\t{hits}/{len(variants)}\t{cond}")
        except Exception as err:  # 答えの形が崩れている場合は、そのまま記録する
            lines.append(f"{path.stem}\t{prop}\tunscorable\t{err}")
    (HERE / "scores.tsv").write_text("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
