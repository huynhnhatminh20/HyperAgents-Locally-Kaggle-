Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

Write-Host "HyperAgents-Ollama Local Setup"
Write-Host "=================================="

if (-not (Test-Path "venv")) {
    Write-Host "Creating virtual environment..."
    python -m venv venv
}

$activateScript = Join-Path "venv" "Scripts/Activate.ps1"
. $activateScript
Write-Host "Virtual environment activated"

Write-Host "Installing dependencies..."
pip install -r requirements_local.txt
Write-Host "Dependencies installed"

Write-Host ""
Write-Host "Checking Ollama..."
if (-not (Get-Command ollama -ErrorAction SilentlyContinue)) {
    Write-Error "Ollama not found. Install it from https://ollama.com/download/windows"
}

Write-Host "Ollama is installed"

try {
    Invoke-RestMethod -Uri "http://localhost:11434/api/tags" -Method Get | Out-Null
    Write-Host "Ollama is running"
}
catch {
    Write-Warning "Ollama is not running. Start it with: ollama serve"
}

$model = if ($env:MODEL_NAME) { $env:MODEL_NAME } else { "ollama/llama3.2" }
$pullModel = if ($model.StartsWith("ollama/")) { $model.Substring(7) } else { $model }

Write-Host ""
Write-Host "Pulling model: $pullModel"
ollama pull $pullModel
Write-Host "Model ready"

if (-not (Test-Path ".env")) {
    Copy-Item ".env.example" ".env"
    Write-Host "Created .env from .env.example"
}

Write-Host ""
Write-Host "=================================="
Write-Host "Setup complete!"
Write-Host ""
Write-Host "Quick start:"
Write-Host "  .\venv\Scripts\Activate.ps1"
Write-Host "  python generate_loop_local.py --domain text_classify --model ollama/llama3.2"
Write-Host ""
Write-Host "Or test the LLM connection:"
Write-Host "  python agent/llm.py"
Write-Host ""
