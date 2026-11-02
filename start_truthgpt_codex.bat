@echo off
title TruthGPT System 6.0 - OpenAI Codex Edition
color 0b
chcp 65001 >nul
set PYTHONIOENCODING=utf-8
set TRUTHGPT_USE_CODEX=1

echo ========================================================================
echo        TRUTHGPT COMMAND CENTER - OPENAI CODEX ORCHESTRATION
echo ========================================================================
echo.
cd /d "%~dp0"

py launch_with_codex.py %*
if %ERRORLEVEL% NEQ 0 (
    python launch_with_codex.py %*
)
pause
