#!/usr/bin/env python3
"""
🚀 TruthGPT Enhanced UI Installation Script
Automatic setup for modern Claude-style interface
"""

import os
import sys
import shutil
from pathlib import Path

from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.panel import Panel
from rich.prompt import Confirm

console = Console()

def install_enhanced_ui():
    """Install enhanced UI components"""
    console.print(Panel("🚀 TruthGPT Enhanced UI Installer", style="bold blue"))
    
    with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}")) as progress:
        
        # Step 1: Install requirements
        task1 = progress.add_task("Installing requirements...", total=100)
        os.system("pip install rich prompt-toolkit keyboard typer")
        progress.update(task1, completed=100)
        
        # Step 2: Setup configuration
        task2 = progress.add_task("Setting up configuration...", total=100)
        create_config_file()
        progress.update(task2, completed=100)
        
        # Step 3: Create shortcuts
        task3 = progress.add_task("Creating shortcuts...", total=100)
        create_shortcuts()
        progress.update(task3, completed=100)
        
        # Step 4: Update main CLI
        task4 = progress.add_task("Updating main CLI...", total=100)
        update_main_cli()
        progress.update(task4, completed=100)
    
    console.print("[green]✅ Enhanced UI installed successfully![/green]")
    console.print("\n[cyan]Available commands:[/cyan]")
    console.print("• python launch_enhanced.py - Modern launcher")
    console.print("• python enhanced_cli.py interactive - Enhanced CLI")
    console.print("• python truthgpt.py --ui modern - Modern UI mode")

def create_config_file():
    """Create configuration file for enhanced UI"""
    config = '''
# TruthGPT Enhanced UI Configuration
ui:
  theme: "claude"  # claude, anthropic, minimalist, industrial
  width: 120
  refresh_rate: 2
  animations: true
  
features:
  terminal_integration: true
  real_time_optimization: true
  research_mode: true
  chat_history: true
  
optimizations:
  chain_of_draft: true
  elastic_reasoning: true
  fp16_stability: true
'''
    
    with open('enhanced_ui_config.yaml', 'w') as f:
        f.write(config)

def create_shortcuts():
    """Create convenient shortcuts"""
    # Windows batch file
    bat_content = '''@echo off
cd /d "%~dp0"
python launch_enhanced.py
pause
'''
    
    with open('TruthGPT-Enhanced.bat', 'w') as f:
        f.write(bat_content)
    
    # PowerShell script
    ps1_content = '''#!/usr/bin/env pwsh
Set-Location $PSScriptRoot
python launch_enhanced.py
Read-Host "Press Enter to continue"
'''
    
    with open('TruthGPT-Enhanced.ps1', 'w') as f:
        f.write(ps1_content)
    
    # Linux/Mac shell script
    sh_content = '''#!/bin/bash
cd "$(dirname "$0")"
python launch_enhanced.py
read -p "Press Enter to continue"
'''
    
    with open('truthgpt-enhanced.sh', 'w') as f:
        f.write(sh_content)
    
    # Make executable on Unix systems
    if os.name != 'nt':
        os.chmod('truthgpt-enhanced.sh', 0o755)

def update_main_cli():
    """Update main CLI to include enhanced UI option"""
    try:
        # Read current CLI
        with open('cli.py', 'r') as f:
            content = f.read()
        
        # Add enhanced UI import and command if not exists
        if 'launch_enhanced' not in content:
            enhanced_command = '''

@app.command()
def ui(
    mode: str = typer.Option("enhanced", help="UI mode: enhanced, modern, classic")
):
    """Launch TruthGPT with enhanced UI"""
    if mode == "enhanced" or mode == "modern":
        from launch_enhanced import main as launch_main
        launch_main()
    else:
        console.print("[yellow]Classic UI not yet implemented[/yellow]")
'''
            
            # Insert before if __name__ == "__main__":
            content = content.replace(
                'if __name__ == "__main__":',
                enhanced_command + '\nif __name__ == "__main__":'
            )
            
            with open('cli.py', 'w') as f:
                f.write(content)
                
    except FileNotFoundError:
        console.print("[yellow]Warning: cli.py not found, skipping update[/yellow]")

def main():
    """Main installation function"""
    if Confirm.ask("Install TruthGPT Enhanced UI?"):
        install_enhanced_ui()
    else:
        console.print("Installation cancelled.")

if __name__ == "__main__":
    main()
