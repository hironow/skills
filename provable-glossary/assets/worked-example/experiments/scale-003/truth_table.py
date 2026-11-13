"""正解表を作る。288 変種 x 4 性質を、すべて TLC で全状態検査する。

前提: Apalache サーバーが localhost:8822 で動いていること (並列実行のため)。
  ~/.quint/apalache-dist-0.62.1/apalache/bin/apalache-mc server --port=8822
使い方: python3 -I truth_table.py
"""
import concurrent.futures
import itertools
import pathlib
import re
import subprocess

HERE = pathlib.Path(__file__).parent
GEN = HERE / "gen"
GRID = {
    "TTL": [1, 2], "EXT": [0, 1, 2, 3], "LAT": [1, 2, 3], "MAINT": [0, 1, 2],
    "FREEZE": [0, 1], "REACQUIRE": [0, 1],
}
BOOLS = {"FREEZE", "REACQUIRE"}
PROPS = ["Q1", "Q2", "Q3", "Q4"]


def args_of(values):
    return ", ".join(
        f"{n} = {('true' if v else 'false') if n in BOOLS else v}" for n, v in zip(GRID, values))


def variant_file(values):
    tag = "".join(map(str, values))
    path = GEN / f"v{tag}.qnt"
    base = (HERE / "timed_sale.qnt").read_text()
    path.write_text(f"{base}\nmodule v{tag} {{\n  import timed_sale({args_of(values)}).*\n}}\n")
    return tag, path


def check(job):
    tag, path, prop = job
    out = subprocess.run(
        ["quint", "verify", "--backend", "tlc", f"--main=v{tag}", f"--invariant={prop}",
         str(path)], capture_output=True, text=True, timeout=600)
    text = out.stdout + out.stderr
    states = re.findall(r"(\d+) distinct states found", text)
    states = states[-1] if states else ""
    if out.returncode == 0 and re.search(r"^\[ok\]", text, re.M):
        return tag, prop, "holds", "", states
    if re.search(r"^\[violation\]", text, re.M):
        # 反例の長さ: 初期状態を除いた操作の数
        steps = len(re.findall(r"^State \d+:", text, re.M)) - 1
        return tag, prop, "violated", str(steps), states
    raise RuntimeError(f"v{tag} {prop}: TLC failed\n{text[-1500:]}")


def main():
    GEN.mkdir(exist_ok=True)
    jobs = []
    for values in itertools.product(*GRID.values()):
        tag, path = variant_file(values)
        jobs += [(tag, path, p) for p in PROPS]
    rows = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
        for i, row in enumerate(pool.map(check, jobs), 1):
            rows.append("\t".join(row))
            if i % 100 == 0:
                print(i, "/", len(jobs), flush=True)
    header = "variant\tproperty\tverdict\tcounterexample_steps\tdistinct_states\n"
    (HERE / "truth.tsv").write_text(header + "\n".join(rows) + "\n")
    print("done", flush=True)


if __name__ == "__main__":
    main()
