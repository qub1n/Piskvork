param([Parameter(Mandatory=$true)][string]$Executable)
$ErrorActionPreference = 'Stop'
$exe = (Resolve-Path -LiteralPath $Executable).Path
$temp = Join-Path $env:RUNNER_TEMP ('piskvork-cli-' + [guid]::NewGuid())
New-Item -ItemType Directory -Path $temp | Out-Null
$key = 'HKCU:\Software\Petr Lastovicka\piskvorky'
# The hosted test account starts with conflicting settings to prove isolation.
$existed = Test-Path -LiteralPath $key
if ($existed) { throw 'Smoke test requires a clean hosted account registry' }
try {
    New-Item -Path $key -Force | Out-Null
    foreach ($name in @('sirka','height','continuous','soundNotification','openingRandomShift1')) {
        New-ItemProperty -Path $key -Name $name -Value 37 -PropertyType DWord | Out-Null
    }
    New-ItemProperty -Path $key -Name cmdGame -Value 'do-not-execute' -PropertyType String | Out-Null
    $before = (Get-ItemProperty -LiteralPath $key | Select-Object sirka,height,continuous,soundNotification,openingRandomShift1,cmdGame | ConvertTo-Json -Compress)
    foreach ($size in @(15,20)) {
        $json = Join-Path $temp "settings-$size.json"
        $process = Start-Process -FilePath $exe -ArgumentList @('-benchmark','-size',"$size",'-rule','1','-timeturn','5000','-timematch','120','-print-settings',"`"$json`"") -WindowStyle Hidden -PassThru
        if (!$process.WaitForExit(10000)) { $process.Kill(); throw 'CLI diagnostic timed out' }
        if ($process.ExitCode -ne 0) { throw "CLI diagnostic failed: $($process.ExitCode)" }
        $s = Get-Content -LiteralPath $json -Raw | ConvertFrom-Json
        if ($s.width -ne $size -or $s.height -ne $size -or $s.rule -ne 1 -or $s.time_move_ms -ne 5000 -or $s.time_match_seconds -ne 120 -or !$s.no_registry -or !$s.completion_commands_empty) { throw 'Wrong effective CLI settings' }
        if ($s.auto_begin -ne 1 -or $s.timeout -ne 1 -or $s.suspend_ai -ne 1 -or $s.random_shift -ne 0 -or $s.tolerance -ne 1000 -or $s.continuous -ne 0 -or $s.debug_ai -ne 0 -or $s.sound -ne 0 -or $s.invert -ne 0) { throw 'Wrong benchmark profile' }
    }
    $after = (Get-ItemProperty -LiteralPath $key | Select-Object sirka,height,continuous,soundNotification,openingRandomShift1,cmdGame | ConvertTo-Json -Compress)
    if ($before -ne $after) { throw 'CLI modified the registry' }
    Write-Output 'CLI settings and registry isolation verified without engine matches'
} finally {
    Remove-Item -LiteralPath $key -Recurse
}
