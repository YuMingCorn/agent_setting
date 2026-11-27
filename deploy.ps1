# Copy settings from this repo into your home folder (the reverse of backup.ps1).
# - Default: Claude Code only (agents, skills and tools -> ~/.claude).
# - -All: also the generated files in .\portable\ (run build.ps1 first):
#     portable\skills              -> ~/.agents/skills   (read by Codex and Antigravity CLI)
#     portable\codex\agents        -> ~/.codex/agents
#     portable\antigravity\agents  -> ~/.gemini/config/agents   (read by Antigravity CLI)
# - Before copying, it compares the home copies with the repo:
#     * A file that differs and is newer at home stops the deploy, so that a
#       direct edit in the home folder is not overwritten. Run backup.ps1
#       first, or pass -Force to overwrite.
#     * An old file is one that was in the repo at some point (git history)
#       and is gone now, but still exists at home. It is listed, and deleted
#       only with -Prune. Files the repo never had are never touched.
# - Before copying, saves the current copies to %TEMP%\claude-deploy-backup\<timestamp>.
# Usage:
#   powershell -ExecutionPolicy Bypass -File .\deploy.ps1 [-All] -DryRun   # list what would change
#   powershell -ExecutionPolicy Bypass -File .\deploy.ps1 [-All]           # copy
#   powershell -ExecutionPolicy Bypass -File .\deploy.ps1 [-All] -Prune    # copy and delete old files
# (Kept ASCII-only so Windows PowerShell 5.1 parses it under any code page.)
param([switch]$All, [switch]$DryRun, [switch]$Prune, [switch]$Force)

$ErrorActionPreference = 'Stop'
$repo = $PSScriptRoot
$home_ = $env:USERPROFILE
$exclude = @('synced', '__pycache__')   # never touch the auto-synced Anthropic skills; skip Python caches

# label, source in repo, target in home
$targets = @(
    @('claude-agents', 'agents', '.claude\agents'),
    @('claude-skills', 'skills', '.claude\skills'),
    @('claude-tools', 'tools', '.claude\tools')
)
if ($All) {
    $targets += ,@('agents-skills', 'portable\skills', '.agents\skills')
    $targets += ,@('codex-agents', 'portable\codex\agents', '.codex\agents')
    $targets += ,@('antigravity-agents', 'portable\antigravity\agents', '.gemini\config\agents')
}

function Invoke-Robocopy([string[]]$rcArgs, [string]$what) {
    robocopy @rcArgs
    # robocopy exit codes below 8 mean success
    if ($LASTEXITCODE -ge 8) { throw "robocopy failed for $what (exit code $LASTEXITCODE)" }
}

function Test-Excluded([string]$rel) {
    foreach ($part in $rel.Split('\')) { if ($exclude -contains $part) { return $true } }
    return $false
}

# Paths of all files under a folder, relative to it, without the excluded folders.
function Get-RelFiles([string]$root) {
    if (-not (Test-Path $root)) { return @() }
    $full = (Resolve-Path $root).Path.TrimEnd('\')
    return @(Get-ChildItem $full -Recurse -File -Force |
        ForEach-Object { $_.FullName.Substring($full.Length + 1) } |
        Where-Object { -not (Test-Excluded $_) })
}

foreach ($t in $targets) {
    if (-not (Test-Path (Join-Path $repo $t[1]))) { throw "Missing $($t[1]) in the repo. Run build.ps1 first." }
}

# ---- Compare the home copies with the repo ----
$homeNewer = @(); $repoNewer = @(); $old = @()
foreach ($t in $targets) {
    $src = Join-Path $repo $t[1]; $dst = Join-Path $home_ $t[2]
    $now = Get-RelFiles $src
    foreach ($rel in $now) {
        $a = Join-Path $src $rel; $b = Join-Path $dst $rel
        if (-not (Test-Path $b)) { continue }
        if ((Get-FileHash $a).Hash -eq (Get-FileHash $b).Hash) { continue }
        if ((Get-Item $b).LastWriteTimeUtc -gt (Get-Item $a).LastWriteTimeUtc) { $homeNewer += $b } else { $repoNewer += $b }
    }
    # Files that the repo had in any commit under this source folder.
    $prefix = $t[1].Replace('\', '/') + '/'
    $ever = @(git -C $repo -c core.quotePath=false log --all --format= --name-only -- $t[1].Replace('\', '/'))
    if ($LASTEXITCODE -ne 0) { throw "git log failed in $repo" }
    foreach ($p in ($ever | Where-Object { $_ -and $_.StartsWith($prefix) } | Sort-Object -Unique)) {
        $rel = $p.Substring($prefix.Length).Replace('/', '\')
        if ((Test-Excluded $rel) -or ($now -contains $rel)) { continue }
        $b = Join-Path $dst $rel
        if ((Test-Path $b -PathType Leaf) -and ($old -notcontains $b)) { $old += $b }
    }
}

if ($repoNewer.Count -gt 0) {
    Write-Host "== Changed in the repo, will be overwritten at home ($($repoNewer.Count)):"
    $repoNewer | ForEach-Object { Write-Host "  $_" }
}
if ($homeNewer.Count -gt 0) {
    Write-Host "== NEWER AT HOME than in the repo ($($homeNewer.Count)):"
    $homeNewer | ForEach-Object { Write-Host "  $_" }
}
if ($old.Count -gt 0) {
    $what = if (-not $Prune) { 'deleted only with -Prune' } elseif ($DryRun) { 'would be deleted with -Prune' } else { 'will be deleted' }
    Write-Host "== Old files no longer in the repo, $what ($($old.Count)):"
    $old | ForEach-Object { Write-Host "  $_" }
}

if ($DryRun) {
    foreach ($t in $targets) {
        Write-Host "== $($t[0]) -> ~\$($t[2]) (dry run: files that would be added or overwritten)"
        Invoke-Robocopy (@((Join-Path $repo $t[1]), (Join-Path $home_ $t[2]), '/E', '/L', '/NJH', '/NJS', '/NDL', '/NP', '/XD') + $exclude) $t[0]
    }
    $global:LASTEXITCODE = 0
    exit 0
}

if ($homeNewer.Count -gt 0 -and -not $Force) {
    throw "Stopped: the files listed above are newer at home. Run backup.ps1 to keep them, or rerun with -Force to overwrite them."
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

if ($Prune -and $old.Count -gt 0) {
    $roots = @($targets | ForEach-Object { (Join-Path $home_ $_[2]).TrimEnd('\') })
    foreach ($b in $old) {
        Remove-Item -LiteralPath $b -Force
        # Remove folders that the delete left empty, up to the target folder.
        $dir = Split-Path $b -Parent
        while (($roots -notcontains $dir) -and (Test-Path $dir) -and -not (Get-ChildItem $dir -Force)) {
            Remove-Item -LiteralPath $dir -Force
            $dir = Split-Path $dir -Parent
        }
    }
    Write-Host "Deleted $($old.Count) old files (copies are in the backup above)"
}
$global:LASTEXITCODE = 0
