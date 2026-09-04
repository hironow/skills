"""Unit tests for manager_loop_dashboard.py (stdlib unittest, no deps).

Run:  python3 -m unittest discover -s skills/manager-loop/scripts -p 'test_*.py'
"""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from datetime import UTC, datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import manager_loop_dashboard as mld

SEED = """# Build a tiny civilization

## Phase 1: World
- [ ] Terrain renders
- [x] Water has physics
- [ ] `just check` green

## Phase 2: People
- [ ] Two people talk
- [ ] `just check` green
"""

T0 = datetime(2026, 9, 4, 12, 0, tzinfo=UTC)


class Workspace(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self.tmp.name)
        (self.dir / "plan.md").write_text(SEED)
        self.page = mld.init(self.dir, seed=self.dir / "plan.md", now=T0, stall_minutes=30)

    def tearDown(self) -> None:
        self.tmp.cleanup()


class InitTest(Workspace):
    def test_init_writes_html_as_the_single_source_of_truth(self) -> None:
        self.assertEqual(self.page.name, "dashboard.html")
        plan = mld.load(self.dir)
        self.assertEqual(plan.title, "Build a tiny civilization")
        self.assertEqual([p.title for p in plan.phases], ["World", "People"])
        self.assertEqual([i.item_id for i in plan.phases[0].items], ["1.1", "1.2", "1.3"])
        self.assertEqual(plan.phases[0].items[1].state, "done")
        self.assertEqual(plan.phases[0].items[1].at, T0)  # pre-checked seed items get the init time
        self.assertEqual(plan.started_at, T0)
        self.assertEqual(plan.stall_minutes, 30)
        self.assertFalse((self.dir / "events.jsonl").exists())
        self.assertFalse((self.dir / "checklist.md").exists())

    def test_init_refuses_to_overwrite_without_force(self) -> None:
        with self.assertRaises(FileExistsError):
            mld.init(self.dir, seed=self.dir / "plan.md", now=T0)

    def test_init_rejects_non_consecutive_phase_numbers(self) -> None:
        bad = SEED.replace("## Phase 2:", "## Phase 7:")
        (self.dir / "bad.md").write_text(bad)
        with self.assertRaises(mld.MalformedSeed):
            mld.init(self.dir, seed=self.dir / "bad.md", now=T0, force=True)

    def test_init_without_seed_writes_scaffold(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            mld.init(Path(d), seed=None, now=T0)
            plan = mld.load(Path(d))
            self.assertGreaterEqual(len(plan.phases), 1)


class TickTest(Workspace):
    def test_tick_by_id_records_state_and_time_in_html(self) -> None:
        item = mld.tick(self.dir, "1.1", now=T0 + timedelta(minutes=3))
        self.assertEqual(item.item_id, "1.1")
        html = self.page.read_text()
        self.assertIn('data-id="1.1" data-state="done" data-at="2026-09-04T12:03:00+00:00"', html)
        self.assertIn("12:03", html)  # the time is visible on the page, not only in attributes
        plan = mld.load(self.dir)
        self.assertEqual(plan.done, 2)

    def test_tick_substring_prefers_current_phase(self) -> None:
        item = mld.tick(self.dir, "just check", now=T0)
        self.assertEqual(item.item_id, "1.3")  # not 2.2, even though both match

    def test_tick_substring_is_case_insensitive(self) -> None:
        self.assertEqual(mld.tick(self.dir, "TERRAIN", now=T0).item_id, "1.1")

    def test_tick_unknown_or_already_done_raises(self) -> None:
        with self.assertRaises(mld.ItemNotFound):
            mld.tick(self.dir, "dragons", now=T0)
        with self.assertRaises(mld.ItemNotFound):
            mld.tick(self.dir, "1.2", now=T0)

    def test_skip_records_reason_and_counts_as_settled(self) -> None:
        item = mld.skip(self.dir, "1.1", note="needs GPU we do not have", now=T0 + timedelta(minutes=9))
        self.assertEqual(item.state, "skipped")
        html = self.page.read_text()
        self.assertIn('data-state="skipped"', html)
        self.assertIn("needs GPU we do not have", html)
        plan = mld.load(self.dir)
        self.assertEqual(plan.done, 1)
        self.assertEqual(plan.settled, 2)


class StatusTest(Workspace):
    def test_status_uses_stored_stall_threshold(self) -> None:
        s = mld.status(self.dir, now=T0 + timedelta(minutes=10))
        self.assertEqual((s["done"], s["skipped"], s["total"]), (1, 0, 5))
        self.assertEqual(s["current_phase"], 1)
        self.assertEqual(s["minutes_since_last_activity"], 10)
        self.assertEqual(s["stall_minutes"], 30)
        self.assertFalse(s["stalled"])
        self.assertTrue(mld.status(self.dir, now=T0 + timedelta(minutes=31))["stalled"])

    def test_stall_clock_resets_on_tick_and_skip(self) -> None:
        mld.tick(self.dir, "1.1", now=T0 + timedelta(minutes=25))
        self.assertFalse(mld.status(self.dir, now=T0 + timedelta(minutes=50))["stalled"])
        mld.skip(self.dir, "1.3", note="later", now=T0 + timedelta(minutes=55))
        self.assertEqual(
            mld.status(self.dir, now=T0 + timedelta(minutes=60))["minutes_since_last_activity"], 5
        )

    def test_skipped_items_let_the_phase_and_run_complete(self) -> None:
        mld.tick(self.dir, "1.1", now=T0)
        mld.skip(self.dir, "1.3", note="flaky gate", now=T0)
        s = mld.status(self.dir, now=T0)
        self.assertTrue(s["phases"][0]["complete"])
        self.assertEqual(s["current_phase"], 2)
        mld.tick(self.dir, "2.1", now=T0)
        mld.tick(self.dir, "2.2", now=T0)
        s = mld.status(self.dir, now=T0 + timedelta(hours=9))
        self.assertTrue(s["all_done"])
        self.assertIsNone(s["current_phase"])
        self.assertFalse(s["stalled"])
        self.assertEqual(
            s["skipped_items"], [{"id": "1.3", "text": "`just check` green", "note": "flaky gate"}]
        )

    def test_status_override_threshold(self) -> None:
        self.assertTrue(mld.status(self.dir, now=T0 + timedelta(minutes=6), stall_minutes=5)["stalled"])


class RenderTest(Workspace):
    def test_page_is_self_contained_with_counter_and_chart(self) -> None:
        mld.tick(self.dir, "1.1", now=T0 + timedelta(minutes=3))
        html = self.page.read_text()
        self.assertIn("2 / 5", html)
        self.assertIn("<svg", html)
        self.assertIn("<polyline", html)
        self.assertIn("Terrain renders", html)
        self.assertNotIn("<script src=", html)
        self.assertIn('http-equiv="refresh"', html)

    def test_roundtrip_preserves_html_special_characters(self) -> None:
        (self.dir / "plan.md").write_text('# A <b> & c\n\n## Phase 1: X\n- [ ] use <div> & "quotes"\n')
        mld.init(self.dir, seed=self.dir / "plan.md", now=T0, force=True)
        plan = mld.load(self.dir)
        self.assertEqual(plan.title, "A <b> & c")
        self.assertEqual(plan.phases[0].items[0].text, 'use <div> & "quotes"')
        mld.tick(self.dir, "quotes", now=T0)
        self.assertEqual(mld.load(self.dir).phases[0].items[0].state, "done")


class CliSmokeTest(unittest.TestCase):
    def test_cli_roundtrip(self) -> None:
        script = Path(__file__).resolve().parent / "manager_loop_dashboard.py"
        with tempfile.TemporaryDirectory() as d:
            dir_ = Path(d)
            (dir_ / "plan.md").write_text(SEED)
            base = [sys.executable, str(script), "--dir", str(dir_)]
            subprocess.run([*base, "init", "--from", str(dir_ / "plan.md")], check=True, capture_output=True)
            r = subprocess.run([*base, "tick", "water"], check=False, capture_output=True, text=True)
            self.assertEqual(r.returncode, 1)  # already done in the seed
            self.assertIn("no unchecked item", r.stderr)
            r = subprocess.run([*base, "tick", "1.1"], check=True, capture_output=True, text=True)
            self.assertIn("1.1", r.stdout)
            r = subprocess.run(
                [*base, "skip", "1.3", "--note", "later"], check=True, capture_output=True, text=True
            )
            self.assertIn("skipped 1.3", r.stdout)
            r = subprocess.run([*base, "status"], check=True, capture_output=True, text=True)
            s = json.loads(r.stdout)
            self.assertEqual((s["done"], s["skipped"], s["current_phase"]), (2, 1, 2))


if __name__ == "__main__":
    unittest.main()
