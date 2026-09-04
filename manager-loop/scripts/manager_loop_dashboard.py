#!/usr/bin/env python3
"""Manager Loop checklist dashboard. The HTML page IS the checklist (stdlib only).

Following the original Manager Loop recipe, the implementer keeps one HTML page
with the full checklist; it ticks boxes as it goes, the tick time is written
into the page, and the page shows a counter plus a chart of boxes ticked over
time. There is no side database: every item lives in `dashboard.html` as
    <li data-id="2.3" data-state="pending|done|skipped" data-at="<ISO>" data-note="...">
and this script edits that file in place.

Layout of --dir (default: ./manager-loop):
    dashboard.html   # the source of truth (checklist + times + chart)
    .dashboard.lock  # transient, guards concurrent ticks

Commands:
    init [--from plan.md] [--stall-minutes N] [--force]   seed the page once from markdown
    tick <id|substring> [--note TEXT]                      mark an item done (records the time)
    skip <id|substring> --note REASON                      settle an item without doing it
    status [--stall-minutes N]                             JSON: counts, current phase, stall signal
    render                                                 re-render the page from its own data

Seed markdown: `# title`, `## Phase N: title` (consecutive from 1), `- [ ]` / `- [x]` items.
"""

from __future__ import annotations

import argparse
import html
import json
import os
import re
import sys
import time
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import UTC, datetime
from html.parser import HTMLParser
from pathlib import Path
from typing import Any

DEFAULT_DIR = "manager-loop"
DASHBOARD = "dashboard.html"
LOCK = ".dashboard.lock"
DEFAULT_STALL_MINUTES = 30
STATES = ("pending", "done", "skipped")

_PHASE_RE = re.compile(r"^##\s+Phase\s+(\d+)\s*:\s*(.+?)\s*$", re.IGNORECASE)
_ITEM_RE = re.compile(r"^\s*[-*]\s+\[( |x|X)\]\s+(.*?)\s*$")
_TITLE_RE = re.compile(r"^#\s+(.+?)\s*$")

SCAFFOLD = """# <goal title>

## Phase 1: <phase title>
- [ ] <first concrete, verifiable to-do>
- [ ] <second to-do>

## Phase 2: Verification
- [ ] <every earlier demo still works from a clean checkout>
"""


class ItemNotFound(LookupError):
    """No open (pending) item matches the given id/substring."""


class MalformedSeed(ValueError):
    """Seed markdown is not in the expected shape."""


@dataclass
class Item:
    item_id: str
    text: str
    state: str = "pending"
    at: datetime | None = None
    note: str = ""

    @property
    def settled(self) -> bool:
        return self.state != "pending"


@dataclass
class Phase:
    index: int
    title: str
    items: list[Item] = field(default_factory=list)

    @property
    def total(self) -> int:
        return len(self.items)

    @property
    def done(self) -> int:
        return sum(1 for i in self.items if i.state == "done")

    @property
    def skipped(self) -> int:
        return sum(1 for i in self.items if i.state == "skipped")

    @property
    def settled(self) -> int:
        return self.done + self.skipped

    @property
    def complete(self) -> bool:
        return self.total > 0 and self.settled == self.total


@dataclass
class Plan:
    title: str
    phases: list[Phase]
    started_at: datetime
    stall_minutes: int = DEFAULT_STALL_MINUTES

    @property
    def items(self) -> list[Item]:
        return [i for p in self.phases for i in p.items]

    @property
    def total(self) -> int:
        return len(self.items)

    @property
    def done(self) -> int:
        return sum(1 for i in self.items if i.state == "done")

    @property
    def skipped(self) -> int:
        return sum(1 for i in self.items if i.state == "skipped")

    @property
    def settled(self) -> int:
        return self.done + self.skipped

    @property
    def all_done(self) -> bool:
        return self.total > 0 and self.settled == self.total

    @property
    def current_phase(self) -> int | None:
        for p in self.phases:
            if not p.complete:
                return p.index
        return None

    @property
    def last_activity(self) -> datetime:
        times = [i.at for i in self.items if i.at is not None]
        return max([self.started_at, *times])


# --- time helpers -----------------------------------------------------------


def _now(now: datetime | None) -> datetime:
    return now if now is not None else datetime.now(UTC).replace(microsecond=0)


def _parse_ts(ts: str) -> datetime:
    dt = datetime.fromisoformat(ts)
    return dt if dt.tzinfo else dt.replace(tzinfo=UTC)


# --- seed markdown -> Plan --------------------------------------------------


def parse_seed(text: str, now: datetime, stall_minutes: int = DEFAULT_STALL_MINUTES) -> Plan:
    title = ""
    phases: list[Phase] = []
    for line in text.splitlines():
        if not title and (m := _TITLE_RE.match(line)):
            title = m.group(1)
            continue
        if m := _PHASE_RE.match(line):
            number = int(m.group(1))
            if number != len(phases) + 1:
                raise MalformedSeed(f"phase headers must be consecutive from 1; got Phase {number}")
            phases.append(Phase(index=number, title=m.group(2)))
            continue
        if phases and (m := _ITEM_RE.match(line)):
            phase = phases[-1]
            done = m.group(1).lower() == "x"
            phase.items.append(
                Item(
                    item_id=f"{phase.index}.{len(phase.items) + 1}",
                    text=m.group(2),
                    state="done" if done else "pending",
                    at=now if done else None,
                )
            )
    if not phases:
        raise MalformedSeed("no `## Phase N: title` headers found")
    return Plan(title=title, phases=phases, started_at=now, stall_minutes=stall_minutes)


# --- HTML <-> Plan ----------------------------------------------------------


class _PageParser(HTMLParser):
    """Reads the dashboard back into a Plan from its data-* attributes."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.main: dict[str, str] = {}
        self.title_parts: list[str] = []
        self.phases: list[Phase] = []
        self._in_h1 = False
        self._in_text = False
        self._text_parts: list[str] = []
        self._item: Item | None = None

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        a = {k: (v or "") for k, v in attrs}
        if tag == "main" and "data-manager-loop" in a:
            self.main = a
        elif tag == "h1":
            self._in_h1 = True
        elif tag == "section" and "data-phase" in a:
            self.phases.append(Phase(index=int(a["data-phase"]), title=a.get("data-title", "")))
        elif tag == "li" and "data-id" in a and self.phases:
            at = _parse_ts(a["data-at"]) if a.get("data-at") else None
            self._item = Item(a["data-id"], "", a.get("data-state", "pending"), at, a.get("data-note", ""))
            self.phases[-1].items.append(self._item)
        elif tag == "span" and a.get("class") == "text" and self._item is not None:
            self._in_text = True
            self._text_parts = []

    def handle_endtag(self, tag: str) -> None:
        if tag == "h1":
            self._in_h1 = False
        elif tag == "span" and self._in_text and self._item is not None:
            self._item.text = "".join(self._text_parts)
            self._in_text = False
        elif tag == "li":
            self._item = None

    def handle_data(self, data: str) -> None:
        if self._in_h1:
            self.title_parts.append(data)
        elif self._in_text:
            self._text_parts.append(data)


def parse_page(text: str) -> Plan:
    p = _PageParser()
    p.feed(text)
    if not p.main:
        raise ValueError("not a manager-loop dashboard (missing <main data-manager-loop>)")
    return Plan(
        title="".join(p.title_parts).strip(),
        phases=p.phases,
        started_at=_parse_ts(p.main["data-started-at"]),
        stall_minutes=int(p.main.get("data-stall-minutes") or DEFAULT_STALL_MINUTES),
    )


def load(dir_: Path) -> Plan:
    return parse_page((dir_ / DASHBOARD).read_text(encoding="utf-8"))


def _chart_svg(plan: Plan, now: datetime) -> str:
    """Inline SVG of boxes done over time. Flat tail to `now` makes a stall visible."""
    w, h, pad = 640, 220, 36
    settled = sorted((i.at for i in plan.items if i.state == "done" and i.at), key=lambda d: d)
    pts: list[tuple[datetime, int]] = [(plan.started_at, 0)]
    for n, t in enumerate(settled, start=1):
        pts.append((t, n))
    pts.append((max(now, pts[-1][0]), pts[-1][1]))
    t0, t1 = pts[0][0], pts[-1][0]
    span = max((t1 - t0).total_seconds(), 1.0)
    ymax = max(plan.total, 1)

    def x(t: datetime) -> float:
        return pad + (w - 2 * pad) * ((t - t0).total_seconds() / span)

    def y(v: int) -> float:
        return h - pad - (h - 2 * pad) * (v / ymax)

    poly = " ".join(f"{x(t):.1f},{y(v):.1f}" for t, v in pts)
    dots = "".join(f'<circle cx="{x(t):.1f}" cy="{y(v):.1f}" r="3" fill="#2563eb"/>' for t, v in pts[1:-1])
    return (
        f'<svg viewBox="0 0 {w} {h}" width="100%" role="img" aria-label="boxes ticked over time">'
        f'<line x1="{pad}" y1="{h - pad}" x2="{w - pad}" y2="{h - pad}" stroke="#999"/>'
        f'<line x1="{pad}" y1="{pad}" x2="{pad}" y2="{h - pad}" stroke="#999"/>'
        f'<text x="{pad - 6}" y="{pad + 4}" text-anchor="end" font-size="11">{ymax}</text>'
        f'<text x="{pad - 6}" y="{h - pad + 4}" text-anchor="end" font-size="11">0</text>'
        f'<text x="{w - pad}" y="{h - pad + 16}" text-anchor="end" font-size="11">{span / 3600:.1f} h</text>'
        f'<polyline points="{poly}" fill="none" stroke="#2563eb" stroke-width="2"/>{dots}</svg>'
    )


def _fmt_time(dt: datetime | None) -> str:
    return dt.astimezone(UTC).strftime("%H:%M UTC") if dt else ""


def render_html(plan: Plan, now: datetime) -> str:
    e = html.escape
    marks = {"pending": "☐", "done": "☑", "skipped": "⊘"}
    sections: list[str] = []
    for p in plan.phases:
        rows = []
        for i in p.items:
            when = (
                f'<time datetime="{i.at.isoformat()}">{_fmt_time(i.at)}</time>' if i.at else "<time></time>"
            )
            note = f'<em class="note">{e(i.note)}</em>' if i.note else ""
            rows.append(
                f'<li data-id="{i.item_id}" data-state="{i.state}" data-at="{i.at.isoformat() if i.at else ""}" '
                f'data-note="{e(i.note, quote=True)}">'
                f'<span class="box">{marks[i.state]}</span> <code>{i.item_id}</code> '
                f'<span class="text">{e(i.text)}</span> {when} {note}</li>'
            )
        pct = round(100 * p.settled / p.total) if p.total else 0
        sections.append(
            f'<section data-phase="{p.index}" data-title="{e(p.title, quote=True)}">'
            f"<h2>Phase {p.index}: {e(p.title)} <small>{p.done}/{p.total}"
            f"{f' (+{p.skipped} skipped)' if p.skipped else ''}</small></h2>"
            f'<div class="bar"><div style="width:{pct}%"></div></div><ol>{"".join(rows)}</ol></section>'
        )
    since = int((now - plan.last_activity).total_seconds() // 60)
    pct_all = round(100 * plan.done / plan.total, 1) if plan.total else 0.0
    current = plan.current_phase
    return f"""<!doctype html>
<meta charset="utf-8"><meta http-equiv="refresh" content="60">
<title>{e(plan.title or "Manager Loop")}</title>
<style>
body{{font:14px/1.5 system-ui,sans-serif;max-width:760px;margin:2rem auto;padding:0 1rem;color:#111;background:#fafafa}}
h1{{margin:0}} .counter{{font-size:2.2rem;font-weight:700}} .muted{{color:#666}}
.bar{{height:8px;background:#e5e7eb;border-radius:4px;overflow:hidden;margin:.3rem 0 .6rem}}
.bar div{{height:100%;background:#2563eb}} ol{{list-style:none;padding:0;margin:0}}
li{{padding:.15rem 0}} li[data-state=done]{{color:#6b7280}} li[data-state=done] .text{{text-decoration:line-through}}
li[data-state=skipped]{{color:#9a6700}} time{{color:#888;font-size:.85em}} .note{{color:#9a6700;font-size:.9em}}
code{{color:#2563eb}} section{{margin:1.2rem 0}} small{{font-weight:400;color:#666}}
</style>
<main data-manager-loop="1" data-started-at="{plan.started_at.isoformat()}" data-stall-minutes="{plan.stall_minutes}" data-rendered-at="{now.isoformat()}">
<h1>{e(plan.title or "Manager Loop")}</h1>
<div class="counter">{plan.done} / {plan.total} <small>({pct_all}%{f", {plan.skipped} skipped" if plan.skipped else ""})</small></div>
<div class="muted">{since} min since last activity · started {plan.started_at.strftime("%Y-%m-%d %H:%M UTC")} · rendered {now.strftime("%H:%M UTC")} · current phase: {current if current else "all done"}</div>
{_chart_svg(plan, now)}
{"".join(sections)}
</main>
"""


def save(dir_: Path, plan: Plan, now: datetime) -> Path:
    out = dir_ / DASHBOARD
    tmp = out.with_suffix(".html.tmp")
    tmp.write_text(render_html(plan, now), encoding="utf-8")
    os.replace(tmp, out)
    return out


# --- locking -----------------------------------------------------------------


@contextmanager
def _locked(dir_: Path, timeout_s: float = 5.0) -> Iterator[None]:
    """Cheap mutual exclusion for concurrent ticks from sub-agents (O_EXCL lock file)."""
    lock = dir_ / LOCK
    deadline = time.monotonic() + timeout_s
    while True:
        try:
            fd = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            os.close(fd)
            break
        except FileExistsError:
            if time.monotonic() > deadline:
                raise TimeoutError(f"could not acquire {lock} within {timeout_s}s") from None
            time.sleep(0.05)
    try:
        yield
    finally:
        lock.unlink(missing_ok=True)


# --- commands ----------------------------------------------------------------


def init(
    dir_: Path,
    seed: Path | None,
    now: datetime | None = None,
    stall_minutes: int = DEFAULT_STALL_MINUTES,
    force: bool = False,
) -> Path:
    """Create dashboard.html once from seed markdown (or a scaffold). Afterwards the page is the checklist."""
    dir_.mkdir(parents=True, exist_ok=True)
    out = dir_ / DASHBOARD
    if out.exists() and not force:
        raise FileExistsError(f"{out} exists; the page is the source of truth (use --force to reseed)")
    text = seed.read_text(encoding="utf-8") if seed else SCAFFOLD
    current = _now(now)
    return save(dir_, parse_seed(text, current, stall_minutes), current)


def _find_open(plan: Plan, pattern: str) -> Item:
    """Exact id first; then substring, preferring the current phase so repeated gate items resolve right."""
    for item in plan.items:
        if not item.settled and item.item_id == pattern:
            return item
    needle = pattern.casefold()
    ordered = sorted(plan.phases, key=lambda p: p.index != plan.current_phase)
    for phase in ordered:
        for item in phase.items:
            if not item.settled and needle in item.text.casefold():
                return item
    raise ItemNotFound(pattern)


def _settle(dir_: Path, pattern: str, state: str, note: str, now: datetime | None) -> Item:
    current = _now(now)
    with _locked(dir_):
        plan = load(dir_)
        item = _find_open(plan, pattern)
        item.state, item.at, item.note = state, current, note
        save(dir_, plan, current)
    return item


def tick(dir_: Path, pattern: str, now: datetime | None = None, note: str = "") -> Item:
    """Mark the first open item matching `pattern` done and record the time in the page."""
    return _settle(dir_, pattern, "done", note, now)


def skip(dir_: Path, pattern: str, note: str, now: datetime | None = None) -> Item:
    """Settle an item without doing it. The reason is written into the page next to the item."""
    if not note.strip():
        raise ValueError("skip needs a reason (--note)")
    return _settle(dir_, pattern, "skipped", note, now)


def status(dir_: Path, now: datetime | None = None, stall_minutes: int | None = None) -> dict[str, Any]:
    plan = load(dir_)
    current = _now(now)
    threshold = stall_minutes if stall_minutes is not None else plan.stall_minutes
    minutes = int((current - plan.last_activity).total_seconds() // 60)
    return {
        "title": plan.title,
        "total": plan.total,
        "done": plan.done,
        "skipped": plan.skipped,
        "remaining": plan.total - plan.settled,
        "percent": round(100 * plan.done / plan.total, 1) if plan.total else 0.0,
        "all_done": plan.all_done,
        "current_phase": plan.current_phase,
        "phases": [
            {
                "index": p.index,
                "title": p.title,
                "total": p.total,
                "done": p.done,
                "skipped": p.skipped,
                "complete": p.complete,
            }
            for p in plan.phases
        ],
        "skipped_items": [
            {"id": i.item_id, "text": i.text, "note": i.note} for i in plan.items if i.state == "skipped"
        ],
        "started_at": plan.started_at.isoformat(),
        "last_activity_at": plan.last_activity.isoformat(),
        "minutes_since_last_activity": minutes,
        "stall_minutes": threshold,
        "stalled": (not plan.all_done) and minutes >= threshold,
    }


def render(dir_: Path, now: datetime | None = None) -> Path:
    current = _now(now)
    return save(dir_, load(dir_), current)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dir", default=DEFAULT_DIR, help=f"work directory (default: ./{DEFAULT_DIR})")
    sub = ap.add_subparsers(dest="cmd", required=True)
    p_init = sub.add_parser("init")
    p_init.add_argument("--from", dest="seed", default=None, help="seed markdown (plan.md)")
    p_init.add_argument("--stall-minutes", type=int, default=DEFAULT_STALL_MINUTES)
    p_init.add_argument("--force", action="store_true")
    p_tick = sub.add_parser("tick")
    p_tick.add_argument("pattern", help="item id like 2.3, or case-insensitive substring of the item text")
    p_tick.add_argument("--note", default="")
    p_skip = sub.add_parser("skip")
    p_skip.add_argument("pattern")
    p_skip.add_argument("--note", required=True, help="why this item is settled without being done")
    p_status = sub.add_parser("status")
    p_status.add_argument("--stall-minutes", type=int, default=None, help="override the page's threshold")
    sub.add_parser("render")
    args = ap.parse_args(argv)
    dir_ = Path(args.dir)

    try:
        if args.cmd == "init":
            out = init(
                dir_,
                Path(args.seed) if args.seed else None,
                stall_minutes=args.stall_minutes,
                force=args.force,
            )
            print(f"seeded {out} (stall threshold {args.stall_minutes} min); open it in a browser")
        elif args.cmd == "tick":
            item = tick(dir_, args.pattern, note=args.note)
            st = status(dir_)
            print(
                f"ticked {item.item_id} {item.text!r} at {_fmt_time(item.at)} -> {st['done']}/{st['total']}"
            )
        elif args.cmd == "skip":
            item = skip(dir_, args.pattern, note=args.note)
            print(f"skipped {item.item_id} {item.text!r}: {item.note}")
        elif args.cmd == "status":
            print(json.dumps(status(dir_, stall_minutes=args.stall_minutes), ensure_ascii=False, indent=2))
        elif args.cmd == "render":
            print(render(dir_))
    except ItemNotFound as exc:
        print(f"no unchecked item matches {exc.args[0]!r}", file=sys.stderr)
        return 1
    except (FileExistsError, MalformedSeed, ValueError, TimeoutError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
