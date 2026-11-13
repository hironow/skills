"""対照を実行する。使い方: python3 -I run_controls.py <作業用の空ディレクトリ>"""
import concurrent.futures
import pathlib
import subprocess
import sys

HERE = pathlib.Path(__file__).parent
SCALE = HERE.parent / "scale-003"
MODELS = {"fable": "claude-fable-5-2", "opus": "claude-opus-5-5", "sonnet": "claude-sonnet-5-5"}
ARMS = ["precise", "design"]
PARAMS = ["TTL", "EXT", "LAT", "MAINT", "FREEZE", "REACQUIRE"]
BOOLS = {"FREEZE", "REACQUIRE"}
PROPS = {
    "Q2": "返金された顧客は 1 人もいない。",
    "Q3": "決済が成功して処理待ちになっている顧客は、必ず座席を確保している。",
    "Q4": "決済サービスの応答を待っている顧客は、必ず座席を確保している。",
}

PROMPT = """次の文書は、映画館のチケット販売の仕組みを説明したものです。上映回は 1 つ、座席は 1 つ、顧客は c1 と c2 の 2 人です。
道具は使わず、読んで考えるだけで答えてください。コードの実行やモデル検査はできません。

<文書>
{doc}
</文書>

パラメータの値:
{switches}

確かめたい性質: {prop}
ここで「座席を確保している」とは、その顧客が座席を仮確保しているか、座席がその顧客に販売済みであることです。

問い: 最初の状態 (サイトは動いていて、座席は空いていて、誰も決済を始めていない) から、文書の決まりに従って
到達できるすべての状態で、この性質は成り立ちますか。

答え方:
- 成り立つなら verdict を "holds" にします。
- 破れるなら verdict を "violated" にして、最初の状態の後に起きる操作の列を trace に書きます。
  列の最後の操作の直後の状態で性質が偽になるようにします。各操作はその時点で実行可能でなければなりません。
- 操作の書き方: `reserve("c1")`, `startPayment("c2")`, `providerSucceeds("c1")`, `providerFails("c1")`,
  `settle("c1")`, `detectVulnerability`, `recover`, `tick`。

考えた後、最後に次の形の JSON を 1 つだけ、```json のコードブロックで出力してください。

```json
{{"verdict": "holds", "trace": []}}
```
"""


def ask(job):
    arm, name, model, item, variant, prop, workdir = job
    out = HERE / "answers" / arm / name / f"{item}.md"
    if out.exists() and out.stat().st_size > 0:
        return f"{arm} {name} {item} cached"
    switches = "\n".join(
        f"- {n} = {('有効' if b == '1' else '無効') if n in BOOLS else b}"
        for n, b in zip(PARAMS, variant))
    prompt = PROMPT.format(doc=(HERE / "docs" / f"{arm}.md").read_text(), switches=switches,
                           prop=PROPS[prop])
    res = subprocess.run(
        ["claude", "-p", "--model", model, "--effort", "high", "--tools", "",
         "--strict-mcp-config", "--setting-sources", ""],
        input=prompt, capture_output=True, text=True, cwd=workdir, timeout=1500)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(res.stdout)
    return f"{arm} {name} {item} exit={res.returncode} bytes={len(res.stdout)}"


def main():
    workdir = sys.argv[1]
    items = [l.split("\t") for l in (SCALE / "items.tsv").read_text().splitlines()[1:]]
    jobs = [(arm, name, model, item, variant, prop, workdir)
            for arm in ARMS for name, model in MODELS.items() for item, variant, prop, *_ in items]
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
        for line in pool.map(ask, jobs):
            print(line, flush=True)


if __name__ == "__main__":
    main()
