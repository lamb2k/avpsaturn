[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$Task,
    [ValidateSet('Auto', 'Codex', 'Claude')]
    [string]$Executor = 'Auto',
    [ValidateSet('Auto', 'Implementation', 'Correction', 'EvidenceRepair')]
    [string]$TaskKind = 'Auto',
    [ValidateSet('Auto', 'low', 'medium')]
    [string]$Effort = 'Auto',
    [string]$ResumeSessionId,
    [string]$FeedbackPath,
    [switch]$PlanOnly,
    [string]$ProjectRoot
)

$ErrorActionPreference = 'Stop'
$projectRoot = if ($ProjectRoot) {
    (Resolve-Path -LiteralPath $ProjectRoot).Path
} else {
    (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '..')).Path
}
$cardPath = Join-Path $projectRoot "docs\task_cards\$Task.md"
$launcher = Join-Path $projectRoot 'tools\start-agent-task.ps1'
$verifyScript = Join-Path $projectRoot 'verify.ps1'
$bundleScript = Join-Path $projectRoot 'tools\New-ReviewBundle.ps1'
$runRoot = Join-Path $projectRoot 'build\task-executor'
New-Item -ItemType Directory -Path $runRoot -Force | Out-Null

function Read-Field {
    param([string]$Text, [string]$Name, [switch]$Optional)
    $match = [regex]::Match($Text, '(?m)^' + [regex]::Escape($Name) +
        ':\s*(.+?)\s*$')
    if (-not $match.Success) {
        if ($Optional) { return $null }
        throw "Missing $Name in task metadata."
    }
    return $match.Groups[1].Value.Trim()
}

function Read-InlineList {
    param([string]$Text, [string]$Name, [switch]$Optional)
    $value = Read-Field -Text $Text -Name $Name -Optional:$Optional
    if ($null -eq $value) { return @() }
    if ($value -notmatch '^\[(?<body>.*)\]$') { throw "$Name must be an inline list." }
    if (-not $Matches['body'].Trim()) { return @() }
    return @($Matches['body'].Split(',') | ForEach-Object { $_.Trim() })
}

function Get-TrackedStatusPaths {
    param([string]$Root)
    return @(git -C $Root status --short --untracked-files=no | ForEach-Object {
            if ($_ -match '^.{2}\s+(?<path>.+)$') { $Matches['path'].Trim() }
        })
}

function Assert-CorrectionScope {
    param([string[]]$Paths, [string[]]$Allowed, [string]$Phase)
    $unexpected = @($Paths | Where-Object { $_ -notin $Allowed } | Sort-Object -Unique)
    if ($unexpected.Count -ne 0) {
        throw ("$Phase contains paths outside CORRECTION_PATHS: " +
            ($unexpected -join ', '))
    }
}

function Resolve-ClaudeCommand {
    $commands = @(
        (Get-Command claude.cmd -ErrorAction SilentlyContinue),
        (Get-Command claude.exe -ErrorAction SilentlyContinue)
    ) | Where-Object { $_ }
    foreach ($command in $commands) {
        $probeCommand = '"' + $command.Source + '" --version >nul 2>nul'
        & cmd.exe /d /c $probeCommand
        if ($LASTEXITCODE -eq 0) { return $command.Source }
    }
    return $null
}

function Resolve-Executor {
    param(
        [string]$Requested,
        [string]$Policy,
        [string]$Preferred,
        [bool]$RequireCommand
    )
    $claudeCommand = Resolve-ClaudeCommand
    if ($Requested -eq 'Claude') {
        if ($Policy -eq 'CODEX') { throw "Task $Task permits only Codex." }
        if ($RequireCommand -and -not $claudeCommand) {
            throw ('Claude was requested, but no working local Claude CLI was found. ' +
                'The installed Windows launcher currently reports an incompatible executable.')
        }
        return [ordered]@{ name = 'Claude'; command = $claudeCommand }
    }
    if ($Requested -eq 'Codex') {
        if ($Policy -eq 'CLAUDE') { throw "Task $Task permits only Claude." }
        $codex = Get-Command codex.exe -ErrorAction SilentlyContinue
        if (-not $codex) { $codex = Get-Command codex -ErrorAction SilentlyContinue }
        if ($RequireCommand -and -not $codex) { throw 'Codex CLI is not installed.' }
        return [ordered]@{ name = 'Codex'; command = if ($codex) { $codex.Source } else { $null } }
    }
    if ($Policy -eq 'CLAUDE' -or
        ($Preferred -eq 'CLAUDE' -and (-not $RequireCommand -or $claudeCommand))) {
        if ($RequireCommand -and -not $claudeCommand) {
            throw 'Task requires Claude, but no working local Claude CLI was found.'
        }
        return [ordered]@{ name = 'Claude'; command = $claudeCommand }
    }
    $codex = Get-Command codex.exe -ErrorAction SilentlyContinue
    if (-not $codex) { $codex = Get-Command codex -ErrorAction SilentlyContinue }
    if ($RequireCommand -and -not $codex) { throw 'Auto could not find a working Codex or Claude CLI.' }
    return [ordered]@{ name = 'Codex'; command = if ($codex) { $codex.Source } else { $null } }
}

function Invoke-AgentTurn {
    param(
        [System.Collections.IDictionary]$Provider,
        [string]$Prompt,
        [string]$Worktree,
        [string]$Model,
        [string]$SessionId,
        [string]$ClaudeModel,
        [string]$ClaudeEffort
    )
    $safeTask = $Task -replace '[^A-Za-z0-9._-]', '-'
    $stamp = (Get-Date).ToUniversalTime().ToString('yyyyMMddTHHmmssZ')
    $prefix = Join-Path $runRoot "$safeTask-$stamp"
    $stdoutPath = "$prefix.stdout"
    $stderrPath = "$prefix.stderr"
    $lastPath = "$prefix.last.txt"
    Push-Location $Worktree
    $savedPreference = $ErrorActionPreference
    $ErrorActionPreference = 'Continue'
    try {
        if ($Provider.name -eq 'Codex') {
            if ($SessionId) {
                $arguments = @('exec', 'resume', $SessionId, '--model', $Model,
                    '--json', '--output-last-message', $lastPath, '-')
            } else {
                $arguments = @('exec', '--cd', $Worktree, '--model', $Model,
                    '--sandbox', 'workspace-write', '--json',
                    '--output-last-message', $lastPath, '-')
            }
            $Prompt | & $Provider.command @arguments 1> $stdoutPath 2> $stderrPath
            $exitCode = $LASTEXITCODE
            $threadEvent = Get-Content -LiteralPath $stdoutPath -ErrorAction SilentlyContinue |
                ForEach-Object { try { $_ | ConvertFrom-Json } catch { $null } } |
                Where-Object { $_.type -eq 'thread.started' } | Select-Object -First 1
            if ($threadEvent) { $SessionId = $threadEvent.thread_id }
        } else {
            if ($SessionId) {
                $arguments = @('-p', '--resume', $SessionId, '--model', $ClaudeModel,
                    '--effort', $ClaudeEffort, '--permission-mode', 'acceptEdits', '--output-format', 'json',
                    '--max-turns', '80')
            } else {
                $arguments = @('-p', '--name', "avp-$safeTask-$($TaskKind.ToLowerInvariant())",
                    '--model', $ClaudeModel, '--effort', $ClaudeEffort,
                    '--permission-mode', 'acceptEdits',
                    '--output-format', 'json', '--max-turns', '80')
            }
            $Prompt | & $Provider.command @arguments 1> $stdoutPath 2> $stderrPath
            $exitCode = $LASTEXITCODE
            try {
                $claudeResult = Get-Content -LiteralPath $stdoutPath -Raw | ConvertFrom-Json
                if ($claudeResult.session_id) { $SessionId = $claudeResult.session_id }
                if ($claudeResult.result) {
                    $claudeResult.result | Set-Content -LiteralPath $lastPath -Encoding UTF8
                }
            } catch { }
        }
    } finally {
        $ErrorActionPreference = $savedPreference
        Pop-Location
    }
    return [ordered]@{
        exit_code = $exitCode
        session_id = $SessionId
        stdout = $stdoutPath
        stderr = $stderrPath
        last_message = $lastPath
    }
}

function Invoke-VerificationLane {
    param([string]$Lane, [string]$Worktree)
    $safeTask = $Task -replace '[^A-Za-z0-9._-]', '-'
    $log = Join-Path $runRoot "verify-$safeTask-$($Lane.ToLowerInvariant()).log"
    & powershell.exe -NoProfile -ExecutionPolicy Bypass -File $verifyScript `
        -Lane $Lane -ProjectRoot $Worktree *>&1 | Tee-Object -FilePath $log
    $exitCode = $LASTEXITCODE
    $summaryPath = Join-Path $Worktree ("build\verification\" +
        $Lane.ToLowerInvariant() + '.json')
    $status = if ($exitCode -eq 0) { 'PASS' } else { 'FAIL' }
    if (Test-Path -LiteralPath $summaryPath) {
        try {
            $summary = Get-Content -LiteralPath $summaryPath -Raw | ConvertFrom-Json
            $status = $summary.status
        } catch { }
    }
    return [ordered]@{
        lane = $Lane
        status = $status
        exit_code = $exitCode
        log = $log
        summary = $summaryPath
    }
}

if (-not (Test-Path -LiteralPath $cardPath)) { throw "Missing task card: $cardPath" }
$card = Get-Content -LiteralPath $cardPath -Raw
$policy = Read-Field -Text $card -Name 'EXECUTOR_POLICY' -Optional
if (-not $policy) { $policy = 'EITHER' }
if ($policy -notin @('CODEX', 'CLAUDE', 'EITHER')) {
    throw "Unsupported EXECUTOR_POLICY: $policy"
}
$correctionPaths = @(Read-InlineList -Text $card -Name 'CORRECTION_PATHS' -Optional)
$preferred = Read-Field -Text $card -Name 'PREFERRED_EXECUTOR' -Optional
if (-not $preferred) { $preferred = 'CODEX' }
if ($preferred -notin @('CODEX', 'CLAUDE')) { throw "Unsupported PREFERRED_EXECUTOR: $preferred" }
$claudeModel = Read-Field -Text $card -Name 'CLAUDE_MODEL' -Optional
if (-not $claudeModel) { $claudeModel = 'fable' }
$claudeEffort = Read-Field -Text $card -Name 'CLAUDE_EFFORT' -Optional
if (-not $claudeEffort) { $claudeEffort = 'medium' }
if ($Effort -ne 'Auto') { $claudeEffort = $Effort }
if ($claudeEffort -notin @('low', 'medium')) {
    throw "Unsupported CLAUDE_EFFORT: $claudeEffort"
}
if ($TaskKind -eq 'Auto') {
    $cardStatus = Read-Field -Text $card -Name 'STATUS'
    switch ($cardStatus) {
        'READY' { $TaskKind = 'Implementation' }
        'CORRECTIONS' { $TaskKind = 'Correction' }
        'EVIDENCE_REPAIR' { $TaskKind = 'EvidenceRepair' }
        default { throw "Task $Task status $cardStatus is not executable by this adapter." }
    }
}
$launchArguments = @('-NoProfile', '-ExecutionPolicy', 'Bypass', '-File',
    $launcher, '-Task', $Task, '-TaskKind', $TaskKind)
if ($TaskKind -eq 'Implementation') { $launchArguments += '-Prepare' }
$launchOutput = @(& powershell.exe @launchArguments)
if ($LASTEXITCODE -ne 0) { throw 'Task launch validation failed.' }
$metadataLine = $launchOutput | Where-Object { $_ -like 'Metadata: *' } |
    Select-Object -Last 1
if (-not $metadataLine) { throw 'Launcher did not return a metadata path.' }
$metadataPath = $metadataLine.Substring(10).Trim()
$metadata = Get-Content -LiteralPath $metadataPath -Raw | ConvertFrom-Json
$worktree = $metadata.worktree
if ($TaskKind -in @('Correction', 'EvidenceRepair')) {
    if ($correctionPaths.Count -eq 0) { throw "$TaskKind must declare CORRECTION_PATHS." }
    Assert-CorrectionScope -Paths (Get-TrackedStatusPaths -Root $worktree) `
        -Allowed $correctionPaths -Phase 'Initial worktree'
}

$provider = Resolve-Executor -Requested $Executor -Policy $policy `
    -Preferred $preferred -RequireCommand:(-not $PlanOnly)
$resolvedModel = if ($provider.name -eq 'Claude') { $claudeModel } else { $metadata.model }
$resolvedEffort = if ($provider.name -eq 'Claude') { $claudeEffort } else { $metadata.reasoning_effort }
$plan = [ordered]@{
    schema = 1
    task = $Task
    task_kind = $TaskKind
    executor = $provider.name
    executor_policy = $policy
    preferred_executor = $preferred
    claude_model = $claudeModel
    claude_effort = $claudeEffort
    model = $resolvedModel
    effort = $resolvedEffort
    base = $metadata.base
    branch = $metadata.branch
    worktree = $worktree
    candidate_head = $metadata.candidate_head
    required_lanes = @($metadata.required_lanes)
    correction_paths = @($correctionPaths)
    preexisting_changes = @($metadata.preexisting_changes)
    resume_session_id = $ResumeSessionId
    feedback_path = $FeedbackPath
    launch_metadata = $metadataPath
}
$planPath = Join-Path $runRoot "executor-$Task-plan.json"
$plan | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $planPath -Encoding UTF8
if ($PlanOnly) {
    Write-Output "PLAN: $planPath"
    $plan | ConvertTo-Json -Depth 8
    exit 0
}

$prompt = Get-Content -LiteralPath $metadata.launch_prompt -Raw
$prompt += @"

EXECUTION CONTRACT:
- Work only in the assigned worktree and bounded task paths.
- Preserve all fingerprinted preexisting changes.
- Do not edit project_state.yaml or choose/activate another task.
- Do not weaken or skip required lanes.
- Stage only authorized task paths and create one coherent commit.
- Finish with WORKFLOW_RESULT: IMPLEMENTATION_COMPLETE or a named hard stop.
"@
if ($FeedbackPath) {
    $feedback = (Resolve-Path -LiteralPath $FeedbackPath).Path
    $prompt += "`nEXTERNAL GOAL-MODE FEEDBACK:`n" +
        (Get-Content -LiteralPath $feedback -Raw)
}
$turn = Invoke-AgentTurn -Provider $provider -Prompt $prompt -Worktree $worktree `
    -Model $metadata.model -SessionId $ResumeSessionId -ClaudeModel $claudeModel `
    -ClaudeEffort $claudeEffort
$status = 'EXECUTOR_FAILED'
$head = (git -C $worktree rev-parse HEAD).Trim()
$dirty = @(Get-TrackedStatusPaths -Root $worktree)
$verification = @()
$bundlePath = $null
if ($turn.exit_code -eq 0 -and $turn.session_id) {
    if ($dirty.Count -ne 0) {
        if ($TaskKind -in @('Correction', 'EvidenceRepair')) {
            Assert-CorrectionScope -Paths $dirty -Allowed $correctionPaths `
                -Phase 'Post-executor worktree'
        }
        $status = 'WORKTREE_DIRTY'
    } elseif ($head -eq $metadata.candidate_head) {
        $status = 'NO_COMMIT'
    } else {
        if ($TaskKind -in @('Correction', 'EvidenceRepair')) {
            $changed = @(git -C $worktree diff --name-only `
                "$($metadata.candidate_head)..$head")
            Assert-CorrectionScope -Paths $changed -Allowed $correctionPaths `
                -Phase 'Committed correction'
        }
        foreach ($lane in @($metadata.required_lanes)) {
            $verification += Invoke-VerificationLane -Lane $lane -Worktree $worktree
        }
        if (@($verification | Where-Object status -ne 'PASS').Count -eq 0) {
            $base = Read-Field -Text $card -Name 'BASE'
            if ($base -eq 'project_state.accepted_head') {
                $state = Get-Content -LiteralPath (Join-Path $projectRoot 'project_state.yaml') -Raw
                $base = Read-Field -Text $state -Name 'accepted_head'
            } elseif ($base -eq 'repository.HEAD') { $base = $metadata.base }
            $bundleOutput = @(& powershell.exe -NoProfile -ExecutionPolicy Bypass `
                -File $bundleScript -Base $base -Task $Task `
                -CandidateRoot $worktree -TaskCard $Task)
            if ($LASTEXITCODE -ne 0) { throw 'Review bundle generation failed.' }
            $bundlePath = @($bundleOutput | Where-Object { $_ -and
                        (Test-Path -LiteralPath $_ -PathType Leaf) }) |
                Select-Object -Last 1
            if (-not $bundlePath) { throw 'Review bundle tool returned no path.' }
            $status = 'READY_FOR_REVIEW'
        } else { $status = 'VERIFICATION_FAILED' }
    }
}

$result = [ordered]@{
    schema = 1
    status = $status
    task = $Task
    task_kind = $TaskKind
    executor = $provider.name
    model = $resolvedModel
    effort = $resolvedEffort
    session_id = $turn.session_id
    executor_exit_code = $turn.exit_code
    base = $metadata.base
    branch = $metadata.branch
    worktree = $worktree
    prior_candidate_head = $metadata.candidate_head
    candidate_head = $head
    dirty_paths = @($dirty)
    verification = @($verification)
    review_bundle = $bundlePath
    stdout = $turn.stdout
    stderr = $turn.stderr
    last_message = $turn.last_message
}
$resultPath = Join-Path $runRoot "executor-$Task-result.json"
$result | ConvertTo-Json -Depth 10 | Set-Content -LiteralPath $resultPath -Encoding UTF8
Write-Output "RESULT: $resultPath"
$result | ConvertTo-Json -Depth 10
