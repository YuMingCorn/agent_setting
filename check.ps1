# Check that the repo is consistent before a commit. Changes nothing except
# that it runs build.ps1, which regenerates .\portable\.
# Checks:
#   1. Each agent: name and description are set, and name equals the file name.
#   2. Each skill: name equals the folder name, and disable-model-invocation
#      is true (every skill runs only when the user calls it).
#   3. Both READMEs list every agent as `name` and every skill as `/name`, and
#      the agent and skill counts in them are right.
#   4. After build.ps1, git shows no change in portable\ (so the generated
#      files are committed together with their sources).
#   5. The .ps1 files contain ASCII characters only.
# Usage: powershell -ExecutionPolicy Bypass -File .\check.ps1
# Exit code 0 when all checks pass, 1 otherwise.
# (Kept ASCII-only so Windows PowerShell 5.1 parses it under any code page.)

$ErrorActionPreference = 'Stop'
$repo = $PSScriptRoot
$utf8 = New-Object Text.UTF8Encoding($false)
$problems = New-Object System.Collections.Generic.List[string]

function Read-Text([string]$path) { return [IO.File]::ReadAllText($path, $utf8).Replace("`r`n", "`n") }

# Simple "key: value" frontmatter, as build.ps1 reads it.
function Read-Frontmatter([string]$path) {
    $t = Read-Text $path
    $fm = @{}
    if (-not $t.StartsWith("---`n")) { return $fm }
    $end = $t.IndexOf("`n---`n", 4)
    if ($end -lt 0) { return $fm }
    foreach ($line in $t.Substring(4, $end - 4).Split("`n")) {
        if ($line -match '^([A-Za-z][\w-]*):\s*(.*)$') { $fm[$Matches[1]] = $Matches[2].Trim().Trim('"').Trim("'") }
    }
    return $fm
}

# 1. Agents
$agents = @()
foreach ($f in (Get-ChildItem (Join-Path $repo 'agents') -Filter '*.md' | Sort-Object Name)) {
    $fm = Read-Frontmatter $f.FullName
    if (-not $fm['name'] -or -not $fm['description']) { $problems.Add("agents/$($f.Name): needs name and description"); continue }
    if ($fm['name'] -cne $f.BaseName) { $problems.Add("agents/$($f.Name): name '$($fm['name'])' differs from the file name") }
    $agents += $fm['name']
}

# 2. Skills
$skills = @()
foreach ($d in (Get-ChildItem (Join-Path $repo 'skills') -Directory | Where-Object { $_.Name -ne 'synced' } | Sort-Object Name)) {
    $file = Join-Path $d.FullName 'SKILL.md'
    if (-not (Test-Path $file)) { $problems.Add("skills/$($d.Name): no SKILL.md"); continue }
    $fm = Read-Frontmatter $file
    if ($fm['name'] -cne $d.Name) { $problems.Add("skills/$($d.Name)/SKILL.md: name '$($fm['name'])' differs from the folder name") }
    if (-not $fm['description']) { $problems.Add("skills/$($d.Name)/SKILL.md: no description") }
    if ($fm['disable-model-invocation'] -ne 'true') { $problems.Add("skills/$($d.Name)/SKILL.md: disable-model-invocation is not true") }
    $skills += $d.Name
}

# 3. READMEs. The zh-TW patterns are regex escapes for the CJK counter word
# (U+500B) and the full-width comma (U+FF0C), so this file stays ASCII.
$cjkCounter = '\' + 'u500B'; $fullComma = '\' + 'uFF0C'
$readmes = @(
    @('README.md', '(\d+) subagents', '(\d+) skills in Claude Code'),
    @('README.zh-TW.md', "(\d+) $cjkCounter subagent", "(\d+) $cjkCounter skill${fullComma}Claude Code")
)
foreach ($r in $readmes) {
    $path = Join-Path $repo $r[0]
    if (-not (Test-Path $path)) { $problems.Add("$($r[0]): missing"); continue }
    $t = Read-Text $path
    foreach ($a in $agents) { if (-not $t.Contains("``$a``")) { $problems.Add("$($r[0]): agent $a is not listed") } }
    foreach ($s in $skills) { if (-not $t.Contains("``/$s``")) { $problems.Add("$($r[0]): skill /$s is not listed") } }
    foreach ($pair in @(@($r[1], $agents.Count, 'agent'), @($r[2], $skills.Count, 'skill'))) {
        $m = [regex]::Match($t, $pair[0])
        if (-not $m.Success) { $problems.Add("$($r[0]): no $($pair[2]) count found") }
        elseif ([int]$m.Groups[1].Value -ne $pair[1]) { $problems.Add("$($r[0]): says $($m.Groups[1].Value) $($pair[2])s, the repo has $($pair[1])") }
    }
}

# 4. portable\ is up to date
& powershell -NoProfile -ExecutionPolicy Bypass -File (Join-Path $repo 'build.ps1') | Out-Null
if ($LASTEXITCODE -ne 0) { $problems.Add("build.ps1 failed (exit code $LASTEXITCODE)") }
else {
    $changed = @(git -C $repo status --porcelain -- portable)
    if ($changed.Count -gt 0) {
        $problems.Add("portable\ changed after build.ps1; commit it with its sources:")
        $changed | ForEach-Object { $problems.Add("    $_") }
    }
}

# 5. ASCII-only PowerShell scripts
foreach ($f in (Get-ChildItem $repo -Filter '*.ps1')) {
    $bytes = [IO.File]::ReadAllBytes($f.FullName)
    $bad = @($bytes | Where-Object { $_ -gt 127 }).Count
    if ($bad -gt 0) { $problems.Add("$($f.Name): $bad non-ASCII bytes") }
}

Write-Host "Checked $($agents.Count) agents and $($skills.Count) skills."
if ($problems.Count -eq 0) { Write-Host 'PASS'; exit 0 }
$problems | ForEach-Object { Write-Host "  $_" }
Write-Host "FAIL ($(@($problems | Where-Object { -not $_.StartsWith('    ') }).Count) problems)"
exit 1
