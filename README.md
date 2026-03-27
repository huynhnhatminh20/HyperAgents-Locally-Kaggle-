# 🧬 HyperAgents-Ollama

**Self-Improving AI Agents with Local Models**

A fork of [facebookresearch/HyperAgents](https://github.com/facebookresearch/HyperAgents) that runs entirely locally using [Ollama](https://ollama.ai) — no cloud API keys required.

> **Paper:** [Hyperagents](https://arxiv.org/abs/2603.19461) — Self-referential agents that integrate a task agent and a meta agent into a single editable program, enabling metacognitive self-modification.

## What is this?

HyperAgents is a framework where AI agents **improve themselves**:

1. A **Task Agent** solves a given problem
2. A **Meta Agent** modifies the Task Agent's code to make it better
3. The modified agent is evaluated, and the best variants survive
4. Repeat — the agents evolve and get better over time

This fork adds **local Ollama support**, **Windows support for the local workflow**, and **MLX support for Apple Silicon Macs** so you can run the entire loop on your own machine.

## Quick Start

### 1. Install Ollama

```bash
# macOS
brew install ollama

# Linux
curl -fsSL https://ollama.com/install.sh | sh

# Start the server
ollama serve
```

On Windows, install Ollama from `https://ollama.com/download/windows` and start it from the desktop app or with:

```powershell
ollama serve
```

### 2. Pull a Model

```bash
ollama pull llama3.2          # Good general-purpose (3B)
ollama pull codellama          # Better for code tasks
ollama pull deepseek-coder-v2  # Strong coding model
ollama pull qwen2.5-coder      # Great coding model
ollama pull mistral            # Fast and capable
```

### 3. Setup & Run

```bash
git clone https://github.com/quantumnic/HyperAgents-Ollama.git
cd HyperAgents-Ollama

# Automated setup (macOS / Linux)
bash setup_local.sh

# Automated setup (Windows PowerShell)
powershell -ExecutionPolicy Bypass -File .\setup_local.ps1

# Or manual (macOS / Linux):
python3 -m venv venv && source venv/bin/activate
pip install -r requirements_local.txt
cp .env.example .env

# Manual (Windows PowerShell):
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements_local.txt
Copy-Item .env.example .env

# Run the self-improvement loop!
python generate_loop_local.py --domain text_classify --model ollama/llama3.2
```

If your repo has local changes, use the isolated runner instead of calling `generate_loop_local.py` directly. This avoids the loop's `git reset --hard` and `git clean -fd` from touching your working tree.

```powershell
.\run_local_isolated.ps1 -Domain text_classify -Model ollama/llama3.2 -MaxGeneration 1 -NumSamples 3
```

### 4. Watch it evolve 🧬

```
============================================================
HyperAgents Local Loop
  Model:      ollama/llama3.2
  Domain:     text_classify
  Gens:       5
============================================================

Generation 1/5 — Score: 0.650 | Parent: initial
Generation 2/5 — Score: 0.700 | Parent: 1
Generation 3/5 — Score: 0.750 | Parent: 2 ⭐
...
```

## Usage

```bash
# Basic run with text classification demo
python generate_loop_local.py --domain text_classify

# Use a specific model
python generate_loop_local.py --model ollama/codellama --domain text_classify

# More generations
python generate_loop_local.py --max-generation 10

# Custom output directory
python generate_loop_local.py --output-dir ./my_experiments

# Test your LLM connection
python agent/llm.py
```

Windows notes:

- Install Git for Windows and make sure `git` is on `PATH`.
- Use PowerShell or Windows Terminal for the local workflow.
- The built-in shell tool automatically uses PowerShell or `cmd` on Windows instead of `/bin/bash`.
- Use `.\run_local_isolated.ps1` when you want a disposable temp-repo run on Windows.

### MLX Models (Apple Silicon Macs)

Run models natively on your Mac's GPU using [mlx-lm](https://github.com/ml-explore/mlx-examples/tree/main/llms) — no Ollama required.

```bash
# Install MLX dependencies
pip install -r requirements_mlx.txt

# Run with an MLX model (downloads from HuggingFace on first use)
python generate_loop_local.py --domain text_classify \
  --model mlx/BeastCode/Qwen3.5-27B-Claude-4.6-Opus-Distilled-MLX-4bit

# Or use any HuggingFace MLX model repo
python generate_loop_local.py --domain text_classify \
  --model mlx/mlx-community/Llama-3.2-3B-Instruct-4bit

# Use a local model path via environment variable
export MLX_MODEL_PATH=/path/to/your/local/mlx-model
python generate_loop_local.py --domain text_classify --model mlx/my-model

# Test MLX connection
python agent/llm.py
```

> **Note:** MLX models use the `mlx/` prefix. The part after `mlx/` is passed directly to `mlx_lm.load()` — it can be a HuggingFace repo ID or a local path.

## Supported Models

### Ollama

| Model | Best For | Size |
|-------|----------|------|
| `ollama/llama3.2` | General purpose | 3B |
| `ollama/codellama` | Code generation | 7B |
| `ollama/deepseek-coder-v2` | Strong coding | 16B |
| `ollama/qwen2.5-coder` | Code + reasoning | 7B |
| `ollama/mistral` | Fast general use | 7B |

### MLX (Apple Silicon only)

| Model | Best For | Size |
|-------|----------|------|
| `mlx/BeastCode/Qwen3.5-27B-Claude-4.6-Opus-Distilled-MLX-4bit` | Code + reasoning (Claude distilled) | 27B 4-bit |
| `mlx/mlx-community/Llama-3.2-3B-Instruct-4bit` | Fast general purpose | 3B 4-bit |

> **Tip:** Larger models produce better self-improvements but run slower. Start with a small model to verify setup, then scale up.

## Configuration

Copy `.env.example` to `.env` and adjust:

```bash
OLLAMA_BASE_URL=http://localhost:11434  # Ollama server URL
MODEL_NAME=ollama/llama3.2              # Default model
MAX_TOKENS=4096                         # Token limit (adjust for model)

# MLX models (Apple Silicon)
# MODEL_NAME=mlx/BeastCode/Qwen3.5-27B-Claude-4.6-Opus-Distilled-MLX-4bit
# MLX_MODEL_PATH=/path/to/local/model  # Optional: override with local path
```

## Cloud APIs (Optional)

You can still use cloud APIs by setting the appropriate keys in `.env`:

```bash
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
GEMINI_API_KEY=...
MODEL_NAME=openai/gpt-4o  # or anthropic/claude-3-5-sonnet-20241022
```

Then run with the Docker-based loop:
```bash
pip install -r requirements.txt
docker build -t hyperagents .
python generate_loop.py --domains paper_review
```

## Project Structure

```
├── generate_loop_local.py   # 🆕 Docker-free local runner
├── generate_loop.py         # Original Docker-based runner
├── agent/
│   ├── llm.py               # LLM interface (Ollama + cloud)
│   ├── base_agent.py        # Base agent class
│   └── llm_withtools.py     # Tool-using agent
├── meta_agent.py            # Self-modification agent
├── task_agent.py             # Task-solving agent
├── domains/
│   ├── text_classify/        # 🆕 Simple demo domain
│   ├── paper_review/         # Academic paper review
│   ├── search_arena/         # Search quality
│   └── ...
├── requirements_local.txt    # 🆕 Minimal local dependencies
├── requirements_mlx.txt      # 🆕 MLX dependencies (Apple Silicon)
├── setup_local.sh            # 🆕 Local setup script
└── .env.example              # 🆕 Environment template
```

## How It Works

```
┌─────────────────────────────────────────────┐
│              Generation Loop                │
│                                             │
│  1. Select parent from archive              │
│  2. Meta Agent modifies Task Agent code     │
│  3. Evaluate modified Task Agent            │
│  4. Store result → archive                  │
│  5. Repeat                                  │
│                                             │
│  ┌──────────┐    modifies    ┌───────────┐  │
│  │Meta Agent│───────────────▶│Task Agent │  │
│  │          │                │           │  │
│  │(improves │   ┌────────┐  │ (solves   │  │
│  │ itself!) │◀──│Archive │──│  tasks)   │  │
│  └──────────┘   └────────┘  └───────────┘  │
└─────────────────────────────────────────────┘
```

## Citation

```bibtex
@misc{zhang2026hyperagents,
  title={Hyperagents},
  author={Jenny Zhang and Bingchen Zhao and Wannan Yang and Jakob Foerster and Jeff Clune and Minqi Jiang and Sam Devlin and Tatiana Shavrina},
  year={2026},
  eprint={2603.19461},
  archivePrefix={arXiv},
  primaryClass={cs.AI},
  url={https://arxiv.org/abs/2603.19461},
}
```

## License

See [LICENSE.md](LICENSE.md) for the original Meta license.
