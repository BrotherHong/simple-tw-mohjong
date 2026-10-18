$ErrorActionPreference = "Stop"

$env:PYTHONUTF8 = "1"
$env:PYTHONHASHSEED = "0"
$env:PYNGUIN_DANGER_AWARE = "1"

$projectRoot = $PSScriptRoot
$python = Join-Path $projectRoot ".venv\Scripts\python.exe"
$runDir = "tests/run_$(Get-Date -Format 'yyyyMMdd_HHmmss_fff')"
$timer = [Diagnostics.Stopwatch]::StartNew()
$process = $null

$modules = Get-ChildItem "$projectRoot/src/tw_mahjong" -Filter "*.py" -File |
    Where-Object { $_.Name -notin @("__init__.py", "__main__.py") } |
    Sort-Object Name

try {
    foreach ($file in $modules) {
        # Reserve the last 30 seconds for cleanup.
        if ($timer.Elapsed.TotalSeconds -ge 1770) {
            Write-Warning "Batch time limit reached."
            break
        }

        $name = $file.BaseName
        $report = "$runDir/reports/$name"
        $reportPath = Join-Path $projectRoot $report
        New-Item -ItemType Directory -Force $reportPath | Out-Null

        $arguments = @(
            "-B", "-m", "pynguin",
            "--project-path", "src",
            "--module-name", "tw_mahjong.$name",
            "--output-path", $runDir,
            "--report-dir", $report,
            "--maximum-search-time", "90",
            "--maximum-mutation-time", "20",
            "--maximum-mutants", "50",
            "--maximum-slicing-time", "5",
            "--maximum-test-execution-timeout", "5",
            "--maximum-module-execution-timeout", "5",
            "--subprocess", "True",
            "--seed", "17",
            "-v"
        )

        Write-Host "Starting $name"
        $moduleStart = $timer.Elapsed.TotalSeconds

        $process = Start-Process -FilePath $python `
            -ArgumentList $arguments `
            -WorkingDirectory $projectRoot `
            -WindowStyle Hidden -PassThru `
            -RedirectStandardOutput "$reportPath/stdout.log" `
            -RedirectStandardError "$reportPath/stderr.log"

        # Limit both this module and the remaining batch time.
        $elapsed = $timer.Elapsed.TotalSeconds
        $seconds = [Math]::Max(0, [Math]::Min(
            150 - ($elapsed - $moduleStart),
            1770 - $elapsed
        ))

        if (-not $process.WaitForExit([int]($seconds * 1000))) {
            Write-Warning "$name timed out; stopping its process tree."
            & taskkill.exe /PID $process.Id /T /F | Out-Null

            if (-not $process.WaitForExit(5000)) {
                throw "Process cleanup failed; stopping the batch."
            }
        }
        else {
            Write-Host "$name finished; exit code: $($process.ExitCode)"
        }

        $process = $null
    }
}
finally {
    # Clean up the active generator if the script is interrupted.
    if ($null -ne $process -and -not $process.HasExited) {
        & taskkill.exe /PID $process.Id /T /F | Out-Null
    }

    Write-Host "Elapsed: $([Math]::Round($timer.Elapsed.TotalMinutes, 2)) minutes"
    Write-Host "Results: $(Join-Path $projectRoot $runDir)"
}