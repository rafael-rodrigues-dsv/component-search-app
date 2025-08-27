@echo off
setlocal enableextensions
title ROBO COLETOR DE E-MAILS - Plug and Play

echo [INFO] === INICIALIZACAO AUTOMATICA ===
echo [INFO] Pasta: %cd%
echo [INFO] Verificando ambiente...

REM Verificar se Python >= 3.11 esta instalado
echo [INFO] Verificando instalacao do Python...
set PYTHON_CMD=
set PYTHON_OK=0

REM Testar python
where python >nul 2>nul && (
  for /f "tokens=2 delims=." %%v in ('python --version 2^>^&1') do (
    if %%v GEQ 11 (
      set PYTHON_CMD=python
      set PYTHON_OK=1
    )
  )
)

REM Testar py se python nao funcionou
if %PYTHON_OK%==0 (
  where py >nul 2>nul && (
    for /f "tokens=2 delims=." %%v in ('py --version 2^>^&1') do (
      if %%v GEQ 11 (
        set PYTHON_CMD=py
        set PYTHON_OK=1
      )
    )
  )
)

REM Instalar se nao tem Python >= 3.11
if %PYTHON_OK%==0 (
  echo [INFO] Python 3.11+ nao encontrado. Instalando versao mais recente...
  powershell -Command "& {[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; Invoke-WebRequest -Uri 'https://www.python.org/ftp/python/3.13.1/python-3.13.1-amd64.exe' -OutFile 'python-installer.exe'}"
  if not exist "python-installer.exe" (
    echo [ERRO] Falha no download do Python. Verifique sua conexao.
    pause & exit /b 1
  )
  echo [INFO] Instalando Python 3.13.1...
  python-installer.exe /quiet InstallAllUsers=0 PrependPath=1 Include_test=0 Include_doc=0
  del python-installer.exe
  echo [OK] Python instalado com sucesso!
  set PYTHON_CMD=python
)

echo [INFO] Verificando versao do Python...
%PYTHON_CMD% --version
%PYTHON_CMD% -c "import sys; print('Executavel:', sys.executable)"
if %errorlevel% neq 0 (
  echo [ERRO] Python nao esta funcionando corretamente.
  pause & exit /b 1
)

REM Adicionar Scripts do Python ao PATH permanentemente
for /f "delims=" %%i in ('%PYTHON_CMD% -c "import sys; print(sys.executable)"') do set PYTHON_PATH=%%i
for %%i in ("%PYTHON_PATH%") do set PYTHON_DIR=%%~dpi
set SCRIPTS_DIR=%PYTHON_DIR%Scripts
echo [INFO] Verificando se %SCRIPTS_DIR% esta no PATH...
echo %PATH% | find /i "%SCRIPTS_DIR%" >nul || (
  echo [INFO] Adicionando %SCRIPTS_DIR% ao PATH do sistema...
  setx PATH "%PATH%;%SCRIPTS_DIR%" >nul
  echo [OK] Scripts do Python adicionado ao PATH permanentemente
)
set PATH=%SCRIPTS_DIR%;%PATH%

echo [INFO] === VERIFICACAO DO CHROME ===
where chrome >nul 2>nul || (
  echo [AVISO] Chrome nao encontrado. Instale o Google Chrome manualmente.
  echo [INFO] Continuando execucao...
)

echo [INFO] === CRIACAO DE PASTAS ===
if not exist "C:\Arquivos" (
  mkdir "C:\Arquivos"
  echo [OK] Pasta C:\Arquivos criada
)
if not exist "data" mkdir data
if not exist "output" mkdir output

echo [INFO] === INSTALACAO DAS DEPENDENCIAS ===
if not exist "requirements.txt" (
  echo [ERRO] requirements.txt nao encontrado.
  pause & exit /b 1
)

echo [INFO] Instalando dependencias necessarias...
%PYTHON_CMD% -m pip install --upgrade pip
%PYTHON_CMD% -m pip install --force-reinstall selenium openpyxl tldextract requests
if %errorlevel% neq 0 (
  echo [INFO] Tentando com --user...
  %PYTHON_CMD% -m pip install --user --force-reinstall selenium openpyxl tldextract requests
)

echo [INFO] Testando importacao...
%PYTHON_CMD% -c "import selenium, openpyxl, tldextract, requests; print('[OK] Dependencias funcionando!')"
if %errorlevel% neq 0 (
  echo [ERRO] Dependencias nao funcionam. Verifique a instalacao do Python.
  pause & exit /b 1
)

echo [INFO] === EXECUCAO DO PROGRAMA ===
if not exist "main.py" (
  echo [ERRO] main.py nao encontrado nesta pasta.
  pause & exit /b 1
)

echo [OK] Iniciando o Robo Coletor de E-mails...
%PYTHON_CMD% main.py

if %errorlevel% neq 0 (
  echo [ERRO] O robo encontrou um erro durante a execucao.
  pause
) else (
  echo [OK] Robo finalizado com sucesso!
  pause
)