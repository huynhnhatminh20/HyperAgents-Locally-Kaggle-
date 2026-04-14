#!/usr/bin/env bash
# HyperAgents-Ollama — one-command installer
# Usage: bash install.sh [--mlx] [--rust]
#   --mlx   also install Apple Silicon MLX support
#   --rust  also build the Rust binary
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

MLX=0
BUILD_RUST=0
for arg in "$@"; do
  case $arg in
    --mlx)  MLX=1 ;;
    --rust) BUILD_RUST=1 ;;
  esac
done

echo "================================================================"
echo "  HyperAgents-Ollama — Setup"
echo "================================================================"

# ── 1. Python version check ─────────────────────────────────────────
if ! command -v python3 &>/dev/null; then
  echo "ERROR: python3 not found. Install Python 3.10+ first." && exit 1
fi
PY_VER=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
PY_MAJOR=$(echo "$PY_VER" | cut -d. -f1)
PY_MINOR=$(echo "$PY_VER" | cut -d. -f2)
if [ "$PY_MAJOR" -lt 3 ] || { [ "$PY_MAJOR" -eq 3 ] && [ "$PY_MINOR" -lt 10 ]; }; then
  echo "ERROR: Python 3.10+ required (found $PY_VER)." && exit 1
fi
echo "  Python $PY_VER ✓"

# ── 2. Virtual environment ──────────────────────────────────────────
if [ ! -d venv ]; then
  echo "  Creating virtual environment..."
  python3 -m venv venv
fi
# shellcheck disable=SC1091
source venv/bin/activate
echo "  Virtual environment active ✓"

# ── 3. Pip install ──────────────────────────────────────────────────
echo "  Installing Python dependencies..."
pip install --quiet --upgrade pip
pip install --quiet -r requirements_local.txt

if [ "$MLX" -eq 1 ]; then
  echo "  Installing MLX support (Apple Silicon)..."
  pip install --quiet "mlx-lm>=0.22.0"
fi
echo "  Python dependencies installed ✓"

# ── 4. .env file ────────────────────────────────────────────────────
if [ ! -f .env ]; then
  cp .env.example .env
  echo "  Created .env from .env.example — edit it to add your API keys ✓"
else
  echo "  .env already exists ✓"
fi

# ── 5. Rust binary (optional) ───────────────────────────────────────
if [ "$BUILD_RUST" -eq 1 ]; then
  if ! command -v cargo &>/dev/null; then
    echo "  WARNING: cargo not found — skipping Rust build."
    echo "           Install Rust: https://rustup.rs"
  else
    echo "  Building Rust binary (this takes ~30s)..."
    (cd rust && cargo build --release --quiet)
    echo "  Rust binary: rust/target/release/hyperagents ✓"
  fi
fi

echo ""
echo "================================================================"
echo "  Setup complete!"
echo "================================================================"
echo ""
echo "  Activate environment:"
echo "    source venv/bin/activate"
echo ""
echo "  Run the hyper loop (Python):"
echo "    python generate_loop_local.py --domain factory \\"
echo "      --model ollama/gemma4:e4b --max-generation 8 --verbose"
echo ""
if [ "$BUILD_RUST" -eq 1 ] && command -v cargo &>/dev/null; then
echo "  Run the hyper loop (Rust):"
echo "    ./rust/target/release/hyperagents --domain factory \\"
echo "      --model ollama/gemma4:e4b --max-generation 8 --verbose"
echo ""
fi
echo "  Domains: text_classify  emotion  rust  factory  search_arena  paper_review"
echo "  Edit .env to configure your model and API keys."
echo ""
