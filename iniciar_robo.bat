@echo off
title ROBO COLETOR DE E-MAILS - Simples

echo [INFO] Iniciando Robo Coletor de E-mails...
echo [INFO] Pasta: %cd%

REM Verificar se Python funciona
py --version >nul 2>nul && (
  echo [OK] Python encontrado via 'py'
  set PYTHON_CMD=py
  goto :run_program
)

python --version >nul 2>nul && (
  echo [OK] Python encontrado via 'python'  
  set PYTHON_CMD=python
  goto :run_program
)

REM Se chegou aqui, nao tem Python
echo [ERRO] Python nao encontrado!
echo [INFO] Instale Python 3.11+ manualmente em: https://python.org
echo [INFO] Durante a instalacao, marque "Add Python to PATH"
pause
exit /b 1

:run_program
REM Adicionar Scripts do Python ao PATH
for /f "delims=" %%i in ('%PYTHON_CMD% -c "import sys; print(sys.executable)"') do set PYTHON_EXE=%%i
for %%i in ("%PYTHON_EXE%") do set PYTHON_DIR=%%~dpi
set SCRIPTS_DIR=%PYTHON_DIR%Scripts
set USER_SCRIPTS_DIR=%APPDATA%\Python\Python313\Scripts
set PATH=%SCRIPTS_DIR%;%USER_SCRIPTS_DIR%;%PATH%

echo [INFO] Instalando dependencias...
%PYTHON_CMD% -m pip install --quiet selenium openpyxl tldextract requests

echo [INFO] Testando dependencias...
%PYTHON_CMD% -c "import selenium, openpyxl, tldextract, requests; print('[OK] Dependencias OK!')" || (
  echo [ERRO] Falha nas dependencias
  pause
  exit /b 1
)

echo [INFO] Executando programa...
%PYTHON_CMD% main.py

if %errorlevel% neq 0 (
  echo [ERRO] Programa falhou
  pause
) else (
  echo [OK] Programa finalizado com sucesso!
  pause
)