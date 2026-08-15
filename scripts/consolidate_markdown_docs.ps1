$ErrorActionPreference = "Stop"

$ProjectRoot = Split-Path -Parent $PSScriptRoot

$FilesToRemove = @(
    "BUILD_VALIDATION.md",
    "UPGRADE_NOTES_LOCAL_FEATURE_COMPLETE.md",
    "UPGRADE_NOTES_PHASES_1_10_UI.md",
    "UPGRADE_NOTES_ROADMAP_1_4.md",
    "UPGRADE_NOTES_UI_V2.md",
    "docs\HARDENING_CHECKLIST.md",
    "docs\LOCAL_RELEASE_CHECKLIST.md",
    "docs\UI_DESIGN_SYSTEM.md"
)

Write-Host "Consolidating historical Markdown into README.md..."
Write-Host ""

foreach ($RelativePath in $FilesToRemove) {
    $Path = Join-Path $ProjectRoot $RelativePath

    if (Test-Path $Path) {
        Remove-Item $Path -Force
        Write-Host "Removed: $RelativePath"
    }
    else {
        Write-Host "Already absent: $RelativePath"
    }
}

Write-Host ""
Write-Host "Retained intentionally:"
Write-Host "  README.md"
Write-Host "  SECURITY.md"
Write-Host "  deploy\certs\README.md"
Write-Host "  deploy\secrets\README.md"
Write-Host ""
Write-Host "Next:"
Write-Host "  pytest -q"
Write-Host "  git add -A"
Write-Host "  git status"
