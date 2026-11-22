# SessionStart hook: count open items in ~/.claude/todo.md for the current project
# and ask Claude to run the todo-review skill. Prints nothing when there is nothing to do.
# Keep this file ASCII-only (Windows PowerShell 5.1 reads BOM-less .ps1 as ANSI).
$ErrorActionPreference = 'Stop'
try {
    [Console]::OutputEncoding = [Text.Encoding]::UTF8

    $hookInput = $null
    if ([Console]::IsInputRedirected) {
        $reader = New-Object IO.StreamReader([Console]::OpenStandardInput(), [Text.Encoding]::UTF8)
        $raw = $reader.ReadToEnd()
        if ($raw.Trim()) { $hookInput = $raw | ConvertFrom-Json }
    }

    # Only on a fresh start, not after /clear, /compact or resume.
    if ($hookInput -and $hookInput.source -and $hookInput.source -ne 'startup') { exit 0 }

    $todoPath = Join-Path $env:USERPROFILE '.claude\todo.md'
    if (-not (Test-Path -LiteralPath $todoPath)) { exit 0 }

    function ConvertTo-NormPath([string]$p) {
        if (-not $p) { return '' }
        $p = $p.Trim().Replace('/', '\')
        if ($p -match '^\\([a-zA-Z])\\(.*)$') { $p = $Matches[1] + ':\' + $Matches[2] }
        return $p.TrimEnd('\').ToLowerInvariant()
    }

    $cwd = $null
    if ($hookInput -and $hookInput.cwd) { $cwd = $hookInput.cwd } else { $cwd = (Get-Location).Path }
    $cwdNorm = ConvertTo-NormPath $cwd

    $lines = Get-Content -LiteralPath $todoPath -Encoding UTF8
    $count = 0
    $inItem = $false; $proj = $null; $status = $null; $inFence = $false
    # An item belongs to this session when its project is '*', equals cwd, or is a parent folder of cwd.
    $flush = {
        if ($inItem -and $status -eq 'open') {
            $pn = $null
            if ($proj) { $pn = ConvertTo-NormPath $proj.Trim('"', "'") }
            if ($proj -eq '*' -or ($pn -and ($pn -eq $cwdNorm -or $cwdNorm.StartsWith($pn + '\')))) { $script:count++ }
        }
    }
    foreach ($line in $lines) {
        # Ignore everything inside ``` or ~~~ code fences.
        if ($line -match '^\s*(```|~~~)') { $inFence = -not $inFence; continue }
        if ($inFence) { continue }
        if ($line -match '^##\s') {
            . $flush
            $inItem = $true; $proj = $null; $status = $null
            continue
        }
        if ($line -match '^#\s') { . $flush; $inItem = $false; continue }
        if ($line -match '^-\s*project:\s*(.+?)\s*$') { $proj = $Matches[1]; continue }
        if ($line -match '^-\s*status:\s*(\S+)') { $status = $Matches[1].ToLowerInvariant(); continue }
    }
    . $flush

    if ($count -eq 0) { exit 0 }

    $ctx = "[todo-review] There are $count open decision(s) for this project in ~/.claude/todo.md. " +
           "In your first reply, before anything else (including other startup prompts such as wiki autopilot), " +
           "invoke the todo-review skill (Skill tool, skill: todo-review) to ask the user about them. " +
           "If the user's first message is a task, do the review first and then the task. " +
           "If the user says to skip the review, skip it for this session."
    # systemMessage in Traditional Chinese, built from char codes to keep this file ASCII.
    $zh = { param([int[]]$c) -join ($c | ForEach-Object { [char]$_ }) }
    $sys = 'todo-review: ' + (& $zh 0x5F85,0x6C7A,0x5B9A) + ' ' + $count + ' ' + (& $zh 0x9805,0xFF0C,0x7B2C,0x4E00,0x6B21,0x56DE,0x8986,0x6642,0x6703,0x5148,0x554F,0x4F60)
    $sysJson = $sys
    $ctxJson = $ctx.Replace('\', '\\').Replace('"', '\"')
    $out = '{"systemMessage":"' + $sysJson + '","hookSpecificOutput":{"hookEventName":"SessionStart","additionalContext":"' + $ctxJson + '"}}'
    [Console]::Out.Write($out)
    exit 0
} catch {
    exit 0
}
