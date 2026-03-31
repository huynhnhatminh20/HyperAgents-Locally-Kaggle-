#!/bin/bash
# ============================================================================
# HyperAgents-Ollama: Grand Tour Benchmark
# ============================================================================
set -e

MODEL=${1:-"ollama/qwen3.5"}
GENS=${2:-2}
SAMPLES=${3:-5}
WORKERS=${4:-4}

echo "🧬 Starting HyperAgents Grand Tour..."
echo "Model:   $MODEL"
echo "Gens:    $GENS"
echo "Samples: $SAMPLES"
echo "Workers: $WORKERS"
echo "============================================================"

DOMAINS=("text_classify" "search_arena" "paper_review")

for DOMAIN in "${DOMAINS[@]}"; do
    echo ""
    echo "🎯 TARGET DOMAIN: $DOMAIN"
    echo "------------------------------------------------------------"
    bash run_local_isolated.sh \
        --domain "$DOMAIN" \
        --model "$MODEL" \
        --max-generation "$GENS" \
        --num-samples "$SAMPLES" \
        --num-workers "$WORKERS"
done

echo ""
echo "============================================================"
echo "✅ Grand Tour Complete!"
echo "Check your outputs directory to see the evolved 'Incredible' agents."
