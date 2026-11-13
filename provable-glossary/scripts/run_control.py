"""Ask a tool-less control one question and save its answer.

The control is a Claude model run in an empty directory with no tools, no MCP servers and no
settings, so it can only read the prompt and think. Use it for the control experiments.

usage: python3 run_control.py --model <model> --prompt-file q.txt --out answers/<model>/01.md [--effort high]

An existing non-empty answer file is kept (answers are run records; never rewrite them). The last
```json block in the answer is what the experiment scores; the script reports whether one exists.
"""
import argparse
import pathlib
import re
import subprocess
import sys
import tempfile


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--model", required=True)
    parser.add_argument("--prompt-file", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--effort", default="high", help="see `claude --help`; pass an empty string to omit")
    parser.add_argument("--timeout", type=int, default=1500)
    args = parser.parse_args()
    out = pathlib.Path(args.out)
    if out.exists() and out.stat().st_size > 0:
        print(f"{out}: kept (already answered)")
        return 0
    command = ["claude", "-p", "--model", args.model, "--tools", "", "--strict-mcp-config", "--setting-sources", ""]
    if args.effort:
        command += ["--effort", args.effort]
    with tempfile.TemporaryDirectory() as empty:
        done = subprocess.run(command, input=pathlib.Path(args.prompt_file).read_text(), capture_output=True,
                              text=True, cwd=empty, timeout=args.timeout)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(done.stdout)
    has_json = bool(re.search(r"```json\s*\{.*?\}\s*```", done.stdout, re.S))
    print(f"{out}: exit {done.returncode}, {len(done.stdout)} bytes, final json block: {has_json}")
    return 0 if done.returncode == 0 and has_json else 1


if __name__ == "__main__":
    sys.exit(main())
