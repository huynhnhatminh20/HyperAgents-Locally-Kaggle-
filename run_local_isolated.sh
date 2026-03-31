#!/bin/bash
# ============================================================================
# HyperAgents-Ollama: Isolated Local Runner (macOS/Linux)
# ============================================================================
set -e

# Default values
DOMAIN="text_classify"
MODEL=""
MAX_GEN=1
NUM_SAMPLES=3
NUM_WORKERS=4
OUTPUT_DIR=""

# Parse arguments
while [[ "$#" -gt 0 ]]; do
    case $1 in
        --domain) DOMAIN="$2"; shift ;;
        --model) MODEL="$2"; shift ;;
        --max-generation) MAX_GEN="$2"; shift ;;
        --num-samples) NUM_SAMPLES="$2"; shift ;;
        --num-workers) NUM_WORKERS="$2"; shift ;;
        --output-dir) OUTPUT_DIR="$2"; shift ;;
        *) echo "Unknown parameter: $1"; exit 1 ;;
    esac
    shift
done

# Create a truly unique temp directory
TEMP_REPO=$(mktemp -d -t hyperagents_repo_XXXXXXXX)
echo "📂 Created temporary repo at: $TEMP_REPO"

# If output dir not specified, create a temp one too
if [ -z "$OUTPUT_DIR" ]; then
    OUTPUT_DIR=$(mktemp -d -t hyperagents_out_XXXXXXXX)
else
    mkdir -p "$OUTPUT_DIR"
    # Get absolute path
    OUTPUT_DIR=$(cd "$OUTPUT_DIR" && pwd)
fi

# Sync files to temp repo (excluding heavy/sensitive dirs)
echo "📦 Copying files..."
rsync -av --progress . "$TEMP_REPO" \
    --exclude .git \
    --exclude outputs_local \
    --exclude outputs \
    --exclude venv \
    --exclude .venv \
    --exclude __pycache__ \
    --exclude ".DS_Store" \
    --exclude "outputs_os_parts*"

# Switch to temp repo
cd "$TEMP_REPO"

# Initialize a clean git state for the loop's diffing mechanism
echo "🔧 Initializing temporary git state..."
git init -q
git config user.email "run@example.com"
git config user.name "run"
git add .
git commit -m "snapshot" -q

# Set environment variables
if [ -n "$MODEL" ]; then
    export MODEL_NAME="$MODEL"
else
    export MODEL_NAME="${MODEL_NAME:-ollama/llama3.2}"
fi

if [ -z "$MAX_TOKENS" ]; then
    export MAX_TOKENS="4096"
fi

echo "🚀 Starting evolution loop in isolation..."
echo "   Domain: $DOMAIN"
echo "   Model:  $MODEL_NAME"
echo "   Output: $OUTPUT_DIR"
echo "------------------------------------------------------------"

# Run the loop
# We use the python in the current PATH (assumed to be the venv if activated)
python3 generate_loop_local.py \
    --domain "$DOMAIN" \
    --model "$MODEL_NAME" \
    --max-generation "$MAX_GEN" \
    --num-samples "$NUM_SAMPLES" \
    --num-workers "$NUM_WORKERS" \
    --output-dir "$OUTPUT_DIR"

echo "------------------------------------------------------------"
echo "✅ Done!"
echo "Temporary repo: $TEMP_REPO"
echo "Results saved:  $OUTPUT_DIR"
