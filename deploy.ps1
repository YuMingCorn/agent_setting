# Copy settings from this repo into ~/.claude (the reverse of backup.ps1).
# - Before copying, saves the current ~/.claude copies to %TEMP%\claude-deploy-backup\<timestamp>.
# - Adds and overwrites files only. Never deletes anything under ~/.claude.
# Usage:
#   powershell -ExecutionPolicy Bypass -File .\deploy.ps1 -DryRun   # list what would change
#   powershell -ExecutionPolicy Bypass -File .\deploy.ps1           # copy
# (Kept ASCII-only so Windows PowerShell 5.1 parses it under any code page.)
param([switch]$DryRun)

$ErrorActionPreference = 'Stop'
$dest = Join-Path $env:USERPROFILE '.claude'
$repo = $PSScriptRoot
$folders = @('agents', 'skills')
$exclude = @('synced')   # never touch the auto-synced Anthropic skills

function Invoke-Robocopy([string[]]$rcArgs, [string]$what) {
    robocopy @rcArgs
    # robocopy exit codes below 8 mean success
    if ($LASTEXITCODE -ge 8) { throw "robocopy failed for $what (exit code $LASTEXITCODE)" }
}

if ($DryRun) {
    foreach ($name in $folders) {
        Write-Host "== $name (dry run: files that would be added or overwritten)"
        Invoke-Robocopy (@((Join-Path $repo $name), (Join-Path $dest $name), '/E', '/L', '/NJH', '/NJS', '/NDL', '/NP', '/XD') + $exclude) $name
    }
    $global:LASTEXITCODE = 0
    exit 0
}

$stamp  = Get-Date -Format 'yyyyMMdd-HHmmss'
$backup = Join-Path $env:TEMP "claude-deploy-backup\$stamp"
foreach ($name in $folders) {
    $from = Join-Path $dest $name
    if (Test-Path $from) {
        Invoke-Robocopy (@($from, (Join-Path $backup $name), '/E', '/NFL', '/NDL', '/NJH', '/NJS', '/NP', '/XD') + $exclude) "backup of $name" | Out-Null
    }
}
Write-Host "Saved current copies to $backup"

foreach ($name in $folders) {
    Invoke-Robocopy (@((Join-Path $repo $name), (Join-Path $dest $name), '/E', '/NFL', '/NDL', '/NJH', '/NJS', '/NP', '/XD') + $exclude) $name | Out-Null
    Write-Host "Deployed $name"
}
$global:LASTEXITCODE = 0
