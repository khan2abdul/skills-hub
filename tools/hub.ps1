#!/usr/bin/env pwsh
# One entry point. Runs the hub's checks in the order that makes failures actionable.
#
#   hub.ps1                 -> health check (harvest + verify + coverage + rating + catalog)
#   hub.ps1 -Setup <tool>   -> print the install page for a tool and stop
#   hub.ps1 -Tools          -> list available install pages
param(
  [string]$Setup = "",
  [switch]$Tools
)
$ErrorActionPreference = 'Continue'
. (Join-Path $PSScriptRoot '_common.ps1')

$hub = Get-HubRoot
$setupDir = Join-Path $hub 'setup'

if ($Tools) {
  Write-Host "Install pages in $setupDir :" -ForegroundColor Cyan
  Get-ChildItem $setupDir -Filter *.md | Where-Object { $_.Name -ne 'README.md' } |
    ForEach-Object { "  {0,-22} {1}" -f ($_.BaseName), (Get-Content $_.FullName -TotalCount 1) }
  exit 0
}

if ($Setup) {
  $page = Join-Path $setupDir "$Setup.md"
  if (-not (Test-Path $page)) {
    Write-Host "no page for '$Setup'. Available:" -ForegroundColor Red
    Get-ChildItem $setupDir -Filter *.md | Where-Object { $_.Name -ne 'README.md' } |
      ForEach-Object { "  $($_.BaseName)" }
    exit 1
  }
  Get-Content $page -Raw
  exit 0
}

$fail = 0
Write-Host "--- harvest ---" -ForegroundColor Cyan
$global:LASTEXITCODE = 0
& (Join-Path $PSScriptRoot 'harvest.ps1')
$code = $LASTEXITCODE
if ($code -eq 2) {
  Write-Host ""
  Write-Host "The source repos are not cloned yet. Run this once:" -ForegroundColor Yellow
  Write-Host "  pwsh tools/clone-repos.ps1" -ForegroundColor Yellow
  exit 2
}
if ($code -ne 0) { $fail++ }

Write-Host ""
Write-Host "--- verify ---" -ForegroundColor Cyan
$global:LASTEXITCODE = 0
& (Join-Path $PSScriptRoot 'verify.ps1')
$code = $LASTEXITCODE
if ($code -eq 2) {
  Write-Host ""
  Write-Host "The source repos are not cloned yet. Run this once:" -ForegroundColor Yellow
  Write-Host "  pwsh tools/clone-repos.ps1" -ForegroundColor Yellow
  exit 2
}
if ($code -ne 0) { $fail++ }

Write-Host ""
Write-Host "--- coverage ---" -ForegroundColor Cyan
$global:LASTEXITCODE = 0
& (Join-Path $PSScriptRoot 'coverage.ps1')
$code = $LASTEXITCODE
if ($code -eq 2) {
  Write-Host ""
  Write-Host "The source repos are not cloned yet. Run this once:" -ForegroundColor Yellow
  Write-Host "  pwsh tools/clone-repos.ps1" -ForegroundColor Yellow
  exit 2
}
if ($code -ne 0) { $fail++ }

Write-Host ""
Write-Host "--- rating ---" -ForegroundColor Cyan
$global:LASTEXITCODE = 0
& (Join-Path $PSScriptRoot 'rate-skills.ps1')
$code = $LASTEXITCODE
if ($code -eq 2) {
  Write-Host ""
  Write-Host "No skills to rate. Run tools/vendor.ps1 -All first." -ForegroundColor Yellow
  exit 2
}
if ($code -ne 0) { $fail++ }

Write-Host ""
Write-Host "--- catalog ---" -ForegroundColor Cyan
$global:LASTEXITCODE = 0
& (Join-Path $PSScriptRoot 'catalog.ps1')
$code = $LASTEXITCODE
if ($code -ne 0) { $fail++ }

Write-Host ""
if ($fail -gt 0) { Write-Host "HUB NOT HEALTHY" -ForegroundColor Red; exit 1 }
Write-Host "HUB HEALTHY" -ForegroundColor Green
