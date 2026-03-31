# 🧬 HyperAgents-Ollama

**Self-Improving AI Agents with Local Models**

A fork of [facebookresearch/HyperAgents](https://github.com/facebookresearch/HyperAgents) that runs entirely locally using [Ollama](https://ollama.ai) or [MLX](https://github.com/ml-explore/mlx-examples) — no cloud API keys required.

> **Paper:** [Hyperagents](https://arxiv.org/abs/2603.19461) — Self-referential agents that integrate a task agent and a meta agent into a single editable program, enabling metacognitive self-modification.

## What is this?

HyperAgents is a framework where AI agents **improve themselves**:

1.  **Task Agent:** Solves a given problem using internal **Chain of Thought (CoT)** reasoning.
2.  **Meta Agent:** Studies the Task Agent's source code and failure cases to modify and improve it.
3.  **Evolution Loop:** The agents evolve over generations, with the best variants surviving and breeding.

This fork adds **local Ollama support**, **Parallel Evaluation**, **Domain-Aware Meta-Agents**, and **macOS/Windows isolated runners** so you can safely run the entire loop on your own machine.

---

## ✨ Incredible New Features

-   **🧠 Chain of Thought (CoT):** The TaskAgent now uses a `ThoughtLog` to reason before answering, providing the Meta-Agent with a rich internal "trace" to optimize.
-   **🔍 Domain-Aware Meta-Agent:** The Meta-Agent now reads the current `task_agent.py` source code and the domain's `dataset.py` to make strategic, data-driven modifications.
-   **⚡ Parallel Evaluation:** Run evaluations across multiple CPU cores with `--num-workers` to speed up the evolution loop by up to 10x.
-   **🌱 Evolution Tree:** Visualize the "tree of life" of your agents directly in the terminal with ASCII lineage and score tracking.
-   **🛠️ Fuzzy JSON Parsing:** Robust handling of minor formatting errors common in smaller local models (like Llama 3.2).
-   **🛡️ Isolated Runners:** Use `run_local_isolated.sh` (macOS/Linux) or `run_local_isolated.ps1` (Windows) to run experiments in a temporary repository without touching your active code.

---

## Quick Start

### 1. Setup & Pull Models
Follow the [Ollama installation guide](https://ollama.ai) and pull your preferred models:
```bash
ollama pull qwen2.5-coder      # Recommended for Meta-Agent
ollama pull llama3.2          # Fast for Task-Agent
```

### 2. Isolated Run (Recommended)
Run a safe evolution experiment in a temporary directory:
```bash
# macOS / Linux
bash run_local_isolated.sh --domain text_classify --model ollama/qwen2.5-coder --max-generation 5

# Windows (PowerShell)
.\run_local_isolated.ps1 -Domain text_classify -Model ollama/qwen2.5-coder -MaxGeneration 5
```

### 3. The "Grand Tour" Benchmark
Test the system's "Incredible" state across multiple domains automatically:
```bash
bash run_all_benchmarks.sh ollama/qwen2.5-coder 2 5 4
```

---

## Watch it evolve 🧬

```
🌱 Evolution Tree:
└── Gen initial (Score: 0.650)
    ├── Gen 1 (Score: 0.700)
    │   └── Gen 3 (Score: 0.850) ⭐
    └── Gen 2 (Score: 0.680)

Best: Gen 3 with score 0.850
Best agent source exported to: ./outputs_local/run_XXXX/best_task_agent.py
```

---

## Usage & Configuration

### Parallelism
Use `--num-workers` to speed up evaluation:
```bash
python generate_loop_local.py --domain search_arena --num-workers 8
```

### MLX Models (Apple Silicon Macs)
Run models natively on your GPU using `mlx-lm`:
```bash
python generate_loop_local.py --domain text_classify --model mlx/mlx-community/Llama-3.2-3B-Instruct-4bit
```

### Configuration (.env)
Copy `.env.example` to `.env` to set your local Ollama URL and default model names.

---

## Project Structure

```
├── generate_loop_local.py   # 🚀 Parallelized local runner with Tree Viz
├── run_local_isolated.sh    # 🛡️ Safe isolated runner (macOS/Linux)
├── run_all_benchmarks.sh    # 🎯 Multi-domain benchmark suite
├── agent/
│   ├── llm.py               # LLM interface (Ollama, MLX, Cloud)
│   └── llm_withtools.py     # Tool loop with Fuzzy JSON parsing
├── meta_agent.py            # 🧠 Source-aware self-modification agent
├── task_agent.py             # 🔍 CoT-enabled task-solving agent
├── domains/
│   ├── text_classify/        # Simple baseline
│   ├── search_arena/         # Search quality
│   └── paper_review/         # Academic reasoning
└── GEMINI.md                # 🧬 Detailed instructional context for AI agents
```

## Citation & License
See the original [Hyperagents Paper](https://arxiv.org/abs/2603.19461) and [LICENSE.md](LICENSE.md).
