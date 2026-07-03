param(
    [switch]$DeleteOnly
)

$ErrorActionPreference = "Stop"

$SkillRoot = Split-Path -Parent $PSScriptRoot
$LocalDir = Join-Path $SkillRoot "local"
$ReferenceDir = Join-Path $SkillRoot "references"

New-Item -ItemType Directory -Force -Path $LocalDir | Out-Null

$Pairs = @(
    @{ Template = "company-context.template.md"; Local = "company-context.local.md" },
    @{ Template = "call-notes.template.md"; Local = "call-notes.local.md" },
    @{ Template = "candidate-tracker.template.md"; Local = "candidate-tracker.local.md" }
)

foreach ($Pair in $Pairs) {
    $Target = Join-Path $LocalDir $Pair.Local
    if (Test-Path -LiteralPath $Target) {
        Remove-Item -LiteralPath $Target -Force
    }

    if (-not $DeleteOnly) {
        $Source = Join-Path $ReferenceDir $Pair.Template
        Copy-Item -LiteralPath $Source -Destination $Target
    }
}

if ($DeleteOnly) {
    Write-Host "Local recruiting context files deleted."
} else {
    Write-Host "Local recruiting context files reset from templates."
}
