"""要求文から成果物を書かせる。使い方: python3 -I generate.py <作業用の空ディレクトリ>"""
import concurrent.futures
import pathlib
import subprocess
import sys

HERE = pathlib.Path(__file__).parent
MODELS = {"fable": "claude-fable-5-2", "opus": "claude-opus-5-5", "sonnet": "claude-sonnet-5-5"}
ARMS = {
    "prose": "この要求から、設計書を日本語で書いてください。コードや形式的な仕様は書きません。",
    "quint": "この要求から、Quint の仕様を書いてください。状態、操作、守るべき性質を書きます。"
             "説明はコードのコメントに書き、Quint のコードだけを 1 つのコードブロックで出力します。",
}
PROMPT = """次は、業務側から届いた要求です。

<要求>
{brief}
</要求>

{task}
実装者は、この成果物だけを見て実装します。成果物だけを出力してください。
"""


def make(job):
    arm, name, model, run, workdir = job
    out = HERE / "artifacts" / f"{arm}-{name}-{run}.md"
    if out.exists() and out.stat().st_size > 0:
        return f"{out.name} cached"
    prompt = PROMPT.format(brief=(HERE / "brief.md").read_text(), task=ARMS[arm])
    res = subprocess.run(
        ["claude", "-p", "--model", model, "--effort", "high", "--tools", "",
         "--strict-mcp-config", "--setting-sources", ""],
        input=prompt, capture_output=True, text=True, cwd=workdir, timeout=1500)
    out.parent.mkdir(exist_ok=True)
    out.write_text(res.stdout)
    return f"{out.name} exit={res.returncode} bytes={len(res.stdout)}"


def main():
    jobs = [(arm, name, model, run, sys.argv[1])
            for arm in ARMS for name, model in MODELS.items() for run in (1, 2)]
    with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:
        for line in pool.map(make, jobs):
            print(line, flush=True)


if __name__ == "__main__":
    main()
