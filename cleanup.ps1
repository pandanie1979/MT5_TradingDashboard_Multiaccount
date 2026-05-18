# cleanup.ps1 — Remove build artifacts and sprint-specific files
# Run from project root: .\cleanup.ps1

$root = $PSScriptRoot

Write-Host "Cleaning project artifacts in: $root"

# Remove __pycache__ directories
Get-ChildItem -Path $root -Filter "__pycache__" -Recurse -Directory -ErrorAction SilentlyContinue |
    Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
Write-Host "  [OK] __pycache__ directories removed"

# Remove compiled Python files
Get-ChildItem -Path $root -Include "*.pyc","*.pyo","*.pyd" -Recurse -ErrorAction SilentlyContinue |
    Remove-Item -Force -ErrorAction SilentlyContinue
Write-Host "  [OK] Compiled .pyc/.pyo/.pyd files removed"

# Remove backup files
Get-ChildItem -Path $root -Include "*.bak","*~" -Recurse -ErrorAction SilentlyContinue |
    Remove-Item -Force -ErrorAction SilentlyContinue
Write-Host "  [OK] Backup files removed"

# Remove CURRENT_SPRINT.md
$sprintFile = Join-Path $root "CURRENT_SPRINT.md"
if (Test-Path $sprintFile) {
    Remove-Item -Path $sprintFile -Force -ErrorAction SilentlyContinue
    Write-Host "  [OK] CURRENT_SPRINT.md removed"
} else {
    Write-Host "  [--] CURRENT_SPRINT.md not found (already removed)"
}

Write-Host "Cleanup complete."
