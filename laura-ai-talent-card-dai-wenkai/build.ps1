$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$templatePath = Join-Path $root "template.html"
$outputPath = Join-Path $root "index.html"

$wechatQrPath = Join-Path $root "assets\wechat-qr.jpg"

function ConvertTo-DataUri {
  param([Parameter(Mandatory = $true)][string]$Path)

  if (-not (Test-Path -LiteralPath $Path)) {
    throw "Missing image: $Path"
  }

  $extension = [System.IO.Path]::GetExtension($Path).ToLowerInvariant()
  $mime = switch ($extension) {
    ".jpg" { "image/jpeg" }
    ".jpeg" { "image/jpeg" }
    ".png" { "image/png" }
    ".webp" { "image/webp" }
    default { throw "Unsupported image extension: $extension" }
  }

  $bytes = [System.IO.File]::ReadAllBytes($Path)
  return "data:$mime;base64,$([Convert]::ToBase64String($bytes))"
}

$template = [System.IO.File]::ReadAllText($templatePath, [System.Text.Encoding]::UTF8)
$template = $template.Replace("__WECHAT_QR__", (ConvertTo-DataUri -Path $wechatQrPath))

$utf8NoBom = New-Object System.Text.UTF8Encoding($false)
[System.IO.File]::WriteAllText($outputPath, $template, $utf8NoBom)

Write-Output "Built $outputPath"
