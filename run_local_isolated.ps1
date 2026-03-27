param(
    [string]$Domain = "text_classify",
    [string]$Model = "",
    [int]$MaxGeneration = 1,
    [int]$NumSamples = 3,
    [string]$OutputDir = ""
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function New-TemporaryDirectory {
    param([string]$Prefix)

    $base = [System.IO.Path]::GetTempPath()
    $name = "{0}{1}" -f $Prefix, [System.Guid]::NewGuid().ToString("N").Substring(0, 8)
    $path = Join-Path $base $name
    return New-Item -ItemType Directory -Path $path -Force
}

function Should-SkipDirectory {
    param([System.IO.DirectoryInfo]$Directory)

    if ($Directory.Name -in @(".git", "outputs_local", "__pycache__", ".vscode", "venv", ".venv")) {
        return $true
    }

    return $Directory.Name -like "outputs_os_parts*"
}

function Should-SkipFile {
    param([System.IO.FileInfo]$File)

    if ($File.Name -eq ".DS_Store") {
        return $true
    }

    return $File.Extension -eq ".pyc"
}

function Copy-RepoTree {
    param(
        [string]$Source,
        [string]$Destination
    )

    Get-ChildItem -LiteralPath $Source -Force | ForEach-Object {
        $target = Join-Path $Destination $_.Name

        if ($_.PSIsContainer) {
            if (Should-SkipDirectory $_) {
                return
            }

            New-Item -ItemType Directory -Path $target -Force | Out-Null
            Copy-RepoTree -Source $_.FullName -Destination $target
            return
        }

        if (Should-SkipFile $_) {
            return
        }

        Copy-Item -LiteralPath $_.FullName -Destination $target
    }
}

$sourceRepo = (Get-Location).Path
$tempRepo = (New-TemporaryDirectory -Prefix "hyperagents_repo_").FullName

if ([string]::IsNullOrWhiteSpace($OutputDir)) {
    $OutputDir = (New-TemporaryDirectory -Prefix "hyperagents_out_").FullName
}
else {
    if (-not (Test-Path -LiteralPath $OutputDir)) {
        New-Item -ItemType Directory -Path $OutputDir -Force | Out-Null
    }
    $OutputDir = (Resolve-Path -LiteralPath $OutputDir).Path
}

Write-Host "Copying repository to $tempRepo"
Copy-RepoTree -Source $sourceRepo -Destination $tempRepo

Push-Location $tempRepo
try {
    git init | Out-Null
    git config user.email run@example.com
    git config user.name run
    git add .
    git commit -m "snapshot" | Out-Null

    if (-not [string]::IsNullOrWhiteSpace($Model)) {
        $env:MODEL_NAME = $Model
    }
    elseif (-not $env:MODEL_NAME) {
        $env:MODEL_NAME = "ollama/llama3.2"
    }

    if (-not $env:MAX_TOKENS) {
        $env:MAX_TOKENS = "1024"
    }

    $runModel = if ($Model) { $Model } else { $env:MODEL_NAME }

    python generate_loop_local.py `
        --domain $Domain `
        --model $runModel `
        --max-generation $MaxGeneration `
        --num-samples $NumSamples `
        --output-dir $OutputDir
}
finally {
    Pop-Location
}

Write-Host ""
Write-Host "Temporary repo: $tempRepo"
Write-Host "Output dir:     $OutputDir"
