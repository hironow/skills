"""Read an existing, human-maintained glossary and prepare its migration.

usage: python3 import_glossary.py <glossary-file> --project <project-dir> [--emit-lean]

Understands: Markdown tables, Markdown lists (`- **Term**: definition`), Markdown headings followed
by a paragraph, definition lists (`Term` / `: definition`), simple YAML, JSON, CSV and TSV.

Writes into <project-dir>/migration/:
  legacy.tsv    term, definition                 the glossary as it was; do not edit
  mapping.tsv   term, status, target             one row per legacy entry (a term defined twice has
                                                 two rows, the second marked "(2)"), status empty for you:
                                                 `mapped` + the term ID in the new glossary, or
                                                 `retired` + the reason. `just check` fails until
                                                 every row is filled in.
  report.md     what the script noticed: duplicates, empty definitions, which terms mention which,
                circular definitions, terms defined but never mentioned

With --emit-lean it also writes <project-dir>/Glossary/Legacy.lean: the glossary exactly as it
was, as a Lean list, with a machine-checked statement of whether it passes the checker. It is the
record of the starting point (pattern 1 in references/patterns.md); the new glossary is a
separate file that you write.
"""
import argparse
import csv
import difflib
import io
import json
import pathlib
import re
import sys

TERM_HEAD = re.compile(r"用語|term|name|word|語|名称|概念", re.I)
DEF_HEAD = re.compile(r"定義|definition|description|meaning|意味|説明|内容", re.I)


def clean(text: str) -> str:
    text = re.sub(r"[*_`]+", "", text)
    return re.sub(r"\s+", " ", text).strip(" :：-—–|")


def from_table(lines):
    entries = []
    for i, line in enumerate(lines):
        if not line.lstrip().startswith("|") or i + 1 >= len(lines):
            continue
        if not re.match(r"^\s*\|?\s*:?-{2,}", lines[i + 1]):
            continue
        head = [clean(c) for c in line.strip().strip("|").split("|")]
        term_col = next((k for k, h in enumerate(head) if TERM_HEAD.search(h)), None)
        def_col = next((k for k, h in enumerate(head) if DEF_HEAD.search(h)), None)
        if term_col is None:
            term_col, def_col = 0, (1 if len(head) > 1 else None)
        if def_col is None:
            def_col = 1 if term_col == 0 and len(head) > 1 else None
        for row in lines[i + 2:]:
            if not row.lstrip().startswith("|"):
                break
            cells = [clean(c) for c in row.strip().strip("|").split("|")]
            if len(cells) > term_col and cells[term_col]:
                entries.append((cells[term_col], cells[def_col] if def_col is not None and len(cells) > def_col else ""))
    return entries


def from_markdown(text: str):
    lines = text.splitlines()
    entries = from_table(lines)
    if entries:
        return entries
    bullet = re.compile(r"^\s*(?:[-*+]|\d+[.)])\s+(?:\*\*|__)?([^:：*_]{1,60}?)(?:\*\*|__)?\s*(?:[:：]|\s[—–-]\s)\s*(.*)$")
    for line in lines:
        m = bullet.match(line)
        if m and clean(m.group(1)):
            entries.append((clean(m.group(1)), clean(m.group(2))))
    if len(entries) >= 3:
        return entries
    entries = []
    for i, line in enumerate(lines):  # definition list: Term / : definition
        if i + 1 < len(lines) and lines[i + 1].startswith(":") and line.strip() and not line.startswith("#"):
            entries.append((clean(line), clean(lines[i + 1][1:])))
    if len(entries) >= 3:
        return entries
    entries, current, body = [], None, []
    for line in lines + ["## "]:  # headings followed by a paragraph
        m = re.match(r"^#{2,6}\s+(.*)$", line)
        if m:
            if current and body:
                entries.append((current, clean(" ".join(body))))
            current, body = clean(m.group(1)), []
        elif current is not None and line.strip() and not line.startswith("#"):
            body.append(line.strip())
    return entries


def from_yaml(text: str):
    entries, term, definition = [], None, None
    for line in text.splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        m = re.match(r"^\s*-?\s*(term|name|用語)\s*:\s*(.+)$", line, re.I)
        if m:
            if term:
                entries.append((term, definition or ""))
            term, definition = clean(m.group(2).strip("\"'")), None
            continue
        m = re.match(r"^\s*(definition|description|定義|説明|meaning)\s*:\s*(.+)$", line, re.I)
        if m and term:
            definition = clean(m.group(2).strip("\"'"))
    if term:
        entries.append((term, definition or ""))
    if entries:
        return entries
    for line in text.splitlines():  # plain mapping  Term: definition
        m = re.match(r"^([^\s#:][^:]{0,60}):\s+(.+)$", line)
        if m:
            entries.append((clean(m.group(1).strip("\"'")), clean(m.group(2).strip("\"'"))))
    return entries


def from_json(text: str):
    data = json.loads(text)
    if isinstance(data, dict):
        inner = next((v for v in data.values() if isinstance(v, list)), None)
        if inner is None:
            return [(clean(str(k)), clean(str(v))) for k, v in data.items() if isinstance(v, str)]
        data = inner
    entries = []
    for item in data if isinstance(data, list) else []:
        if isinstance(item, dict):
            term = next((str(v) for k, v in item.items() if TERM_HEAD.search(k)), None)
            definition = next((str(v) for k, v in item.items() if DEF_HEAD.search(k)), "")
            if term:
                entries.append((clean(term), clean(definition)))
    return entries


def from_delimited(text: str, delimiter: str):
    rows = list(csv.reader(io.StringIO(text), delimiter=delimiter))
    if not rows:
        return []
    head = rows[0]
    term_col = next((k for k, h in enumerate(head) if TERM_HEAD.search(h)), 0)
    def_col = next((k for k, h in enumerate(head) if DEF_HEAD.search(h)), 1 if len(head) > 1 else None)
    start = 1 if any(TERM_HEAD.search(h) or DEF_HEAD.search(h) for h in head) else 0
    return [(clean(r[term_col]), clean(r[def_col]) if def_col is not None and len(r) > def_col else "")
            for r in rows[start:] if len(r) > term_col and clean(r[term_col])]


def parse_glossary(path: pathlib.Path):
    """A list of (term, definition), in the order they appear."""
    text = path.read_text(errors="replace")
    suffix = path.suffix.lower()
    if suffix in (".yaml", ".yml"):
        return from_yaml(text)
    if suffix == ".json":
        return from_json(text)
    if suffix == ".csv":
        return from_delimited(text, ",")
    if suffix == ".tsv":
        return from_delimited(text, "\t")
    return from_markdown(text)


def mentions(entries):
    """For each entry, the other terms whose name occurs in its definition (longest names first).

    Returns (per_entry, per_term): a list parallel to `entries`, and the union per term. A term
    defined twice has two entries, each with its own mentions.
    """
    names = sorted({t for t, _ in entries}, key=len, reverse=True)
    per_entry, per_term = [], {}
    for term, definition in entries:
        found, rest = [], definition
        for name in names:
            if name != term and name and name in rest:
                found.append(name)
                rest = rest.replace(name, " ")
        per_entry.append(found)
        merged = per_term.setdefault(term, [])
        for name in found:
            if name not in merged:
                merged.append(name)
    return per_entry, per_term


def cycles(graph):
    """The circular definitions, each as a closed path [a, b, ..., a].

    For every term, the shortest path of mentions that leads back to it. Two terms that mention
    each other give one cycle; a longer ring gives one cycle. The same ring is reported once.
    """
    found, seen = [], set()
    for start in graph:
        # breadth-first search for the shortest way back to `start`
        parent, queue, back = {start: None}, [start], None
        while queue and back is None:
            node = queue.pop(0)
            for nxt in graph.get(node, []):
                if nxt == start:
                    back = node
                    break
                if nxt not in parent:
                    parent[nxt] = node
                    queue.append(nxt)
        if back is None:
            continue
        path = [back]
        while parent[path[-1]] is not None:
            path.append(parent[path[-1]])
        path.reverse()  # start ... back
        key = frozenset(path)
        if key not in seen:
            seen.add(key)
            found.append(path + [start])
    return found


def lean_id(term: str, used: set, n: int) -> str:
    words = re.findall(r"[A-Za-z][A-Za-z0-9]*", term)
    ident = (words[0].lower() + "".join(w.capitalize() for w in words[1:])) if words else f"t{n:02d}"
    if ident in used or ident in {"end", "def", "theorem", "if", "then", "else", "match", "with", "open", "in", "at", "do"}:
        ident = f"{ident}{n:02d}"
    used.add(ident)
    return ident


def passes_checker(order, deps):
    seen = set()
    for term in order:
        if term in seen or any(d not in seen for d in deps[term]):
            return False
        seen.add(term)
    return True


def emit_lean(entries, per_entry, deps, source_name: str, circular) -> str:
    used, ids = set(), {}
    order = []
    for n, (term, _) in enumerate(entries, 1):
        if term not in ids:
            ids[term] = lean_id(term, used, n)
        order.append(term)
    unique = list(dict.fromkeys(order))
    ok = len(unique) == len(order) and passes_checker(order, deps)  # a term defined twice fails on the ID
    quote = lambda s: s.replace("\\", "\\\\").replace('"', '\\"')
    rows = []
    for (term, definition), own in zip(entries, per_entry):
        dep = ", ".join(ids[d] for d in own)
        rows.append(f'  {{ id := {ids[term]}, label := "{quote(term)}", context := .legacy,\n'
                    f'    gloss := "{quote(definition)}"' + (f",\n    defDeps := [{dep}]" if dep else "") + " }")
    names = " | ".join(dict.fromkeys(ids[t] for t in order))
    def entry_with(src, dst):
        """The position of the first entry of `src` whose own definition mentions `dst`."""
        return next(n for n, (term, _) in enumerate(entries) if term == src and dst in per_entry[n])
    cycle_theorems = ""
    for number, path in enumerate(circular[:5], 1):
        steps, labels = [], " → ".join(path)
        for k in range(len(path) - 1):
            src, dst = path[k], path[k + 1]
            steps.append(f"  have s{k + 1} : DefDep draft {ids[src]} {ids[dst]} :=\n"
                         f"    ⟨draft[{entry_with(src, dst)}]'(by decide), List.getElem_mem _, rfl, by decide⟩")
        chain = "(.single s1)"
        for k in range(2, len(path)):
            chain = f"(.tail {chain} s{k})"
        cycle_theorems += (f"\n/-- The old glossary is circular: {labels}. -/\n"
                           f"theorem draft_cycle_{number} : ¬ Acyclic (DefDep draft) := by\n  intro h\n"
                           + "\n".join(steps) + f"\n  exact h {ids[path[0]]} {chain}\n")
    return f'''import Glossary.Core

/-!
# The glossary as it was before the migration

Generated once by `import_glossary.py` from `{source_name}`. It records the starting point and is
not the new glossary. A term's `defDeps` are the other terms whose names occur in its definition.

The statement at the end is checked by Lean: it says whether the old glossary, exactly as written,
passes the checker (unique IDs, references that exist, no circular definitions).
-/

namespace Glossary.Legacy

inductive Term where
  | {names}
  deriving DecidableEq, Repr

inductive Ctx where
  | legacy
  deriving DecidableEq, Repr

open Term

def draft : List (Entry Term Ctx) := [
{(",\n").join(rows)}
]

theorem draft_check : check draft = {"true" if ok else "false"} := by decide
{cycle_theorems}
end Glossary.Legacy
'''


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("glossary")
    parser.add_argument("--project", required=True)
    parser.add_argument("--emit-lean", action="store_true")
    args = parser.parse_args()
    source = pathlib.Path(args.glossary)
    entries = parse_glossary(source)
    if len(entries) < 1:
        print(f"import_glossary: no entries recognised in {source}. Convert it to a Markdown table "
              "with the columns Term and Definition and run again.", file=sys.stderr)
        return 1
    project = pathlib.Path(args.project).resolve()
    out = project / "migration"
    out.mkdir(parents=True, exist_ok=True)
    tsv = lambda s: s.replace("\t", " ").replace("\n", " ")
    # One row per entry. A term that is defined twice gets "(2)" on its second row, so that each
    # definition has to be accounted for on its own.
    keys, times = [], {}
    for term, _ in entries:
        times[term] = times.get(term, 0) + 1
        keys.append(term if times[term] == 1 else f"{term} ({times[term]})")
    (out / "legacy.tsv").write_text("term\tdefinition\n" + "".join(
        f"{tsv(k)}\t{tsv(d)}\n" for k, (_, d) in zip(keys, entries)))
    mapping = out / "mapping.tsv"
    if not mapping.exists():
        mapping.write_text("term\tstatus\ttarget\n" + "".join(f"{tsv(k)}\t\t\n" for k in keys))
    per_entry, deps = mentions(entries)
    counts = {}
    for term, _ in entries:
        counts[term] = counts.get(term, 0) + 1
    duplicates = [t for t, n in counts.items() if n > 1]
    folded = {}
    for term in counts:
        folded.setdefault(re.sub(r"[\s_-]+", "", term).lower(), []).append(term)
    near = [group for group in folded.values() if len(group) > 1]
    distinct = list(counts)
    for i, first in enumerate(distinct):  # names that are almost the same: likely one term spelled two ways
        for second in distinct[i + 1:]:
            if min(len(first), len(second)) >= 3 and first not in second and second not in first \
                    and difflib.SequenceMatcher(None, first, second).ratio() >= 0.8:
                near.append([first, second])
    empty = [t for t, d in entries if not d]
    circular = cycles(deps)
    mentioned = {d for ds in deps.values() for d in ds}
    isolated = [t for t in counts if t not in mentioned and not deps[t]]
    forward = []
    position = {t: i for i, (t, _) in reversed(list(enumerate(entries)))}
    for term, _ in entries:
        for d in deps[term]:
            if position[d] > position[term] and not any(term in g and d in g for g in circular):
                forward.append((term, d))
    lines = [f"# Migration report for `{source.name}`", "",
             "Written by `import_glossary.py`. It lists what a program can notice. Decide each point yourself.", "",
             f"- Entries: {len(entries)} ({len(counts)} distinct terms)",
             f"- Terms defined more than once: {len(duplicates)}",
             f"- Terms with nearly the same name: {len(near)}",
             f"- Terms with no definition: {len(empty)}",
             f"- Circular definitions: {len(circular)}",
             f"- Terms used before they are defined: {len(forward)}",
             f"- Terms that neither mention nor are mentioned by another term: {len(isolated)}", ""]
    def section(title, rows, note):
        lines.extend([f"## {title}", "", note, ""] + ([f"- {r}" for r in rows] or ["None."]) + [""])
    section("Circular definitions", [" → ".join(g) for g in circular],
            "Each line is one closed path: every term mentions the next in its definition, and the last is the first again. The checker rejects these. "
            "Usually one of the mentions is an association (\"a customer places orders\"), not part of the definition.")
    section("Defined more than once", duplicates, "Keep one definition, or split the term into two terms with different names.")
    section("Same term written differently", [" / ".join(g) for g in near], "Probably one term. Pick one spelling.")
    section("No definition", empty, "Write a definition, or retire the term with a reason.")
    section("Used before defined", [f"{a} mentions {b}" for a, b in forward],
            "Not an error in the old glossary, but the new one lists a term after the terms it is defined from.")
    section("Isolated terms", isolated, "Check whether each is still used. A term nobody uses is a candidate to retire.")
    lines.extend(["## Which terms mention which", "", "| Term | Mentions in its definition |", "|---|---|"]
                 + [f"| {t} | {', '.join(deps[t]) or '—'} |" for t in counts] + [""])
    (out / "report.md").write_text("\n".join(lines))
    print(f"import_glossary: {len(entries)} entries -> {out}/legacy.tsv, mapping.tsv, report.md")
    print(f"  circular definitions: {len(circular)}; defined twice: {len(duplicates)}; "
          f"nearly the same name: {len(near)}; no definition: {len(empty)}")
    if args.emit_lean:
        target = project / "Glossary" / "Legacy.lean"
        if target.exists():
            print(f"  kept the existing {target}")
        else:
            target.write_text(emit_lean(entries, per_entry, deps, source.name, circular))
            print(f"  wrote {target}; add `import Glossary.Legacy` to Glossary.lean and a line to Audit.lean:")
            print("    #print axioms Glossary.Legacy.draft_check")
            for number in range(1, min(len(circular), 5) + 1):
                print(f"    #print axioms Glossary.Legacy.draft_cycle_{number}")
    print("next: fill in migration/mapping.tsv as you write the new glossary; `just check` fails until every row is filled")
    return 0


if __name__ == "__main__":
    sys.exit(main())
