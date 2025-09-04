@echo off
title Monitor PythonSearchApp - Tempo Real
echo.
echo ========================================
echo   MONITOR PYTHONSEARCHAPP - TEMPO REAL
echo ========================================
echo.
echo Monitora as 3 funcionalidades do robo:
echo   - Coleta de dados (emails/telefones)
echo   - Geolocalizacao das empresas
echo   - Exportacao de planilha Excel
echo.
echo Escolha o tipo de monitor:
echo.
echo [1] Monitor Simples (atualiza a cada 5s)
echo [2] Monitor Avancado (metricas completas)
echo [3] Sair
echo.
set /p opcao="Digite sua opcao (1-3): "

if "%opcao%"=="1" (
    echo.
    echo Iniciando Monitor Simples...
    cd /d "%~dp0"
    python scripts\monitoring\realtime_monitor.py
) else if "%opcao%"=="2" (
    echo.
    echo Iniciando Monitor Avancado...
    cd /d "%~dp0"
    python scripts\monitoring\advanced_monitor.py
) else if "%opcao%"=="3" (
    echo.
    echo Saindo...
    exit
) else (
    echo.
    echo Opcao invalida! Tente novamente.
    pause
    goto :eof
)

pause