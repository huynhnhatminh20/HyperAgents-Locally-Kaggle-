Kaggle kernel template for running the bundled HyperAgents repo on Kaggle.

Build the pushable bundle from the repo root:

    python3 scripts/build_kaggle_kernel.py

Then push it from WSL:

    kaggle kernels push -p dist/kaggle_kernel --accelerator NvidiaTeslaT4

Before running on Kaggle, make sure the kernel has access to:

- internet enabled
- a secret or environment variable named `OPENROUTER_API_KEY`

Optional runtime overrides:

- `MODEL_NAME`
- `MAX_TOKENS`
- `HYPERAGENTS_MAX_GENERATION`
- `HYPERAGENTS_NUM_SAMPLES`
- `HYPERAGENTS_NUM_WORKERS`
