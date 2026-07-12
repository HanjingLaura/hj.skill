param(
    [string]$LocalRoot = "",
    [string]$RoleCase = "",
    [string]$ContextId = "",
    [switch]$Force
)

$ErrorActionPreference = "Stop"

$SkillRoot = Split-Path -Parent $PSScriptRoot
$RoleTemplate = Join-Path $SkillRoot "references\role-context.template.md"
$TableTemplate = Join-Path $SkillRoot "references\candidate-screening-table.template.md"
$FeedbackTemplate = Join-Path $SkillRoot "references\feedback-calibration-log.template.md"

if (-not $LocalRoot) {
    $BaseLocalRoot = Join-Path (Get-Location) ".hj-skill-local\candidate-fit-tracker"
    if (-not $RoleCase -and $ContextId) {
        $RoleCase = $ContextId
    }
    if ($RoleCase) {
        $LocalRoot = Join-Path $BaseLocalRoot $RoleCase
    } else {
        $LocalRoot = $BaseLocalRoot
    }
}

New-Item -ItemType Directory -Force -Path $LocalRoot | Out-Null

if ($ContextId) {
    $RoleFile = "role-context.$ContextId.local.md"
    $TableFile = "candidate-screening-table.$ContextId.local.md"
    $FeedbackFile = "feedback-calibration-log.$ContextId.local.md"
} else {
    $RoleFile = "role-context.local.md"
    $TableFile = "candidate-screening-table.local.md"
    $FeedbackFile = "feedback-calibration-log.local.md"
}

$RoleTarget = Join-Path $LocalRoot $RoleFile
$TableTarget = Join-Path $LocalRoot $TableFile
$FeedbackTarget = Join-Path $LocalRoot $FeedbackFile

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

if ((Test-Path -LiteralPath $FeedbackTarget) -and -not $Force) {
    Write-Host "Local feedback calibration log already exists: $FeedbackTarget"
} else {
    Copy-Item -LiteralPath $FeedbackTemplate -Destination $FeedbackTarget -Force
    if ($ContextId) {
        $content = Get-Content -Raw -Encoding UTF8 -LiteralPath $FeedbackTarget
        $content = $content -replace "- Context ID:", "- Context ID: $ContextId"
        Set-Content -Encoding UTF8 -LiteralPath $FeedbackTarget -Value $content
    }
    Write-Host "Created local feedback calibration log template: $FeedbackTarget"
}

