"""Keep provable-glossary usable on Windows.

Two things broke there (found on a Windows 11 machine with Git Bash, 2026-11-18):

- The edit-blocking hook compared paths with forward slashes only. Claude Code on
  Windows passes `C:\\...\\docs\\generated\\x.md`, so the hook let hand edits through.
- Quint 0.32.0 starts the Apalache server by spawning `apalache-mc.bat` without a
  shell, which Node and Bun refuse with EINVAL on Windows. The template's
  `quint-verify` entry therefore starts the server itself with `java`, waits until
  it accepts connections, and stops only the server it started.

The server handling is chosen by `os()` and can be forced with
`QUINT_APALACHE_SERVER=manage`, so these tests also run on the Linux CI.
"""

import json
import os
import shutil
import socket
import subprocess
import sys
import time
from pathlib import Path

import pytest

SKILL = Path(__file__).resolve().parents[2] / "provable-glossary"
TEMPLATE = SKILL / "assets" / "template"
HOOK = TEMPLATE / "dot-claude" / "hooks" / "protect_generated.py"
JUSTFILE = TEMPLATE / "justfile"
APALACHE = "0.56.1"
# The exit code with which a Claude Code hook stops a tool call.
HOOK_STOPS = 2
# The exit code the fake Quint returns when a test asks its verification to fail.
VERIFY_FAILS = 3


# ── the edit-blocking hook ──────────────────────────────────────────────────


def hook_exit(tool: str, tool_input: dict) -> int:
    call = {"tool_name": tool, "tool_input": tool_input}
    return subprocess.run(
        [sys.executable, "-I", str(HOOK)],
        input=json.dumps(call),
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
    ).returncode


@pytest.mark.parametrize(
    "path",
    [
        r"C:\repo\glossary\docs\generated\glossary.md",
        r"glossary\docs\generated\new.md",
        r"docs\generated\new.md",
        "C:/repo/glossary/docs/generated/glossary.md",
        "/repo/glossary/docs/generated/glossary.md",
        "docs/generated/new.md",
    ],
)
def test_hook_refuses_an_edit_of_a_generated_document_with_either_slash(
    path: str,
) -> None:
    assert hook_exit("Edit", {"file_path": path}) == HOOK_STOPS
    assert hook_exit("Write", {"file_path": path}) == HOOK_STOPS


@pytest.mark.parametrize(
    "path",
    [r"C:\repo\glossary\docs\findings.md", r"C:\repo\docs\generated-notes.md"],
)
def test_hook_lets_an_authored_document_through(path: str) -> None:
    assert hook_exit("Edit", {"file_path": path}) == 0


@pytest.mark.parametrize(
    "command",
    [
        r"echo x >> glossary\docs\generated\glossary.md",
        r"echo x > glossary\docs\generated\glossary.md",
        r"sed -i s/a/b/ glossary\docs\generated\glossary.md",
        r"rm glossary\docs\generated\glossary.md",
        r"cat notes.md | tee glossary\docs\generated\glossary.md",
        r"rm C:\\repo\\glossary\\docs\\generated\\glossary.md",
    ],
)
def test_hook_refuses_a_shell_rewrite_of_a_generated_document_with_backslashes(
    command: str,
) -> None:
    assert hook_exit("Bash", {"command": command}) == HOOK_STOPS


def test_hook_lets_a_read_of_a_generated_document_with_backslashes_through() -> None:
    assert (
        hook_exit("Bash", {"command": r"cat glossary\docs\generated\glossary.md"}) == 0
    )


# ── the quint-verify entry ──────────────────────────────────────────────────

FAKE_JAVA = r'''#!/usr/bin/env python3
"""A stand-in for `java -jar apalache.jar server --port=N`."""
import os, socket, sys, time
port = int(next(a.split("=", 1)[1] for a in sys.argv if a.startswith("--port=")))
beat = os.environ["FAKE_JAVA_HEARTBEAT"]
with open(os.environ["FAKE_JAVA_LOG"], "a") as log:
    log.write(" ".join(sys.argv[1:]) + "\n")
time.sleep(float(os.environ.get("FAKE_JAVA_DELAY", "0")))
server = None
if os.environ.get("FAKE_JAVA_NEVER") != "1":
    server = socket.socket()
    server.bind(("127.0.0.1", port))
    server.listen()
    server.settimeout(0.1)
while True:
    with open(beat, "a") as b:
        b.write(".")
    if server is None:
        time.sleep(0.1)
        continue
    try:
        server.accept()[0].close()
    except OSError:
        pass
'''

FAKE_QUINT = r'''#!/usr/bin/env python3
"""A stand-in for Quint: `verify --help`, and `verify` that needs a running server."""
import os, socket, sys
args = sys.argv[1:]
with open(os.environ["FAKE_QUINT_LOG"], "a") as log:
    log.write(" ".join(args) + "\n")
if args[:2] == ["verify", "--help"]:
    print('  --apalache-version     The version of Apalache to use, if no running server is')
    print('                         found (using this option may result in incompatibility)')
    print('                                                    [string] [default: "0.56.1"]')
    sys.exit(0)
endpoint = next((a.split("=", 1)[1] for a in args if a.startswith("--server-endpoint=")), "localhost:8822")
host, port = endpoint.rsplit(":", 1)
try:
    socket.create_connection((host, int(port)), timeout=1).close()
except OSError:
    print("error: spawn apalache-mc.bat EINVAL")
    sys.exit(1)
print("[ok] fake verification")
sys.exit(int(os.environ.get("FAKE_QUINT_EXIT", "0")))
'''


def free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def listening(port: int) -> bool:
    try:
        socket.create_connection(("127.0.0.1", port), timeout=0.5).close()
        return True
    except OSError:
        return False


def write_script(path: Path, text: str) -> None:
    path.write_text(text, encoding="utf-8", newline="\n")
    path.chmod(0o755)


class World:
    """A project folder with the template justfile, a fake java and quint, and an Apalache jar."""

    def __init__(self, tmp: Path, *, jar: bool = True) -> None:
        self.project = tmp / "project"
        self.project.mkdir()
        shutil.copy2(JUSTFILE, self.project / "justfile")
        (self.project / "quint-version").write_text("0.32.0\n", encoding="utf-8")
        bin_dir = tmp / "bin"
        bin_dir.mkdir()
        write_script(bin_dir / "java", FAKE_JAVA)
        write_script(bin_dir / "quint", FAKE_QUINT)
        self.home = tmp / "home"
        lib = self.home / ".quint" / f"apalache-dist-{APALACHE}" / "apalache" / "lib"
        lib.mkdir(parents=True)
        if jar:
            (lib / "apalache.jar").write_bytes(b"not a real jar")
        self.java_log = tmp / "java.log"
        self.quint_log = tmp / "quint.log"
        self.heartbeat = tmp / "heartbeat"
        self.port = free_port()
        self.env = {
            **os.environ,
            "PATH": os.pathsep.join([str(bin_dir), os.environ.get("PATH", "")]),
            "HOME": self.home.as_posix(),
            "QUINT": "quint",
            "QUINT_APALACHE_SERVER": "manage",
            "APALACHE_PORT": str(self.port),
            "APALACHE_WAIT_SECONDS": "10",
            "FAKE_JAVA_LOG": self.java_log.as_posix(),
            "FAKE_JAVA_HEARTBEAT": self.heartbeat.as_posix(),
            "FAKE_QUINT_LOG": self.quint_log.as_posix(),
        }

    def run(self, **env: str) -> subprocess.CompletedProcess:
        just = shutil.which("just")
        assert just is not None
        return subprocess.run(
            [just, "quint-verify", "--backend", "tlc", "--main=guarded", "spec.qnt"],
            cwd=self.project,
            env={**self.env, **env},
            capture_output=True,
            text=True,
            timeout=120,
            check=False,
        )

    def java_stopped(self) -> bool:
        """The fake server writes a heartbeat every 0.1 s while it lives."""
        if not self.heartbeat.exists():
            return True
        time.sleep(0.5)
        before = self.heartbeat.stat().st_size
        time.sleep(0.6)
        return self.heartbeat.stat().st_size == before

    def verify_calls(self) -> list[str]:
        if not self.quint_log.exists():
            return []
        return [
            line
            for line in self.quint_log.read_text(encoding="utf-8").splitlines()
            if line.startswith("verify ") and "--help" not in line
        ]


needs_just = pytest.mark.skipif(
    shutil.which("just") is None, reason="just is not installed"
)


@needs_just
def test_quint_verify_waits_for_a_slow_server_and_then_stops_it(tmp_path: Path) -> None:
    world = World(tmp_path)

    ran = world.run(FAKE_JAVA_DELAY="2")

    assert ran.returncode == 0, ran.stdout + ran.stderr
    assert "[ok] fake verification" in ran.stdout
    assert world.verify_calls() == [
        f"verify --server-endpoint=localhost:{world.port} --backend tlc --main=guarded spec.qnt"
    ]
    assert not listening(world.port)
    assert world.java_stopped()


@needs_just
def test_quint_verify_stops_the_server_it_started_when_verification_fails(
    tmp_path: Path,
) -> None:
    world = World(tmp_path)

    ran = world.run(FAKE_QUINT_EXIT=str(VERIFY_FAILS))

    assert ran.returncode == VERIFY_FAILS, ran.stdout + ran.stderr
    # The server was started and the verification ran against it, then it was stopped.
    assert world.java_log.exists()
    assert "[ok] fake verification" in ran.stdout
    assert not listening(world.port)
    assert world.java_stopped()


@needs_just
def test_quint_verify_uses_a_server_that_is_already_running_and_leaves_it(
    tmp_path: Path,
) -> None:
    world = World(tmp_path)
    with socket.socket() as theirs:
        theirs.bind(("127.0.0.1", world.port))
        theirs.listen()
        theirs.settimeout(0.1)

        ran = world.run()

        assert ran.returncode == 0, ran.stdout + ran.stderr
        assert not world.java_log.exists()
        assert listening(world.port)


@needs_just
def test_quint_verify_gives_up_on_a_server_that_never_listens(tmp_path: Path) -> None:
    world = World(tmp_path)

    ran = world.run(FAKE_JAVA_NEVER="1", APALACHE_WAIT_SECONDS="2")

    assert ran.returncode != 0
    assert "did not accept connections" in ran.stderr
    assert world.verify_calls() == []
    # It was started (its heartbeat exists) and then stopped.
    assert world.java_log.exists() and world.heartbeat.exists()
    assert world.java_stopped()


@needs_just
def test_quint_verify_refuses_to_let_quint_fetch_a_missing_apalache(
    tmp_path: Path,
) -> None:
    world = World(tmp_path, jar=False)

    ran = world.run()

    assert ran.returncode != 0
    assert "apalache.jar" in ran.stderr
    assert not world.java_log.exists()
    assert world.verify_calls() == []


@needs_just
def test_quint_verify_leaves_the_server_to_quint_outside_windows_unless_asked(
    tmp_path: Path,
) -> None:
    world = World(tmp_path)

    ran = world.run(QUINT_APALACHE_SERVER="quint")

    # Quint is called with the arguments as given; nothing starts a server.
    assert world.verify_calls() == ["verify --backend tlc --main=guarded spec.qnt"]
    assert not world.java_log.exists()
    assert (
        ran.returncode == 1
    )  # the fake Quint finds no server, as the real one on Windows


def test_the_template_manages_the_server_on_windows_and_spec_check_goes_through_it() -> (
    None
):
    text = JUSTFILE.read_text(encoding="utf-8")
    assert '"{{os()}}" == "windows"' in text or 'os() == "windows"' in text
    spec_check = text[
        text.index("\nspec-check:") : text.index("\n# Rebuild the generated documents")
    ]
    assert "quint-verify" in spec_check
    assert "{{quint}} verify" not in spec_check
    # just_executable() is a Windows path with backslashes there; unquoted, bash eats them
    # ("C:Usersabsin...just.exe: command not found", seen on Windows 11, 2026-11-18).
    assert "{{just_executable()}}" not in spec_check
    assert "{{quote(just_executable())}}" in spec_check
