# TruthGPT System Continuity Manager
# Manage persistence and background agent execution

$ProjectRoot = Get-Location
$ContinuityScript = "$ProjectRoot\scripts\background_persistence.py"

function Show-Help {
    Write-Host "TruthGPT Continuity Manager" -ForegroundColor Cyan
    Write-Host "----------------------------"
    Write-Host "Usage:"
    Write-Host "  .\system_continuity.ps1 --status    Check for interrupted tasks"
    Write-Host "  .\system_continuity.ps1 --resume    Resume all pending tasks"
    Write-Host "  .\system_continuity.ps1 --install   Register as Windows Startup Task (survive reboots)"
    Write-Host "  .\system_continuity.ps1 --uninstall Remove from Windows Startup"
    Write-Host "  .\system_continuity.ps1 --deactivate Stop and clear all active tasks"
    Write-Host "  .\system_continuity.ps1 --cloud-status Check results from remote Swarm Node"
}

if ($args.Count -eq 0) {
    Show-Help
    exit
}

switch ($args[0]) {
    "--status" {
        Write-Host "Checking agent snapshots..." -ForegroundColor Yellow
        python $ContinuityScript
    }
    "--resume" {
        Write-Host "Resuming all persistent agents..." -ForegroundColor Green
        python $ContinuityScript
    }
    "--install" {
        Write-Host "Installing TruthGPT Continuity Engine to Windows Task Scheduler..." -ForegroundColor Cyan
        python $ContinuityScript --install
    }
    "--uninstall" {
        Write-Host "Removing TruthGPT Continuity Engine..." -ForegroundColor Red
        schtasks /delete /tn "TruthGPT_Continuity_Engine" /f
    }
    "--deactivate" {
        Write-Host "Deactivating all persistent agents..." -ForegroundColor Red
        python -c "import sqlite3; conn = sqlite3.connect('agent_persistence.db'); conn.execute('UPDATE task_snapshots SET status = ''completed'' WHERE status = ''running'''); conn.commit(); conn.close()"
        Write-Host "All active tasks marked as completed/deactivated." -ForegroundColor Green
    }
    "--cloud-status" {
        Write-Host "Querying Cloud Swarm Node for results..." -ForegroundColor Cyan
        python -c "import asyncio; from modules.persistence.task_manager import get_persistence_manager; async def check(): pm = get_persistence_manager(); tasks = await pm.list_active_tasks(); print(f'Checking {len(tasks)} tasks...'); [print(f'Task {t.task_id}: ', await pm.fetch_remote_result(t.task_id)) for t in tasks]; asyncio.run(check())"
    }
    default {
        Show-Help
    }
}
