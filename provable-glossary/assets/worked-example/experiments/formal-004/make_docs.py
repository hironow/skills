"""仕様を自然言語の文書に書き換えさせる。使い方: python3 -I make_docs.py <作業用の空ディレクトリ>"""
import pathlib
import subprocess
import sys

HERE = pathlib.Path(__file__).parent
SPEC = (HERE.parent / "scale-003" / "timed_sale.qnt").read_text()
COMMON = """
決まりごと:
- 日本語で書きます。コード、擬似コード、数式、Quint の構文は使いません。
- パラメータ TTL, EXT, LAT, MAINT, FREEZE, REACQUIRE は、値を決めずに名前のまま使います。
- 操作の名前 (reserve, startPayment, providerSucceeds, providerFails, settle, detectVulnerability, recover, tick)
  は、どの業務上の出来事に当たるかが分かるように、本文の中で 1 度ずつ示します。
- 不変条件 (Q1〜Q4) には触れません。性質の成否についての考察も書きません。
- 文書だけを出力します。前置きや後書きは書きません。

```quint
{spec}
```
"""
ARMS = {
    "precise": ("claude-fable-5-2", """次の Quint の仕様を、日本語の文書に言い換えてください。
この文書だけを読んだ人が、仕様とまったく同じ振る舞いを再現できるように、条件を 1 つも漏らさずに書きます。"""),
    "design": ("claude-opus-5-5", """次の Quint の仕様が表している仕組みについて、設計書を書いてください。
開発チームの同僚に渡す、普通の設計書の書き方にします。目的、登場するもの、処理の流れ、決まりを説明します。
仕様を 1 行ずつ訳すのではなく、人が設計を説明するときの書き方で書きます。"""),
}


def main():
    workdir = sys.argv[1]
    (HERE / "docs").mkdir(exist_ok=True)
    for arm, (model, head) in ARMS.items():
        out = HERE / "docs" / f"{arm}.md"
        if out.exists() and out.stat().st_size > 0:
            continue
        res = subprocess.run(
            ["claude", "-p", "--model", model, "--effort", "high", "--tools", "",
             "--strict-mcp-config", "--setting-sources", ""],
            input=head + COMMON.format(spec=SPEC), capture_output=True, text=True,
            cwd=workdir, timeout=1500)
        out.write_text(res.stdout)
        print(arm, res.returncode, len(res.stdout))


if __name__ == "__main__":
    main()
