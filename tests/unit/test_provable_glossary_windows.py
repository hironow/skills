"""Keep provable-glossary usable on Windows.

Four things broke there (found on a Windows 11 machine with Git Bash, 2026-11-18):

- The edit-blocking hook compared paths with forward slashes only. Claude Code on
  Windows passes `C:\\...\\docs\\generated\\x.md`, so the hook let hand edits through.
- Quint 0.32.0 starts the Apalache server by spawning `apalache-mc.bat` without a
  shell, which Node and Bun refuse with EINVAL on Windows. The template's
  `quint-verify` entry therefore starts the server itself with `java`, waits until
  it accepts connections, and stops only the server it started.
- The scripts and the hook handled text in the locale's encoding and line ending:
  cp932 and CRLF on a Japanese Windows. They now name UTF-8 and LF (or keep the
  line ending of a file they extend), as on Linux.
- The scripts wrote repository paths with str(), which uses backslashes there:
  anchors a Lean string rejects, a test-folder filter that missed, and git
  revisions (`commit:path`) that found nothing. They now use forward slashes.

The server handling is chosen by `os()` and can be forced with
`QUINT_APALACHE_SERVER=manage`, so these tests also run on the Linux CI.
"""

import ast
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
# A git hook exports these, and git would then act on the repository they name instead of the
# temporary folders these tests create.
GIT_REPOSITORY_VARS = (
    "GIT_DIR",
    "GIT_WORK_TREE",
    "GIT_INDEX_FILE",
    "GIT_COMMON_DIR",
    "GIT_OBJECT_DIRECTORY",
    "GIT_ALTERNATE_OBJECT_DIRECTORIES",
    "GIT_PREFIX",
)


@pytest.fixture(autouse=True)
def _no_repository_named_by_the_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    """Every subprocess here inherits os.environ; the git-hook test sets GIT_DIR itself."""
    for var in GIT_REPOSITORY_VARS:
        monkeypatch.delenv(var, raising=False)


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


def test_hook_reads_its_input_as_utf8_whatever_the_locale() -> None:
    """Claude Code sends UTF-8. Python 3.14 and older on a Japanese Windows decode a
    pipe as cp932, where "既存の" does not decode; the hook then crashed with exit 1,
    which Claude Code treats as "go ahead". PYTHONIOENCODING stands in for that
    locale on any system (the hook itself runs with -I, which ignores the variable)."""
    call = {
        "tool_name": "Bash",
        "tool_input": {"command": "echo 既存の > docs/generated/x.md"},
    }
    done = subprocess.run(
        [sys.executable, str(HOOK)],
        input=json.dumps(call, ensure_ascii=False).encode("utf-8"),
        capture_output=True,
        env={**os.environ, "PYTHONIOENCODING": "cp932"},
        timeout=60,
        check=False,
    )
    assert done.returncode == HOOK_STOPS, done.stderr.decode("utf-8", "replace")


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
            # The recipe's own default. A busy Windows machine once took more than 10 s
            # to start the fake server; the wait ends as soon as the server listens.
            "APALACHE_WAIT_SECONDS": "60",
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

    def explain(self, ran: subprocess.CompletedProcess) -> str:
        """What the run printed, and how far the fake server got (the recipe hides its output)."""
        started = self.java_log.exists()
        listened = self.heartbeat.exists()
        return f"{ran.stdout}{ran.stderr}fake java started: {started}; it listened: {listened}"

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

    assert ran.returncode == 0, world.explain(ran)
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

        assert ran.returncode == 0, world.explain(ran)
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


# ── text encodings and line endings ─────────────────────────────────────────
#
# Unless told otherwise, Python up to 3.14 handles text in the locale's encoding,
# which is cp932 on a Japanese Windows (UTF-8 Japanese does not decode there), and
# on Windows every version writes each "\n" as "\r\n". The scripts name both, so
# they do what they do on Linux.

SCRIPTS = SKILL / "scripts"


def run_init(repo: Path) -> None:
    """Run init_project.py so that a text read or write without an encoding fails,
    on Linux as well as on Windows."""
    done = subprocess.run(
        [
            sys.executable,
            "-I",
            "-X",
            "warn_default_encoding",
            "-W",
            "error::EncodingWarning",
            str(SCRIPTS / "init_project.py"),
            str(repo),
        ],
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=300,
        check=False,
    )
    assert done.returncode == 0, done.stderr


def test_init_extends_a_utf8_repository_and_keeps_its_line_endings(
    tmp_path: Path,
) -> None:
    """On a Japanese Windows, init_project.py could not read a justfile with Japanese
    in it (cp932), and Path.write_text turned every \\n into \\r\\n, so adding
    `mod glossary` rewrote a whole LF justfile (and .gitignore, settings.json) as
    CRLF. A test of that repository that split the justfile on blank lines then
    read it as one recipe (m4k3-co/.gpus, 2026-11-18)."""
    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(["git", "init", "-q", str(repo)], check=True)
    (repo / "go.mod").write_bytes(b"module example\n")
    (repo / "justfile").write_bytes(
        "# 既存の recipe\nbuild:\n    echo build\n".encode()
    )
    (repo / ".gitignore").write_bytes(b"/out/\n")
    (repo / ".claude").mkdir()
    (repo / ".claude" / "settings.json").write_bytes(
        '{\n  "env": {"NOTE": "既存"}\n}\n'.encode()
    )

    run_init(repo)

    for rel in [
        "justfile",
        ".gitignore",
        ".claude/settings.json",
        ".githooks/pre-commit",
    ]:
        assert b"\r" not in (repo / rel).read_bytes(), rel
    justfile = (repo / "justfile").read_bytes().decode("utf-8")
    assert justfile.startswith("# 既存の recipe\nbuild:\n    echo build\n")
    assert justfile.endswith("\nmod glossary\n")
    assert (repo / ".gitignore").read_bytes() == b"/out/\n/glossary-scan/\n"
    settings = json.loads((repo / ".claude" / "settings.json").read_bytes())
    assert settings["env"] == {"NOTE": "既存"}
    assert "protect_generated.py" in json.dumps(settings["hooks"])


def test_init_keeps_a_crlf_justfile_crlf(tmp_path: Path) -> None:
    """A justfile kept in CRLF stays CRLF, and the lines added match it."""
    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(["git", "init", "-q", str(repo)], check=True)
    (repo / "justfile").write_bytes(b"build:\r\n    echo build\r\n")

    run_init(repo)

    data = (repo / "justfile").read_bytes()
    assert data.startswith(b"build:\r\n    echo build\r\n")
    assert data.endswith(b"\r\nmod glossary\r\n")
    assert b"\n" not in data.replace(b"\r\n", b"")


def test_init_appends_to_a_file_of_mixed_line_endings_without_rewriting_it(
    tmp_path: Path,
) -> None:
    """One CRLF line must not turn the whole file into CRLF: a shebang ending in
    "\\r" no longer runs on Linux. The file's bytes stay as they are, and the added
    line ends in "\\n" unless every line of the file ends in "\\r\\n"."""
    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(["git", "init", "-q", str(repo)], check=True)
    hook = repo / ".githooks" / "pre-commit"
    hook.parent.mkdir()
    original = b"#!/usr/bin/env bash\n# a note\r\necho ok\n"
    hook.write_bytes(original)

    run_init(repo)

    assert hook.read_bytes() == original + b"just generated-check\n"


def run_import(source: Path, project: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        [
            sys.executable,
            "-I",
            str(SCRIPTS / "import_glossary.py"),
            str(source),
            "--project",
            str(project),
        ],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=120,
        check=False,
    )


def test_import_stops_on_a_glossary_that_is_not_utf8(tmp_path: Path) -> None:
    """A glossary saved in cp932 imported as replacement characters (or, on a Japanese
    Windows, by luck as text). It now stops, names the file, and writes nothing."""
    source = tmp_path / "legacy.tsv"
    source.write_bytes("term\tdefinition\n猫\t動物\n".encode("cp932"))
    project = tmp_path / "project"
    project.mkdir()

    done = run_import(source, project)

    assert done.returncode != 0
    assert "legacy.tsv" in done.stderr
    assert "UTF-8" in done.stderr
    assert not (project / "migration").exists()


def test_import_reads_a_utf8_glossary(tmp_path: Path) -> None:
    source = tmp_path / "legacy.tsv"
    source.write_bytes("term\tdefinition\n猫\t動物\n".encode())
    project = tmp_path / "project"
    project.mkdir()

    done = run_import(source, project)

    assert done.returncode == 0, done.stderr
    legacy = (project / "migration" / "legacy.tsv").read_bytes().decode("utf-8")
    assert legacy == "term\tdefinition\n猫\t動物\n"


def called_name(call: ast.Call) -> tuple[str, int] | None:
    """The name of what is called, and where its mode argument sits: first for
    `path.open(mode)`, second for `open(file, mode)` and `io.open(file, mode)`."""
    if isinstance(call.func, ast.Attribute):
        owner = call.func.value
        takes_file_first = isinstance(owner, ast.Name) and owner.id in {
            "io",
            "builtins",
        }
        return call.func.attr, 1 if takes_file_first else 0
    if isinstance(call.func, ast.Name):
        return call.func.id, 1
    return None


def open_mode(call: ast.Call, at: int) -> str:
    given = next(
        (k.value for k in call.keywords if k.arg == "mode"),
        call.args[at] if len(call.args) > at else None,
    )
    if isinstance(given, ast.Constant) and isinstance(given.value, str):
        return given.value
    return "r"


def unnamed_text_io(source: str) -> list[str]:
    """The calls that handle text without naming its encoding, or write text
    without naming its line ending."""
    found = []
    for node in ast.walk(ast.parse(source)):
        if not isinstance(node, ast.Call) or (called := called_name(node)) is None:
            continue
        name, at = called
        mode = open_mode(node, at) if name == "open" else ""
        if "b" in mode:
            continue
        need = set()
        if name in {"read_text", "write_text", "open"} or any(
            k.arg == "text" for k in node.keywords
        ):
            need.add("encoding")
        if name == "write_text" or set(mode) & set("wax+"):
            need.add("newline")
        if missing := need - {k.arg for k in node.keywords}:
            found.append(
                f"line {node.lineno}: {name}() names no {' or '.join(sorted(missing))}"
            )
    return found


def test_the_check_finds_text_handled_in_the_locale_encoding() -> None:
    source = "\n".join(
        [
            'p.read_text(errors="replace")',
            'p.write_text(s, encoding="utf-8")',
            'out.open("a")',
            "subprocess.run(c, text=True)",
            'p.read_text(encoding="utf-8")',
            'p.write_text(s, encoding="utf-8", newline="\\n")',
            'open(f, "rb")',
            'io.open("blob.txt", "w")',
        ]
    )
    assert unnamed_text_io(source) == [
        "line 1: read_text() names no encoding",
        "line 2: write_text() names no newline",
        "line 3: open() names no encoding or newline",
        "line 4: run() names no encoding",
        "line 8: open() names no encoding or newline",
    ]


@pytest.mark.parametrize("script", sorted(SCRIPTS.glob("*.py")), ids=lambda p: p.name)
def test_every_script_names_the_encoding_and_line_ending_of_its_text(
    script: Path,
) -> None:
    assert unnamed_text_io(script.read_text(encoding="utf-8")) == []


# ── repository paths ────────────────────────────────────────────────────────
#
# On Windows, str() of a path joins its parts with backslashes. Anchors, git
# revisions (`commit:path`) and the path filters all want forward slashes.


def test_scan_terms_writes_anchors_with_forward_slashes_and_skips_tests(
    tmp_path: Path,
) -> None:
    """On Windows the anchors read `src\\app\\state.go#...`, which a Lean string
    rejects (`\\a` is no escape), and the filter for test folders, written with
    "/", let `src/tests/` through."""
    repo = tmp_path / "repo"
    (repo / "src" / "app").mkdir(parents=True)
    (repo / "src" / "tests").mkdir()
    (repo / "src" / "app" / "state.go").write_bytes(
        b"package app\n\nfunc PlaceHold() {}\n"
    )
    (repo / "src" / "tests" / "helper.go").write_bytes(
        b"package tests\n\nfunc HelperOnly() {}\n"
    )

    done = subprocess.run(
        [sys.executable, "-I", str(SCRIPTS / "scan_terms.py"), str(repo)],
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=120,
        check=False,
    )

    assert done.returncode == 0, done.stderr
    scan = repo / "glossary-scan"
    identifiers = (scan / "identifiers.tsv").read_bytes().decode("utf-8")
    assert "src/app/state.go#func PlaceHold" in identifiers
    assert "HelperOnly" not in identifiers
    assert "\\" not in identifiers
    words = (scan / "words.tsv").read_bytes().decode("utf-8")
    assert "\tsrc/app\t" in words


def test_scan_terms_reads_a_repository_that_sits_in_a_folder_named_tests(
    tmp_path: Path,
) -> None:
    """The test-folder filter looks at the path inside the repository only; a
    repository under `.../tests/shop/` is not a test folder."""
    repo = tmp_path / "tests" / "shop"
    (repo / "src").mkdir(parents=True)
    (repo / "src" / "app.go").write_bytes(b"package app\n\nfunc PlaceHold() {}\n")

    done = subprocess.run(
        [sys.executable, "-I", str(SCRIPTS / "scan_terms.py"), str(repo)],
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=120,
        check=False,
    )

    assert done.returncode == 0, done.stderr
    identifiers = (repo / "glossary-scan" / "identifiers.tsv").read_bytes().decode()
    assert "src/app.go#func PlaceHold" in identifiers


def test_shared_files_finds_the_earlier_versions_of_a_template_file(
    tmp_path: Path,
) -> None:
    """`git show <commit>:<path>` wants forward slashes. With the backslashes of
    str() on Windows every lookup failed, so only the current template counted and
    status.py called a project made from an earlier template "changed"."""
    repo = tmp_path / "skill"
    template = repo / "assets" / "template"
    (template / "Glossary").mkdir(parents=True)
    subprocess.run(["git", "init", "-q", str(repo)], check=True)
    core = template / "Glossary" / "Core.lean"
    for version in (b"-- one\n", b"-- two\n"):
        core.write_bytes(version)
        subprocess.run(["git", "-C", str(repo), "add", "-A"], check=True)
        subprocess.run(
            [
                "git",
                "-C",
                str(repo),
                "-c",
                "user.name=t",
                "-c",
                "user.email=t@example.invalid",
                "commit",
                "-q",
                "-m",
                version.decode().strip(),
            ],
            check=True,
        )
    probe = (
        "import pathlib, sys\n"
        f"sys.path.insert(0, {str(SCRIPTS)!r})\n"
        "import shared_files\n"
        "found = shared_files.template_versions(pathlib.Path(sys.argv[1]), 'Glossary/Core.lean')\n"
        "print(sorted(v.decode() for v in found))\n"
    )

    done = subprocess.run(
        [sys.executable, "-I", "-c", probe, str(template)],
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=120,
        check=False,
    )

    assert done.returncode == 0, done.stderr
    assert done.stdout.strip() == repr(["-- one\n", "-- two\n"])


def str_of_relative_path(source: str) -> list[str]:
    """`str(x.relative_to(y))`: a repository path written with backslashes on Windows."""
    found = []
    for node in ast.walk(ast.parse(source)):
        if (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id == "str"
            and node.args
            and isinstance(inner := node.args[0], ast.Call)
            and isinstance(inner.func, ast.Attribute)
            and inner.func.attr == "relative_to"
        ):
            found.append(f"line {node.lineno}: str() of relative_to(); use .as_posix()")
    return found


def test_the_check_finds_a_relative_path_written_with_str() -> None:
    source = "a = str(p.relative_to(root))\nb = p.relative_to(root).as_posix()\n"
    assert str_of_relative_path(source) == [
        "line 1: str() of relative_to(); use .as_posix()"
    ]


@pytest.mark.parametrize("script", sorted(SCRIPTS.glob("*.py")), ids=lambda p: p.name)
def test_every_script_writes_repository_paths_with_forward_slashes(
    script: Path,
) -> None:
    assert str_of_relative_path(script.read_text(encoding="utf-8")) == []


# ── the gate inside a git hook ──────────────────────────────────────────────
#
# Git exports GIT_DIR to its hooks, and with GIT_DIR set and no GIT_WORK_TREE,
# git takes the current folder for the top of the work tree. A pre-commit hook
# that runs the whole gate therefore ran anchor-check with the project folder as
# the "repository root", and every anchor said "no such file" (m4k3-co/.gpus,
# 2026-11-18). This is not about Windows; it happens wherever a hook runs it.

FAKE_LAKE = r"""#!/usr/bin/env python3
# A stand-in for `lake exe claims anchors`: one term and one anchor at the repository root.
import sys
if sys.argv[1:] == ["exe", "claims", "anchors"]:
    print("slot\tsrc/app.go#func PlaceHold")
    sys.exit(0)
sys.exit(2)
"""


needs_rg = pytest.mark.skipif(
    shutil.which("rg") is None, reason="ripgrep is not installed (anchor-check uses it)"
)


@needs_just
@needs_rg
def test_anchor_check_finds_the_repository_root_inside_a_git_hook(
    tmp_path: Path,
) -> None:
    repo = tmp_path / "repo"
    project = repo / "glossary"
    project.mkdir(parents=True)
    subprocess.run(["git", "init", "-q", str(repo)], check=True)
    (repo / "src").mkdir()
    (repo / "src" / "app.go").write_bytes(b"package app\n\nfunc PlaceHold() {}\n")
    shutil.copy2(JUSTFILE, project / "mod.just")
    (project / "quint-version").write_text("0.32.0\n", encoding="utf-8")
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    write_script(bin_dir / "lake", FAKE_LAKE)
    git_dir = subprocess.run(
        ["git", "-C", str(repo), "rev-parse", "--absolute-git-dir"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=True,
    ).stdout.strip()
    just = shutil.which("just")
    assert just is not None

    done = subprocess.run(
        [
            just,
            "--justfile",
            str(project / "mod.just"),
            "--working-directory",
            str(project),
            "anchor-check",
        ],
        env={
            **os.environ,
            "PATH": os.pathsep.join([str(bin_dir), os.environ.get("PATH", "")]),
            "GIT_DIR": git_dir,
        },
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=120,
        check=False,
    )

    assert done.returncode == 0, done.stdout + done.stderr
    assert "1 anchors resolve" in done.stdout


def test_the_recipes_that_ask_git_ignore_the_hook_environment() -> None:
    """control-check reads git history by path, with the same hook problem."""
    text = JUSTFILE.read_text(encoding="utf-8")
    for recipe in ("\nanchor-check:", "\ncontrol-check:"):
        start = text.index(recipe)
        body = text[start : text.index("\n\n", start + 1)]
        assert "unset GIT_DIR GIT_WORK_TREE GIT_INDEX_FILE" in body, recipe


def test_the_git_calls_leave_a_repository_named_by_the_environment_alone(
    tmp_path: Path,
) -> None:
    """Run inside a git hook, these tests inherit GIT_DIR and GIT_WORK_TREE. Their git calls in
    temporary folders must not commit to the repository those name."""
    decoy = tmp_path / "decoy"
    subprocess.run(["git", "init", "-q", str(decoy)], check=True)
    (decoy / "kept.txt").write_text("kept\n", encoding="utf-8")
    ident = ["-c", "user.name=t", "-c", "user.email=t@example.invalid"]
    subprocess.run(["git", "-C", str(decoy), "add", "-A"], check=True)
    subprocess.run(
        ["git", "-C", str(decoy), *ident, "commit", "-q", "-m", "one"], check=True
    )

    done = subprocess.run(
        [
            sys.executable,
            "-m",
            "pytest",
            "-q",
            "-p",
            "no:cacheprovider",
            f"{Path(__file__).resolve()}::test_shared_files_finds_the_earlier_versions_of_a_template_file",
        ],
        env={**os.environ, "GIT_DIR": str(decoy / ".git"), "GIT_WORK_TREE": str(decoy)},
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=300,
        check=False,
    )

    assert done.returncode == 0, done.stdout + done.stderr
    count = subprocess.run(
        ["git", "-C", str(decoy), "rev-list", "--count", "HEAD"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=True,
    ).stdout.strip()
    assert count == "1"
