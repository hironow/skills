"""正解表を作る。64 変種 x 6 性質。

シミュレータが反例を見つけた組は「violated」。見つからなかった組は TLC で全状態を調べ、
通れば「holds」。まとめて調べて反例が出たら、1 つずつ調べ直す。
使い方: python3 -I truth_table.py
"""
import itertools
import pathlib
import re
import subprocess

HERE = pathlib.Path(__file__).parent
GEN = HERE / "gen"
SWITCHES = ["GUARD_ISSUE", "FREEZE_HOLD", "REFUND", "FAIL_RELEASES", "DRAIN_WAITS",
            "RESERVE_CHECKS_TICKET"]
PROPS = ["P1", "P2", "P3", "P4", "P5", "P6"]


def variant_file(bits):
    tag = "".join(map(str, bits))
    args = ", ".join(f"{n} = {'true' if b else 'false'}" for n, b in zip(SWITCHES, bits))
    path = GEN / f"v{tag}.qnt"
    base = (HERE / "ticket_sale.qnt").read_text()
    path.write_text(f"{base}\nmodule v{tag} {{\n  import ticket_sale({args}).*\n}}\n")
    return tag, path


def simulate(tag, path, prop):
    out = subprocess.run(
        ["quint", "run", f"--main=v{tag}", f"--invariant={prop}", "--seed=0x5eed",
         "--max-samples=3000", "--max-steps=16", str(path)],
        capture_output=True, text=True)
    return "[violation]" in out.stdout + out.stderr


def tlc_ok(tag, path, props):
    """TLC で全状態を調べる。props のすべてが成り立てば True。"""
    out = subprocess.run(
        ["quint", "verify", "--backend", "tlc", f"--main=v{tag}", str(path),
         "--invariants", *props], capture_output=True, text=True)
    text = out.stdout + out.stderr
    if out.returncode == 0 and re.search(r"^\[ok\]", text, re.M):
        return True
    if re.search(r"^\[violation\]", text, re.M):
        return False
    raise RuntimeError(f"v{tag}: TLC failed\n{text[-2000:]}")


def main():
    GEN.mkdir(exist_ok=True)
    rows = []
    for bits in itertools.product([0, 1], repeat=len(SWITCHES)):
        tag, path = variant_file(bits)
        verdict = {}
        pending = []
        for p in PROPS:
            if simulate(tag, path, p):
                verdict[p] = ("violated", "simulator")
            else:
                pending.append(p)
        if pending and tlc_ok(tag, path, pending):
            for p in pending:
                verdict[p] = ("holds", "tlc")
        else:
            # どれかが破れている。TLC は名前を言わないので、1 つずつ調べる。
            for p in pending:
                verdict[p] = ("holds", "tlc") if tlc_ok(tag, path, [p]) else ("violated", "tlc")
        for p in PROPS:
            rows.append(f"{tag}\t{p}\t{verdict[p][0]}\t{verdict[p][1]}")
        print(tag, " ".join(f"{p}={verdict[p][0][0]}" for p in PROPS), flush=True)
    (HERE / "truth.tsv").write_text("variant\tproperty\tverdict\tmethod\n" + "\n".join(rows) + "\n")


if __name__ == "__main__":
    main()
