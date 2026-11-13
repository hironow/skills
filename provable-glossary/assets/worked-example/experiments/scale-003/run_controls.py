"""対照を実行する。各問を、道具なしのモデルに 1 回ずつ解かせる。

使い方: python3 -I run_controls.py <作業用の空ディレクトリ>
"""
import concurrent.futures
import pathlib
import subprocess
import sys

HERE = pathlib.Path(__file__).parent
MODELS = {"fable": "claude-fable-5-2", "opus": "claude-opus-5-5", "sonnet": "claude-sonnet-5-5"}
PARAMS = ["TTL", "EXT", "LAT", "MAINT", "FREEZE", "REACQUIRE"]
BOOLS = {"FREEZE", "REACQUIRE"}

PROMPT = """次の Quint の仕様は、映画館のチケット販売の、時間つきの状態遷移モデルです。
道具は使わず、読んで考えるだけで答えてください。コードの実行やモデル検査はできません。

```quint
{spec}
```

パラメータの値:
{switches}

問い: `init` から `step` を繰り返して到達できるすべての状態で、不変条件 `{prop}` は成り立ちますか。

答え方:
- 成り立つなら verdict を "holds" にします。
- 破れるなら verdict を "violated" にして、`init` の後に実行する操作の列を trace に書きます。
  列の最後の操作の直後の状態で `{prop}` が偽になるようにします。各操作はその時点で実行可能でなければなりません。
- 操作の書き方: `reserve("c1")`, `startPayment("c2")`, `providerSucceeds("c1")`, `providerFails("c1")`,
  `settle("c1")`, `detectVulnerability`, `recover`, `tick`。

考えた後、最後に次の形の JSON を 1 つだけ、```json のコードブロックで出力してください。

```json
{{"verdict": "holds", "trace": []}}
```
"""


def ask(job):
    name, model, item, variant, prop, workdir = job
    out = HERE / "answers" / name / f"{item}.md"
    if out.exists() and out.stat().st_size > 0:
        return f"{name} {item} cached"
    switches = "\n".join(
        f"- {n} = {('true' if b == '1' else 'false') if n in BOOLS else b}"
        for n, b in zip(PARAMS, variant))
    prompt = PROMPT.format(spec=(HERE / "timed_sale.qnt").read_text(), switches=switches, prop=prop)
    res = subprocess.run(
        ["claude", "-p", "--model", model, "--effort", "high", "--tools", "",
         "--strict-mcp-config", "--setting-sources", ""],
        input=prompt, capture_output=True, text=True, cwd=workdir, timeout=1500)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(res.stdout)
    return f"{name} {item} exit={res.returncode} bytes={len(res.stdout)}"


def main():
    workdir = sys.argv[1]
    items = [l.split("\t") for l in (HERE / "items.tsv").read_text().splitlines()[1:]]
    jobs = [(name, model, item, variant, prop, workdir)
            for name, model in MODELS.items() for item, variant, prop, *_ in items]
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
        for line in pool.map(ask, jobs):
            print(line, flush=True)


if __name__ == "__main__":
    main()
