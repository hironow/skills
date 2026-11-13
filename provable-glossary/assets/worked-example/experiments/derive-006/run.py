"""条件の式を書かせる。使い方: python3 -I run.py <作業用の空ディレクトリ>"""
import concurrent.futures
import pathlib
import subprocess
import sys

HERE = pathlib.Path(__file__).parent
SPEC = (HERE.parent / "scale-003" / "timed_sale.qnt").read_text()
MODELS = {"fable": "claude-fable-5-2", "opus": "claude-opus-5-5", "sonnet": "claude-sonnet-5-5"}
PROMPT = """次の Quint の仕様は、映画館のチケット販売の、時間つきの状態遷移モデルです。
道具は使わず、読んで考えるだけで答えてください。コードの実行やモデル検査はできません。

```quint
{spec}
```

パラメータは、TTL と LAT が 1 以上の整数、EXT と MAINT が 0 以上の整数、FREEZE と REACQUIRE が真偽値です。

問い: `init` から `step` を繰り返して到達できるすべての状態で不変条件 `{prop}` が成り立つための、
パラメータについての必要十分条件を求めてください。

考えた後、最後に次の形の JSON を 1 つだけ、```json のコードブロックで出力してください。
condition は Python の真偽式です。使える名前は TTL, EXT, LAT, MAINT, FREEZE, REACQUIRE だけです。
使える演算は、比較、+, -, *, and, or, not, 括弧、整数の定数、True, False です。

```json
{{"condition": "TTL >= 1 and (FREEZE or MAINT == 0)"}}
```
"""


def ask(job):
    name, model, prop, run, workdir = job
    out = HERE / "answers" / f"{name}-{prop}-{run}.md"
    if out.exists() and out.stat().st_size > 0:
        return f"{out.name} cached"
    res = subprocess.run(
        ["claude", "-p", "--model", model, "--effort", "high", "--tools", "",
         "--strict-mcp-config", "--setting-sources", ""],
        input=PROMPT.format(spec=SPEC, prop=prop), capture_output=True, text=True,
        cwd=workdir, timeout=1500)
    out.parent.mkdir(exist_ok=True)
    out.write_text(res.stdout)
    return f"{out.name} exit={res.returncode} bytes={len(res.stdout)}"


def main():
    jobs = [(n, m, p, r, sys.argv[1]) for n, m in MODELS.items() for p in ("Q2", "Q4") for r in (1, 2)]
    with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:
        for line in pool.map(ask, jobs):
            print(line, flush=True)


if __name__ == "__main__":
    main()
