param(
    [string]$LocalRoot,
    [switch]$DeleteOnly
)

$ErrorActionPreference = "Stop"

$SkillRoot = Split-Path -Parent $PSScriptRoot
$ReferenceDir = Join-Path $SkillRoot "references"

if ([string]::IsNullOrWhiteSpace($LocalRoot)) {
    $LocalRoot = Join-Path (Get-Location) ".hj-skill-local\hackathon-application-answerer"
}

$LocalDir = $LocalRoot

New-Item -ItemType Directory -Force -Path $LocalDir | Out-Null

$Pairs = @(
    @{ Template = "profile.template.md"; Local = "profile.local.md" },
    @{ Template = "answer-bank.template.md"; Local = "answer-bank.local.md" }
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
    Write-Host "Local memory files deleted from $LocalDir."
} else {
    Write-Host "Local memory files reset from templates at $LocalDir."
}
