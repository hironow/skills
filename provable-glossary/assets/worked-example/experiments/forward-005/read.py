"""成果物を読み手に読ませ、14 の場面に答えさせる。使い方: python3 -I read.py <作業用の空ディレクトリ>"""
import concurrent.futures
import pathlib
import subprocess
import sys

HERE = pathlib.Path(__file__).parent
MODELS = {"fable": "claude-fable-5-2", "opus": "claude-opus-5-5", "sonnet": "claude-sonnet-5-5"}
PROMPT = """次は、映画館のチケット販売の成果物 (設計書、または Quint の仕様) です。

<成果物>
{artifact}
</成果物>

あなたは実装者です。次の 14 の場面について、この成果物に従うとどうなるかを答えてください。

決まり:
- 根拠にしてよいのは成果物だけです。常識や一般的な実装の習慣で補ってはいけません。
- 成果物に書かれていない場合、または複数の読み方ができる場合は、Z を選びます。
- 成果物が「未決」「要確認」としている場合も、Z を選びます。
- 道具は使えません。読んで考えるだけで答えます。

<場面>
{scenarios}
</場面>

場面ごとに短く根拠を書いた後、最後に次の形の JSON を 1 つだけ、```json のコードブロックで出力してください。

```json
{{"S01": "A", "S02": "Z", "S03": "B", "S04": "A", "S05": "A", "S06": "B", "S07": "A", "S08": "B", "S09": "Z", "S10": "A", "S11": "Z", "S12": "A", "S13": "A", "S14": "A"}}
```
"""


def ask(job):
    artifact, name, model, workdir = job
    out = HERE / "readings" / artifact.stem / f"{name}.md"
    if out.exists() and out.stat().st_size > 0:
        return f"{artifact.stem} {name} cached"
    prompt = PROMPT.format(artifact=artifact.read_text(),
                           scenarios=(HERE / "scenarios.md").read_text())
    res = subprocess.run(
        ["claude", "-p", "--model", model, "--effort", "high", "--tools", "",
         "--strict-mcp-config", "--setting-sources", ""],
        input=prompt, capture_output=True, text=True, cwd=workdir, timeout=1500)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(res.stdout)
    return f"{artifact.stem} {name} exit={res.returncode} bytes={len(res.stdout)}"


def main():
    jobs = [(a, name, model, sys.argv[1])
            for a in sorted((HERE / "artifacts").glob("*.md")) for name, model in MODELS.items()]
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
        for line in pool.map(ask, jobs):
            print(line, flush=True)


if __name__ == "__main__":
    main()
