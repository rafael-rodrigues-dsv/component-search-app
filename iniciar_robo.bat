@echo off
setlocal enableextensions
title ROBO 2 - E-mails reais (Firefox visivel)

echo [INFO] Pasta atual esperada: %cd%
echo [OK] Pasta atual: %cd%

if not exist "chromedriver.exe" (
  echo [ERRO] chromedriver.exe NAO encontrado nesta pasta.
  echo [INFO] Baixe em: https://chromedriver.chromium.org/
  pause & exit /b
) else (
  echo [OK] chromedriver.exe encontrado.
)

where python >nul 2>nul || (echo [ERRO] Python 3.11+ nao encontrado no PATH. & pause & exit /b)

if not exist ".venv" (
  echo [INFO] Criando venv...
  python -m venv .venv || (echo [ERRO] Falha ao criar venv. & pause & exit /b)
)

call ".venv\Scripts\activate.bat" || (echo [ERRO] Nao consegui ativar a venv. & pause & exit /b)
echo [OK] Venv ativada.

python -m pip install --upgrade pip
pip install -r requirements.txt

set "PATH=%PATH%;%cd%"

if not exist "main.py" (
  echo [ERRO] main.py nao encontrado nesta pasta.
  pause & exit /b
)

echo [INFO] Iniciando o ROBO 2...
python "main.py"
echo [INFO] Robo finalizado.