#!/bin/bash
# ============================================================================
# HyperAgents-Ollama: Local Setup Script
# ============================================================================
set -e

echo "🚀 HyperAgents-Ollama Local Setup"
echo "=================================="

# 1. Create virtual environment
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi
source venv/bin/activate
echo "✅ Virtual environment activated"

# 2. Install dependencies
echo "📦 Installing dependencies..."
pip install -r requirements_local.txt
echo "✅ Dependencies installed"

# 3. Check Ollama
echo ""
echo "🦙 Checking Ollama..."
if command -v ollama &> /dev/null; then
    echo "✅ Ollama is installed"
    if curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
        echo "✅ Ollama is running"
    else
        echo "⚠️  Ollama is not running. Start it with: ollama serve"
        echo "   (or it may already be running as a service)"
    fi
else
    echo "❌ Ollama not found. Install it from: https://ollama.ai"
    echo "   brew install ollama  (macOS)"
    exit 1
fi

# 4. Pull default model
MODEL=${MODEL_NAME:-"llama3.2"}
# Strip ollama/ prefix for pull command
PULL_MODEL=${MODEL#ollama/}
echo ""
echo "📥 Pulling model: $PULL_MODEL"
ollama pull "$PULL_MODEL"
echo "✅ Model ready"

# 5. Copy .env if not exists
if [ ! -f ".env" ]; then
    cp .env.example .env
    echo "✅ Created .env from .env.example"
fi

echo ""
echo "=================================="
echo "✅ Setup complete!"
echo ""
echo "Quick start:"
echo "  source venv/bin/activate"
echo "  python generate_loop_local.py --domain text_classify --model ollama/llama3.2"
echo ""
echo "Or test the LLM connection:"
echo "  python agent/llm.py"
echo ""
