# 🚀 TruthGPT System Service Manager
# This script ensures TruthGPT runs as a persistent background system.

$SystemRoot = "C:\blatam-academy\agents\backend\onyx\server\features\Frontier-Model-run-polyglot\scripts\TruthGPT-main\optimization_core"
$ApiScript = "$SystemRoot\optimization_core\system_core_api.py"

function Start-TruthGPT-System {
    Write-Host "➤ Starting TruthGPT System Core Daemon..." -ForegroundColor Cyan
    Start-Job -Name "TruthGPT_Core" -ScriptBlock {
        param($path)
        cd (Split-Path $path)
        python $path
    } -ArgumentList $ApiScript
    
    Start-Sleep -Seconds 2
    $job = Get-Job -Name "TruthGPT_Core"
    if ($job.State -eq "Running") {
        Write-Host "✓ TruthGPT System Core is now running in the background (Port 8080)." -ForegroundColor Green
        Write-Host "The system is now persistent and available for all layers." -ForegroundColor Green
    } else {
        Write-Error "Failed to start TruthGPT System Core."
    }
}

function Stop-TruthGPT-System {
    Write-Host "➤ Terminating TruthGPT System Core..." -ForegroundColor Yellow
    Stop-Job -Name "TruthGPT_Core"
    Get-Process -Name "python" | Where-Object { $_.CommandLine -like "*system_core_api.py*" } | Stop-Process -Force
    Write-Host "✓ System Core suspended." -ForegroundColor Red
}

# Auto-start if requested
# Start-TruthGPT-System
