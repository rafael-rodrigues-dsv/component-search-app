@echo off
setlocal enableextensions
title ROBO 2 - E-mails reais (Firefox visivel)

echo [INFO] Pasta atual esperada: %cd%
echo [OK] Pasta atual: %cd%

where py >nul 2>nul || (echo [ERRO] Python 3.11+ nao encontrado no PATH. & pause & exit /b)

echo [INFO] Verificando dependencias...
py -m pip install -r requirements.txt

if not exist "main.py" (
  echo [ERRO] main.py nao encontrado nesta pasta.
  pause & exit /b
)

echo [INFO] Iniciando o ROBO 2...
py "main.py"
echo [INFO] Robo finalizado.