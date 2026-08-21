[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [ValidatePattern('^[0-9a-f]{40}$')]
    [string]$Base,

    [Parameter(Mandatory = $true)]
    [string]$Task,

    [string]$OutputPath,
    [string]$CandidateRoot,
    [string]$TaskCard
)

$ErrorActionPreference = 'Stop'
$projectRoot = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '..')).Path
if ($CandidateRoot) {
    $candidateRoot = (Resolve-Path -LiteralPath $CandidateRoot).Path
}
else {
    $candidateRoot = $projectRoot
}
$head = (git -C $candidateRoot rev-parse HEAD).Trim()
$tree = (git -C $candidateRoot rev-parse 'HEAD^{tree}').Trim()
$branch = (git -C $candidateRoot branch --show-current).Trim()
$trackedStatus = @(git -C $candidateRoot status --porcelain --untracked-files=no)

if ($trackedStatus.Count -ne 0) {
    throw 'Review bundles require a clean committed candidate; tracked staged or working-tree changes remain.'
}

git -C $candidateRoot merge-base --is-ancestor $Base $head
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

$commits = @(git -C $candidateRoot log --reverse --format='- `%H` %s' "$Base..$head")
$paths = @(git -C $candidateRoot diff --name-status "$Base..$head" |
    ForEach-Object { '- `' + $_ + '`' })
$patchLines = @(git -C $candidateRoot diff --full-index --binary --no-ext-diff `
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
$verificationRoot = Join-Path $candidateRoot 'build\verification'
$exactVerification = @{}
if (Test-Path -LiteralPath $verificationRoot) {
    Get-ChildItem -LiteralPath $verificationRoot -Filter '*.json' -File |
        Sort-Object Name | ForEach-Object {
            try {
                $summary = Get-Content -LiteralPath $_.FullName -Raw |
                    ConvertFrom-Json
                if (-not $summary.lane) {
                    return
                }
                $exact = ($summary.git_head -eq $head -and
                    $summary.git_tree -eq $tree -and
                    [int]$summary.tracked_dirty_before_count -eq 0 -and
                    [int]$summary.tracked_dirty_entry_count -eq 0)
                if (-not $exact) {
                    [void]$verification.Add('- `' + $summary.lane +
                        '`: **STALE/EXCLUDED**; summary is not bound to this clean tree.')
                }
                else {
                    $exactVerification[$summary.lane] = $summary.status
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
if ($TaskCard) {
    if ($TaskCard -notmatch '^[A-Za-z0-9][A-Za-z0-9._-]*$') {
        throw 'TaskCard must be a task-card id without a path.'
    }
    $cardRelative = "docs/task_cards/$TaskCard.md"
}
elseif ($cardMatch.Success) {
    $cardRelative = $cardMatch.Groups[1].Value.Trim()
}
else {
    throw 'project_state.yaml does not name an active task card.'
}
$cardPath = Join-Path $projectRoot $cardRelative
if (-not (Test-Path -LiteralPath $cardPath)) {
    throw "Active task card is missing: $cardPath"
}
$cardText = Get-Content -LiteralPath $cardPath -Raw
$requiredMatch = [regex]::Match($cardText,
    '(?m)^REQUIRED_LANES:\s*\[(?<body>[^\]]*)\]\s*$')
$optionalMatch = [regex]::Match($cardText,
    '(?m)^OPTIONAL_LANES:\s*\[(?<body>[^\]]*)\]\s*$')
if (-not $requiredMatch.Success -or -not $optionalMatch.Success) {
    throw 'Active task card must declare REQUIRED_LANES and OPTIONAL_LANES.'
}
$requiredLanes = @($requiredMatch.Groups['body'].Value.Split(',') |
    ForEach-Object { $_.Trim() } | Where-Object { $_ })
$optionalLanes = @($optionalMatch.Groups['body'].Value.Split(',') |
    ForEach-Object { $_.Trim() } | Where-Object { $_ })
foreach ($lane in $requiredLanes) {
    if (-not $exactVerification.ContainsKey($lane)) {
        [void]$verification.Add('- `' + $lane +
            '`: **MISSING REQUIRED**; no exact-tree summary was found.')
    }
}

$bundle = @(
    '# Generated review bundle',
    '',
    "Task: $Task",
    ('Branch: `' + $branch + '`'),
    ('Base: `' + $Base + '`'),
    ('Head: `' + $head + '`'),
    ('Tree: `' + $tree + '`'),
    ('Patch SHA-256: `' + $patchSha256 + '`'),
    ('Required lanes: `' + ($requiredLanes -join ', ') + '`'),
    ('Optional lanes: `' + ($optionalLanes -join ', ') + '`'),
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
