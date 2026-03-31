# 🧬 HyperAgents-Ollama: Instructional Context

## Project Overview
**HyperAgents-Ollama** is a self-improving AI agent framework that runs locally using [Ollama](https://ollama.ai) or [MLX](https://github.com/ml-explore/mlx-examples) (for Apple Silicon). It is a fork of Meta's [HyperAgents](https://github.com/facebookresearch/HyperAgents), modified for local execution without cloud API dependencies.

The core architecture follows a **self-referential loop**:
1.  **Task Agent (`task_agent.py`):** Solves problems in a specific domain (e.g., sentiment classification, search arena).
2.  **Meta Agent (`meta_agent.py`):** Observes the Task Agent's performance and modifies its source code using `bash` and `edit` tools to improve its score.
3.  **Evolution Loop (`generate_loop_local.py`):** Manages a population of agent variants, selecting the best parents for further improvement and maintaining a git-based archive of patches.

### Key Technologies
- **Python 3.10+**: Primary programming language.
- **litellm**: Unified interface for various LLM backends (Ollama, OpenAI, Claude, etc.).
- **Ollama**: Local LLM server for cross-platform local inference.
- **MLX**: Native local inference on Apple Silicon GPUs via `mlx-lm`.
- **Git**: Used to track agent versions and apply "self-modifications" via diffs.

---

## Building and Running

### Setup
- **macOS / Linux:** `bash setup_local.sh`
- **Windows (PowerShell):** `powershell -ExecutionPolicy Bypass -File .\setup_local.ps1`
- **Manual (Generic):**
    ```bash
    python3 -m venv venv && source venv/bin/activate
    pip install -r requirements_local.txt
    cp .env.example .env
    ```

### Running the Evolution Loop
Run the local generation loop on a specific domain (default: `text_classify`):
```bash
python generate_loop_local.py --domain text_classify --model ollama/llama3.2
```

### Isolated Execution (Safe for Development)
To prevent the loop from wiping your local changes (via `git reset --hard`), use the isolated runner:
- **macOS / Linux:** `bash run_local_isolated.sh --domain text_classify --model ollama/llama3.2`
- **Windows:** `.\run_local_isolated.ps1 -Domain text_classify -Model ollama/llama3.2`

These runners create a temporary repository in your system's `tmp` folder, copy only the necessary files, and run the loop there.

### Testing LLM Connectivity
Verify that your local model (Ollama/MLX) is reachable:
```bash
python agent/llm.py
```

---

### Parallel Evaluation
Evaluation is now significantly faster using the `--num-workers` flag (default: 4). This parallelizes the `harness.py` execution across your CPU cores.

---

## Architecture & File Structure

### Core Logic
- `generate_loop_local.py`: The main driver. Manages generations, parent selection, and evaluation. Now features **Parallel Evaluation**, an **ASCII Evolution Tree**, and automatic **Best Agent Export**.
- `meta_agent.py`: Implementation of the self-improving agent. Now **Domain-Aware**: it studies the current `task_agent.py` source code, the domain's `dataset.py`, and the latest `report.json` to make strategic, data-driven modifications.
- `task_agent.py`: The agent being optimized. Now features a **Chain of Thought (CoT)** architecture with a `ThoughtLog`, giving the Meta-Agent more internal reasoning to tune.

### Agent Infrastructure (`agent/`)
- `llm.py`: Handles model calls (Ollama via `litellm`, MLX via `mlx-lm`, or cloud APIs).
- `llm_withtools.py`: Implements the ReAct-style loop for tool use. Includes **fuzzy JSON parsing** to help smaller local models successfully call tools even with minor formatting errors (like trailing commas).

---

## Evolution & Optimization Strategy

HyperAgents-Ollama doesn't just prompt a model; it evolves a **program**.

1.  **Reasoning:** The `TaskAgent` is encouraged to use Chain of Thought.
2.  **Inspection:** The `MetaAgent` inspects the `TaskAgent`'s source code and failure cases.
3.  **Action:** The `MetaAgent` uses the `editor` tool to rewrite `task_agent.py`—adding few-shot examples, refining prompts, or implementing hardcoded rules based on evaluation feedback.
4.  **Lineage:** The system tracks the "tree of life" for your agents, allowing you to see which modifications led to the biggest breakthroughs.
- `tools/`:
    - `bash.py`: Allows agents to run shell commands.
    - `edit.py`: Allows agents to read and modify files (essential for self-improvement).

### Evaluation Domains (`domains/`)
- `harness.py`: Standard interface for running an agent against a dataset.
- `report.py`: Aggregates evaluation results into JSON reports.
- `text_classify/`: A lightweight sentiment classification baseline for testing.
- `search_arena/`, `paper_review/`, `imo/`: Complex, high-reasoning domains.

---

## Development Conventions

### Self-Modification Loop
- The `MetaAgent` modifies `task_agent.py` (and potentially other files) via the `edit` tool.
- Every generation is stored as a `.diff` file relative to the base commit.
- **Caution:** The loop uses `git reset --hard` and `git clean -fd` to switch between versions. Always develop on a clean branch or use the isolated runner.

### Model Selection
- Models are configured via the `MODEL_NAME` environment variable or the `--model` flag.
- Prefixes:
    - `ollama/`: Uses the Ollama server (e.g., `ollama/llama3.2`).
    - `mlx/`: Uses MLX-LM on Apple Silicon (e.g., `mlx/mlx-community/Llama-3.2-3B-Instruct-4bit`).
    - `openai/`, `anthropic/`, `gemini/`: Uses cloud APIs (requires corresponding keys in `.env`).

### Extending Domains
To add a new task:
1. Create a subdirectory in `domains/`.
2. Implement an evaluator that follows the `domains.harness` interface.
3. Add the domain to the `choices` in `generate_loop_local.py`.
