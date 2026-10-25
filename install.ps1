# skills-hub installer for Windows.
#
# Four steps, then one hand-off. Every write happens in bootstrap.py, so Windows,
# Linux and macOS run the same logic. This file only finds Python, fetches the
# hub, and calls it.
#
#   irm https://raw.githubusercontent.com/khan2abdul/skills-hub/main/install.ps1 | iex

$ErrorActionPreference = 'Stop'
$HubUrl = 'https://github.com/khan2abdul/skills-hub/archive/refs/heads/main.zip'
$HubDir = Join-Path $env:LOCALAPPDATA 'skills-hub'

# The real work is top level, so a dot-source would install for real. This guard
# is what lets a test or the parser load the file without running it.
if ($MyInvocation.InvocationName -eq '.') { return }

function Write-Step($Text) { Write-Host "  $Text" -ForegroundColor Cyan }
function Write-Warn2($Text) { Write-Host "  $Text" -ForegroundColor Yellow }
function Write-Bad($Text) { Write-Host "  $Text" -ForegroundColor Red }

# 1. Python 3.11 or newer. `py -3` is the Windows launcher; `python` may be a
# Store stub that opens the Store instead of running, so test the version.
function Find-Python {
    foreach ($cand in @(@{Exe='python'; Prefix=@()}, @{Exe='py'; Prefix=@('-3')})) {
        $exe = Get-Command $cand.Exe -ErrorAction SilentlyContinue
        if (-not $exe) { continue }
        try {
            $raw = & $exe.Source @($cand.Prefix) -c 'import sys; print(sys.version_info[0], sys.version_info[1])' 2>$null
        } catch { continue }
        if (-not $raw) { continue }
        $parts = "$raw".Trim() -split '\s+'
        if ($parts.Count -lt 2) { continue }
        $major = [int]$parts[0]; $minor = [int]$parts[1]
        if ($major -gt 3 -or ($major -eq 3 -and $minor -ge 11)) {
            return @{ Exe = $exe.Source; Prefix = $cand.Prefix; Version = "$major.$minor" }
        }
    }
    return $null
}

# 2. Install Python with winget, user scope, no admin. winget asks for the
# licence; this script never elevates.
function Add-Python {
    if (-not (Get-Command winget -ErrorAction SilentlyContinue)) {
        Write-Bad 'Python 3.11+ is missing and winget is not available.'
        Write-Warn2 'Install Python from https://www.python.org/downloads/ and run this again.'
        exit 1
    }
    Write-Step 'Python 3.11+ is missing. winget can install it for your user only.'
    $answer = Read-Host '  Install Python 3.12 now? [y/N]'
    if ($answer -notmatch '^(y|yes)$') {
        Write-Warn2 'Nothing was installed.'
        exit 1
    }
    & winget install --scope user --id Python.Python.3.12 --accept-package-agreements --accept-source-agreements
}

# 3. The hub zip, unpacked to %LOCALAPPDATA%\skills-hub. A re-run reuses it.
function Get-Hub {
    if (Test-Path (Join-Path $HubDir 'tools\bootstrap.py')) {
        Write-Step "Hub already at $HubDir"
        return
    }
    Write-Step "Downloading the hub to $HubDir"
    $zip = Join-Path $env:TEMP ("skills-hub-" + [guid]::NewGuid().ToString('N') + '.zip')
    $tmp = Join-Path $env:TEMP ("skills-hub-" + [guid]::NewGuid().ToString('N'))
    try {
        Invoke-WebRequest -Uri $HubUrl -OutFile $zip -UseBasicParsing
        Expand-Archive -Path $zip -DestinationPath $tmp -Force
        $inner = Get-ChildItem $tmp -Directory | Select-Object -First 1
        New-Item -ItemType Directory -Force -Path $HubDir | Out-Null
        Copy-Item -Path (Join-Path $inner.FullName '*') -Destination $HubDir -Recurse -Force
    } catch {
        # A partial hub is worse than none: every later run would read it.
        Write-Bad "Download or unpack failed: $_"
        if (Test-Path $tmp) { Remove-Item $tmp -Recurse -Force -ErrorAction SilentlyContinue }
        exit 1
    } finally {
        if (Test-Path $zip) { Remove-Item $zip -Force -ErrorAction SilentlyContinue }
        if (Test-Path $tmp) { Remove-Item $tmp -Recurse -Force -ErrorAction SilentlyContinue }
    }
    if (-not (Test-Path (Join-Path $HubDir 'tools\bootstrap.py'))) {
        Write-Bad "The hub is incomplete at $HubDir"
        exit 1
    }
}

Write-Host ''
Write-Host 'skills-hub' -ForegroundColor White
Write-Host '42 skills and one writing style for your AI tools.' -ForegroundColor Gray
Write-Host ''

$py = Find-Python
if (-not $py) {
    Add-Python
    $py = Find-Python
    if (-not $py) {
        Write-Bad 'Python is still missing. Open a new terminal and run this again.'
        exit 1
    }
}
Write-Step "Python $($py.Version) found"

Get-Hub

# 4. The one hand-off. Args from the caller pass through: -Only cursor, -All.
$forward = @()
if ($args -contains '-All' -or $args -contains '--all') { $forward += '--all' }
$onlyIdx = [array]::IndexOf($args, '-Only')
if ($onlyIdx -ge 0 -and $onlyIdx + 1 -lt $args.Count) {
    $forward += @('--only', $args[$onlyIdx + 1])
}
$script = Join-Path $HubDir 'tools\bootstrap.py'
& $py.Exe @($py.Prefix) $script @forward
exit $LASTEXITCODE
