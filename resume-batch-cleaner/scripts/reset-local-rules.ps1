param(
    [string]$LocalRoot = "",
    [switch]$Force
)

$ErrorActionPreference = "Stop"

$SkillRoot = Split-Path -Parent $PSScriptRoot
$Template = Join-Path $SkillRoot "references\screening-rules.template.md"

if (-not $LocalRoot) {
    $LocalRoot = Join-Path (Get-Location) ".hj-skill-local\resume-batch-cleaner"
}

New-Item -ItemType Directory -Force -Path $LocalRoot | Out-Null

$Target = Join-Path $LocalRoot "screening-rules.local.md"
if ((Test-Path -LiteralPath $Target) -and -not $Force) {
    Write-Host "Local screening rules already exist: $Target"
    Write-Host "Re-run with -Force to overwrite them."
    exit 0
}

Copy-Item -LiteralPath $Template -Destination $Target -Force
Write-Host "Created local screening rules template: $Target"
