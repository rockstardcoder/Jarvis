param(
    [Parameter(Mandatory = $true)]
    [string]$InstallDir,

    [string]$PullOllamaModel = "true"
)

$ErrorActionPreference = "Stop"
$log = Join-Path $InstallDir "install_log.txt"

function Write-Step {
    param([string]$Message)
    $line = "[$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')] $Message"
    Add-Content -Path $log -Value $line
    Write-Host $line
}

function Command-Exists {
    param([string]$Name)
    return [bool](Get-Command $Name -ErrorAction SilentlyContinue)
}

function Refresh-Path {
    $machine = [Environment]::GetEnvironmentVariable("Path", "Machine")
    $user = [Environment]::GetEnvironmentVariable("Path", "User")
    $env:Path = "$machine;$user"
}

function Install-WingetPackage {
    param(
        [string]$PackageId,
        [string]$Name
    )

    if (-not (Command-Exists "winget")) {
        throw "winget is not installed. Install App Installer from Microsoft Store, then run Jarvis installer again."
    }

    Write-Step "Installing $Name using winget..."
    winget install --id $PackageId --exact --silent --accept-package-agreements --accept-source-agreements
    Refresh-Path
}

Set-Location $InstallDir
Write-Step "Jarvis post-install started."
Write-Step "Install directory: $InstallDir"

Write-Step "Scanning Python 3.11..."
$python311 = Get-Command py -ErrorAction SilentlyContinue
$hasPython311 = $false

if ($python311) {
    try {
        $version = py -3.11 --version 2>&1
        if ($LASTEXITCODE -eq 0 -and "$version" -match "3\.11") {
            $hasPython311 = $true
            Write-Step "Python 3.11 found: $version"
        }
    } catch {}
}

if (-not $hasPython311) {
    if (Command-Exists "python") {
        $pyv = python --version 2>&1
        if ("$pyv" -match "3\.11") {
            $hasPython311 = $true
            Write-Step "Python 3.11 found through python command: $pyv"
        }
    }
}

if (-not $hasPython311) {
    Install-WingetPackage -PackageId "Python.Python.3.11" -Name "Python 3.11"
}

Write-Step "Scanning uv..."
if (-not (Command-Exists "uv")) {
    Write-Step "uv not found. Installing uv..."
    powershell -ExecutionPolicy Bypass -NoProfile -Command "irm https://astral.sh/uv/install.ps1 | iex"
    Refresh-Path
} else {
    Write-Step "uv found."
}

if (-not (Command-Exists "uv")) {
    throw "uv installation failed or uv is not available in PATH."
}

Write-Step "Creating/updating Jarvis Python environment..."
if (Test-Path "uv.lock") {
    uv sync --frozen
} else {
    uv sync
}

Write-Step "Scanning Ollama..."
if (-not (Command-Exists "ollama")) {
    Install-WingetPackage -PackageId "Ollama.Ollama" -Name "Ollama"
} else {
    Write-Step "Ollama found."
}

if (Command-Exists "ollama") {
    Write-Step "Starting Ollama service/app if needed..."
    try {
        Start-Process -FilePath "ollama" -ArgumentList "serve" -WindowStyle Hidden -ErrorAction SilentlyContinue
        Start-Sleep -Seconds 3
    } catch {
        Write-Step "Ollama serve may already be running."
    }

    if ($PullOllamaModel -eq "true") {
        Write-Step "Checking Ollama model llama3.1:8b..."
        $models = ollama list 2>&1
        if ("$models" -notmatch "llama3\.1:8b") {
            Write-Step "Downloading llama3.1:8b. This is around 5 GB and may take time..."
            ollama pull llama3.1:8b
        } else {
            Write-Step "llama3.1:8b already installed."
        }
    } else {
        Write-Step "Ollama model download skipped by installer task option."
    }
}

Write-Step "Jarvis post-install completed successfully."
