param(
    [string]$Output = "dist/modupdater.pyz"
)

$ErrorActionPreference = "Stop"
$repoRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
Push-Location $repoRoot
try {
    $python = Get-Command python -ErrorAction SilentlyContinue
    if (-not $python) {
        throw "Python nicht gefunden. Bitte stelle sicher, dass python im PATH ist."
    }

    python scripts/build_pyz.py --output $Output

    $outDir = Split-Path -Parent $Output
    if ($outDir) {
        Copy-Item "modupdater.global.toml" (Join-Path $outDir "modupdater.global.toml") -Force
        Copy-Item "modupdater.example.toml" (Join-Path $outDir "modupdater.example.toml") -Force
        Copy-Item "modupdater.example.en.toml" (Join-Path $outDir "modupdater.example.en.toml") -Force
        Copy-Item "README.md" (Join-Path $outDir "README.md") -Force
        Copy-Item "README.en.md" (Join-Path $outDir "README.en.md") -Force
    }
}
finally {
    Pop-Location
}
