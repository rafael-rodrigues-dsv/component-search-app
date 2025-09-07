@echo off
title Monitor PythonSearchApp - Tempo Real
echo.
echo ========================================
echo   MONITOR PYTHONSEARCHAPP - TEMPO REAL
echo ========================================
echo.
echo Monitora as 5 funcionalidades do robo:
echo   - Coleta de dados (emails/telefones)
echo   - Enriquecimento CEP (ViaCEP)
echo   - Geolocalizacao (Nominatim)
echo   - Exportacao Excel
echo   - Estatisticas completas
echo.
echo Iniciando Monitor em Tempo Real...
echo.

cd /d "%~dp0"

REM Ativar ambiente virtual se existir
if exist ".venv\Scripts\activate.bat" (
    echo [INFO] Ativando ambiente virtual...
    call .venv\Scripts\activate.bat
)

echo.
echo Iniciando Monitor...
python scripts\monitoring\realtime_monitor.py

pause