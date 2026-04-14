#!/usr/bin/env python3
"""HyperAgents Terminal Control Panel"""
import os, sys, subprocess, time, json, shutil, importlib, importlib.util, urllib.request
from dataclasses import replace as dc_replace
from dataclasses import dataclass, field
from typing import Optional, List
from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.rule import Rule
from rich.prompt import Prompt, Confirm
from rich.live import Live
from rich.align import Align
from rich import box

ROOT       = Path(__file__).parent
PYTHON_DIR = ROOT / "python"
RUST_COMMS = ROOT / "rust" / "target" / "release" / "hyperagents-comms"
RUST_TASK  = ROOT / "rust" / "target" / "release" / "hyperagents"
VENV_PY    = ROOT / "venv" / "bin" / "python"
PYTHON_BIN = str(VENV_PY) if VENV_PY.exists() else sys.executable
console    = Console()


# ── Charts ─────────────────────────────────────────────────────────────────────

SPARK = "▁▂▃▄▅▆▇█"

def sparkline(values):
    if not values: return ""
    mn, mx = min(values), max(values)
    span = mx - mn or 1
    return "".join(SPARK[int((v-mn)/span*7)] for v in values)

def hbar(value, max_val=10, width=22):
    """Returns (bar_str, color_name)."""
    frac   = max(0.0, min(1.0, value / (max_val or 1)))
    filled = int(frac * width)
    bar    = "█" * filled + "░" * (width - filled)
    color  = "bright_green" if frac >= 0.7 else "yellow" if frac >= 0.4 else "red"
    return bar, color

def score_color(s):
    return "bright_green" if s >= 7 else "yellow" if s >= 4 else "red"

def vertical_score_chart(scores, max_val=10):
    """Return list of plain strings forming a vertical bar chart (ANSI colored)."""
    if not scores: return ["(no scores yet)"]
    lines = []
    ANSI = {"bright_green": "92", "yellow": "93", "red": "91"}
    for level in range(max_val, 0, -1):
        prefix = f"{level:>3} │" if level % 2 == 0 else "    │"
        row = prefix
        for sc in scores:
            if sc >= level:
                col = ANSI[score_color(sc)]
                row += f"\x1b[{col}m██\x1b[0m  "
            else:
                row += "    "
        lines.append(row)
    lines.append("    └" + "────" * len(scores))
    lines.append("     " + "".join(f"R{i+1:<3}" for i in range(len(scores))))
    return lines


# ── Prerequisites ──────────────────────────────────────────────────────────────

@dataclass
class DepCheck:
    name: str; ok: bool; detail: str
    fixable: bool = False; fix_label: str = ""
    fix_cmd: list = field(default_factory=list)
    fix_cwd: str = ""; warning: bool = False

HAS_BREW = bool(shutil.which("brew"))

def _q(cmd, cwd=None):
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=10, cwd=cwd)
        return r.returncode, (r.stdout+r.stderr).strip()
    except Exception as e:
        return -1, str(e)

def _chk_ollama():
    if not shutil.which("ollama"):
        return DepCheck("ollama", False, "not found — needed for --model ollama/…",
            HAS_BREW, "brew install ollama",
            ["brew","install","ollama"] if HAS_BREW else [])
    _, out = _q(["ollama","--version"])
    ver = out.split()[-1] if out else "?"
    try:
        with urllib.request.urlopen("http://localhost:11434/api/tags", timeout=2) as r:
            n = len(json.loads(r.read()).get("models", []))
        return DepCheck("ollama", True, f"{ver}  ·  daemon running  ({n} models)")
    except Exception:
        return DepCheck("ollama", True, f"{ver}  ·  installed but daemon NOT running",
            warning=True, fixable=True, fix_label="start ollama",
            fix_cmd=["ollama","serve"])

def _chk_llama():
    b = shutil.which("llama-server")
    if not b:
        return DepCheck("llama-server (llama.cpp)", False,
            "not found — needed for --model llamacpp/…",
            HAS_BREW, "brew install llama.cpp",
            ["brew","install","llama.cpp"] if HAS_BREW else [])
    return DepCheck("llama-server (llama.cpp)", True, f"found at {b}")

def _chk_cargo():
    if not shutil.which("cargo"):
        return DepCheck("cargo (Rust)", False, "not found — needed to build Rust binaries",
            HAS_BREW, "brew install rust",
            ["brew","install","rust"] if HAS_BREW else [])
    _, out = _q(["cargo","--version"])
    return DepCheck("cargo (Rust)", True, out.split()[1] if " " in out else out)

def _chk_bins():
    miss = [b.name for b in [RUST_COMMS, RUST_TASK] if not b.exists()]
    if not miss:
        return DepCheck("Rust binaries", True, "hyperagents + hyperagents-comms  ✓")
    return DepCheck("Rust binaries", False, f"not built: {', '.join(miss)}",
        bool(shutil.which("cargo")), "cargo build --release",
        ["cargo","build","--release","--bins"], str(ROOT/"rust"))

def _chk_pydeps():
    miss = [m for m in ["requests","litellm","pandas","git","dotenv"]
            if not importlib.util.find_spec(m)]
    if not miss:
        return DepCheck("Python deps", True,
            "requests  litellm  pandas  gitpython  dotenv")
    return DepCheck("Python deps", False, f"missing: {', '.join(miss)}",
        True, "pip install -r requirements.txt",
        [PYTHON_BIN,"-m","pip","install","-r",str(ROOT/"requirements.txt")])

def run_checks():
    return [_chk_ollama(), _chk_llama(), _chk_cargo(), _chk_pydeps(), _chk_bins()]

def _install_dep(dep):
    if not dep.fix_cmd: return False
    if dep.fix_cmd == ["ollama","serve"]:
        console.print("\n  [dim]Launching ollama in background…[/]")
        subprocess.Popen(["ollama","serve"],stdout=subprocess.DEVNULL,
                         stderr=subprocess.DEVNULL,start_new_session=True)
        time.sleep(2)
        try: urllib.request.urlopen("http://localhost:11434/api/tags",timeout=3); return True
        except: return False
    console.print(f"\n  [dim]$ {' '.join(dep.fix_cmd)}[/]\n")
    proc = subprocess.Popen(dep.fix_cmd, cwd=dep.fix_cwd or None,
                            stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                            text=True, bufsize=1)
    for line in proc.stdout:
        console.print(f"  [dim]{line.rstrip()}[/]", highlight=False, markup=False)
    proc.wait()
    return proc.returncode == 0

# Status cache (30 s TTL)
_sc: dict = {}; _sc_ts: float = 0.0
def get_status():
    global _sc, _sc_ts
    if time.time() - _sc_ts > 30:
        ok, n = False, 0
        try:
            with urllib.request.urlopen("http://localhost:11434/api/tags",timeout=1) as r:
                n = len(json.loads(r.read()).get("models",[])); ok = True
        except: pass
        _sc = {"ollama": ok, "models": n, "llama": bool(shutil.which("llama-server"))}
        _sc_ts = time.time()
    return _sc

def show_prereq_screen(force=False):
    console.clear()
    console.print(Panel(Text("System Check", justify="center", style="bold white"),
                        border_style="bright_white", padding=(0,2)))
    console.print()
    checks = []
    with Live(Text("  Checking prerequisites…", style="dim"),
              refresh_per_second=8, console=console) as live:
        checks = run_checks(); live.update(Text(""))

    t = Table(box=box.SIMPLE, show_header=False, padding=(0,2))
    t.add_column("i", width=3, no_wrap=True)
    t.add_column("name", style="white", no_wrap=True, min_width=30)
    t.add_column("detail", style="dim", no_wrap=True)
    all_ok = True
    for d in checks:
        if d.ok and not d.warning:   icon = "[bold green]✓[/]"
        elif d.warning:              icon = "[bold yellow]⚠[/]"; all_ok = False
        else:                        icon = "[bold red]✗[/]";    all_ok = False
        t.add_row(icon, d.name, d.detail)
    console.print(t)

    if all_ok and not force:
        console.print("  [dim green]All prerequisites satisfied.[/]\n"); return

    problems = [d for d in checks if not d.ok or d.warning]
    if problems:
        console.print(); console.print(Rule("[yellow]Issues found[/]", style="yellow"))
        console.print()
        for dep in problems:
            st = "yellow" if dep.warning else "red"
            ic = "⚠" if dep.warning else "✗"
            console.print(f"  [{st}]{ic}[/]  [white]{dep.name}[/]  —  {dep.detail}")
            if dep.fixable:
                lbl = dep.fix_label or " ".join(dep.fix_cmd)
                try:
                    if Confirm.ask(f"     Fix now?  [dim]({lbl})[/]", default=True):
                        console.print("  [green]  ✓  Done.[/]" if _install_dep(dep)
                                      else "  [red]  ✗  Failed.[/]")
                except (KeyboardInterrupt, EOFError): pass
            else:
                console.print("     [dim]Manual install required (see README).[/]")
            console.print()
    console.print("[dim]Press Enter to continue.[/]")
    try: input()
    except (KeyboardInterrupt, EOFError): pass


# ── Settings ───────────────────────────────────────────────────────────────────

@dataclass
class Settings:
    model:            str = "ollama/llama3.2"
    overseer_model:   str = ""
    rounds:           int = 4
    exchanges:        int = 3
    workers:          int = 4
    samples:          int = -1
    generations:      int = 5
    parent_selection: str = "best"
    rust_output_dir:  str = "./outputs_comms"
    py_output_dir:    str = ""

SETTINGS = Settings()

# ── Scenario registry ──────────────────────────────────────────────────────────

@dataclass
class Scenario:
    sid: int; kind: str; label: str; description: str
    detail: str; tags: List[str]
    domain: Optional[str] = None; task: Optional[str] = None
    scenario_idx: Optional[int] = None; topic: Optional[str] = None

SCENARIOS: List[Scenario] = [
    Scenario(1,"py-loop","text_classify","Text classification",
        "A meta-agent iteratively rewrites the task-agent's Python code to improve "
        "classification accuracy. Each generation it sees its own previous score and "
        "proposes targeted code edits — watch prompt-engineering evolve automatically.",
        ["evolution","multi-gen","python"], domain="text_classify"),
    Scenario(2,"py-loop","rust","Rust code generation",
        "The meta-agent improves an AI agent that writes Rust solutions from scratch. "
        "Correctness is measured by compiled + passing test suites, so the reward signal "
        "is unambiguous. Interesting to watch how code style evolves.",
        ["evolution","code-gen","python"], domain="rust"),
    Scenario(3,"py-loop","factory","Factory optimisation",
        "Agent self-improves on a factory scheduling and resource-allocation task. "
        "Numeric reward makes the optimisation curve very visible. "
        "Usually shows the fastest score improvement across generations.",
        ["evolution","numeric","python"], domain="factory"),
    Scenario(4,"py-loop","paper_review","Paper review",
        "Meta-agent refines an academic paper reviewer over multiple generations. "
        "Evaluates review quality, completeness, and constructiveness. "
        "Interesting for observing how critique style and depth evolve.",
        ["evolution","NLP","python"], domain="paper_review"),
    Scenario(5,"py-loop","search_arena","Search arena",
        "Agent improves a web-search-and-answer pipeline. Multi-hop reasoning "
        "quality is the reward signal. Tests whether the agent learns to decompose "
        "complex queries and synthesize answers from multiple sources.",
        ["evolution","retrieval","python"], domain="search_arena"),
    Scenario(6,"rust-comms","relay · s0","Project briefing relay",
        "Agent A receives a dense project brief (deadline, budget, team changes, "
        "endpoints, credentials, blockers) and relays it to B as efficiently as possible. "
        "The Overseer quizzes B on specific facts — every missed detail costs score.",
        ["relay","fidelity","4 rounds"], task="relay", scenario_idx=0),
    Scenario(7,"rust-comms","relay · s1","Incident report relay",
        "Agent A relays a live production incident (service, impact %, root cause, "
        "timeline, action items, on-call owner) to Agent B. "
        "Tests information density and recall under compressed communication.",
        ["relay","fidelity","4 rounds"], task="relay", scenario_idx=1),
    Scenario(8,"rust-comms","collaborate · s0","Treasure hunt (split clues)",
        "A and B each hold different clues to a hidden location. They must exchange "
        "only what is needed to reconstruct the full 5-step route — "
        "without repeating what the other already knows.",
        ["collaborate","puzzle","4 rounds"], task="collaborate", scenario_idx=0),
    Scenario(9,"rust-comms","collaborate · s1","Q1 profit analysis",
        "A holds sales data, B holds cost data. Together they compute Q1 profit, "
        "best-margin month, and worst-margin month. Tests arithmetic collaboration "
        "and efficient information handoff between agents.",
        ["collaborate","math","4 rounds"], task="collaborate", scenario_idx=1),
    Scenario(10,"rust-comms","protocol","Compressed notation game",
        "Both agents develop a shared shorthand for project status reports across rounds. "
        "A's message must get shorter every round while B still reconstructs 100% of the data. "
        "Watch a private language emerge from pure efficiency pressure.",
        ["protocol","compression","5 rounds"], task="protocol"),
    Scenario(11,"rust-comms","free discussion","Open-ended topic debate",
        "Two agents discuss a complex technical or philosophical topic, "
        "coached by the Overseer to eliminate hedging, filler, and repetition. "
        "Score rewards insight-density: maximum signal per word.",
        ["free","debate","4 rounds"], task="free"),
    Scenario(12,"rust-comms","language · mission ops","Invent symbols: operations",
        "Agents invent a brand-new symbol language for mission operations from scratch. "
        "Round 1 is a Bootstrap negotiation. From Round 2 Agent A encodes messages in "
        "PURE SYMBOLS — no natural language. B decodes and the Overseer scores fidelity + compression.",
        ["language","symbols","5 rounds"], task="language", scenario_idx=0),
    Scenario(13,"rust-comms","language · environment","Invent symbols: survival",
        "Same emergent-language game but for weather and survival. "
        "Concepts: elements, intensity levels, directions, danger signals, time. "
        "Watch emoji and ASCII glyphs become a real communication protocol across rounds.",
        ["language","symbols","5 rounds"], task="language", scenario_idx=1),
    Scenario(14,"rust-comms","language · trade","Invent symbols: economy",
        "Agents build a trading-floor symbol language: goods, prices, quantities, "
        "market trends (rising / falling / stable), and conditional buy / sell orders. "
        "Tests whether invented symbols survive increasingly complex financial messages.",
        ["language","symbols","5 rounds"], task="language", scenario_idx=2),
    Scenario(15,"rust-task","text_classify","Text classification (Rust)",
        "The Rust port of the evolution loop on the text_classify domain. "
        "Faster than the Python version — useful for longer evolution runs without Python overhead.",
        ["evolution","rust","multi-gen"], domain="text_classify"),
    Scenario(16,"rust-task","emotion","Emotion detection (Rust)",
        "Rust evolution loop on the emotion-detection domain. "
        "The meta-agent rewrites the task agent each generation guided by accuracy scores. "
        "Five emotions are classified from short text snippets.",
        ["evolution","rust","NLP"], domain="emotion"),
    Scenario(17,"rust-task","factory","Factory optimisation (Rust)",
        "Rust port of the factory loop. Numeric reward + native execution = "
        "fastest evolution scenario in the suite.",
        ["evolution","rust","numeric"], domain="factory"),
]

@dataclass
class RunRecord:
    label: str; exit_code: int; duration: float; ts: str
    session: Optional[Path] = None

run_history: List[RunRecord] = []


# ── Command builders ───────────────────────────────────────────────────────────

def build_cmd(s: Scenario) -> List[str]:
    if s.kind == "py-loop":
        cmd = [PYTHON_BIN, str(PYTHON_DIR/"loop.py"),
               "--domain", s.domain, "--model", SETTINGS.model,
               "--max-generation", str(SETTINGS.generations),
               "--num-samples", str(SETTINGS.samples),
               "--num-workers", str(SETTINGS.workers),
               "--parent-selection", SETTINGS.parent_selection, "--verbose"]
        if SETTINGS.py_output_dir: cmd += ["--output-dir", SETTINGS.py_output_dir]
        return cmd
    elif s.kind == "rust-comms":
        if not RUST_COMMS.exists(): return []
        cmd = [str(RUST_COMMS), "--task", s.task,
               "--model", SETTINGS.model,
               "--overseer-model", SETTINGS.overseer_model or SETTINGS.model,
               "--rounds", str(SETTINGS.rounds),
               "--exchanges", str(SETTINGS.exchanges),
               "--output-dir", SETTINGS.rust_output_dir]
        if s.scenario_idx is not None: cmd += ["--scenario", str(s.scenario_idx)]
        if s.topic: cmd += ["--topic", s.topic]
        return cmd
    elif s.kind == "rust-task":
        if not RUST_TASK.exists(): return []
        return [str(RUST_TASK), "--domain", s.domain, "--model", SETTINGS.model,
                "--max-generation", str(SETTINGS.generations),
                "--num-samples", str(SETTINGS.samples),
                "--num-workers", str(SETTINGS.workers),
                "--parent-selection", SETTINGS.parent_selection]
    return []

# ── Dashboard helpers ──────────────────────────────────────────────────────────

def find_latest_session(task: str) -> Optional[Path]:
    candidates = []
    for base in [ROOT/"outputs_comms", Path(SETTINGS.rust_output_dir)]:
        if not base.exists(): continue
        for d in base.iterdir():
            if d.is_dir() and task in d.name:
                p = d/"session.json"
                if p.exists(): candidates.append((p.stat().st_mtime, p))
    if not candidates: return None
    return sorted(candidates, reverse=True)[0][1]

def render_comms_dashboard(session: dict, elapsed: float):
    console.clear()
    task   = session.get("task","?")
    model  = session.get("agent_model","?")
    omodel = session.get("overseer_model","?")
    scores = session.get("scores",[])
    log    = session.get("log",[])

    console.print(Panel(
        Text(f"  Session Dashboard  ·  {task.upper()}", justify="center",
             style="bold white"),
        border_style="bright_cyan", padding=(0,1)))
    console.print()

    # ── Overview ──
    avg   = round(sum(scores)/len(scores), 1) if scores else 0
    best  = max(scores) if scores else 0
    best_r= scores.index(best)+1 if scores else 0
    delta = (scores[-1]-scores[0]) if len(scores) > 1 else 0
    trend = (f"[bright_green]↑ +{delta}[/]" if delta > 0
             else f"[red]↓ {delta}[/]" if delta < 0 else "[dim]→ steady[/]")
    mins  = int(elapsed//60); secs = int(elapsed%60)
    domain_val = ""
    if log:
        domain_val = (log[0].get("domain") or log[0].get("scenario") or
                      log[0].get("topic") or "")

    ov = Table(box=box.ROUNDED, border_style="dim", padding=(0,2), expand=True)
    for _ in range(4): ov.add_column(no_wrap=True)
    ov.add_row("[dim]Model[/]",     f"[bright_white]{model}[/]",
               "[dim]Duration[/]",  f"[bright_white]{mins}m {secs}s[/]")
    ov.add_row("[dim]Overseer[/]",
               f"[bright_white]{omodel if omodel!=model else '(= model)'}[/]",
               "[dim]Avg score[/]", f"[bright_white]{avg} / 10[/]")
    ov.add_row("[dim]Task[/]",      f"[bright_white]{task}[/]",
               "[dim]Best round[/]",f"[bright_white]Round {best_r}  ({best}/10)[/]" if best_r else "—")
    ov.add_row("[dim]Domain[/]",    f"[bright_white]{domain_val or '—'}[/]",
               "[dim]Trend[/]",     trend)
    console.print(ov)
    console.print()

    # ── Score history ──
    console.print(Rule("[bold bright_cyan]Score History[/]", style="bright_cyan"))
    console.print()
    if scores:
        for line in vertical_score_chart(scores):
            print("  " + line)          # raw print preserves ANSI
        seq = " → ".join(str(s) for s in scores)
        sp  = sparkline(scores)
        console.print(f"\n  [dim]Scores:[/]   {seq}")
        console.print(f"  [dim]Sparkline:[/] [bright_cyan]{sp}[/]   "
                      f"[dim]Trend:[/] {trend}")
    console.print()

    # ── Round breakdown ──
    console.print(Rule("[bold bright_cyan]Round Breakdown[/]", style="bright_cyan"))
    console.print()
    rt = Table(box=box.SIMPLE_HEAD, border_style="dim",
               header_style="bold dim", expand=True, padding=(0,1))
    rt.add_column("Rnd", width=4, justify="right", no_wrap=True)
    rt.add_column("Concepts / Phase", min_width=24, no_wrap=True, overflow="ellipsis")
    is_lang = (task == "language")
    if is_lang: rt.add_column("Lex", width=5, justify="right", no_wrap=True)
    rt.add_column("Score", width=20, no_wrap=True)
    rt.add_column("Verdict", no_wrap=True, overflow="ellipsis")
    for entry in log:
        rnd     = entry.get("round","?")
        concept = str(entry.get("concepts") or entry.get("project") or
                      entry.get("topic",""))[:30]
        sc      = entry.get("score", 0)
        verdict = str(entry.get("verdict",""))[:52]
        bar, col = hbar(sc, 10, 12)
        score_cell = f"[{col}]{bar}[/] [bold]{sc}[/]"
        if is_lang:
            rt.add_row(str(rnd), concept, str(entry.get("lexicon_size","—")),
                       score_cell, f"[dim]{verdict}[/]")
        else:
            rt.add_row(str(rnd), concept, score_cell, f"[dim]{verdict}[/]")
    console.print(rt)
    console.print()

    # ── Compression trend ──
    if task in ("language","protocol"):
        console.print(Rule("[bold bright_cyan]Compression Trend[/]", style="bright_cyan"))
        console.print()
        console.print("  [dim]Lower % = more compressed (fewer symbols vs natural language)[/]\n")
        ct = Table(box=None, show_header=False, padding=(0,1))
        ct.add_column("rnd",  width=4,  no_wrap=True, style="dim")
        ct.add_column("bar",  width=28, no_wrap=True)
        ct.add_column("pct",  width=6,  no_wrap=True, justify="right")
        ct.add_column("note", no_wrap=True, style="dim", overflow="ellipsis")
        first_skip = True
        for entry in log:
            pct = entry.get("compression_pct")
            if pct is None:
                wa = entry.get("words_a")
                if wa is None: continue
                pct = min(100, wa * 5)
            rnd = entry.get("round","?")
            if first_skip and task == "language":
                first_skip = False; continue   # skip bootstrap
            inverted = 100 - pct
            bar, col = hbar(inverted, 100, 24)
            msg  = str(entry.get("message",""))[:42]
            note = f'"{msg}"' if msg else f"words_a={entry.get('words_a','?')}"
            pct_txt = f"[bold {col}]{pct}%[/]"
            ct.add_row(f"R{rnd}", f"[{col}]{bar}[/]", pct_txt, note)
        console.print(ct)
        console.print()

    # ── Final lexicon ──
    if is_lang:
        last_lex = []
        for entry in reversed(log):
            if entry.get("lexicon"):
                last_lex = entry["lexicon"]; break
        if last_lex:
            console.print(Rule(f"[bold bright_cyan]Final Lexicon  "
                               f"({len(last_lex)} symbols)[/]", style="bright_cyan"))
            console.print()
            COLS = 3
            lg = Table(box=None, show_header=False, padding=(0,2))
            for _ in range(COLS): lg.add_column(style="bright_white", no_wrap=True, min_width=22)
            row = []
            for e in last_lex:
                row.append(str(e))
                if len(row) == COLS: lg.add_row(*row); row = []
            if row:
                while len(row) < COLS: row.append("")
                lg.add_row(*row)
            console.print(lg)
            console.print()

    # ── Top tips ──
    tips, seen = [], set()
    for entry in log:
        for tip in entry.get("tips_a",[]) + entry.get("tips_b",[]):
            t = tip.strip()
            if t and t not in seen: seen.add(t); tips.append(t)
    if tips:
        console.print(Rule("[bold bright_cyan]Overseer Coaching Tips[/]", style="bright_cyan"))
        console.print()
        for tip in tips[:6]:
            console.print(f"  [dim cyan]•[/]  [dim]{tip}[/]")
        console.print()


# ── UI ─────────────────────────────────────────────────────────────────────────

KIND_COLOR = {"py-loop":"bright_blue","rust-comms":"bright_cyan","rust-task":"bright_magenta"}
KIND_LABEL = {
    "py-loop":    "Python · Evolution Loop",
    "rust-comms": "Rust   · Comms Scenarios",
    "rust-task":  "Rust   · Task Evolution",
}

def _status_bar() -> Text:
    st = get_status()
    t  = Text()
    if st["ollama"]:
        t.append("  ● ", style="bright_green")
        t.append(f"ollama  {st['models']} models", style="dim green")
    else:
        t.append("  ○ ", style="red")
        t.append("ollama offline", style="dim red")
    if st["llama"]:
        t.append("    ● ", style="bright_green")
        t.append("llama-server", style="dim green")
    else:
        t.append("    ○ ", style="dim")
        t.append("llama-server —", style="dim")
    t.append("    model: ", style="dim")
    t.append(SETTINGS.model, style="bright_white")
    return t

def _make_table(group: str) -> Table:
    col = KIND_COLOR[group]
    t   = Table(box=box.SIMPLE_HEAD, border_style=col, show_header=True,
                header_style=f"bold {col}", expand=True, padding=(0,1), show_edge=True)
    t.add_column("#",    style="bold white",  width=4, justify="right", no_wrap=True)
    t.add_column("Name", style="white",       min_width=24, no_wrap=True, overflow="ellipsis")
    t.add_column("Description  +  tags",      style="dim white", no_wrap=True, overflow="ellipsis")
    for s in SCENARIOS:
        if s.kind != group: continue
        bin_  = RUST_COMMS if s.kind=="rust-comms" else (RUST_TASK if s.kind=="rust-task" else None)
        avail = bin_ is None or bin_.exists()
        dim   = "" if avail else " dim"
        flag  = "" if avail else "  [dim red]⚠ build first[/]"
        tags  = "  " + "  ".join(f"[dim cyan][{g}][/]" for g in s.tags[:3])
        t.add_row(f"[bold {col}]{s.sid}[/]",
                  f"[{col}{dim}]{s.label}[/]{flag}",
                  f"[dim]{s.description[:42]}[/]{tags}")
    return t

def _settings_panel() -> Panel:
    txt = Text()
    rows = [("model",     SETTINGS.model),
            ("overseer",  SETTINGS.overseer_model or "(= model)"),
            ("rounds",    str(SETTINGS.rounds)),
            ("exchanges", str(SETTINGS.exchanges)),
            ("workers",   str(SETTINGS.workers)),
            ("samples",   "all" if SETTINGS.samples==-1 else str(SETTINGS.samples)),
            ("gens",      str(SETTINGS.generations)),
            ("parent",    SETTINGS.parent_selection)]
    for k, v in rows:
        txt.append(f" {k:<10}", style="dim")
        txt.append(f" {v}\n",   style="bright_white")
    return Panel(txt, title="[bold yellow]⚙  Settings[/]", border_style="yellow", padding=(0,0))

def _history_panel() -> Panel:
    if not run_history:
        body = Text(" No runs yet", style="dim")
    else:
        body = Text()
        for r in reversed(run_history[-6:]):
            ic  = "✓" if r.exit_code==0 else "✗"
            col = "green" if r.exit_code==0 else "red"
            body.append(f" [{col}]{ic}[/{col}] {r.label[:17]:<17}  ", style="")
            body.append(f"{r.duration:>4.0f}s  {r.ts}\n", style="dim")
    return Panel(body, title="[bold green]◆  History[/]", border_style="green", padding=(0,0))

def render_menu():
    console.clear()
    hdr = Text()
    hdr.append("HyperAgents  Control Panel\n", style="bold white")
    hdr.append_text(_status_bar())
    console.print(Panel(Align.center(hdr), border_style="bright_white", padding=(0,1)))
    console.print()

    right = Table.grid(); right.add_column(min_width=32)
    right.add_row(_settings_panel()); right.add_row(_history_panel())

    left = Table.grid(expand=True); left.add_column()
    left.add_row(Rule(f"[bright_blue]{KIND_LABEL['py-loop']}[/]", style="bright_blue"))
    left.add_row(_make_table("py-loop"))
    left.add_row(Rule(f"[bright_cyan]{KIND_LABEL['rust-comms']}[/]", style="bright_cyan"))
    left.add_row(_make_table("rust-comms"))
    left.add_row(Rule(f"[bright_magenta]{KIND_LABEL['rust-task']}[/]", style="bright_magenta"))
    left.add_row(_make_table("rust-task"))

    grid = Table.grid(expand=True, padding=(0,1))
    grid.add_column(ratio=3); grid.add_column(min_width=32)
    grid.add_row(left, right)
    console.print(grid)
    console.print()
    console.print(Rule(style="dim"))
    console.print("  [bold white]number[/] run  "
                  "[yellow][s][/] settings  "
                  "[yellow][b][/] build rust  "
                  "[yellow][c][/] check deps  "
                  "[red][q][/] quit", highlight=False)
    console.print()

def render_scenario_preview(s: Scenario) -> bool:
    console.clear()
    col  = KIND_COLOR[s.kind]
    tags = "  ".join(f"[dim cyan][{t}][/]" for t in s.tags)
    console.print(Panel(
        f"[bold {col}]▶  {s.label}[/]\n[dim]{KIND_LABEL[s.kind]}[/]  {tags}",
        border_style=col, padding=(0,2)))
    console.print()
    console.print(Panel(s.detail, title="[dim]What happens[/]",
                        border_style="dim", padding=(1,2)))
    console.print()

    # Config table
    ov = SETTINGS.overseer_model or "(= model)"
    samp = "all" if SETTINGS.samples==-1 else str(SETTINGS.samples)
    cfg = Table(box=box.ROUNDED, border_style="dim", padding=(0,2), expand=True)
    for _ in range(4): cfg.add_column(no_wrap=True)
    if s.kind == "rust-comms":
        cfg.add_row("[dim]Model[/]",    f"[bright_white]{SETTINGS.model}[/]",
                    "[dim]Task[/]",     f"[bright_white]{s.task}[/]")
        cfg.add_row("[dim]Overseer[/]", f"[bright_white]{ov}[/]",
                    "[dim]Rounds[/]",   f"[bright_white]{SETTINGS.rounds}[/]")
        cfg.add_row("[dim]Exchanges[/]",f"[bright_white]{SETTINGS.exchanges}[/]",
                    "[dim]Scenario[/]",
                    f"[bright_white]#{s.scenario_idx}[/]" if s.scenario_idx is not None else "—")
    else:
        cfg.add_row("[dim]Model[/]",    f"[bright_white]{SETTINGS.model}[/]",
                    "[dim]Domain[/]",   f"[bright_white]{s.domain}[/]")
        cfg.add_row("[dim]Workers[/]",  f"[bright_white]{SETTINGS.workers}[/]",
                    "[dim]Gens[/]",     f"[bright_white]{SETTINGS.generations}[/]")
        cfg.add_row("[dim]Samples[/]",  f"[bright_white]{samp}[/]",
                    "[dim]Parent[/]",   f"[bright_white]{SETTINGS.parent_selection}[/]")
    console.print(cfg)
    console.print()
    console.print("  [dim]Press [bold]Enter[/bold] to start · [bold]q[/bold] to cancel[/]")
    try:
        return input("  > ").strip().lower() != "q"
    except (KeyboardInterrupt, EOFError):
        return False


# ── Settings editor ────────────────────────────────────────────────────────────

SETTINGS_FIELDS = [
    ("model",            "Model  (ollama/…  llamacpp/…  openrouter/…  anthropic/…)"),
    ("overseer_model",   "Overseer model  (blank = same as agent model)"),
    ("rounds",           "Rounds  (Rust comms)"),
    ("exchanges",        "Exchanges per round  (Rust comms)"),
    ("workers",          "Parallel workers  (Python / Rust task)"),
    ("samples",          "Samples to evaluate  (-1 = all)"),
    ("generations",      "Evolution generations"),
    ("parent_selection", "Parent selection  [best / latest / proportional]"),
    ("rust_output_dir",  "Rust comms output directory"),
    ("py_output_dir",    "Python output directory  (blank = auto)"),
]

def edit_settings():
    console.clear()
    console.print(Panel("[bold yellow]⚙  Settings Editor[/]  —  blank = keep current",
                        border_style="yellow"))
    console.print()
    for attr, label in SETTINGS_FIELDS:
        cur = getattr(SETTINGS, attr)
        console.print(f"  [dim]{label}[/]")
        console.print(f"  Current: [bright_white]{cur if cur != '' else '(empty)'}[/]")
        try:
            val = Prompt.ask("  New value", default="", show_default=False)
        except (KeyboardInterrupt, EOFError):
            break
        if val.strip():
            if attr in ("rounds","exchanges","workers","samples","generations"):
                try: setattr(SETTINGS, attr, int(val.strip()))
                except ValueError: console.print("  [red]Not a number — skipped.[/]")
            else:
                setattr(SETTINGS, attr, val.strip())
        console.print()
    console.print("[dim]Saved. Press Enter.[/]")
    try: input()
    except (KeyboardInterrupt, EOFError): pass

# ── Build ──────────────────────────────────────────────────────────────────────

def build_rust():
    console.clear()
    console.print(Panel("[bold bright_magenta]Building Rust binaries[/]",
                        border_style="bright_magenta"))
    console.print()
    cmd = ["cargo","build","--release","--bins"]
    console.print(f"[dim]$ {' '.join(cmd)}[/]\n")
    start = time.time()
    proc  = subprocess.Popen(cmd, cwd=ROOT/"rust",
                             stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                             text=True, bufsize=1)
    for line in proc.stdout:
        l = line.rstrip()
        if l.startswith("error"):    console.print(f"[red]{l}[/]",    highlight=False, markup=False)
        elif l.startswith("warning"):console.print(f"[yellow]{l}[/]", highlight=False, markup=False)
        else:                         console.print(f"[dim]{l}[/]",    highlight=False, markup=False)
    proc.wait()
    console.print()
    if proc.returncode == 0:
        console.print(f"[bold green]✓  Built in {time.time()-start:.1f}s[/]")
    else:
        console.print(f"[bold red]✗  Build failed (exit {proc.returncode})[/]")
    console.print("\n[dim]Press Enter.[/]")
    try: input()
    except (KeyboardInterrupt, EOFError): pass

# ── Topic picker ───────────────────────────────────────────────────────────────

FREE_TOPICS = [
    "Trade-offs between consistency and availability in distributed systems",
    "Why do large language models sometimes confidently produce wrong answers?",
    "How should autonomous AI agents decide when to ask for human help?",
    "What makes a good abstraction in software engineering?",
    "Can emergent communication between AI agents lead to genuinely novel representations?",
]

def pick_free_topic() -> Optional[str]:
    console.print("\n  [bold yellow]Free discussion — choose a topic:[/]")
    for i, t in enumerate(FREE_TOPICS, 1):
        console.print(f"  [dim cyan]{i}.[/]  {t}")
    console.print(f"  [dim cyan]{len(FREE_TOPICS)+1}.[/]  Enter custom topic")
    try:
        idx = int(Prompt.ask("  Choice", default="1").strip()) - 1
        return FREE_TOPICS[idx] if 0 <= idx < len(FREE_TOPICS) else Prompt.ask("  Topic")
    except (ValueError, KeyboardInterrupt, EOFError):
        return None

# ── Run a scenario ─────────────────────────────────────────────────────────────

def run_scenario(s: Scenario):
    if not render_scenario_preview(s): return

    cmd = build_cmd(s)
    if not cmd:
        console.clear()
        bin_ = RUST_COMMS if s.kind == "rust-comms" else RUST_TASK
        console.print(f"\n[bold red]Binary not found:[/] {bin_}")
        console.print("[yellow]Press [bold]b[/bold] from the menu to build it.[/]")
        console.print("\n[dim]Press Enter.[/]")
        try: input()
        except (KeyboardInterrupt, EOFError): pass
        return

    col = KIND_COLOR[s.kind]
    ts  = time.strftime("%H:%M:%S")
    console.clear()

    # Run header
    ov  = SETTINGS.overseer_model or "(= model)"
    hdr = Table.grid(padding=(0,2))
    hdr.add_column(); hdr.add_column()
    hdr.add_row(Text(f"▶  {s.label}", style=f"bold {col}"),
                Text(f"started {ts}", style="dim"))
    hdr.add_row(Text(f"model: {SETTINGS.model}  ·  overseer: {ov}", style="dim"),
                Text(f"rounds: {SETTINGS.rounds}  ·  exchanges: {SETTINGS.exchanges}", style="dim"))
    cmd_display = " ".join(cmd)
    if len(cmd_display) > 88: cmd_display = cmd_display[:85] + "…"
    console.print(Panel(hdr, border_style=col, padding=(0,1)))
    console.print(f"[dim]$ {cmd_display}[/]")
    console.print(Rule(style=col)); console.print()

    start = time.time(); exit_code = -1
    try:
        proc = subprocess.Popen(cmd,
                                cwd=str(PYTHON_DIR) if s.kind=="py-loop" else str(ROOT),
                                stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                text=True, bufsize=1,
                                env={**os.environ, "PYTHONPATH": str(PYTHON_DIR)})
        for line in proc.stdout:
            console.print(line, end="", highlight=False, markup=False)
        proc.wait(); exit_code = proc.returncode
    except KeyboardInterrupt:
        proc.terminate(); console.print("\n[yellow]Interrupted.[/]")
    except Exception as e:
        console.print(f"\n[bold red]Error:[/] {e}"); return

    elapsed = time.time() - start
    console.print(); console.print(Rule(style=col))
    if exit_code == 0:
        console.print(f"[bold green]✓  Finished[/]  —  {int(elapsed//60)}m {int(elapsed%60)}s")
    else:
        console.print(f"[bold red]✗  Exit {exit_code}[/]  —  {int(elapsed//60)}m {int(elapsed%60)}s")

    session_path = None
    if s.kind == "rust-comms" and exit_code == 0:
        session_path = find_latest_session(s.task or "")

    run_history.append(RunRecord(s.label, exit_code, elapsed, ts, session_path))

    console.print()
    if session_path:
        console.print("  [dim]Press [bold]d[/bold] for dashboard  ·  Enter to return[/]")
    else:
        console.print("  [dim]Press Enter to return.[/]")
    try:
        if input("  > ").strip().lower() == "d" and session_path:
            try:
                render_comms_dashboard(json.loads(session_path.read_text()), elapsed)
                console.print("\n[dim]Press Enter.[/]"); input()
            except Exception as e:
                console.print(f"[red]Dashboard error:[/] {e}"); input()
    except (KeyboardInterrupt, EOFError): pass

# ── Main ───────────────────────────────────────────────────────────────────────

SCENARIO_MAP = {str(s.sid): s for s in SCENARIOS}

FREE_TOPICS_EXTRA = [
    "Trade-offs between consistency and availability in distributed systems",
    "Why do large language models sometimes confidently produce wrong answers?",
    "How should autonomous AI agents decide when to ask for human help?",
    "What makes a good abstraction in software engineering?",
]

def main():
    checks = run_checks()
    if any(not d.ok or d.warning for d in checks):
        show_prereq_screen()

    while True:
        render_menu()
        try: raw = input("  > ").strip().lower()
        except (KeyboardInterrupt, EOFError): raw = "q"

        if   raw == "q": console.print("\n[dim]Bye.[/]\n"); break
        elif raw == "s": edit_settings()
        elif raw == "b": build_rust()
        elif raw == "c": show_prereq_screen(force=True)
        elif raw in SCENARIO_MAP:
            s = SCENARIO_MAP[raw]
            if s.task == "free" and not s.topic:
                topic = pick_free_topic()
                if topic: s = dc_replace(s, topic=topic)
            run_scenario(s)
        else:
            console.print(f"[red]Unknown:[/] {raw!r}  [dim](number / s / b / c / q)[/]")
            time.sleep(1)

if __name__ == "__main__":
    main()
