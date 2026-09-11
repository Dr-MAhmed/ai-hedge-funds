$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path
$batPath = Join-Path $scriptPath "run_server.bat"

Start-Process -FilePath "cmd.exe" `
    -ArgumentList "/c `"$batPath`"" `
    -WindowStyle Hidden `
    -WorkingDirectory $scriptPath

Write-Host "[SYSTEM] AI Hedge Fund started in background"
Start-Sleep -Seconds 2
Write-Host "[SYSTEM] Dashboard: http://localhost:8000"
