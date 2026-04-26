param(
    [string]$KaggleJsonPath = "$HOME\Downloads\kaggle.json",
    [switch]$InstallCli,
    [switch]$CreateVenv,
    [string]$VenvDir = "venv"
)

$ErrorActionPreference = "Stop"

function Get-PythonCommand {
    foreach ($candidate in @("py -3", "python", "python3")) {
        try {
            & cmd /c "$candidate --version" *> $null
            if ($LASTEXITCODE -eq 0) {
                return $candidate
            }
        } catch {
        }
    }

    return $null
}

function Invoke-Python {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Command,
        [Parameter(Mandatory = $true)]
        [string[]]$Args
    )

    if ($Command -eq "py -3") {
        & py -3 @Args
        return
    }

    & $Command @Args
}

$repoRoot = Split-Path -Parent $PSScriptRoot
$destDir = Join-Path $HOME ".kaggle"
$destFile = Join-Path $destDir "kaggle.json"

if (-not (Test-Path -LiteralPath $KaggleJsonPath)) {
    throw "Cannot find kaggle.json at '$KaggleJsonPath'. Pass -KaggleJsonPath explicitly if your file lives elsewhere."
}

New-Item -ItemType Directory -Path $destDir -Force | Out-Null
if (Test-Path -LiteralPath $destFile) {
    $sourceHash = (Get-FileHash -LiteralPath $KaggleJsonPath -Algorithm SHA256).Hash
    $destHash = (Get-FileHash -LiteralPath $destFile -Algorithm SHA256).Hash
    if ($sourceHash -eq $destHash) {
        Write-Host "Credentials already present at $destFile"
    } else {
        Copy-Item -LiteralPath $KaggleJsonPath -Destination $destFile -Force
        Write-Host "Updated credentials at $destFile"
    }
} else {
    Copy-Item -LiteralPath $KaggleJsonPath -Destination $destFile -Force
    Write-Host "Copied credentials to $destFile"
}

$pythonCommand = Get-PythonCommand
if (-not $pythonCommand) {
    Write-Warning "No working Python interpreter found. Install Python 3.10+ first, then rerun this script with -InstallCli."
    exit 0
}

Write-Host "Using Python command: $pythonCommand"

if ($CreateVenv) {
    $venvPath = Join-Path $repoRoot $VenvDir
    if (-not (Test-Path -LiteralPath $venvPath)) {
        Write-Host "Creating virtual environment at $venvPath"
        Invoke-Python -Command $pythonCommand -Args @("-m", "venv", $venvPath)
    }
}

if ($InstallCli) {
    $pipArgs = @("-m", "pip", "install", "--upgrade", "pip", "kaggle")
    if ($CreateVenv) {
        $venvPython = Join-Path $repoRoot $VenvDir
        $venvPython = Join-Path $venvPython "Scripts\python.exe"
        $venvKaggle = Join-Path $repoRoot $VenvDir
        $venvKaggle = Join-Path $venvKaggle "Scripts\kaggle.exe"
        if (-not (Test-Path -LiteralPath $venvPython)) {
            throw "Expected venv Python at '$venvPython' but it does not exist."
        }

        & $venvPython @pipArgs
        if (Test-Path -LiteralPath $venvKaggle) {
            & $venvKaggle --version
        } else {
            & $venvPython -m kaggle.cli --version
        }
    } else {
        Invoke-Python -Command $pythonCommand -Args $pipArgs
        Invoke-Python -Command $pythonCommand -Args @("-m", "kaggle.cli", "--version")
    }
}

Write-Host ""
Write-Host "Next checks:"
Write-Host "  1. If you want repo-local setup: .\scripts\setup_kaggle.ps1 -InstallCli -CreateVenv"
Write-Host "  2. Then verify auth:        .\venv\Scripts\kaggle.exe config view"
Write-Host "  3. Test the API:            .\venv\Scripts\kaggle.exe datasets list -s titanic"
