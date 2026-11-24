# SessionStart hook: count the open items in the current project's to-do list (a file in
# ~/.agents/todo/ whose "project:" line is the current folder or a parent of it) and ask the agent
# to run the todo-review skill. Prints nothing when there is nothing to do.
# Works with Claude Code, Codex and Gemini CLI: all three read systemMessage and
# hookSpecificOutput.additionalContext from a SessionStart hook. Runs on Windows PowerShell 5.1 or pwsh.
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

    $todoDir = [IO.Path]::Combine($HOME, '.agents', 'todo')
    if (-not (Test-Path -LiteralPath $todoDir)) { exit 0 }

    function ConvertTo-NormPath([string]$p) {
        if (-not $p) { return '' }
        $p = $p.Trim().Trim('"', "'").Replace('/', '\')
        if ($p -match '^\\([a-zA-Z])\\(.*)$') { $p = $Matches[1] + ':\' + $Matches[2] }
        return $p.TrimEnd('\').ToLowerInvariant()
    }

    $cwd = $null
    if ($hookInput -and $hookInput.cwd) { $cwd = $hookInput.cwd } else { $cwd = (Get-Location).Path }
    $cwdNorm = ConvertTo-NormPath $cwd

    # Find the list for this project: its project line equals cwd or a parent of cwd.
    # When several match, the longest project path wins.
    $best = $null; $bestLen = -1
    foreach ($f in (Get-ChildItem -LiteralPath $todoDir -Filter '*.md' -File)) {
        $proj = $null
        foreach ($line in (Get-Content -LiteralPath $f.FullName -Encoding UTF8 -TotalCount 10)) {
            if ($line -match '^-?\s*project:\s*(.+?)\s*$') { $proj = ConvertTo-NormPath $Matches[1]; break }
        }
        if (-not $proj) { continue }
        if (($proj -eq $cwdNorm -or $cwdNorm.StartsWith($proj + '\')) -and $proj.Length -gt $bestLen) {
            $best = $f.FullName; $bestLen = $proj.Length
        }
    }
    if (-not $best) { exit 0 }

    $count = 0; $inItem = $false; $status = $null; $inFence = $false
    foreach ($line in (Get-Content -LiteralPath $best -Encoding UTF8)) {
        # Ignore everything inside ``` or ~~~ code fences.
        if ($line -match '^\s*(```|~~~)') { $inFence = -not $inFence; continue }
        if ($inFence) { continue }
        if ($line -match '^##\s') {
            if ($inItem -and $status -eq 'open') { $count++ }
            $inItem = $true; $status = $null
            continue
        }
        if ($line -match '^-\s*status:\s*(\S+)') { $status = $Matches[1].ToLowerInvariant(); continue }
    }
    if ($inItem -and $status -eq 'open') { $count++ }

    if ($count -eq 0) { exit 0 }

    $ctx = "[todo-review] There are $count open decision(s) in this project's to-do list. " +
           "In your first reply, before anything else (including other startup prompts), " +
           "use the todo-review skill to ask the user about them. " +
           "If the user's first message is a task, do the review first and then the task. " +
           "If the user says to skip the review, skip it for this session."
    $sysJson = "todo-review: $count open decision(s) for this project. The agent will ask you about them first."
    $ctxJson = $ctx.Replace('\', '\\').Replace('"', '\"')
    $out = '{"systemMessage":"' + $sysJson + '","hookSpecificOutput":{"hookEventName":"SessionStart","additionalContext":"' + $ctxJson + '"}}'
    [Console]::Out.Write($out)
    exit 0
} catch {
    exit 0
}
