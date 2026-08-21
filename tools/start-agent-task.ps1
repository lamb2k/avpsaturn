[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$Task,

    [string]$WorktreePath,
    [switch]$Prepare,

    [ValidateSet('Auto', 'Implementation', 'Correction', 'Review',
        'EvidenceRepair')]
    [string]$TaskKind = 'Auto'
)

$ErrorActionPreference = 'Stop'
$projectRoot = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '..')).Path
$statePath = Join-Path $projectRoot 'project_state.yaml'
$Task = $Task.Trim()
if ($Task -notmatch '^[A-Za-z0-9][A-Za-z0-9._-]*$') {
    throw 'Task must contain only letters, digits, dot, underscore, or hyphen.'
}
$cardPath = Join-Path $projectRoot ("docs\task_cards\$Task.md")

function Read-Field {
    param([string]$Text, [string]$Name)
    $match = [regex]::Match($Text, '(?m)^' + [regex]::Escape($Name) +
        ':\s*(.+?)\s*$')
    if (-not $match.Success) {
        throw "Missing $Name in task metadata."
    }
    return $match.Groups[1].Value.Trim()
}

function Read-InlineList {
    param([string]$Text, [string]$Name)
    $value = Read-Field -Text $Text -Name $Name
    if ($value -notmatch '^\[(?<body>.*)\]$') {
        throw "$Name must be an inline list."
    }
    $body = $Matches['body'].Trim()
    if (-not $body) {
        return @()
    }
    return @($body.Split(',') | ForEach-Object { $_.Trim() })
}

function Read-Blockers {
    param([string]$Text)
    $section = [regex]::Match($Text,
        '(?m)^open_blockers:[ \t]*\r?\n(?<body>(?:^[ \t]+[^\r\n]*(?:\r?\n|$))*)')
    if ($section.Success) {
        return @([regex]::Matches($section.Groups['body'].Value,
                '(?m)^\s*-\s+(?<value>\S.*)$') |
            ForEach-Object { $_.Groups['value'].Value.Trim() })
    }
    $inline = [regex]::Match($Text,
        '(?m)^open_blockers:[ \t]*(?<value>[^\r\n]+?)[ \t]*$')
    if ($inline.Success -and $inline.Groups['value'].Value.Trim() -ne '[]') {
        return @($inline.Groups['value'].Value.Trim())
    }
    return @()
}

if (-not (Test-Path -LiteralPath $statePath)) {
    throw "Missing project state: $statePath"
}
if (-not (Test-Path -LiteralPath $cardPath)) {
    throw "Missing task card: $cardPath"
}

$state = Get-Content -LiteralPath $statePath -Raw
$card = Get-Content -LiteralPath $cardPath -Raw
$status = Read-Field -Text $card -Name 'STATUS'
$stateStatus = Read-Field -Text $state -Name 'task_status'
$activeCard = (Read-Field -Text $state -Name 'active_task_card').Replace('/', '\')
$expectedCard = "docs\task_cards\$Task.md"
if ($activeCard -ne $expectedCard) {
    throw "Task $Task is not active. project_state names $activeCard."
}
if ($stateStatus -ne $status) {
    throw "Task/card status mismatch: project_state=$stateStatus card=$status."
}
$candidateStatus = Read-Field -Text $state -Name 'review_candidate_status'
if ($TaskKind -eq 'Auto') {
    switch ($status) {
        'READY' { $TaskKind = 'Implementation' }
        'CORRECTIONS' { $TaskKind = 'Correction' }
        'REVIEW' { $TaskKind = 'Review' }
        'EVIDENCE_REPAIR' { $TaskKind = 'EvidenceRepair' }
        default { throw "Task $Task status $status has no launch kind." }
    }
}

switch ($TaskKind) {
    'Implementation' {
        if ($status -ne 'READY') {
            throw "Implementation launch requires READY; task is $status."
        }
    }
    'Correction' {
        if ($status -ne 'CORRECTIONS' -or
            $candidateStatus -ne 'CORRECTIONS_REQUIRED') {
            throw ('Correction launch requires task_status=CORRECTIONS and ' +
                'review_candidate_status=CORRECTIONS_REQUIRED.')
        }
        if ($Prepare) {
            throw 'Corrections must reuse the existing branch/worktree; omit -Prepare.'
        }
    }
    'Review' {
        if ($status -ne 'REVIEW') {
            throw "Review launch requires REVIEW; task is $status."
        }
        if ($Prepare) {
            throw 'Review is read-only and cannot prepare a worktree.'
        }
    }
    'EvidenceRepair' {
        if ($status -ne 'EVIDENCE_REPAIR') {
            throw "Evidence repair requires EVIDENCE_REPAIR; task is $status."
        }
        if ($Prepare) {
            throw 'Evidence repair must reuse the existing branch/worktree; omit -Prepare.'
        }
    }
}
$checkpoint = Read-Field -Text $card -Name 'CHECKPOINT'
$stateCheckpoint = Read-Field -Text $state -Name 'current_checkpoint'
if ($checkpoint -ne $stateCheckpoint) {
    throw "Checkpoint mismatch: project_state=$stateCheckpoint card=$checkpoint."
}
$dependencies = @(Read-InlineList -Text $card -Name 'DEPENDENCIES')
$acceptedTasks = @(Read-InlineList -Text $state -Name 'accepted_tasks')
if ($TaskKind -eq 'Implementation') {
    foreach ($dependency in $dependencies) {
        if ($dependency -notin $acceptedTasks) {
            throw "Task $Task depends on unaccepted task $dependency."
        }
    }
}
$requiredLanes = @(Read-InlineList -Text $card -Name 'REQUIRED_LANES')
$optionalLanes = @(Read-InlineList -Text $card -Name 'OPTIONAL_LANES')
if ($requiredLanes.Count -eq 0) {
    throw "Task $Task does not declare any required verification lane."
}

$blockers = @(Read-Blockers -Text $state)
if ($TaskKind -eq 'Implementation' -and $blockers.Count -ne 0) {
    throw 'A new implementation cannot launch while project_state has blockers.'
}
if ($TaskKind -in @('Correction', 'EvidenceRepair') -and
    $blockers.Count -eq 0) {
    throw "$TaskKind requires a non-empty consolidated blocker list."
}

$acceptedHead = Read-Field -Text $state -Name 'accepted_head'
$candidateHead = Read-Field -Text $state -Name 'review_candidate_head'
if ($TaskKind -eq 'Implementation' -and $acceptedHead -ne $candidateHead) {
    throw 'A new implementation requires the review candidate to be accepted.'
}
if ($TaskKind -in @('Correction', 'Review', 'EvidenceRepair') -and
    $acceptedHead -eq $candidateHead) {
    throw "$TaskKind requires a candidate newer than the accepted head."
}

$trackedStatus = @(git -C $projectRoot status --porcelain --untracked-files=no)
if ($TaskKind -in @('Implementation', 'EvidenceRepair') -and
    $trackedStatus.Count -ne 0) {
    throw 'Commit or restore tracked workflow changes before launching a task.'
}

$branch = Read-Field -Text $card -Name 'BRANCH'
$tierText = Read-Field -Text $card -Name 'TIER'
$baseToken = Read-Field -Text $card -Name 'BASE'
if ($baseToken -eq 'project_state.accepted_head') {
    $base = $acceptedHead
}
elseif ($baseToken -eq 'repository.HEAD') {
    $base = (git -C $projectRoot rev-parse HEAD).Trim()
}
else {
    $base = $baseToken
}
if ($base -notmatch '^[0-9a-f]{40}$') {
    throw "Resolved BASE is not a full Git SHA: $base"
}

$tier = [int]$tierText
switch ($tier) {
    0 { $model = 'gpt-5.6-terra'; $reasoning = 'medium' }
    1 { $model = 'gpt-5.6-sol'; $reasoning = 'high' }
    2 { $model = 'gpt-5.6-sol'; $reasoning = 'xhigh' }
    default { throw "Unsupported review tier: $tier" }
}

git -C $projectRoot cat-file -e "$base^{commit}" 2>$null
if ($LASTEXITCODE -ne 0) {
    throw "BASE is not present in the repository: $base"
}
git -C $projectRoot merge-base --is-ancestor $acceptedHead $base
if ($LASTEXITCODE -ne 0) {
    throw "Launch BASE $base does not contain accepted HEAD $acceptedHead."
}

if (-not $WorktreePath) {
    $parent = Split-Path -Parent $projectRoot
    $leaf = (Split-Path -Leaf $projectRoot) + '-' + $Task.ToLowerInvariant()
    $WorktreePath = Join-Path $parent $leaf
}
$WorktreePath = [IO.Path]::GetFullPath($WorktreePath)

$branchExists = $false
git -C $projectRoot show-ref --verify --quiet "refs/heads/$branch"
if ($LASTEXITCODE -eq 0) {
    $branchExists = $true
}

$porcelain = @(git -C $projectRoot worktree list --porcelain)
$existingWorktree = $null
for ($index = 0; $index -lt $porcelain.Count; $index++) {
    if ($porcelain[$index] -eq "branch refs/heads/$branch") {
        for ($scan = $index - 1; $scan -ge 0; $scan--) {
            if ($porcelain[$scan] -like 'worktree *') {
                $existingWorktree = $porcelain[$scan].Substring(9)
                break
            }
        }
        break
    }
}

if ($branchExists) {
    $branchHead = (git -C $projectRoot rev-parse $branch).Trim()
    git -C $projectRoot merge-base --is-ancestor $base $branchHead
    if ($LASTEXITCODE -ne 0) {
        throw "Existing branch $branch is not descended from BASE $base."
    }
    if ($existingWorktree) {
        $WorktreePath = [IO.Path]::GetFullPath($existingWorktree)
    }
    elseif ($Prepare) {
        if (Test-Path -LiteralPath $WorktreePath) {
            throw "Worktree target already exists: $WorktreePath"
        }
        git -C $projectRoot worktree add $WorktreePath $branch
        if ($LASTEXITCODE -ne 0) {
            throw 'Could not attach the existing checkpoint branch.'
        }
    }
}
elseif ($Prepare) {
    if (Test-Path -LiteralPath $WorktreePath) {
        throw "Worktree target already exists: $WorktreePath"
    }
    git -C $projectRoot worktree add -b $branch $WorktreePath $base
    if ($LASTEXITCODE -ne 0) {
        throw 'Could not create the checkpoint branch/worktree.'
    }
}

if ($TaskKind -in @('Correction', 'Review', 'EvidenceRepair')) {
    if (-not $branchExists) {
        throw "$TaskKind requires the existing branch $branch."
    }
    if (-not $existingWorktree) {
        throw "$TaskKind requires an attached worktree for $branch."
    }
    $WorktreePath = [IO.Path]::GetFullPath($existingWorktree)
    $branchHead = (git -C $WorktreePath rev-parse HEAD).Trim()
    git -C $WorktreePath merge-base --is-ancestor $candidateHead $branchHead
    if ($LASTEXITCODE -ne 0) {
        throw ("Reviewed candidate $candidateHead is not an ancestor of " +
            "the current $TaskKind branch head $branchHead.")
    }
}

$preexistingChanges = @()
if (Test-Path -LiteralPath $WorktreePath) {
    $preexistingChanges = @(git -C $WorktreePath status --short --untracked-files=no |
        ForEach-Object {
            if ($_ -match '^(?<status>.{2})\s+(?<path>.+)$') {
                [ordered]@{
                    status = $Matches['status'].Trim()
                    path = $Matches['path'].Trim()
                }
            }
        })
}

$launchRoot = Join-Path $projectRoot 'build\task-launch'
New-Item -ItemType Directory -Path $launchRoot -Force | Out-Null
$stamp = (Get-Date).ToUniversalTime().ToString('yyyyMMddTHHmmssZ')
$launchPath = Join-Path $launchRoot ("$Task-$stamp.txt")
$metadataPath = Join-Path $launchRoot ("$Task-$stamp.json")

$prompt = @(
    "TASK_LAUNCH: $Task",
    "TASK_KIND: $TaskKind",
    "MODEL: $model",
    "REASONING_EFFORT: $reasoning",
    "BASE: $base",
    "BRANCH: $branch",
    "WORKTREE: $WorktreePath",
    "REQUIRED_LANES: $($requiredLanes -join ', ')",
    "OPTIONAL_LANES: $($optionalLanes -join ', ')",
    '',
    'The control-plane snapshots below are authoritative for this invocation.',
    'Read the worktree AGENTS.md for repository mechanics, but do not let an',
    'older candidate-branch state override these snapshots.',
    '',
    'CONTROL-PLANE POLICY SNAPSHOT:',
    (Get-Content -LiteralPath (Join-Path $projectRoot 'AGENTS.md') -Raw).Trim(),
    '',
    'CONTROL-PLANE STATE SNAPSHOT:',
    $state.Trim(),
    '',
    'ACTIVE TASK CARD:',
    '',
    $card.Trim()
)
if ($TaskKind -in @('Correction', 'EvidenceRepair')) {
    $prompt += @(
        '',
        'CONSOLIDATED BLOCKERS (all are required correction objectives):'
    )
    $prompt += @($blockers | ForEach-Object { "- $_" })
    if ($preexistingChanges.Count -ne 0) {
        $prompt += @(
            '',
            'PREEXISTING WORKTREE CHANGES:',
            'These changes predate this invocation and are part of the bounded correction.',
            'Preserve them. Do not reset, restore, stash, or replace them.'
        )
        $prompt += @($preexistingChanges | ForEach-Object {
                "- $($_.status) $($_.path)"
            })
    }
}
$prompt | Set-Content -LiteralPath $launchPath -Encoding UTF8

[ordered]@{
    schema = 1
    task = $Task
    task_kind = $TaskKind
    tier = $tier
    model = $model
    reasoning_effort = $reasoning
    base = $base
    branch = $branch
    worktree = $WorktreePath
    dependencies = @($dependencies)
    required_lanes = @($requiredLanes)
    optional_lanes = @($optionalLanes)
    candidate_head = $candidateHead
    candidate_status = $candidateStatus
    blockers = @($blockers)
    preexisting_changes = @($preexistingChanges)
    prepared = [bool]$Prepare
    launch_prompt = $launchPath
} | ConvertTo-Json -Depth 4 | Set-Content -LiteralPath $metadataPath -Encoding UTF8

Write-Output "Launch card: $launchPath"
Write-Output "Metadata: $metadataPath"
Write-Output "Model: $model ($reasoning)"
Write-Output "Worktree: $WorktreePath"
