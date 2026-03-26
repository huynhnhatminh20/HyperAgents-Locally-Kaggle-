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

This fork adds **local Ollama support** so you can run the entire loop on your own machine.

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

# Automated setup
bash setup_local.sh

# Or manual:
python3 -m venv venv && source venv/bin/activate
pip install -r requirements_local.txt
cp .env.example .env

# Run the self-improvement loop!
python generate_loop_local.py --domain text_classify --model ollama/llama3.2
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

## Supported Models

| Model | Best For | Size |
|-------|----------|------|
| `ollama/llama3.2` | General purpose | 3B |
| `ollama/codellama` | Code generation | 7B |
| `ollama/deepseek-coder-v2` | Strong coding | 16B |
| `ollama/qwen2.5-coder` | Code + reasoning | 7B |
| `ollama/mistral` | Fast general use | 7B |

> **Tip:** Larger models produce better self-improvements but run slower. Start with `llama3.2` to verify setup, then scale up.

## Configuration

Copy `.env.example` to `.env` and adjust:

```bash
OLLAMA_BASE_URL=http://localhost:11434  # Ollama server URL
MODEL_NAME=ollama/llama3.2              # Default model
MAX_TOKENS=4096                         # Token limit (adjust for model)
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
