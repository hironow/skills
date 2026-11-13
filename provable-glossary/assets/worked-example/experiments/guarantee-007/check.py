"""座席の保証の条件を、元の格子の外で確かめる。

条件: Q2 (返金された顧客はいない) が成り立つ ⇔ EXT >= LAT + (FREEZE または MAINT == 0 なら 0、そうでなければ MAINT)

前提: Apalache サーバーが localhost:8822 で動いていること。
使い方: python3 -I check.py
"""
import concurrent.futures
import itertools
import pathlib
import re
import subprocess

HERE = pathlib.Path(__file__).parent
GEN = HERE / "gen"
BASE = (HERE.parent / "scale-003" / "timed_sale.qnt").read_text()
NAMES = ["TTL", "EXT", "LAT", "MAINT", "FREEZE", "REACQUIRE"]
# 元の格子は TTL 1〜2, EXT 0〜3, LAT 1〜3, MAINT 0〜2。
WIDE = [[1, 3], [0, 1, 2, 3, 4, 5], [1, 2, 3, 4], [0, 1, 2, 3], [0, 1], [0, 1]]
ORIGINAL = [[1, 2], [0, 1, 2, 3], [1, 2, 3], [0, 1, 2], [0, 1], [0, 1]]
TWO = 'pure val Customers = Set("c1", "c2")'
THREE = 'pure val Customers = Set("c1", "c2", "c3")'


def predicted(v):
    ttl, ext, lat, maint, freeze, _ = v
    return ext >= lat + (0 if (freeze or maint == 0) else maint)


def check(job):
    label, spec, v = job
    tag = label + "".join(map(str, v))
    args = ", ".join(f"{n} = {('true' if x else 'false') if n in ('FREEZE', 'REACQUIRE') else x}"
                     for n, x in zip(NAMES, v))
    path = GEN / f"{tag}.qnt"
    path.write_text(f"{spec}\nmodule {tag} {{\n  import timed_sale({args}).*\n}}\n")
    out = subprocess.run(["quint", "verify", "--backend", "tlc", f"--main={tag}", "--invariant=Q2",
                          str(path)], capture_output=True, text=True, timeout=900)
    text = out.stdout + out.stderr
    states = (re.findall(r"(\d+) distinct states found", text) or [""])[-1]
    if re.search(r"^\[ok\]", text, re.M):
        holds = True
    elif re.search(r"^\[violation\]", text, re.M):
        holds = False
    else:
        raise RuntimeError(f"{tag}: TLC failed\n{text[-1200:]}")
    return label, "".join(map(str, v)), holds, predicted(v), states


def main():
    assert TWO in BASE
    GEN.mkdir(exist_ok=True)
    jobs = [("wide", BASE, v) for v in itertools.product(*WIDE)]
    jobs += [("three", BASE.replace(TWO, THREE), v) for v in itertools.product(*ORIGINAL)]
    rows = ["set\tvariant\tholds\tpredicted\tdistinct_states"]
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
        for i, (label, tag, holds, pred, states) in enumerate(pool.map(check, jobs), 1):
            rows.append(f"{label}\t{tag}\t{int(holds)}\t{int(pred)}\t{states}")
            if i % 200 == 0:
                print(i, "/", len(jobs), flush=True)
    (HERE / "results.tsv").write_text("\n".join(rows) + "\n")
    for label in ("wide", "three"):
        sel = [r.split("\t") for r in rows[1:] if r.startswith(label)]
        agree = sum(r[2] == r[3] for r in sel)
        top = max(int(r[4]) for r in sel if r[4])
        print(f"{label}: 条件と一致 {agree}/{len(sel)}, 最大の状態数 {top}")
    print("done", flush=True)


if __name__ == "__main__":
    main()
