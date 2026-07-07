param(
    [string]$LocalRoot = "",
    [string]$ContextId = "",
    [switch]$Force
)

$ErrorActionPreference = "Stop"

$SkillRoot = Split-Path -Parent $PSScriptRoot
$RoleTemplate = Join-Path $SkillRoot "references\role-context.template.md"
$TableTemplate = Join-Path $SkillRoot "references\candidate-screening-table.template.md"

if (-not $LocalRoot) {
    $LocalRoot = Join-Path (Get-Location) ".hj-skill-local\candidate-fit-tracker"
}

New-Item -ItemType Directory -Force -Path $LocalRoot | Out-Null

if ($ContextId) {
    $RoleFile = "role-context.$ContextId.local.md"
    $TableFile = "candidate-screening-table.$ContextId.local.md"
} else {
    $RoleFile = "role-context.local.md"
    $TableFile = "candidate-screening-table.local.md"
}

$RoleTarget = Join-Path $LocalRoot $RoleFile
$TableTarget = Join-Path $LocalRoot $TableFile

if ((Test-Path -LiteralPath $RoleTarget) -and -not $Force) {
    Write-Host "Local role context already exists: $RoleTarget"
} else {
    Copy-Item -LiteralPath $RoleTemplate -Destination $RoleTarget -Force
    if ($ContextId) {
        $content = Get-Content -Raw -Encoding UTF8 -LiteralPath $RoleTarget
        $content = $content -replace "- Context ID:", "- Context ID: $ContextId"
        Set-Content -Encoding UTF8 -LiteralPath $RoleTarget -Value $content
    }
    Write-Host "Created local role context template: $RoleTarget"
}

if ((Test-Path -LiteralPath $TableTarget) -and -not $Force) {
    Write-Host "Local candidate table already exists: $TableTarget"
} else {
    Copy-Item -LiteralPath $TableTemplate -Destination $TableTarget -Force
    Write-Host "Created local candidate table template: $TableTarget"
}

