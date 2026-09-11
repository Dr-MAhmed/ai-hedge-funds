$procs = Get-Process | Where-Object {
    $_.ProcessName -eq "python" -and
    $_.CommandLine -like "*main.py*"
} 2>$null

if (-not $procs) {
    $procs = Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue |
        Select-Object OwningProcess -Unique |
        ForEach-Object { Get-Process -Id $_.OwningProcess }
}

if ($procs) {
    foreach ($p in $procs) {
        Write-Host "[SYSTEM] Stopping process $($p.Id) ($($p.ProcessName))..."
        Stop-Process -Id $p.Id -Force -ErrorAction SilentlyContinue
    }
    Write-Host "[SYSTEM] All AI Hedge Fund processes stopped"
} else {
    Write-Host "[SYSTEM] No running AI Hedge Fund processes found"
}
