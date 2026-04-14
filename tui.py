#!/usr/bin/env python3
"""HyperAgents Terminal Control Panel — rich-based TUI"""
import os, sys, subprocess, time, json, shutil, importlib, urllib.request, urllib.error
from dataclasses import dataclass, field
from typing import Optional, List
from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.columns import Columns
from rich.rule import Rule
from rich.prompt import Prompt, Confirm
from rich.spinner import Spinner
from rich.live import Live
from rich import box

# ── Paths ─────────────────────────────────────────────────────────────────────

ROOT        = Path(__file__).parent
PYTHON_DIR  = ROOT / "python"
RUST_COMMS  = ROOT / "rust" / "target" / "release" / "hyperagents-comms"
RUST_TASK   = ROOT / "rust" / "target" / "release" / "hyperagents"
VENV_PY     = ROOT / "venv" / "bin" / "python"
PYTHON_BIN  = str(VENV_PY) if VENV_PY.exists() else sys.executable

console = Console()

# ── Prerequisite checks ───────────────────────────────────────────────────────

@dataclass
class DepCheck:
    name:       str
    ok:         bool
    detail:     str            # shown in the status line
    fixable:    bool  = False  # can TUI offer to fix it?
    fix_label:  str   = ""     # "Install via brew", "Build binaries", …
    fix_cmd:    list  = field(default_factory=list)   # shell command to run
    fix_cwd:    str   = ""
    warning:    bool  = False  # ok=True but something to note

IS_MACOS = sys.platform == "darwin"
HAS_BREW  = shutil.which("brew") is not None

def _run_quiet(cmd: list[str], cwd: str | None = None) -> tuple[int, str]:
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=10, cwd=cwd)
        return r.returncode, (r.stdout + r.stderr).strip()
    except Exception as e:
        return -1, str(e)

def _check_ollama() -> DepCheck:
    binary = shutil.which("ollama")
    if not binary:
        fix_cmd = ["brew", "install", "ollama"] if HAS_BREW else []
        return DepCheck(
            "ollama", False,
            "not found — needed for  --model ollama/…",
            fixable=HAS_BREW,
            fix_label="brew install ollama",
            fix_cmd=fix_cmd,
        )
    rc, out = _run_quiet(["ollama", "--version"])
    version = out.split()[-1] if out else "?"

    # Check if daemon is running
    running = False
    model_count = 0
    try:
        with urllib.request.urlopen(
            "http://localhost:11434/api/tags", timeout=2
        ) as resp:
            data = json.loads(resp.read())
            model_count = len(data.get("models", []))
            running = True
    except Exception:
        pass

    if running:
        detail = f"{version}  ·  running  ({model_count} model{'s' if model_count != 1 else ''})"
        return DepCheck("ollama", True, detail)
    else:
        return DepCheck(
            "ollama", True,
            f"{version}  ·  installed but NOT running",
            warning=True,
            fixable=True,
            fix_label="start ollama service",
            fix_cmd=["ollama", "serve"],
            fix_cwd="",
        )

def _check_llamacpp() -> DepCheck:
    binary = shutil.which("llama-server")
    if not binary:
        fix_cmd = ["brew", "install", "llama.cpp"] if HAS_BREW else []
        return DepCheck(
            "llama-server (llama.cpp)", False,
            "not found — needed for  --model llamacpp/…",
            fixable=HAS_BREW,
            fix_label="brew install llama.cpp",
            fix_cmd=fix_cmd,
        )
    rc, out = _run_quiet(["llama-server", "--version"])
    # version buried in output; just confirm it runs
    detail = Path(binary).parent.parent.name   # e.g. Cellar/llama.cpp/…
    return DepCheck("llama-server (llama.cpp)", True, f"found at {binary}")

def _check_cargo() -> DepCheck:
    binary = shutil.which("cargo")
    if not binary:
        fix_cmd = ["brew", "install", "rust"] if HAS_BREW else []
        return DepCheck(
            "cargo (Rust)", False,
            "not found — needed to build Rust binaries",
            fixable=HAS_BREW,
            fix_label="brew install rust",
            fix_cmd=fix_cmd,
        )
    rc, out = _run_quiet(["cargo", "--version"])
    version = out.split()[1] if " " in out else out
    return DepCheck("cargo (Rust)", True, version)

def _check_rust_binaries() -> DepCheck:
    comms_ok = RUST_COMMS.exists()
    task_ok  = RUST_TASK.exists()
    if comms_ok and task_ok:
        return DepCheck("Rust binaries", True, "hyperagents + hyperagents-comms  ✓")
    missing = []
    if not comms_ok: missing.append("hyperagents-comms")
    if not task_ok:  missing.append("hyperagents")
    cargo_ok = shutil.which("cargo") is not None
    return DepCheck(
        "Rust binaries", False,
        f"not built: {', '.join(missing)}",
        fixable=cargo_ok,
        fix_label="cargo build --release",
        fix_cmd=["cargo", "build", "--release", "--bins"],
        fix_cwd=str(ROOT / "rust"),
    )

def _check_python_deps() -> DepCheck:
    required = ["requests", "litellm", "pandas", "git", "dotenv"]
    missing = []
    for mod in required:
        try:
            importlib.import_module(mod)
        except ImportError:
            missing.append(mod)
    if not missing:
        return DepCheck("Python deps", True, "requests  litellm  pandas  gitpython  dotenv")
    return DepCheck(
        "Python deps", False,
        f"missing: {', '.join(missing)}",
        fixable=True,
        fix_label=f"pip install -r requirements.txt",
        fix_cmd=[PYTHON_BIN, "-m", "pip", "install", "-r", str(ROOT / "requirements.txt")],
    )

def run_checks() -> List[DepCheck]:
    return [
        _check_ollama(),
        _check_llamacpp(),
        _check_cargo(),
        _check_python_deps(),
        _check_rust_binaries(),
    ]

def _install_dep(dep: DepCheck) -> bool:
    """Run the fix command for a dep, streaming output. Returns True on success."""
    if not dep.fix_cmd:
        return False

    # Special case: ollama serve — launch in background
    if dep.fix_cmd == ["ollama", "serve"]:
        console.print(f"\n  [dim]Launching ollama in the background…[/]")
        subprocess.Popen(
            ["ollama", "serve"],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            start_new_session=True,
        )
        time.sleep(2)
        # verify
        try:
            urllib.request.urlopen("http://localhost:11434/api/tags", timeout=3)
            return True
        except Exception:
            return False

    console.print(f"\n  [dim]$ {' '.join(dep.fix_cmd)}[/]")
    console.print()
    cwd = dep.fix_cwd or None
    proc = subprocess.Popen(
        dep.fix_cmd, cwd=cwd,
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        text=True, bufsize=1,
    )
    for line in proc.stdout:
        console.print(f"  [dim]{line.rstrip()}[/]", highlight=False, markup=False)
    proc.wait()
    return proc.returncode == 0

def show_prereq_screen(force: bool = False):
    """Run prerequisite checks and offer to fix issues. Skip if all ok and not forced."""
    console.clear()
    console.print(Panel(
        Text("System Check", justify="center", style="bold white"),
        border_style="bright_white", padding=(0, 2),
    ))
    console.print()

    # Run checks with a spinner
    checks: List[DepCheck] = []
    with Live(
        Text("  Checking…", style="dim"), refresh_per_second=8, console=console
    ) as live:
        checks = run_checks()
        live.update(Text(""))

    # Render results table
    t = Table(box=box.SIMPLE, show_header=False, padding=(0, 2), expand=False)
    t.add_column("icon",   width=3,  no_wrap=True)
    t.add_column("name",   style="white",        no_wrap=True, min_width=28)
    t.add_column("detail", style="dim",          no_wrap=True)

    all_ok = True
    for dep in checks:
        if dep.ok and not dep.warning:
            icon = "[bold green]✓[/]"
        elif dep.warning:
            icon = "[bold yellow]⚠[/]"
            all_ok = False
        else:
            icon = "[bold red]✗[/]"
            all_ok = False
        t.add_row(icon, dep.name, dep.detail)

    console.print(t)

    if all_ok and not force:
        console.print("  [dim green]All prerequisites satisfied.[/]")
        console.print()
        return

    # Offer fixes for broken deps
    problems = [d for d in checks if not d.ok or d.warning]
    if problems:
        console.print()
        console.print(Rule("[yellow]Issues found[/]", style="yellow"))
        console.print()

        for dep in problems:
            if not dep.fixable:
                console.print(
                    f"  [red]✗[/]  [white]{dep.name}[/]  —  {dep.detail}\n"
                    f"     [dim]Manual install required. See README for instructions.[/]"
                )
                console.print()
                continue

            label = dep.fix_label or " ".join(dep.fix_cmd)
            style = "yellow" if dep.warning else "red"
            console.print(f"  [{style}]{'⚠' if dep.warning else '✗'}[/]  [white]{dep.name}[/]  —  {dep.detail}")

            try:
                do_fix = Confirm.ask(f"     Fix now?  [dim]({label})[/]", default=True)
            except (KeyboardInterrupt, EOFError):
                do_fix = False

            if do_fix:
                ok = _install_dep(dep)
                if ok:
                    console.print(f"  [green]  ✓  Done.[/]")
                else:
                    console.print(f"  [red]  ✗  Failed — check output above.[/]")
            console.print()

    console.print("[dim]Press Enter to continue.[/]")
    try:
        input()
    except (KeyboardInterrupt, EOFError):
        pass


# ── Settings ──────────────────────────────────────────────────────────────────

@dataclass
class Settings:
    model:            str = "ollama/llama3.2"
    overseer_model:   str = ""          # empty → same as model
    rounds:           int = 4
    exchanges:        int = 3
    workers:          int = 4
    samples:          int = -1
    generations:      int = 5
    parent_selection: str = "best"
    rust_output_dir:  str = "./outputs_comms"
    py_output_dir:    str = ""          # empty → auto

SETTINGS = Settings()

# ── Scenario registry ─────────────────────────────────────────────────────────

@dataclass
class Scenario:
    sid:         int
    kind:        str          # "py-loop" | "rust-comms" | "rust-task"
    label:       str
    description: str
    domain:      Optional[str] = None
    task:        Optional[str] = None
    scenario_idx: Optional[int] = None
    topic:       Optional[str] = None

SCENARIOS: list[Scenario] = [
    # ── Python evolution loop ──────────────────────────────────────────────────
    Scenario( 1, "py-loop",   "text_classify",          "Text classification",        domain="text_classify"),
    Scenario( 2, "py-loop",   "rust",                   "Rust code generation",       domain="rust"),
    Scenario( 3, "py-loop",   "factory",                "Factory optimisation",       domain="factory"),
    Scenario( 4, "py-loop",   "paper_review",           "Paper review",               domain="paper_review"),
    Scenario( 5, "py-loop",   "search_arena",           "Search arena",               domain="search_arena"),
    # ── Rust comms scenarios ───────────────────────────────────────────────────
    Scenario( 6, "rust-comms","relay · s0",             "Project briefing relay",     task="relay",       scenario_idx=0),
    Scenario( 7, "rust-comms","relay · s1",             "Incident report relay",      task="relay",       scenario_idx=1),
    Scenario( 8, "rust-comms","collaborate · s0",       "Treasure hunt (split clues)",task="collaborate", scenario_idx=0),
    Scenario( 9, "rust-comms","collaborate · s1",       "Q1 profit analysis",         task="collaborate", scenario_idx=1),
    Scenario(10, "rust-comms","protocol",               "Compressed notation game",   task="protocol"),
    Scenario(11, "rust-comms","free discussion",        "Open-ended topic debate",    task="free"),
    Scenario(12, "rust-comms","language · mission ops", "Invent symbols: operations", task="language",    scenario_idx=0),
    Scenario(13, "rust-comms","language · environment", "Invent symbols: survival",   task="language",    scenario_idx=1),
    Scenario(14, "rust-comms","language · trade",       "Invent symbols: economy",    task="language",    scenario_idx=2),
    # ── Rust task evolution loop ───────────────────────────────────────────────
    Scenario(15, "rust-task", "text_classify",          "Text classify (Rust port)",  domain="text_classify"),
    Scenario(16, "rust-task", "emotion",                "Emotion detection",          domain="emotion"),
    Scenario(17, "rust-task", "factory",                "Factory (Rust port)",        domain="factory"),
]

# ── Run history ───────────────────────────────────────────────────────────────

@dataclass
class RunRecord:
    label:     str
    exit_code: int
    duration:  float
    ts:        str

run_history: list[RunRecord] = []

# ── Command builders ──────────────────────────────────────────────────────────

def build_cmd(s: Scenario) -> list[str]:
    if s.kind == "py-loop":
        cmd = [
            PYTHON_BIN, str(PYTHON_DIR / "loop.py"),
            "--domain",           s.domain,
            "--model",            SETTINGS.model,
            "--max-generation",   str(SETTINGS.generations),
            "--num-samples",      str(SETTINGS.samples),
            "--num-workers",      str(SETTINGS.workers),
            "--parent-selection", SETTINGS.parent_selection,
            "--verbose",
        ]
        if SETTINGS.py_output_dir:
            cmd += ["--output-dir", SETTINGS.py_output_dir]
        return cmd

    elif s.kind == "rust-comms":
        if not RUST_COMMS.exists():
            return []
        overseer = SETTINGS.overseer_model or SETTINGS.model
        cmd = [
            str(RUST_COMMS),
            "--task",          s.task,
            "--model",         SETTINGS.model,
            "--overseer-model",overseer,
            "--rounds",        str(SETTINGS.rounds),
            "--exchanges",     str(SETTINGS.exchanges),
            "--output-dir",    SETTINGS.rust_output_dir,
        ]
        if s.scenario_idx is not None:
            cmd += ["--scenario", str(s.scenario_idx)]
        if s.topic:
            cmd += ["--topic", s.topic]
        return cmd

    elif s.kind == "rust-task":
        if not RUST_TASK.exists():
            return []
        return [
            str(RUST_TASK),
            "--domain",          s.domain,
            "--model",           SETTINGS.model,
            "--max-generation",  str(SETTINGS.generations),
            "--num-samples",     str(SETTINGS.samples),
            "--num-workers",     str(SETTINGS.workers),
            "--parent-selection",SETTINGS.parent_selection,
        ]

    return []

# ── UI helpers ────────────────────────────────────────────────────────────────

KIND_COLOR = {
    "py-loop":    "bright_blue",
    "rust-comms": "bright_cyan",
    "rust-task":  "bright_magenta",
}
KIND_LABEL = {
    "py-loop":    "Python · Evolution Loop",
    "rust-comms": "Rust   · Comms Scenarios",
    "rust-task":  "Rust   · Task Evolution",
}

def make_scenario_table(group: str) -> Table:
    color = KIND_COLOR[group]
    t = Table(box=box.SIMPLE_HEAD, border_style=color, show_header=True,
              header_style=f"bold {color}", expand=True, padding=(0, 1),
              show_edge=True)
    t.add_column("#",    style="bold white", width=4, justify="right", no_wrap=True)
    t.add_column("Name", style="white",      min_width=24, no_wrap=True, overflow="ellipsis")
    t.add_column("Description", style="dim white", no_wrap=True, overflow="ellipsis")

    for s in SCENARIOS:
        if s.kind != group:
            continue
        available = True
        if s.kind in ("rust-comms", "rust-task"):
            bin_ = RUST_COMMS if s.kind == "rust-comms" else RUST_TASK
            if not bin_.exists():
                available = False
        dim  = "" if available else " dim"
        flag = "" if available else "  [dim red]⚠ build first[/]"
        t.add_row(
            f"[bold {color}]{s.sid}[/]",
            f"[{color}{dim}]{s.label}[/]{flag}",
            f"[dim]{s.description}[/]",
        )
    return t

def make_settings_panel() -> Panel:
    overseer_display = SETTINGS.overseer_model if SETTINGS.overseer_model else "(= model)"
    samples_display  = "all" if SETTINGS.samples == -1 else str(SETTINGS.samples)

    rows = [
        ("model",       SETTINGS.model),
        ("overseer",    overseer_display),
        ("rounds",      str(SETTINGS.rounds)),
        ("exchanges",   str(SETTINGS.exchanges)),
        ("workers",     str(SETTINGS.workers)),
        ("samples",     samples_display),
        ("gens",        str(SETTINGS.generations)),
        ("parent",      SETTINGS.parent_selection),
    ]

    lines = Text()
    for k, v in rows:
        lines.append(f" {k:<10}", style="dim")
        lines.append(f" {v}\n", style="bright_white")

    return Panel(lines, title="[bold yellow]⚙  Settings[/]", border_style="yellow",
                 padding=(0, 0))

def make_history_panel() -> Panel:
    if not run_history:
        body = Text(" No runs yet", style="dim")
    else:
        lines = Text()
        for r in reversed(run_history[-6:]):
            icon  = "✓" if r.exit_code == 0 else "✗"
            color = "green" if r.exit_code == 0 else "red"
            name  = r.label[:18].ljust(18)
            lines.append(f" [{color}]{icon}[/{color}] ", style="")
            lines.append(f"{name}", style="white")
            lines.append(f"  {r.duration:>4.0f}s  {r.ts}\n", style="dim")
        body = lines
    return Panel(body, title="[bold green]◆  History[/]", border_style="green",
                 padding=(0, 0))

def render_menu():
    console.clear()
    # ── header ──
    console.print(Panel(
        Text("HyperAgents  Control Panel", justify="center", style="bold white"),
        border_style="bright_white", padding=(0, 2),
    ))
    console.print()

    # ── scenario tables (left) + settings/history (right) ──
    py_table    = make_scenario_table("py-loop")
    comms_table = make_scenario_table("rust-comms")
    task_table  = make_scenario_table("rust-task")

    right_col = Table.grid()
    right_col.add_column(min_width=32)
    right_col.add_row(make_settings_panel())
    right_col.add_row(make_history_panel())

    left_col = Table.grid(expand=True)
    left_col.add_column()
    left_col.add_row(Rule(f"[bright_blue]{KIND_LABEL['py-loop']}[/]",     style="bright_blue"))
    left_col.add_row(py_table)
    left_col.add_row(Rule(f"[bright_cyan]{KIND_LABEL['rust-comms']}[/]",  style="bright_cyan"))
    left_col.add_row(comms_table)
    left_col.add_row(Rule(f"[bright_magenta]{KIND_LABEL['rust-task']}[/]",style="bright_magenta"))
    left_col.add_row(task_table)

    main_grid = Table.grid(expand=True, padding=(0, 1))
    main_grid.add_column(ratio=3)
    main_grid.add_column(min_width=32)
    main_grid.add_row(left_col, right_col)
    console.print(main_grid)

    # ── footer ──
    console.print()
    console.print(Rule(style="dim"))
    console.print(
        "  [bold white]Enter number[/] to run · "
        "[bold yellow][s][/] settings · "
        "[bold yellow][b][/] build rust · "
        "[bold yellow][c][/] check deps · "
        "[bold red][q][/] quit",
        highlight=False,
    )
    console.print()

# ── Settings editor ───────────────────────────────────────────────────────────

SETTINGS_FIELDS = [
    ("model",            "Model (e.g. ollama/llama3.2  llamacpp/local  openrouter/…)"),
    ("overseer_model",   "Overseer model (leave blank = same as model)"),
    ("rounds",           "Rounds (Rust comms)"),
    ("exchanges",        "Exchanges per round (Rust comms)"),
    ("workers",          "Parallel workers (Python / Rust task)"),
    ("samples",          "Samples to eval (-1 = all)"),
    ("generations",      "Evolution generations"),
    ("parent_selection", "Parent selection  [best / latest / proportional]"),
    ("rust_output_dir",  "Rust comms output directory"),
    ("py_output_dir",    "Python output directory (blank = auto)"),
]

def edit_settings():
    console.clear()
    console.print(Panel("[bold yellow]⚙  Settings Editor[/]  (blank = keep current)",
                        border_style="yellow"))
    console.print()

    for attr, label in SETTINGS_FIELDS:
        current = getattr(SETTINGS, attr)
        display = str(current) if current != "" else "[dim](empty)[/]"
        console.print(f"  [dim]{label}[/]")
        console.print(f"  Current: [bright_white]{display}[/]")
        try:
            new_val = Prompt.ask("  New value", default="", show_default=False)
        except (KeyboardInterrupt, EOFError):
            break
        if new_val.strip():
            # coerce ints
            if attr in ("rounds", "exchanges", "workers", "samples", "generations"):
                try:
                    setattr(SETTINGS, attr, int(new_val.strip()))
                except ValueError:
                    console.print("  [red]Not a number — skipped[/]")
            else:
                setattr(SETTINGS, attr, new_val.strip())
        console.print()

    console.print("[dim]Settings saved. Press Enter to return.[/]")
    try:
        input()
    except (KeyboardInterrupt, EOFError):
        pass

# ── Build helper ──────────────────────────────────────────────────────────────

def build_rust():
    console.clear()
    console.print(Panel("[bold bright_magenta]Building Rust binaries…[/]",
                        border_style="bright_magenta"))
    console.print()
    rust_dir = ROOT / "rust"
    cmd = ["cargo", "build", "--release", "--bins"]
    console.print(f"[dim]$ cd {rust_dir}  &&  {' '.join(cmd)}[/]")
    console.print()
    start = time.time()
    proc = subprocess.Popen(cmd, cwd=rust_dir,
                            stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                            text=True, bufsize=1)
    for line in proc.stdout:
        line = line.rstrip()
        if line.startswith("error"):
            console.print(f"[red]{line}[/]")
        elif line.startswith("warning"):
            console.print(f"[yellow]{line}[/]")
        else:
            console.print(f"[dim]{line}[/]")
    proc.wait()
    elapsed = time.time() - start
    console.print()
    if proc.returncode == 0:
        console.print(f"[bold green]✓  Build succeeded[/]  ({elapsed:.1f}s)")
    else:
        console.print(f"[bold red]✗  Build failed[/]  (exit {proc.returncode})")
    console.print()
    console.print("[dim]Press Enter to return.[/]")
    try:
        input()
    except (KeyboardInterrupt, EOFError):
        pass

# ── Run a scenario ────────────────────────────────────────────────────────────

def run_scenario(s: Scenario):
    cmd = build_cmd(s)
    if not cmd:
        console.clear()
        bin_ = RUST_COMMS if s.kind == "rust-comms" else RUST_TASK
        console.print(f"\n[bold red]Binary not found:[/] {bin_}")
        console.print("[yellow]Run [b][/b] from the menu to build it first.[/]")
        console.print("\n[dim]Press Enter to return.[/]")
        try:
            input()
        except (KeyboardInterrupt, EOFError):
            pass
        return

    color = KIND_COLOR[s.kind]
    ts    = time.strftime("%H:%M:%S")

    console.clear()
    console.print(Panel(
        f"[bold {color}]Running[/]  [white]{s.label}[/]  "
        f"[dim]({s.kind})[/]  [dim]{ts}[/]",
        border_style=color, padding=(0, 1),
    ))
    console.print(f"[dim]$ {' '.join(cmd)}[/]")
    console.print(Rule(style=color))
    console.print()

    start = time.time()
    try:
        workdir = str(PYTHON_DIR) if s.kind == "py-loop" else str(ROOT)
        proc = subprocess.Popen(
            cmd, cwd=workdir,
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            text=True, bufsize=1,
            env={**os.environ, "PYTHONPATH": str(PYTHON_DIR)},
        )
        for line in proc.stdout:
            console.print(line, end="", highlight=False, markup=False)
        proc.wait()
    except KeyboardInterrupt:
        proc.terminate()
        console.print("\n[yellow]Interrupted by user.[/]")
        proc.returncode = -1
    except Exception as e:
        console.print(f"\n[bold red]Error starting process:[/] {e}")
        return

    elapsed = time.time() - start
    console.print()
    console.print(Rule(style=color))
    if proc.returncode == 0:
        console.print(f"[bold green]✓  Done[/]  ({elapsed:.1f}s)")
    else:
        console.print(f"[bold red]✗  Exit {proc.returncode}[/]  ({elapsed:.1f}s)")

    run_history.append(RunRecord(
        label=s.label, exit_code=proc.returncode,
        duration=elapsed, ts=ts,
    ))

    console.print()
    console.print("[dim]Press Enter to return to the menu.[/]")
    try:
        input()
    except (KeyboardInterrupt, EOFError):
        pass

# ── Quick topic picker for free discussion ────────────────────────────────────

FREE_TOPICS = [
    "Trade-offs between consistency and availability in distributed systems",
    "Why do large language models sometimes confidently produce wrong answers?",
    "How should autonomous AI agents decide when to ask for human help?",
    "What makes a good abstraction in software engineering?",
]

def pick_free_topic() -> Optional[str]:
    console.print("\n  [bold yellow]Free discussion — pick a topic:[/]")
    for i, t in enumerate(FREE_TOPICS, 1):
        console.print(f"  [dim]{i}.[/] {t}")
    console.print(f"  [dim]{len(FREE_TOPICS)+1}.[/] Enter custom topic")
    try:
        choice = Prompt.ask("  Choice", default="1")
        idx = int(choice.strip()) - 1
        if 0 <= idx < len(FREE_TOPICS):
            return FREE_TOPICS[idx]
        else:
            return Prompt.ask("  Topic")
    except (ValueError, KeyboardInterrupt, EOFError):
        return None

# ── Main loop ─────────────────────────────────────────────────────────────────

SCENARIO_MAP = {str(s.sid): s for s in SCENARIOS}

def main():
    # Startup check — auto-skip if everything is fine
    checks = run_checks()
    has_issues = any(not d.ok or d.warning for d in checks)
    if has_issues:
        show_prereq_screen()

    while True:
        render_menu()
        try:
            raw = input("  > ").strip().lower()
        except (KeyboardInterrupt, EOFError):
            raw = "q"

        if raw == "q":
            console.print("\n[dim]Bye.[/]\n")
            break
        elif raw == "s":
            edit_settings()
        elif raw == "b":
            build_rust()
        elif raw == "c":
            show_prereq_screen(force=True)
        elif raw in SCENARIO_MAP:
            s = SCENARIO_MAP[raw]
            # special handling for free discussion — ask for topic
            if s.task == "free" and not s.topic:
                topic = pick_free_topic()
                if topic:
                    s = Scenario(**{**s.__dict__, "topic": topic})
            run_scenario(s)
        else:
            console.print(f"[red]Unknown command:[/] {raw!r}  "
                          "[dim](enter a number, s, b, or q)[/]")
            time.sleep(1)

if __name__ == "__main__":
    main()
