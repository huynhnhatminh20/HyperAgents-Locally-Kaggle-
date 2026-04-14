# HyperAgents-Ollama

**Self-Improving AI Agents — Local, Cloud, or Free**

A fork of [facebookresearch/HyperAgents](https://github.com/facebookresearch/HyperAgents) extended with local Ollama, Apple Silicon MLX, OpenRouter cloud gateway, and a Rust port of the evolution loop.

> **Paper:** [Hyperagents](https://arxiv.org/abs/2603.19461) — Self-referential agents that integrate a task agent and a meta agent into a single editable program, enabling metacognitive self-modification.

---

## How it works

```
┌─────────────────────────────────────────────────────────┐
│  Hyper Loop                                             │
│                                                         │
│  Gen 0:  TaskAgent solves tasks  →  baseline score      │
│                                                         │
│  Gen N:  MetaAgent (expert) reads:                      │
│            • task_agent.py source code                  │
│            • failure cases from last eval               │
│            • previous patch history                     │
│          → rewrites task_agent.py                       │
│          TaskAgent (new version) → new score            │
│          Best score survives, tree grows                │
└─────────────────────────────────────────────────────────┘
```

- **Task Agent** (`python/task_agent.py`) — solves domain tasks with Chain-of-Thought reasoning
- **Meta Agent** (`python/meta_agent.py`) — studies failures and rewrites the Task Agent's code
- **Evolution Loop** — iterates for N generations, selecting the best-scoring lineage

---

## Install

```bash
git clone <repo>
cd HyperAgents-Ollama
bash install.sh          # Python venv + dependencies
bash install.sh --rust   # also build the Rust binary (~30s)
bash install.sh --mlx    # also install Apple Silicon MLX support
```

Then edit `.env` to set your model and API keys (created automatically from `.env.example`).

---

## Configuration (`.env`)

```bash
# ── Local Ollama ──────────────────────────────────────
OLLAMA_BASE_URL=http://localhost:11434
MODEL_NAME=ollama/gemma4:e4b        # any model you have pulled

# ── Apple Silicon (MLX) ──────────────────────────────
# MODEL_NAME=mlx/BeastCode/Qwen3.5-27B-Claude-4.6-Opus-Distilled-MLX-4bit

# ── OpenRouter (300+ models, many free) ──────────────
# OPENROUTER_API_KEY=sk-or-...
# MODEL_NAME=openrouter/google/gemma-3-4b-it:free
```

### OpenRouter free models

| Model | `MODEL_NAME` |
|---|---|
| Gemma 3 4B | `openrouter/google/gemma-3-4b-it:free` |
| Llama 4 Scout | `openrouter/meta-llama/llama-4-scout:free` |
| Qwen3 8B | `openrouter/qwen/qwen3-8b:free` |
| DeepSeek R1 | `openrouter/deepseek/deepseek-r1-0528:free` |

> **Note:** Free models are rate-limited to 20 req/min — use `--num-workers 1`.

---

## Python — Running the hyper loop

```bash
# Activate venv first
source venv/bin/activate

# Ollama (local) — factory domain (hardest, 5-class)
python python/loop.py --domain factory --model ollama/gemma4:e4b --max-generation 8 --num-workers 3 --verbose

# OpenRouter — Gemma 3 4B (free, num-workers 1)
python python/loop.py --domain factory --model openrouter/google/gemma-3-4b-it:free --max-generation 8 --num-workers 1 --verbose

# OpenRouter — Qwen3 8B (free, num-workers 1)
python python/loop.py --domain factory --model openrouter/qwen/qwen3-8b:free --max-generation 8 --num-workers 1 --verbose

# Apple Silicon MLX
python python/loop.py --domain factory --model mlx/BeastCode/Qwen3.5-27B-Claude-4.6-Opus-Distilled-MLX-4bit --max-generation 5
```

### All options

```
python python/loop.py [OPTIONS]

  --domain           {text_classify, emotion, rust, factory, search_arena, paper_review}
  --model            Model string (ollama/*, openrouter/*, mlx/*)
  --max-generation   Number of evolution generations  [default: 5]
  --num-samples      Samples per eval, -1 for all     [default: -1]
  --num-workers      Parallel eval threads            [default: 4]
  --parent-selection {best, latest, proportional}     [default: best]
  --output-dir       Where to write results           [default: ./outputs_local]
  --verbose / -v     Stream all subprocess output live
```

### 3-terminal workflow

**Terminal 1 — run**
```bash
source venv/bin/activate
python python/loop.py --domain factory --model openrouter/google/gemma-3-4b-it:free --max-generation 8 --num-samples 20 --num-workers 1 --verbose > /tmp/hyperloop.log 2>&1
```

**Terminal 2 — live log**
```bash
tail -f /tmp/hyperloop.log
```

**Terminal 3 — score graph**
```bash
watch -n3 'LATEST=$(ls outputs_local/ | sort | tail -1) && echo "Run: $LATEST" && cat outputs_local/$LATEST/archive.jsonl 2>/dev/null | python3 -c "import sys,json
for line in sys.stdin:
    r=json.loads(line)
    bar=\"#\"*int(r.get(\"score\",0)*30)
    print(f\"  Gen {r[\"gen\"]:>2}  {r.get(\"score\",0):.3f}  {bar}\")
" || echo "  waiting..."'
```

---

## Rust — Running the hyper loop

### Build

```bash
# Via install script (recommended)
bash install.sh --rust

# Or directly
cd rust && cargo build --release
# binary: rust/target/release/hyperagents
```

### Run

```bash
# Ollama (local) — factory domain
./rust/target/release/hyperagents --domain factory --model ollama/qwen2.5-coder:7b --max-generation 8 --num-workers 4 --parent-selection best --verbose

# OpenRouter — Gemma 3 4B (free, num-workers 1)
./rust/target/release/hyperagents --domain factory --model openrouter/google/gemma-3-4b-it:free --max-generation 8 --num-workers 1 --verbose

# OpenRouter — Qwen3 8B (free, num-workers 1)
./rust/target/release/hyperagents --domain factory --model openrouter/qwen/qwen3-8b:free --max-generation 8 --num-workers 1 --verbose
```

Or via cargo:

```bash
cd rust && cargo run --release -- --domain factory --model openrouter/google/gemma-3-4b-it:free --max-generation 8 --num-workers 1 --verbose
```

### All Rust options

```
hyperagents [OPTIONS]

  --domain           {text_classify, emotion, factory, search_arena, paper_review}
  --model            Model string (ollama/*, openrouter/*)  [default: ollama/llama3.2]
  --max-generation   Evolution generations                  [default: 5]
  --num-samples      Samples per eval, -1 for all          [default: -1]
  --num-workers      Rayon parallel threads                [default: 4]
  --output-dir       Output directory                       [default: ./outputs_local]
  --parent-selection {best, latest, proportional}          [default: best]
  --verbose / -v     Verbose output
```

---

## Domains

| Domain | Labels | Description | Python | Rust |
|---|---|---|:---:|:---:|
| `text_classify` | positive / negative / neutral | Sentiment classification — good baseline | ✓ | ✓ |
| `emotion` | joy / anger / fear / … | Emotion classification | ✓ | ✓ |
| `factory` | expedite / prioritize_urgent / rebalance / batch_production / optimize_throughput | Virtual factory floor dispatch — 5-class, rule-based, hardest | ✓ | ✓ |
| `rust` | compiles / borrow_error / type_error | Rust compile-error classification | ✓ | — |
| `search_arena` | a / b | Which of two search responses is better (CSV dataset required) | ✓ | — |
| `paper_review` | accept / reject / … | Academic paper outcome (CSV dataset required) | ✓ | — |

---

## Reading the results

All output lands in `outputs_local/run_YYYYMMDD_HHMMSS/`:

```
run_20260414_164911/
├── archive.jsonl          # generation scores + lineage
├── best_task_agent.py     # best evolved agent code
├── gen_initial/           # baseline evaluation
├── gen_1/
│   ├── agent_output/
│   │   ├── meta_agent_chat_history.md   # what the expert thought
│   │   └── model_patch.diff             # the code change it made
│   └── agent_evals/
│       └── chat_history_<id>.md         # per-sample reasoning
└── gen_2/ …
```

```bash
# Score summary
cat outputs_local/$(ls outputs_local/ | sort | tail -1)/archive.jsonl

# Best evolved agent
cat outputs_local/$(ls outputs_local/ | sort | tail -1)/best_task_agent.py
```

---

## Project structure

```
├── install.sh                # One-command setup
├── requirements.txt          # Python dependencies
├── .env.example              # Configuration template
├── python/                   # Python implementation
│   ├── loop.py               # Evolution loop — main entry point
│   ├── task_agent.py         # Task agent — evolves each generation
│   ├── meta_agent.py         # Meta agent — reads code + failures, writes patch
│   ├── run_meta_agent.py     # Run meta agent standalone
│   ├── agent/
│   │   ├── llm.py            # LLM interface: Ollama / MLX / OpenRouter
│   │   ├── llm_withtools.py  # Tool-use loop + fuzzy JSON parser
│   │   ├── base_agent.py     # Base agent class
│   │   └── tools/            # Editor + Bash tools
│   ├── domains/
│   │   ├── text_classify/    # Sentiment (20 train / 15 val / 15 test)
│   │   ├── emotion/          # Emotion classification
│   │   ├── factory/          # Virtual factory dispatch (5-class, hardest)
│   │   ├── rust/             # Rust compile-error classification
│   │   ├── search_arena/     # Search quality comparison (CSV)
│   │   ├── paper_review/     # Academic review outcome (CSV)
│   │   ├── harness.py        # Parallel evaluation harness
│   │   └── report.py         # Accuracy + per-label metrics
│   └── utils/
│       ├── git_utils.py      # Git reset / clean / patch apply
│       ├── common.py         # JSON extraction helpers
│       └── thread_logger.py  # Thread-safe file logging
└── rust/                     # Rust port of the evolution loop
    ├── Cargo.toml
    └── src/
        ├── main.rs           # CLI entry point
        ├── runner.rs         # Evolution loop
        ├── llm.rs            # HTTP LLM client (Ollama + OpenRouter)
        ├── agent/            # Task + Meta agent
        ├── domains/          # Domain harness + datasets
        ├── tools/            # Editor + Bash tools
        └── utils/            # Shared utilities
```

---

## Citation & License

See the original [HyperAgents paper](https://arxiv.org/abs/2603.19461) and [LICENSE.md](LICENSE.md).
