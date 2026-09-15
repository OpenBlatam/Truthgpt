@echo off
title TruthGPT Cloud - Servidor y Panel de Control de Cobros
color 0b
echo ========================================================================
echo       VERIFICADOR FORMAL Y PLATAFORMA DE COBROS TRUTHGPT CLOUD
echo ========================================================================
echo.
echo [1/2] Iniciando servidor FastAPI en segundo plano...
cd /d "%~dp0"

start "" "http://localhost:8080/dashboard"

python truthgpt_cloud_server.py
pause
