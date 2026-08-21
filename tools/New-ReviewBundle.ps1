[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [ValidatePattern('^[0-9a-f]{40}$')]
    [string]$Base,

    [Parameter(Mandatory = $true)]
    [string]$Task,

    [string]$OutputPath
)

$ErrorActionPreference = 'Stop'
$projectRoot = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '..')).Path
$head = (git -C $projectRoot rev-parse HEAD).Trim()
$tree = (git -C $projectRoot rev-parse 'HEAD^{tree}').Trim()
$branch = (git -C $projectRoot branch --show-current).Trim()
$trackedStatus = @(git -C $projectRoot status --porcelain --untracked-files=no)

if ($trackedStatus.Count -ne 0) {
    throw 'Review bundles require a clean committed candidate; tracked staged or working-tree changes remain.'
}

git -C $projectRoot merge-base --is-ancestor $Base $head
if ($LASTEXITCODE -ne 0) {
    throw "Base $Base is not an ancestor of HEAD $head."
}

$reviewRoot = [IO.Path]::GetFullPath((Join-Path $projectRoot 'build\review'))
New-Item -ItemType Directory -Path $reviewRoot -Force | Out-Null
if (-not $OutputPath) {
    $safeTask = $Task -replace '[^A-Za-z0-9._-]', '-'
    $OutputPath = Join-Path $reviewRoot `
        ("$safeTask-" + $head.Substring(0, 12) + '.md')
}
else {
    $OutputPath = [IO.Path]::GetFullPath($OutputPath)
    $reviewPrefix = $reviewRoot.TrimEnd('\') + '\'
    if (-not $OutputPath.StartsWith($reviewPrefix,
            [StringComparison]::OrdinalIgnoreCase)) {
        throw 'Review bundle output must remain under build\review.'
    }
    New-Item -ItemType Directory -Path (Split-Path -Parent $OutputPath) `
        -Force | Out-Null
}

$commits = @(git -C $projectRoot log --reverse --format='- `%H` %s' "$Base..$head")
$paths = @(git -C $projectRoot diff --name-status "$Base..$head" |
    ForEach-Object { '- `' + $_ + '`' })
$patchLines = @(git -C $projectRoot diff --full-index --binary --no-ext-diff `
    "$Base..$head")
$patchText = ($patchLines -join "`n") + "`n"
$sha = [Security.Cryptography.SHA256]::Create()
try {
    $patchBytes = [Text.Encoding]::UTF8.GetBytes($patchText)
    $patchSha256 = [BitConverter]::ToString($sha.ComputeHash($patchBytes)).Replace('-', '').ToLowerInvariant()
}
finally {
    $sha.Dispose()
}

$verification = New-Object System.Collections.ArrayList
$verificationRoot = Join-Path $projectRoot 'build\verification'
if (Test-Path -LiteralPath $verificationRoot) {
    Get-ChildItem -LiteralPath $verificationRoot -Filter '*.json' -File |
        Sort-Object Name | ForEach-Object {
            try {
                $summary = Get-Content -LiteralPath $_.FullName -Raw |
                    ConvertFrom-Json
                $exact = ($summary.git_head -eq $head -and
                    $summary.git_tree -eq $tree -and
                    [int]$summary.tracked_dirty_before_count -eq 0 -and
                    [int]$summary.tracked_dirty_entry_count -eq 0)
                if (-not $exact) {
                    [void]$verification.Add('- `' + $summary.lane +
                        '`: **STALE/EXCLUDED**; summary is not bound to this clean tree.')
                }
                else {
                    [void]$verification.Add('- `' + $summary.lane + '`: **' +
                        $summary.status + '**; started `' + $summary.started_utc +
                        '`; finished `' + $summary.finished_utc +
                        '`; tracked dirty after `' +
                        $summary.tracked_dirty_entry_count + '`')
                    foreach ($check in @($summary.checks)) {
                        [void]$verification.Add('  - `' + $check.status +
                            '` exit `' + $check.exit_code + '` — ' + $check.name +
                            '; command: `' + (($check.command -replace '`', "''")) + '`')
                    }
                    if ($summary.failure) {
                        [void]$verification.Add('  - failure: `' +
                            (($summary.failure -replace '`', "''")) + '`')
                    }
                }
            }
            catch {
                [void]$verification.Add('- `' + $_.Name +
                    '`: **UNREADABLE/EXCLUDED**')
            }
        }
}
if ($verification.Count -eq 0) {
    [void]$verification.Add('- No exact-tree verification summaries were found.')
}
if ($commits.Count -eq 0) {
    $commits = @('- No commits in the selected range.')
}
if ($paths.Count -eq 0) {
    $paths = @('- No tracked path changes in the selected range.')
}

$statePath = Join-Path $projectRoot 'project_state.yaml'
$stateText = Get-Content -LiteralPath $statePath -Raw
$cardMatch = [regex]::Match($stateText,
    '(?m)^active_task_card:\s*(.+?)\s*$')
if (-not $cardMatch.Success) {
    throw 'project_state.yaml does not name an active task card.'
}
$cardPath = Join-Path $projectRoot $cardMatch.Groups[1].Value.Trim()
if (-not (Test-Path -LiteralPath $cardPath)) {
    throw "Active task card is missing: $cardPath"
}
$cardText = Get-Content -LiteralPath $cardPath -Raw

$bundle = @(
    '# Generated review bundle',
    '',
    "Task: $Task",
    ('Branch: `' + $branch + '`'),
    ('Base: `' + $Base + '`'),
    ('Head: `' + $head + '`'),
    ('Tree: `' + $tree + '`'),
    ('Patch SHA-256: `' + $patchSha256 + '`'),
    "Generated UTC: $((Get-Date).ToUniversalTime().ToString('o'))",
    'Tracked candidate state: clean',
    '',
    '## Project state',
    '',
    '```yaml',
    $stateText.TrimEnd(),
    '```',
    '',
    '## Active task card',
    '',
    $cardText.TrimEnd(),
    '',
    '## Commits',
    ''
) + $commits + @(
    '',
    '## Changed paths',
    ''
) + $paths + @(
    '',
    '## Verification',
    ''
) + @($verification) + @(
    '',
    '## Exact patch',
    '',
    '```diff',
    $patchText.TrimEnd(),
    '```',
    '',
    '## Reviewer result',
    '',
    '```text',
    'VERDICT: ACCEPTED | CORRECTIONS REQUIRED | NOT REVIEWABLE',
    'BLOCKING:',
    'NONBLOCKING:',
    'EVIDENCE:',
    'NEXT ACTION:',
    '```'
)

$bundle | Set-Content -LiteralPath $OutputPath -Encoding UTF8
Write-Output $OutputPath
