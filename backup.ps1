# One-way copy of global Claude Code settings from ~/.claude into this repo.
# Writes only into the repo. Never writes to or deletes anything under ~/.claude.
# Usage: powershell -ExecutionPolicy Bypass -File .\backup.ps1
# (Kept ASCII-only so Windows PowerShell 5.1 parses it under any code page.)

$ErrorActionPreference = 'Stop'
$src  = Join-Path $env:USERPROFILE '.claude'
$repo = $PSScriptRoot

# Folder to back up => subfolders to exclude
$items = [ordered]@{
    'agents' = @()
    'skills' = @('synced')   # synced = Anthropic skills auto-synced from claude.ai
}

foreach ($name in $items.Keys) {
    $from = Join-Path $src $name
    $to   = Join-Path $repo $name
    if (-not (Test-Path $from)) { Write-Warning "Not found: $from (skipped)"; continue }

    $rcArgs = @($from, $to, '/MIR', '/NFL', '/NDL', '/NJH', '/NJS', '/NP')
    if ($items[$name].Count -gt 0) { $rcArgs += '/XD'; $rcArgs += $items[$name] }
    robocopy @rcArgs | Out-Null
    # robocopy exit codes below 8 mean success
    if ($LASTEXITCODE -ge 8) { throw "robocopy failed for $name (exit code $LASTEXITCODE)" }
    Write-Host "Synced $name"
}
$global:LASTEXITCODE = 0
