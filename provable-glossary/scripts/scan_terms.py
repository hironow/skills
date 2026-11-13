"""List the names an existing implementation uses, as raw material for a glossary.

usage: python3 scan_terms.py <repo-dir> [--out <dir>] [--src <subdir> ...]

Reads source files (Go, Rust, TypeScript/JavaScript, Python, Java, Kotlin, Ruby, C#, PHP, Swift,
SQL, protobuf, GraphQL) with simple patterns and writes three tables into <dir>
(default: <repo-dir>/glossary-scan/):

  words.tsv        domain words, most frequent first: word, count, where it occurs, examples
  identifiers.tsv  every declared type, function, constant and table: name, kind, other_uses, anchor
                   The anchor column is ready to paste into a term's `anchors` list. other_uses is how
                   often the name appears elsewhere in the scanned code; 0 means declared and never used.
  states.tsv       groups of constants or enum cases that look like the states of something:
                   group, members, anchor. These are the candidates for state machines.

It is a word counter, not an analysis. It cannot tell a domain word from a technical one, and it
cannot see that two names mean the same thing. Use it to make sure no name in the code is missed;
decide what is a term by reading the code.
"""
import argparse
import collections
import pathlib
import re
import sys

from glossary_project import walk_files

SUFFIXES = {".go", ".rs", ".ts", ".tsx", ".js", ".jsx", ".py", ".java", ".kt", ".rb", ".cs", ".php", ".swift",
            ".scala", ".ex", ".exs", ".sql", ".proto", ".graphql"}
DECLARATIONS = [
    ("type", re.compile(r"^\s*(?:export\s+|public\s+|private\s+|internal\s+|abstract\s+|final\s+|sealed\s+|data\s+|pub(?:\([a-z]+\))?\s+)*"
                        r"(?:class|struct|interface|enum|trait|record|type|message|object)\s+([A-Za-z_]\w*)")),
    ("function", re.compile(r"^\s*(?:export\s+|public\s+|private\s+|protected\s+|internal\s+|static\s+|async\s+|override\s+|pub(?:\([a-z]+\))?\s+)*"
                            r"(?:func(?:\s*\([^)]*\))?|fn|def|function|fun)\s+([A-Za-z_]\w*)")),
    # methods declared without a keyword (TypeScript, Java, C#, Kotlin class bodies)
    ("function", re.compile(r"^\s+(?:public\s+|private\s+|protected\s+|static\s+|async\s+|override\s+|final\s+)*"
                            r"(?!if\b|for\b|while\b|switch\b|catch\b|return\b|else\b|function\b|constructor\b|super\b|new\b|throw\b|await\b)"
                            r"([a-z][A-Za-z0-9]*)\s*\([^;{}]*\)\s*(?::\s*[^{;=]+)?\{\s*$")),
    ("table", re.compile(r"^\s*CREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?[`\"]?([A-Za-z_]\w*)", re.I)),
    ("constant", re.compile(r"^\s*(?:export\s+|public\s+|private\s+|static\s+|final\s+|pub\s+)*(?:const|val|let|static)?\s*"
                            r"([A-Z][A-Za-z0-9]*(?:_[A-Z0-9]+)+|[A-Z][a-z0-9]+(?:[A-Z][a-z0-9]+)+)\b[^=(){};]*=(?!=)")),
    ("case", re.compile(r"^\s*(?:case\s+)?([A-Z][A-Za-z0-9_]*)\s*(?:=\s*(?:\"[^\"]*\"|'[^']*'|\d+|iota))?\s*[,;]?\s*(?://.*|#.*)?$")),
]
STOP = set("""get set new create make build init is has to from with of for in on at by and or not the a an
handle handler service manager helper util utils impl default base abstract test tests mock fake err error
errors result response request req res ctx context config option options param params args arg value values
key keys id ids list map string int bool data info item items type types kind name names main run start
str num obj fn func def var val let const true false null nil none self this that it be do if else then
http json sql db api url uri path file dir repo repository store storage client server controller model
view dto entity factory builder provider adapter port ports wrapper interface struct class enum""".split())


def words_of(identifier: str):
    parts = re.findall(r"[A-Z]+(?=[A-Z][a-z])|[A-Z]?[a-z]+|[A-Z]+|\d+", identifier)
    return [p.lower() for p in parts if len(p) > 2 and not p.isdigit() and p.lower() not in STOP]


def common_affix(names):
    prefix = names[0]
    for n in names[1:]:
        while not n.startswith(prefix):
            prefix = prefix[:-1]
    return prefix if len(prefix) >= 3 else ""


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("repo")
    parser.add_argument("--out")
    parser.add_argument("--src", action="append", help="limit the scan to these subfolders")
    args = parser.parse_args()
    repo = pathlib.Path(args.repo).resolve()
    out = pathlib.Path(args.out) if args.out else repo / "glossary-scan"
    roots = [repo / s for s in args.src] if args.src else [repo]
    identifiers, word_count, word_where, word_examples, states = [], collections.Counter(), {}, {}, []
    scanned = 0
    corpus = ""
    for root in roots:
        for path in walk_files(root):
            if path.suffix not in SUFFIXES or re.search(r"(_test|\.test|\.spec|_spec)\.|/tests?/|/__tests__/", str(path)):
                continue
            scanned += 1
            rel = str(path.relative_to(repo))
            run = []  # consecutive enum-like lines
            try:
                source = path.read_text(errors="replace")
                lines = source.splitlines()
                corpus += source + "\n"
            except OSError:
                continue
            for number, line in enumerate(lines + [""], 1):
                matched = None
                for kind, pattern in DECLARATIONS:
                    m = pattern.match(line)
                    if m:
                        # anchor text: the declaration up to and including the name. For an enum case
                        # or a constant the bare name is too loose, so keep its value as well.
                        text = line[: m.end(1)].strip()
                        if kind in ("case", "constant"):
                            text = re.sub(r"\s*[,;]?\s*(//.*|#.*)?$", "", line.strip())
                        matched = (kind, m.group(1), text)
                        break
                if matched and matched[0] in ("case", "constant"):
                    run.append((matched[1], matched[2], number))
                else:
                    if len(run) >= 2:
                        names = [n for n, _, _ in run]
                        group = common_affix(names) or f"{pathlib.Path(rel).stem}:{run[0][2]}"
                        states.append((group, names, f"{rel}#{run[0][1][:80]}"))
                    run = []
                if not matched or (matched[0] == "case" and len(run) < 2 and not re.search(r"[=,]", line)):
                    continue
                kind, name, text = matched
                identifiers.append((name, kind, f"{rel}#{text[:80]}"))
                for word in words_of(name):
                    word_count[word] += 1
                    word_where.setdefault(word, collections.Counter())[str(pathlib.Path(rel).parent)] += 1
                    examples = word_examples.setdefault(word, [])
                    if name not in examples and len(examples) < 4:
                        examples.append(name)
    out.mkdir(parents=True, exist_ok=True)
    (out / "words.tsv").write_text("word\tcount\twhere\texamples\n" + "".join(
        f"{w}\t{n}\t{', '.join(d for d, _ in word_where[w].most_common(3))}\t{', '.join(word_examples[w])}\n"
        for w, n in word_count.most_common()))
    seen = set()
    rows = []
    occurrences = collections.Counter(re.findall(r"[A-Za-z_]\w*", corpus))
    for name, kind, anchor in identifiers:
        if (name, kind) not in seen:
            seen.add((name, kind))
            # how often the name appears in the scanned code besides its declaration
            rows.append(f"{name}\t{kind}\t{max(occurrences[name] - 1, 0)}\t{anchor}\n")
    (out / "identifiers.tsv").write_text("name\tkind\tother_uses\tanchor\n" + "".join(rows))
    (out / "states.tsv").write_text("group\tmembers\tanchor\n" + "".join(
        f"{g}\t{', '.join(m)}\t{a}\n" for g, m, a in states))
    print(f"scan_terms: {scanned} source files; {len(word_count)} words, {len(rows)} identifiers, "
          f"{len(states)} state-like groups -> {out}")
    print("next: read words.tsv from the top and states.tsv in full; see references/start-from-code.md")
    return 0


if __name__ == "__main__":
    sys.exit(main())
