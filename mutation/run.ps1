#Requires -Version 5.1
param(
    [Parameter(Mandatory)][ValidateSet('first', 'second', 'third')][string] $Run,
    [string] $Mutants = 'mutation/sampled-mutants.sqlite',
    [switch] $Resume
)

$ErrorActionPreference = 'Stop'
$PSNativeCommandUseErrorActionPreference = $false
if ($Resume -and $PSBoundParameters.ContainsKey('Mutants')) { throw '-Resume cannot be combined with -Mutants.' }
$Run = $Run.ToLowerInvariant()
$timer = [Diagnostics.Stopwatch]::StartNew()
Push-Location (Split-Path -Parent $PSScriptRoot)
try {
    # Use the activated virtual environment and deterministic UTF-8 output.
    $env:PYTHONUTF8 = '1'
    $env:PYTHONHASHSEED = '0'
    $config = "mutation/$Run.toml"
    $report = "tests/$Run/reports/mutation"
    $session = "$report/session.sqlite"
    if (-not (Test-Path -LiteralPath $config -PathType Leaf)) { throw "Missing configuration: $config" }
    if ($Resume) {
        if (-not (Test-Path -LiteralPath $session -PathType Leaf)) { throw 'No session exists to resume.' }
    } else {
        if (Test-Path -LiteralPath $session) { throw 'Session already exists. Use -Resume.' }
        if (-not (Test-Path -LiteralPath $Mutants -PathType Leaf)) { throw "Missing mutant template: $Mutants" }
    }

    # Verify the original tests before copying or resuming a session.
    cosmic-ray --verbosity INFO baseline $config
    if ($LASTEXITCODE -ne 0) { throw "Baseline failed (exit $LASTEXITCODE)." }
    New-Item -ItemType Directory -Force $report | Out-Null
    if (-not $Resume) { Copy-Item -LiteralPath $Mutants -Destination $session }
    cosmic-ray --verbosity INFO exec $config $session
    if ($LASTEXITCODE -ne 0) { throw "Mutation execution failed (exit $LASTEXITCODE). Use -Resume to continue." }

    # Export reports without opening the browser.
    cr-report $session --show-pending | Set-Content -Encoding utf8 "$report/report.txt"
    if ($LASTEXITCODE -ne 0) { throw 'Text report export failed.' }
    cosmic-ray dump $session | Set-Content -Encoding utf8 "$report/results.jsonl"
    if ($LASTEXITCODE -ne 0) { throw 'JSONL export failed.' }
    cr-html $session | Set-Content -Encoding utf8 "$report/report.html"
    if ($LASTEXITCODE -ne 0) { throw 'HTML export failed.' }
    Write-Host "Reports: $report"
}
finally {
    $timer.Stop()
    Write-Host "Elapsed: $([Math]::Round($timer.Elapsed.TotalSeconds, 2)) seconds."
    Pop-Location
}
