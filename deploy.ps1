# Copy settings from this repo into your home folder (the reverse of backup.ps1).
# - Default: Claude Code only (agents and skills -> ~/.claude).
# - -All: also the generated files in .\portable\ (run build.ps1 first):
#     portable\skills              -> ~/.agents/skills   (read by Codex and Antigravity CLI)
#     portable\codex\agents        -> ~/.codex/agents
#     portable\antigravity\agents  -> ~/.gemini/agents   (read by Antigravity CLI)
# - Before copying, saves the current copies to %TEMP%\claude-deploy-backup\<timestamp>.
# - Adds and overwrites files only. Never deletes anything in the target folders.
# Usage:
#   powershell -ExecutionPolicy Bypass -File .\deploy.ps1 [-All] -DryRun   # list what would change
#   powershell -ExecutionPolicy Bypass -File .\deploy.ps1 [-All]           # copy
# (Kept ASCII-only so Windows PowerShell 5.1 parses it under any code page.)
param([switch]$All, [switch]$DryRun)

$ErrorActionPreference = 'Stop'
$repo = $PSScriptRoot
$home_ = $env:USERPROFILE
$exclude = @('synced')   # never touch the auto-synced Anthropic skills

# label, source in repo, target in home
$targets = @(
    @('claude-agents', 'agents', '.claude\agents'),
    @('claude-skills', 'skills', '.claude\skills')
)
if ($All) {
    $targets += ,@('agents-skills', 'portable\skills', '.agents\skills')
    $targets += ,@('codex-agents', 'portable\codex\agents', '.codex\agents')
    $targets += ,@('antigravity-agents', 'portable\antigravity\agents', '.gemini\agents')
}

function Invoke-Robocopy([string[]]$rcArgs, [string]$what) {
    robocopy @rcArgs
    # robocopy exit codes below 8 mean success
    if ($LASTEXITCODE -ge 8) { throw "robocopy failed for $what (exit code $LASTEXITCODE)" }
}

foreach ($t in $targets) {
    if (-not (Test-Path (Join-Path $repo $t[1]))) { throw "Missing $($t[1]) in the repo. Run build.ps1 first." }
}

if ($DryRun) {
    foreach ($t in $targets) {
        Write-Host "== $($t[0]) -> ~\$($t[2]) (dry run: files that would be added or overwritten)"
        Invoke-Robocopy (@((Join-Path $repo $t[1]), (Join-Path $home_ $t[2]), '/E', '/L', '/NJH', '/NJS', '/NDL', '/NP', '/XD') + $exclude) $t[0]
    }
    $global:LASTEXITCODE = 0
    exit 0
}

$stamp  = Get-Date -Format 'yyyyMMdd-HHmmss'
$backup = Join-Path $env:TEMP "claude-deploy-backup\$stamp"
foreach ($t in $targets) {
    $from = Join-Path $home_ $t[2]
    if (Test-Path $from) {
        Invoke-Robocopy (@($from, (Join-Path $backup $t[0]), '/E', '/NFL', '/NDL', '/NJH', '/NJS', '/NP', '/XD') + $exclude) "backup of $($t[0])" | Out-Null
    }
}
Write-Host "Saved current copies to $backup"

foreach ($t in $targets) {
    Invoke-Robocopy (@((Join-Path $repo $t[1]), (Join-Path $home_ $t[2]), '/E', '/NFL', '/NDL', '/NJH', '/NJS', '/NP', '/XD') + $exclude) $t[0] | Out-Null
    Write-Host "Deployed $($t[0]) -> ~\$($t[2])"
}
$global:LASTEXITCODE = 0
