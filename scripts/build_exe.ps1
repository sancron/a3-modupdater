param(
    [string]$SpecPath = "modupdater.spec"
)

$ErrorActionPreference = "Stop"
$repoRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
Push-Location $repoRoot
try {
    if (-not (Test-Path -Path $SpecPath)) {
        throw "Spec file '$SpecPath' not found."
    }

    $python = Get-Command python -ErrorAction SilentlyContinue
    if (-not $python) {
        throw "Python nicht gefunden. Bitte stelle sicher, dass python im PATH ist."
    }

    $prevRoot = $env:MODUPDATER_ROOT
    $env:MODUPDATER_ROOT = $repoRoot
    try {
        python -m PyInstaller --clean --noconfirm $SpecPath

        $distDir = Join-Path $repoRoot "dist/modupdater"
        if (Test-Path $distDir) {
            Copy-Item (Join-Path $repoRoot "modupdater.global.toml") (Join-Path $distDir "modupdater.global.toml") -Force
            Copy-Item (Join-Path $repoRoot "modupdater.example.toml") (Join-Path $distDir "modupdater.example.toml") -Force
            Copy-Item (Join-Path $repoRoot "modupdater.example.en.toml") (Join-Path $distDir "modupdater.example.en.toml") -Force
            Copy-Item (Join-Path $repoRoot "README.md") (Join-Path $distDir "README.md") -Force
            Copy-Item (Join-Path $repoRoot "README.en.md") (Join-Path $distDir "README.en.md") -Force
        }
    }
    finally {
        $env:MODUPDATER_ROOT = $prevRoot
    }
}
finally {
    Pop-Location
}
