[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [ValidateSet('Fast', 'Oracle', 'Target', 'Full')]
    [string]$Lane,

    [string]$PythonPath,

    [string[]]$Test = @(),
    [string[]]$Command = @(),

    [ValidateSet('Default', 'Release', 'VisualTest', 'FrontendTest',
        'FrontendShotTest', 'EncounterTest', 'StreetTest', 'BossHitTest',
        'BossKoTest', 'PlayerSalvageBench', 'PlayerPromotionBench',
        'CameraStageSalvageBench', 'CameraStagePromotionBench',
        'HudPcmSalvageBench', 'HudPromotionBench', 'PcmPromotionBench',
        'CddaResidencySalvageBench', 'CddaResidencyPromotionBench',
        'EnemySalvageBench',
        'EnemyPromotionBench', 'PlayerEnemyIntegration',
        'CollisionSalvageBench', 'HitKoPromotionBench',
        'CombatIntegrationBench', 'PlayableSlice', 'Probe3')]
    [string]$TargetProfile = 'Default',

    [switch]$Regenerate,
    [switch]$BuildOnly,
    [switch]$Emulator,
    [string]$EmulatorPath,
    [string[]]$EmulatorCheck = @(),
    [string]$ProjectRoot
)

$ErrorActionPreference = 'Stop'
if ($ProjectRoot) {
    $projectRoot = (Resolve-Path -LiteralPath $ProjectRoot).Path
}
else {
    $projectRoot = $PSScriptRoot
}
$results = New-Object System.Collections.ArrayList
$laneStarted = Get-Date
$laneStatus = 'PASS'
$laneIncomplete = $false
$failure = $null
$trackedStatusBefore = @(git -C $projectRoot status --porcelain `
    --untracked-files=no)

function Resolve-Python {
    if ($script:PythonPath -and (Test-Path -LiteralPath $script:PythonPath)) {
        return (Resolve-Path -LiteralPath $script:PythonPath).Path
    }

    foreach ($name in @('py.exe', 'python.exe')) {
        $candidate = Get-Command $name -ErrorAction SilentlyContinue
        if ($candidate -and $candidate.Source -notlike '*WindowsApps*') {
            return $candidate.Source
        }
    }

    $bundled = Join-Path $env:LOCALAPPDATA `
        'codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
    if (Test-Path -LiteralPath $bundled) {
        return $bundled
    }

    throw 'Python 3 is required. Pass -PythonPath explicitly.'
}

function Add-Result {
    param(
        [string]$Name,
        [string]$Status,
        [int]$ExitCode,
        [string]$Command
    )
    [void]$script:results.Add([ordered]@{
        name = $Name
        status = $Status
        exit_code = $ExitCode
        command = $Command
    })
    if ($Status -eq 'SKIP' -or $Status -eq 'UNRUN') {
        $script:laneIncomplete = $true
    }
}

function Invoke-ExternalCheck {
    param(
        [string]$Name,
        [string]$Executable,
        [string[]]$Arguments
    )

    $display = $Executable + ' ' + ($Arguments -join ' ')
    Write-Host "[$Lane] $Name"
    & $Executable @Arguments
    $exitCode = $LASTEXITCODE
    if ($null -eq $exitCode) {
        $exitCode = 0
    }
    if ($exitCode -ne 0) {
        Add-Result -Name $Name -Status 'FAIL' -ExitCode $exitCode -Command $display
        throw "$Name failed with exit code $exitCode."
    }
    Add-Result -Name $Name -Status 'PASS' -ExitCode 0 -Command $display
}

function Invoke-PowerShellCheck {
    param(
        [string]$Name,
        [string]$ScriptPath,
        [string[]]$Arguments
    )

    $windowsPowerShell = Join-Path $env:SystemRoot `
        'System32\WindowsPowerShell\v1.0\powershell.exe'
    if (Test-Path -LiteralPath $windowsPowerShell) {
        $hostPath = $windowsPowerShell
    }
    else {
        $hostPath = (Get-Process -Id $PID).Path
    }
    if (-not $hostPath -or -not (Test-Path -LiteralPath $hostPath)) {
        throw 'Could not resolve the current PowerShell host.'
    }
    $hostArguments = @('-NoProfile', '-ExecutionPolicy', 'Bypass', '-File',
        $ScriptPath) + $Arguments
    Invoke-ExternalCheck -Name $Name -Executable $hostPath `
        -Arguments $hostArguments
}

function Invoke-PythonTest {
    param([string]$RelativePath)
    $path = Join-Path $projectRoot $RelativePath
    if (-not (Test-Path -LiteralPath $path)) {
        throw "Focused test does not exist: $RelativePath"
    }
    Invoke-ExternalCheck -Name $RelativePath -Executable $script:resolvedPython `
        -Arguments @('-B', $path)
}

function Invoke-FastLane {
    if (Test-Path -LiteralPath (Join-Path $projectRoot `
            'tests\test_workflow_policy.py')) {
        Invoke-PythonTest 'tests\test_workflow_policy.py'
    }
    Invoke-PythonTest 'tests\test_task_card_state.py'
    Invoke-PythonTest 'tests\test_port_v2_migration_map.py'
    Invoke-PythonTest 'tests\test_avsp_hit_ko_writer_set.py'
    Invoke-PythonTest 'tests\port_v2\combat\hit_ko\test_contract.py'
    Invoke-PythonTest 'tests\port_v2\integration\combat\test_contract.py'
    Invoke-PythonTest 'tests\port_v2\integration\slice\test_contract.py'
    Invoke-PythonTest 'tests\port_v2\camera_stage\test_contract.py'
    Invoke-PythonTest 'tests\port_v2\cdda_residency_bench\test_contract.py'
    Invoke-PythonTest 'tests\port_v2\cdda_residency\test_contract.py'
    Invoke-PythonTest 'tests\test_avsp_vertical_slice_oracle.py'
    Invoke-PythonTest 'tests\test_oracle04_predator_controls.py'
    Invoke-PythonTest 'tests\test_oracle05_street_alien_ai.py'
    Invoke-PythonTest 'tests\test_oracle06_round1_encounter.py'
    Invoke-PythonTest 'tests\test_avsp_translation_boundary.py'
    Invoke-PythonTest 'tests\hardware\probe3\test_probe3.py'

    $portV2Root = Join-Path $projectRoot 'tests\port_v2'
    if (Test-Path -LiteralPath $portV2Root) {
        Get-ChildItem -LiteralPath $portV2Root -Filter 'test_*.py' -File |
            Sort-Object Name | ForEach-Object {
                Invoke-ExternalCheck -Name ("tests\port_v2\" + $_.Name) `
                    -Executable $script:resolvedPython -Arguments @('-B', $_.FullName)
            }
    }

    foreach ($relative in $Test) {
        Invoke-PythonTest $relative
    }

    $hostPath = (Get-Process -Id $PID).Path
    foreach ($commandText in $Command) {
        if ([string]::IsNullOrWhiteSpace($commandText)) {
            throw 'Focused -Command entries cannot be empty.'
        }
        Invoke-ExternalCheck -Name 'focused portable command' `
            -Executable $hostPath -Arguments @('-NoProfile', '-ExecutionPolicy',
                'Bypass', '-Command', $commandText)
    }
}

function Invoke-OracleLane {
    $mapper = Join-Path $projectRoot 'tools\map_avsp_hit_ko_writer_set.py'
    $privateWriterInputs = @(
        '.deps\mame\vertical_slice\cold_run_1\maincpu.trace',
        '.deps\mame\vertical_slice\cold_run_1\semantic_ledger.jsonl',
        '.deps\mame\vertical_slice\hit_ko_writer_context_watchpoint_5\error.log',
        '.deps\mame\vertical_slice\hit_ko_writer_context_watchpoint_5\target_actor_samples.tsv',
        '.deps\mame\actorprobe\decrypted_opcodes_2m.bin',
        '.deps\mame\actorprobe\decrypted_program_2m.bin'
    )
    $missingWriterInputs = @($privateWriterInputs | Where-Object {
            -not (Test-Path -LiteralPath (Join-Path $projectRoot $_))
        })
    if ($missingWriterInputs.Count -eq 0) {
        Invoke-ExternalCheck -Name 'writer map self-test' `
            -Executable $script:resolvedPython `
            -Arguments @('-B', $mapper, '--self-test')
        Invoke-ExternalCheck -Name 'writer map scratch mutations' `
            -Executable $script:resolvedPython `
            -Arguments @('-B', $mapper, '--scratch-mutation-test')
    }
    else {
        Add-Result -Name 'writer map self-test' -Status 'SKIP' -ExitCode 0 `
            -Command 'ignored private writer inputs absent'
        Add-Result -Name 'writer map scratch mutations' -Status 'SKIP' -ExitCode 0 `
            -Command 'ignored private writer inputs absent'
    }
    Invoke-PythonTest 'tests\test_avsp_hit_ko_writer_set.py'
    Invoke-PythonTest 'tests\port_v2\combat\hit_ko\test_contract.py'
    Invoke-PythonTest 'tests\port_v2\integration\combat\test_contract.py'
    Invoke-PythonTest 'tests\port_v2\integration\slice\test_contract.py'
    Invoke-PythonTest 'tests\test_avsp_vertical_slice_oracle.py'
    Invoke-PythonTest 'tests\test_oracle04_predator_controls.py'
    Invoke-PythonTest 'tests\test_oracle05_street_alien_ai.py'
    Invoke-PythonTest 'tests\test_oracle06_round1_encounter.py'
    Invoke-PythonTest 'tests\test_avsp_translation_boundary.py'

    $mame = Join-Path $projectRoot '.deps\mame\mame0289\mame.exe'
    $romRoot = Join-Path $projectRoot 'avspu'
    if ((Test-Path -LiteralPath $mame) -and (Test-Path -LiteralPath $romRoot)) {
        Invoke-ExternalCheck -Name 'MAME avspu identity' -Executable $mame `
            -Arguments @('-rompath', $projectRoot, '-verifyroms', 'avspu')
    }
    else {
        Add-Result -Name 'MAME avspu identity' -Status 'SKIP' -ExitCode 0 `
            -Command 'pinned private MAME executable or avspu input absent'
    }

    if ($Regenerate) {
        $privateManifest = Join-Path $projectRoot `
            '.deps\mame\vertical_slice\input_manifest.json'
        if (-not (Test-Path -LiteralPath $privateManifest)) {
            throw '-Regenerate requires the pinned private vertical-slice inputs.'
        }
        Invoke-ExternalCheck -Name 'regenerate vertical-slice oracle' `
            -Executable $script:resolvedPython -Arguments @(
                '-B', (Join-Path $projectRoot `
                    'tools\verify_avsp_vertical_slice_oracle.py'), '--generate')
        Invoke-ExternalCheck -Name 'regenerate translation boundary' `
            -Executable $script:resolvedPython -Arguments @(
                '-B', (Join-Path $projectRoot `
                    'tools\map_avsp_translation_boundary.py'), '--generate')
        Invoke-ExternalCheck -Name 'regenerate HIT/KO writer set' `
            -Executable $script:resolvedPython `
            -Arguments @('-B', $mapper, '--generate')
    }
}

function Invoke-TargetLane {
    if ($BuildOnly -and $Emulator) {
        throw 'Choose either explicit -BuildOnly or -Emulator evidence.'
    }
    if (-not $BuildOnly -and -not $Emulator) {
        throw 'Target requires explicit -BuildOnly or -Emulator with readback checks.'
    }

    $arguments = @('-Clean', '-SkipHostTests')
    if ($TargetProfile -ne 'Default') {
        $arguments += ('-' + $TargetProfile)
    }
    Invoke-PowerShellCheck -Name "Saturn build ($TargetProfile)" `
        -ScriptPath (Join-Path $projectRoot 'build.ps1') -Arguments $arguments

    $profileNames = @{
        Default = 'debug-normal-release'
        Release = 'release-normal-release'
        VisualTest = 'debug-visual-test'
        FrontendTest = 'debug-frontend-test'
        FrontendShotTest = 'debug-frontend-shot-test'
        EncounterTest = 'debug-encounter-test'
        StreetTest = 'debug-street-test'
        BossHitTest = 'debug-boss-hit-test'
        BossKoTest = 'debug-boss-ko-test'
        PlayerSalvageBench = 'debug-player-salvage-bench'
        PlayerPromotionBench = 'debug-player-promotion-bench'
        CameraStageSalvageBench = 'debug-camera-stage-salvage-bench'
        CameraStagePromotionBench = 'debug-camera-stage-promotion-bench'
        HudPcmSalvageBench = 'debug-hud-pcm-salvage-bench'
        HudPromotionBench = 'debug-hud-promotion-bench'
        PcmPromotionBench = 'debug-pcm-promotion-bench'
        CddaResidencySalvageBench = 'debug-cdda-residency-salvage-bench'
        CddaResidencyPromotionBench = 'debug-cdda-residency-promotion-bench'
        EnemySalvageBench = 'debug-enemy-salvage-bench'
        EnemyPromotionBench = 'debug-enemy-promotion-bench'
        PlayerEnemyIntegration = 'debug-player-enemy-integration'
        CollisionSalvageBench = 'debug-collision-salvage-bench'
        HitKoPromotionBench = 'debug-hit-ko-promotion-bench'
        CombatIntegrationBench = 'debug-combat-integration-bench'
        PlayableSlice = 'debug-playable-slice'
        Probe3 = 'debug-probe3'
    }
    $expectedProfile = $profileNames[$TargetProfile]
    $profilePath = Join-Path $projectRoot 'build\last_compile_profile.txt'
    $actualProfile = (Get-Content -LiteralPath $profilePath -Raw).Trim()
    if ($actualProfile -ne $expectedProfile) {
        throw "Target profile is $actualProfile, expected $expectedProfile."
    }

    foreach ($relative in @('build\last_compile_profile.txt',
            'build\hardware_release_manifest.txt', 'game.iso', 'game.cue')) {
        $path = Join-Path $projectRoot $relative
        if (-not (Test-Path -LiteralPath $path)) {
            throw "Required Target artifact is missing: $relative"
        }
        $hash = (Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash.ToLowerInvariant()
        Add-Result -Name $relative -Status 'RECORDED' -ExitCode 0 `
            -Command "sha256=$hash"
    }

    if ($Emulator) {
        if ($TargetProfile -ne 'Release') {
            throw 'Emulator acceptance requires TargetProfile Release.'
        }
        if ($EmulatorCheck.Count -eq 0) {
            throw '-Emulator requires at least one profile-specific readback collector/check.'
        }
        $readbackReport = Join-Path $projectRoot `
            'build\target\release_readback.json'
        $arguments = @()
        if ($EmulatorPath) {
            $arguments += @('-EmulatorPath', $EmulatorPath)
        }
        Invoke-PowerShellCheck -Name 'launch pinned Saturn image' `
            -ScriptPath (Join-Path $projectRoot 'run.ps1') -Arguments $arguments
        foreach ($relative in $EmulatorCheck) {
            if ([IO.Path]::IsPathRooted($relative)) {
                throw "Emulator checks must be repository-relative: $relative"
            }
            $checkPath = [IO.Path]::GetFullPath((Join-Path $projectRoot $relative))
            $rootPrefix = $projectRoot.TrimEnd('\') + '\'
            if (-not $checkPath.StartsWith($rootPrefix,
                    [StringComparison]::OrdinalIgnoreCase)) {
                throw "Emulator check escapes the repository: $relative"
            }
            if (-not (Test-Path -LiteralPath $checkPath)) {
                throw "Emulator readback check does not exist: $relative"
            }
            git -C $projectRoot ls-files --error-unmatch -- $relative 2>$null |
                Out-Null
            if ($LASTEXITCODE -ne 0) {
                throw "Emulator readback check is not committed: $relative"
            }
            if ([IO.Path]::GetExtension($checkPath) -eq '.py') {
                Invoke-ExternalCheck -Name "emulator readback: $relative" `
                    -Executable $script:resolvedPython -Arguments @('-B', $checkPath)
            }
            elseif ([IO.Path]::GetExtension($checkPath) -eq '.ps1') {
                Invoke-PowerShellCheck -Name "emulator readback: $relative" `
                    -ScriptPath $checkPath -Arguments @()
            }
            else {
                throw "Emulator checks must be .py or .ps1: $relative"
            }
        }
        if (-not (Test-Path -LiteralPath $readbackReport)) {
            throw 'Readback collector did not create build\target\release_readback.json.'
        }
        if ((Get-Item -LiteralPath $readbackReport).LastWriteTimeUtc -lt
            $laneStarted.ToUniversalTime()) {
            throw 'Release readback report was not refreshed during this Target run.'
        }
        $readbackHash = (Get-FileHash -LiteralPath $readbackReport `
            -Algorithm SHA256).Hash.ToLowerInvariant()
        Add-Result -Name 'build\target\release_readback.json' `
            -Status 'RECORDED' -ExitCode 0 -Command "sha256=$readbackHash"
        Invoke-ExternalCheck -Name 'canonical release readback verification' `
            -Executable $script:resolvedPython -Arguments @('-B',
                (Join-Path $projectRoot `
                    'tests\target\verify_release_readback.py'))
        Add-Result -Name 'emulator evidence scope' -Status 'PASS' -ExitCode 0 `
            -Command 'profile-specific checks executed; physical evidence remains separate'
    }
    else {
        $script:laneStatus = 'BUILD_ONLY'
        Add-Result -Name 'target evidence scope' -Status 'RECORDED' -ExitCode 0 `
            -Command 'BUILD_ONLY; insufficient for Saturn-facing acceptance'
    }
}

function Invoke-FullLane {
    $temporaryRoot = Join-Path ([IO.Path]::GetTempPath()) `
        ('avp-full-' + [Guid]::NewGuid().ToString('N'))
    $shadowRoot = Join-Path $temporaryRoot 'worktree'
    $linkedInputs = New-Object System.Collections.ArrayList
    $testFailure = $null
    $diffReport = $null

    New-Item -ItemType Directory -Path $temporaryRoot -Force | Out-Null
    try {
        Write-Host "[$Lane] create detached shadow worktree"
        # Equivalent command: git worktree add --detach <shadow> HEAD
        git -C $projectRoot worktree add --detach $shadowRoot HEAD
        if ($LASTEXITCODE -ne 0) {
            throw 'Could not create the Full-lane shadow worktree.'
        }

        foreach ($relative in @('.deps', 'avspu')) {
            $source = Join-Path $projectRoot $relative
            $destination = Join-Path $shadowRoot $relative
            if ((Test-Path -LiteralPath $source) -and
                -not (Test-Path -LiteralPath $destination)) {
                New-Item -ItemType Junction -Path $destination -Target $source |
                    Out-Null
                [void]$linkedInputs.Add($destination)
            }
        }
        $ignoredGenerated = @(git -C $projectRoot ls-files --others --ignored `
            --exclude-standard -- 'generated')
        foreach ($relative in $ignoredGenerated) {
            $source = Join-Path $projectRoot $relative
            if (-not (Test-Path -LiteralPath $source -PathType Leaf)) {
                continue
            }
            $destination = Join-Path $shadowRoot $relative
            New-Item -ItemType Directory -Path (Split-Path -Parent $destination) `
                -Force | Out-Null
            Copy-Item -LiteralPath $source -Destination $destination -Force
        }

        try {
            Invoke-PowerShellCheck -Name 'complete legacy/generator regression' `
                -ScriptPath (Join-Path $shadowRoot 'test.ps1') `
                -Arguments @('-PythonPath', $script:resolvedPython)
        }
        catch {
            $testFailure = $_.Exception.Message
        }

        $changes = @(git -C $shadowRoot diff --name-status --)
        $entries = New-Object System.Collections.ArrayList
        foreach ($change in $changes) {
            $parts = $change -split "`t", 2
            $relative = $parts[-1]
            $committedPath = Join-Path $projectRoot $relative
            $generatedPath = Join-Path $shadowRoot $relative
            $committedHash = $null
            $generatedHash = $null
            if (Test-Path -LiteralPath $committedPath -PathType Leaf) {
                $committedHash = (Get-FileHash -LiteralPath $committedPath `
                    -Algorithm SHA256).Hash.ToLowerInvariant()
            }
            if (Test-Path -LiteralPath $generatedPath -PathType Leaf) {
                $generatedHash = (Get-FileHash -LiteralPath $generatedPath `
                    -Algorithm SHA256).Hash.ToLowerInvariant()
            }
            [void]$entries.Add([ordered]@{
                status = $parts[0]
                path = $relative.Replace('\', '/')
                committed_sha256 = $committedHash
                generated_sha256 = $generatedHash
            })
        }
        $patchText = (@(git -C $shadowRoot diff --full-index --binary `
            --no-ext-diff --) -join "`n") + "`n"
        $sha = [Security.Cryptography.SHA256]::Create()
        try {
            $patchBytes = [Text.Encoding]::UTF8.GetBytes($patchText)
            $patchHash = [BitConverter]::ToString(
                $sha.ComputeHash($patchBytes)).Replace('-', '').ToLowerInvariant()
        }
        finally {
            $sha.Dispose()
        }

        $reportRoot = Join-Path $projectRoot 'build\verification'
        New-Item -ItemType Directory -Path $reportRoot -Force | Out-Null
        $diffReport = Join-Path $reportRoot 'full-shadow-diff.json'
        [ordered]@{
            schema = 1
            candidate_head = (git -C $projectRoot rev-parse HEAD).Trim()
            candidate_tree = (git -C $projectRoot rev-parse 'HEAD^{tree}').Trim()
            changed_tracked_count = $changes.Count
            patch_sha256 = $patchHash
            entries = @($entries)
        } | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath $diffReport `
            -Encoding UTF8

        if ($changes.Count -ne 0) {
            Add-Result -Name 'Full generated-artifact byte comparison' `
                -Status 'FAIL' -ExitCode 1 `
                -Command "tracked drift recorded in $diffReport"
            throw "Full changed $($changes.Count) tracked artifact(s) in the shadow worktree."
        }
        Add-Result -Name 'Full generated-artifact byte comparison' `
            -Status 'PASS' -ExitCode 0 `
            -Command "no tracked drift; report=$diffReport"
        if ($testFailure) {
            throw $testFailure
        }
    }
    finally {
        foreach ($link in @($linkedInputs)) {
            if (Test-Path -LiteralPath $link) {
                # Windows PowerShell 5 can throw a null-reference while
                # Remove-Item handles a junction. Directory.Delete removes
                # only the junction entry and never traverses its target.
                [IO.Directory]::Delete($link)
            }
        }
        if (Test-Path -LiteralPath $shadowRoot) {
            $resolvedShadow = [IO.Path]::GetFullPath($shadowRoot)
            $temporaryPrefix = [IO.Path]::GetFullPath($temporaryRoot).TrimEnd('\') + '\'
            if (-not $resolvedShadow.StartsWith($temporaryPrefix,
                    [StringComparison]::OrdinalIgnoreCase)) {
                throw 'Refusing to remove a shadow path outside the lane temporary root.'
            }
            git -C $projectRoot worktree remove --force $resolvedShadow
        }
        if (Test-Path -LiteralPath $temporaryRoot) {
            $resolvedTemporary = [IO.Path]::GetFullPath($temporaryRoot)
            $systemTemporary = [IO.Path]::GetFullPath(
                [IO.Path]::GetTempPath()).TrimEnd('\') + '\'
            if (-not $resolvedTemporary.StartsWith($systemTemporary,
                    [StringComparison]::OrdinalIgnoreCase)) {
                throw 'Refusing to remove a Full-lane path outside the system temp root.'
            }
            Remove-Item -LiteralPath $resolvedTemporary -Recurse -Force
        }
    }
}

try {
    $resolvedPython = Resolve-Python
    switch ($Lane) {
        'Fast' { Invoke-FastLane }
        'Oracle' { Invoke-OracleLane }
        'Target' { Invoke-TargetLane }
        'Full' { Invoke-FullLane }
    }
    if ($laneIncomplete) {
        $laneStatus = 'INCOMPLETE'
        $failure = 'Required verification evidence was skipped or unrun.'
    }
}
catch {
    $laneStatus = 'FAIL'
    $failure = $_.Exception.Message
}
finally {
    $statusLines = @(git -C $projectRoot status --short)
    $trackedStatusAfter = @(git -C $projectRoot status --porcelain `
        --untracked-files=no)
    $summary = [ordered]@{
        schema = 2
        lane = $Lane
        status = $laneStatus
        started_utc = $laneStarted.ToUniversalTime().ToString('o')
        finished_utc = (Get-Date).ToUniversalTime().ToString('o')
        git_head = (git -C $projectRoot rev-parse HEAD).Trim()
        git_tree = (git -C $projectRoot rev-parse 'HEAD^{tree}').Trim()
        dirty_entry_count = $statusLines.Count
        tracked_dirty_before_count = $trackedStatusBefore.Count
        tracked_dirty_entry_count = $trackedStatusAfter.Count
        regenerate = [bool]$Regenerate
        target_profile = $TargetProfile
        build_only = [bool]$BuildOnly
        emulator = [bool]$Emulator
        emulator_checks = @($EmulatorCheck)
        focused_tests = @($Test)
        focused_commands = @($Command)
        checks = @($results)
        failure = $failure
    }
    $outputRoot = Join-Path $projectRoot 'build\verification'
    New-Item -ItemType Directory -Path $outputRoot -Force | Out-Null
    $outputPath = Join-Path $outputRoot ($Lane.ToLowerInvariant() + '.json')
    $summary | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $outputPath `
        -Encoding UTF8
    Write-Host "Verification summary: $outputPath"
}

if ($laneStatus -notin @('PASS', 'BUILD_ONLY')) {
    throw $failure
}
