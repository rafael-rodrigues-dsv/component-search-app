@echo off
setlocal enabledelayedexpansion
title COLETOR DE E-MAILS E CONTATOS

echo [INFO] Iniciando Coletor de E-mails e Contatos...
echo [INFO] Pasta: %cd%

REM Verificar se Python funciona e versao minima
py --version >nul 2>nul && (
  for /f "tokens=2,3,4 delims=. " %%a in ('py --version 2^>^&1') do (
    set /a "major=%%a" 2>nul
    set /a "minor=%%b" 2>nul
    set /a "patch=%%c" 2>nul
    if !major! EQU 3 (
      if !minor! GTR 13 (
        echo [OK] Python %%a.%%b.%%c encontrado via 'py' - compativel
        set PYTHON_CMD=py
        goto :run_program
      ) else if !minor! EQU 13 (
        if !patch! GEQ 7 (
          echo [OK] Python %%a.%%b.%%c encontrado via 'py' - compativel
          set PYTHON_CMD=py
          goto :run_program
        )
      )
    ) else if !major! GTR 3 (
      echo [OK] Python %%a.%%b.%%c encontrado via 'py' - compativel
      set PYTHON_CMD=py
      goto :run_program
    )
    echo [ERRO] Python %%a.%%b.%%c incompativel - necessario 3.13.7+
    goto :install_python
  )
)

python --version >nul 2>nul && (
  for /f "tokens=2,3,4 delims=. " %%a in ('python --version 2^>^&1') do (
    set /a "major=%%a" 2>nul
    set /a "minor=%%b" 2>nul
    set /a "patch=%%c" 2>nul
    if !major! EQU 3 (
      if !minor! GTR 13 (
        echo [OK] Python %%a.%%b.%%c encontrado via 'python' - compativel
        set PYTHON_CMD=python
        goto :run_program
      ) else if !minor! EQU 13 (
        if !patch! GEQ 7 (
          echo [OK] Python %%a.%%b.%%c encontrado via 'python' - compativel
          set PYTHON_CMD=python
          goto :run_program
        )
      )
    ) else if !major! GTR 3 (
      echo [OK] Python %%a.%%b.%%c encontrado via 'python' - compativel
      set PYTHON_CMD=python
      goto :run_program
    )
    echo [ERRO] Python %%a.%%b.%%c incompativel - necessario 3.13.7+
    goto :install_python
  )
)

REM Se chegou aqui, nao tem Python
echo [INFO] Python nao encontrado. Executando instalador automatico...

:install_python
REM Tentar usar Python existente para baixar e instalar
echo [INFO] Testando se Python funciona para instalacao...
python --version >nul 2>nul && (
  echo [INFO] Usando Python existente para instalacao...
  python scripts\verification\download_python.py
  echo [INFO] Reinicie o script para usar o novo Python.
  pause & exit /b 0
)
py --version >nul 2>nul && (
  echo [INFO] Usando py existente para instalacao...
  py scripts\verification\download_python.py
  echo [INFO] Reinicie o script para usar o novo Python.
  pause & exit /b 0
)

REM Fallback para PowerShell se nao tem Python
echo [INFO] Baixando Python 3.13.7 via PowerShell...
if not exist "drivers" mkdir drivers
powershell -Command "& {[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; Invoke-WebRequest -Uri 'https://www.python.org/ftp/python/3.13.7/python-3.13.7-amd64.exe' -OutFile 'drivers\python-installer.exe'}"
if not exist "drivers\python-installer.exe" (
  echo [ERRO] Falha no download do Python. Verifique sua conexao.
  pause & exit /b 1
)
echo [INFO] Instalando Python 3.13.7 com PATH automatico...
drivers\python-installer.exe /quiet InstallAllUsers=0 PrependPath=1 Include_test=0 Include_doc=0
echo [OK] Python 3.13.7 instalado com sucesso!
echo [INFO] Atualizando PATH da sessao atual...
for /f "skip=2 tokens=2*" %%a in ('reg query "HKCU\Environment" /v PATH 2^>nul') do set USER_PATH=%%b
for /f "skip=2 tokens=2*" %%a in ('reg query "HKLM\SYSTEM\CurrentControlSet\Control\Session Manager\Environment" /v PATH 2^>nul') do set SYSTEM_PATH=%%b
set PATH=%SYSTEM_PATH%;%USER_PATH%
echo [INFO] Verificando se Python esta disponivel...
py --version >nul 2>nul && (
  echo [OK] Python disponivel! Continuando execucao...
  set PYTHON_CMD=py
  goto :run_program
)
python --version >nul 2>nul && (
  echo [OK] Python disponivel! Continuando execucao...
  set PYTHON_CMD=python
  goto :run_program
)
echo [AVISO] Python instalado mas nao detectado. Reinicie o script.
pause
exit /b 0

:run_program
echo [INFO] Verificando detalhes do Python...
%PYTHON_CMD% --version
for /f "delims=" %%i in ('%PYTHON_CMD% -c "import sys; print(sys.executable)"') do set PYTHON_EXE=%%i
echo [INFO] Executavel Python: !PYTHON_EXE!
for %%i in ("!PYTHON_EXE!") do set PYTHON_DIR=%%~dpi
echo [INFO] Diretorio Python: !PYTHON_DIR!

REM Verificar se banco de dados existe
if not exist "data\pythonsearch.accdb" (
  echo [AVISO] Banco de dados nao encontrado em data\pythonsearch.accdb
  echo [INFO] Recriando ambiente virtual do zero...
  
  REM Deletar ambiente virtual anterior se existir
  if exist ".venv" (
    echo [INFO] Removendo ambiente virtual anterior...
    rmdir /s /q ".venv" 2>nul
  )
  
  REM Criar novo ambiente virtual
  echo [INFO] Criando novo ambiente virtual...
  %PYTHON_CMD% -m venv .venv
) else (
  echo [OK] Banco de dados encontrado
  
  REM Criar ambiente virtual se nao existir
  if not exist ".venv" (
    echo [INFO] Criando ambiente virtual...
    %PYTHON_CMD% -m venv .venv
  )
)

if exist ".venv\Scripts\activate.bat" (
  echo [INFO] Ativando ambiente virtual...
  call .venv\Scripts\activate.bat
)

echo [INFO] Verificando e instalando dependencias...
%PYTHON_CMD% scripts\verification\verify_python_installation.py || (
  echo [ERRO] Falha na verificacao das dependencias
  pause
  exit /b 1
)

echo [INFO] Verificando dependencias do dashboard web...
%PYTHON_CMD% -c "import flask, flask_socketio" >nul 2>nul || (
  echo [INFO] Instalando Flask para dashboard web...
  %PYTHON_CMD% -m pip install flask>=3.0.0 flask-socketio>=5.3.0 --quiet
  echo [OK] Flask instalado com sucesso!
)

echo [INFO] Verificando ChromeDriver...
%PYTHON_CMD% scripts\verification\verify_chromedriver.py || (
  echo [ERRO] ChromeDriver nao disponivel
  pause
  exit /b 1
)

echo [INFO] Executando programa...
%PYTHON_CMD% main.py

if %errorlevel% neq 0 (
  echo [ERRO] Programa falhou
  pause
)