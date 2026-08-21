[CmdletBinding(SupportsShouldProcess = $true)]
param(
    [Parameter(Mandatory = $true)]
    [string]$DispositionPath,
    [string]$ProjectRoot
)

$ErrorActionPreference = 'Stop'
$projectRoot = if ($ProjectRoot) {
    (Resolve-Path -LiteralPath $ProjectRoot).Path
} else {
    (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '..')).Path
}
$statePath = Join-Path $projectRoot 'project_state.yaml'
$buildRoot = [IO.Path]::GetFullPath((Join-Path $projectRoot 'build'))
$dispositionPath = (Resolve-Path -LiteralPath $DispositionPath).Path
if (-not $dispositionPath.StartsWith($buildRoot.TrimEnd('\') + '\',
        [StringComparison]::OrdinalIgnoreCase)) {
    throw 'External review dispositions must remain under ignored build/.'
}

function Read-Field {
    param([string]$Text, [string]$Name, [switch]$Optional)
    $match = [regex]::Match($Text, '(?m)^' + [regex]::Escape($Name) +
        ':\s*(.+?)\s*$')
    if (-not $match.Success) {
        if ($Optional) { return $null }
        throw "Missing $Name in workflow metadata."
    }
    return $match.Groups[1].Value.Trim()
}

function Read-InlineList {
    param([string]$Text, [string]$Name)
    $value = Read-Field -Text $Text -Name $Name
    if ($value -notmatch '^\[(?<body>.*)\]$') { throw "$Name must be an inline list." }
    if (-not $Matches['body'].Trim()) { return @() }
    return @($Matches['body'].Split(',') | ForEach-Object { $_.Trim() })
}

function Set-Field {
    param([string]$Text, [string]$Name, [string]$Value)
    $pattern = '(?m)^' + [regex]::Escape($Name) + ':\s*.*$'
    if ($Text -notmatch $pattern) { throw "Cannot update missing field $Name." }
    return [regex]::Replace($Text, $pattern, "$Name`: $Value", 1)
}

function Set-Blockers {
    param([string]$Text, [string[]]$Blockers)
    $replacement = if ($Blockers.Count -eq 0) {
        'open_blockers: []'
    } else {
        'open_blockers:' + "`r`n" + (($Blockers | ForEach-Object {
                    '  - ' + (($_ -replace '[\r\n]+', ' ').Trim())
                }) -join "`r`n")
    }
    $pattern = '(?m)^open_blockers:[ \t]*\r?\n(?:^[ \t]+[^\r\n]*(?:\r?\n|$))*'
    if ($Text -match $pattern) {
        return [regex]::Replace($Text, $pattern, $replacement + "`r`n", 1)
    }
    return [regex]::Replace($Text, '(?m)^open_blockers:.*$', $replacement, 1)
}

function Set-CardStatusText {
    param([string]$Text, [string]$Status)
    return Set-Field -Text $Text -Name 'STATUS' -Value $Status
}

function Get-Sha256 {
    param([string]$Path)
    $stream = [IO.File]::OpenRead($Path)
    $sha = [Security.Cryptography.SHA256]::Create()
    try {
        return ([BitConverter]::ToString($sha.ComputeHash($stream))).Replace('-', '').ToLowerInvariant()
    }
    finally {
        $sha.Dispose()
        $stream.Dispose()
    }
}

function Resolve-BuildArtifact {
    param([string]$Path, [string]$ExpectedSha256, [string]$Name)
    $resolved = (Resolve-Path -LiteralPath $Path).Path
    if (-not $resolved.StartsWith($buildRoot.TrimEnd('\') + '\',
            [StringComparison]::OrdinalIgnoreCase)) {
        throw "$Name must remain under ignored build/."
    }
    $actual = Get-Sha256 -Path $resolved
    if ($actual -ne $ExpectedSha256.ToLowerInvariant()) {
        throw "$Name SHA-256 mismatch."
    }
    return $resolved
}

$disposition = Get-Content -LiteralPath $dispositionPath -Raw | ConvertFrom-Json
if ([int]$disposition.schema -ne 1) { throw 'Disposition schema must be 1.' }
if ($disposition.task -notmatch '^[A-Za-z0-9][A-Za-z0-9._-]*$') {
    throw 'Disposition task id is invalid.'
}
if ($disposition.candidate_head -notmatch '^[0-9a-f]{40}$') {
    throw 'Disposition candidate_head must be a full lowercase Git SHA.'
}
$allowedVerdicts = @('ACCEPTED', 'CORRECTIONS REQUIRED', 'NOT REVIEWABLE')
if ($disposition.verdict -notin $allowedVerdicts) { throw 'Unsupported disposition verdict.' }

$reviews = @($disposition.reviews)
$requiredRoles = @('semantic', 'provenance', 'saturn')
if ($reviews.Count -ne 3 -or
    @($reviews.role | Sort-Object -Unique).Count -ne 3 -or
    @($requiredRoles | Where-Object { $_ -notin $reviews.role }).Count -ne 0) {
    throw 'Disposition requires exactly semantic, provenance, and saturn reviews.'
}
foreach ($review in $reviews) {
    if ($review.verdict -notin $allowedVerdicts) {
        throw "Review $($review.role) has an unsupported verdict."
    }
    $reviewPath = Resolve-BuildArtifact -Path $review.output_path `
        -ExpectedSha256 $review.output_sha256 -Name "$($review.role) review"
    $reviewText = Get-Content -LiteralPath $reviewPath -Raw
    if ($reviewText -notmatch ('(?im)^\s*VERDICT:\s*' +
            [regex]::Escape($review.verdict) + '\s*$')) {
        throw "Review $($review.role) output does not contain its declared verdict."
    }
}
$expectedVerdict = if (@($reviews | Where-Object verdict -eq 'NOT REVIEWABLE').Count) {
    'NOT REVIEWABLE'
} elseif (@($reviews | Where-Object verdict -eq 'CORRECTIONS REQUIRED').Count) {
    'CORRECTIONS REQUIRED'
} else { 'ACCEPTED' }
if ($disposition.verdict -ne $expectedVerdict) {
    throw "Disposition must conservatively resolve to $expectedVerdict."
}
$blockers = @($disposition.blocking | ForEach-Object { [string]$_ } |
    Where-Object { -not [string]::IsNullOrWhiteSpace($_) })
if ($disposition.verdict -eq 'ACCEPTED' -and $blockers.Count -ne 0) {
    throw 'ACCEPTED cannot carry blocking findings.'
}
if ($disposition.verdict -ne 'ACCEPTED' -and $blockers.Count -eq 0) {
    throw "$($disposition.verdict) requires at least one blocking finding."
}

$bundlePath = Resolve-BuildArtifact -Path $disposition.review_bundle_path `
    -ExpectedSha256 $disposition.review_bundle_sha256 -Name 'review bundle'
$bundleText = Get-Content -LiteralPath $bundlePath -Raw
if ($bundleText -notmatch ('(?m)^Task:\s*' + [regex]::Escape($disposition.task) + '\s*$') -or
    $bundleText -notmatch ('(?m)^Head:\s*`?' + $disposition.candidate_head + '`?\s*$')) {
    throw 'Review bundle is not bound to the declared task and candidate.'
}

$state = Get-Content -LiteralPath $statePath -Raw
$activeCardRelative = Read-Field -Text $state -Name 'active_task_card'
$activeTask = [IO.Path]::GetFileNameWithoutExtension($activeCardRelative)
if ($activeTask -ne $disposition.task) {
    throw "Disposition task $($disposition.task) is not active ($activeTask)."
}
$cardPath = Join-Path $projectRoot ($activeCardRelative -replace '/', '\')
$card = Get-Content -LiteralPath $cardPath -Raw
$branch = Read-Field -Text $card -Name 'BRANCH'
$priorCandidate = Read-Field -Text $state -Name 'review_candidate_head'

$porcelain = @(git -C $projectRoot worktree list --porcelain)
$candidateRoot = $null
for ($index = 0; $index -lt $porcelain.Count; $index++) {
    if ($porcelain[$index] -eq "branch refs/heads/$branch") {
        for ($scan = $index - 1; $scan -ge 0; $scan--) {
            if ($porcelain[$scan] -like 'worktree *') {
                $candidateRoot = $porcelain[$scan].Substring(9)
                break
            }
        }
        break
    }
}
if (-not $candidateRoot) { throw "Active candidate branch has no attached worktree: $branch" }
$candidateHead = (git -C $candidateRoot rev-parse HEAD).Trim()
if ($candidateHead -ne $disposition.candidate_head) {
    throw "Candidate moved: disposition=$($disposition.candidate_head) worktree=$candidateHead."
}
$candidateDirty = @(git -C $candidateRoot status --porcelain --untracked-files=no)
if ($candidateDirty.Count -ne 0) { throw 'Candidate worktree must be clean and committed.' }
git -C $candidateRoot merge-base --is-ancestor $priorCandidate $candidateHead
if ($LASTEXITCODE -ne 0) { throw 'Candidate is not descended from the reviewed checkpoint.' }

$controllerDirty = @(git -C $projectRoot status --porcelain --untracked-files=no)
if ($controllerDirty.Count -ne 0) {
    throw 'Controller worktree must be clean before applying a disposition.'
}
if ($disposition.verdict -eq 'ACCEPTED') {
    git -C $projectRoot merge-base --is-ancestor $candidateHead HEAD
    if ($LASTEXITCODE -ne 0) {
        throw 'Accepted candidate must be integrated into controller HEAD before state promotion.'
    }
}

$state = Set-Field $state 'review_candidate_head' $candidateHead
$changedPaths = @($statePath, $cardPath)
switch ($disposition.verdict) {
    'CORRECTIONS REQUIRED' {
        $state = Set-Field $state 'review_candidate_status' 'CORRECTIONS_REQUIRED'
        $state = Set-Field $state 'task_status' 'CORRECTIONS'
        $state = Set-Blockers $state $blockers
        $card = Set-CardStatusText $card 'CORRECTIONS'
    }
    'NOT REVIEWABLE' {
        $state = Set-Field $state 'review_candidate_status' 'NOT_REVIEWABLE'
        $state = Set-Field $state 'task_status' 'NOT_REVIEWABLE'
        $state = Set-Blockers $state $blockers
        $card = Set-CardStatusText $card 'NOT_REVIEWABLE'
    }
    'ACCEPTED' {
        $accepted = @(Read-InlineList -Text $state -Name 'accepted_tasks')
        if ($activeTask -notin $accepted) { $accepted += $activeTask }
        $nextTask = Read-Field -Text $card -Name 'NEXT_TASK'
        if (-not $nextTask -or $nextTask -eq 'AUTO') {
            throw 'ACCEPTED requires an explicitly predeclared NEXT_TASK; automatic selection is forbidden.'
        }
        $nextCardPath = Join-Path $projectRoot "docs\task_cards\$nextTask.md"
        if (-not (Test-Path -LiteralPath $nextCardPath)) { throw "Missing NEXT_TASK card: $nextTask" }
        $nextCard = Get-Content -LiteralPath $nextCardPath -Raw
        $dependencies = @(Read-InlineList -Text $nextCard -Name 'DEPENDENCIES')
        $missingDependencies = @($dependencies | Where-Object { $_ -notin $accepted })
        if ($missingDependencies.Count -ne 0) {
            throw "NEXT_TASK has unaccepted dependencies: $($missingDependencies -join ', ')"
        }
        $state = Set-Field $state 'accepted_head' $candidateHead
        $state = Set-Field $state 'review_candidate_status' 'ACCEPTED'
        $state = Set-Field $state 'accepted_tasks' ('[' + ($accepted -join ', ') + ']')
        $state = Set-Field $state 'current_checkpoint' `
            (Read-Field -Text $nextCard -Name 'CHECKPOINT')
        $state = Set-Field $state 'active_task_card' "docs/task_cards/$nextTask.md"
        $state = Set-Field $state 'task_status' 'READY'
        $state = Set-Blockers $state @()
        $card = Set-CardStatusText $card 'ACCEPTED'
        $nextCard = Set-CardStatusText $nextCard 'READY'
        $changedPaths += $nextCardPath
        $script:nextCardText = $nextCard
        $manifest = Join-Path $projectRoot 'data\avsp_hit_ko_writer_set.json'
        if (Test-Path -LiteralPath $manifest) {
            $hash = Get-Sha256 -Path $manifest
            $state = Set-Field $state 'writer_set_manifest_sha256' $hash
        }
    }
}

if ($PSCmdlet.ShouldProcess($projectRoot,
        "apply $($disposition.verdict) for $activeTask at $candidateHead")) {
    $state | Set-Content -LiteralPath $statePath -Encoding UTF8
    $card | Set-Content -LiteralPath $cardPath -Encoding UTF8
    if ($script:nextCardText) {
        $script:nextCardText | Set-Content -LiteralPath $changedPaths[-1] -Encoding UTF8
    }
}

[ordered]@{
    schema = 1
    task = $activeTask
    candidate_head = $candidateHead
    verdict = $disposition.verdict
    changed_paths = @($changedPaths)
    commit_required = $true
    next_action = 'Goal Mode must inspect the diff, run Fast, and commit explicit paths.'
} | ConvertTo-Json -Depth 5
