param(
    [switch]$SkipFrontendBuild
)

$ErrorActionPreference = "Stop"

function Find-InnoCompiler {
    $paths = @(
        "${env:ProgramFiles(x86)}\Inno Setup 6\ISCC.exe",
        "${env:ProgramFiles}\Inno Setup 6\ISCC.exe",
        "$env:LOCALAPPDATA\Programs\Inno Setup 6\ISCC.exe"
    )

    foreach ($path in $paths) {
        if (Test-Path $path) {
            return $path
        }
    }

    $cmd = Get-Command ISCC.exe -ErrorAction SilentlyContinue
    if ($cmd) {
        return $cmd.Source
    }

    throw "Inno Setup 6 compiler ISCC.exe was not found. Install Inno Setup 6 first."
}

Set-Location (Resolve-Path "$PSScriptRoot\..")

Write-Host "Building Jarvis frontend..."
if (-not $SkipFrontendBuild) {
    if (-not (Test-Path "frontend\package.json")) {
        throw "frontend\package.json not found."
    }

    Push-Location frontend

    if (-not (Test-Path "node_modules")) {
        npm install
    }

    npm run build
    Pop-Location
}

if (-not (Test-Path "frontend\dist\index.html")) {
    throw "frontend\dist\index.html missing. Build frontend first."
}

if (-not (Test-Path "pyproject.toml")) {
    throw "pyproject.toml missing."
}

if (-not (Test-Path "src\ui_app.py")) {
    throw "src\ui_app.py missing."
}

$iscc = Find-InnoCompiler

Write-Host "Using Inno compiler: $iscc"
Write-Host "Compiling installer..."

Push-Location installer
& $iscc "JarvisSetup.iss"
Pop-Location

Write-Host ""
Write-Host "Done."
Write-Host "Installer created at:"
Write-Host "D:\1\1\Coding\Files\Python\Jarvis\installer\Output\JarvisSetup.exe"
