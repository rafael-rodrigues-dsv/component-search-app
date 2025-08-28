@echo off
setlocal enableextensions
title ROBO COLETOR DE E-MAILS - Plug and Play

echo [INFO] === INICIALIZACAO AUTOMATICA ===
echo [INFO] Pasta: %cd%
echo [INFO] Verificando ambiente...

REM Verificar instalacoes do Python
echo [INFO] Analisando instalacoes do Python...
set PYTHON_CMD=
set PYTHON_OK=0
set PYTHON_COUNT=0
set BEST_VERSION=0
set BEST_CMD=

REM Contar e avaliar instalacoes
where python >nul 2>nul && (
  set /a PYTHON_COUNT+=1
  for /f "tokens=2 delims=." %%v in ('python --version 2^>^&1') do (
    if %%v GEQ 11 (
      if %%v GTR %BEST_VERSION% (
        set BEST_VERSION=%%v
        set BEST_CMD=python
        set PYTHON_OK=1
      )
    )
  )
)

where py >nul 2>nul && (
  set /a PYTHON_COUNT+=1
  for /f "tokens=2 delims=." %%v in ('py --version 2^>^&1') do (
    if %%v GEQ 11 (
      if %%v GTR %BEST_VERSION% (
        set BEST_VERSION=%%v
        set BEST_CMD=py
        set PYTHON_OK=1
      )
    )
  )
)

REM Decisao baseada no numero de instalacoes
if %PYTHON_COUNT% EQU 0 (
  echo [INFO] Nenhum Python encontrado. Instalando versao mais recente...
  goto :install_latest
) else if %PYTHON_COUNT% EQU 1 (
  if %PYTHON_OK% EQU 1 (
    echo [OK] Python %BEST_VERSION% encontrado. Usando instalacao existente.
    set PYTHON_CMD=%BEST_CMD%
  ) else (
    echo [INFO] Python encontrado mas versao muito antiga. Instalando versao mais recente...
    goto :install_latest
  )
) else (
  if %PYTHON_OK% EQU 1 (
    echo [INFO] Multiplas instalacoes encontradas. Usando Python %BEST_VERSION%.
    echo [INFO] Limpando instalacoes antigas...
    powershell -Command "Get-WmiObject -Class Win32_Product | Where-Object {$_.Name -like '*Python*' -and $_.Version -notlike '*%BEST_VERSION%*'} | ForEach-Object {$_.Uninstall()}"
    set PYTHON_CMD=%BEST_CMD%
  ) else (
    echo [INFO] Multiplas instalacoes antigas encontradas. Limpando e instalando versao mais recente...
    powershell -Command "Get-WmiObject -Class Win32_Product | Where-Object {$_.Name -like '*Python*'} | ForEach-Object {$_.Uninstall()}"
    goto :install_latest
  )
)
goto :continue

:install_latest
powershell -Command "& {[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; $latest = (Invoke-RestMethod 'https://api.github.com/repos/python/cpython/releases/latest').tag_name -replace 'v',''; $url = \"https://www.python.org/ftp/python/$latest/python-$latest-amd64.exe\"; Write-Host \"Baixando Python $latest...\"; Invoke-WebRequest -Uri $url -OutFile 'python-installer.exe'}"
if not exist "python-installer.exe" (
  echo [ERRO] Falha no download do Python. Verifique sua conexao.
  pause & exit /b 1
)
echo [INFO] Instalando Python (versao mais recente)...
python-installer.exe /quiet InstallAllUsers=0 PrependPath=1 Include_test=0 Include_doc=0
del python-installer.exe
echo [OK] Python instalado com sucesso!
set PYTHON_CMD=python

:continue

echo [INFO] Verificando versao do Python...
%PYTHON_CMD% --version
for /f "delims=" %%i in ('%PYTHON_CMD% -c "import sys; print(sys.executable)"') do set PYTHON_EXE=%%i
echo [INFO] Executavel Python: %PYTHON_EXE%
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

echo [INFO] Limpando instalacoes anteriores...
"%PYTHON_EXE%" -m pip uninstall -y selenium openpyxl tldextract requests 2>nul

echo [INFO] Instalando dependencias necessarias...
"%PYTHON_EXE%" -m pip install --upgrade pip
"%PYTHON_EXE%" -m pip install --no-cache-dir selenium==4.35.0 openpyxl==3.1.5 tldextract==5.3.0 requests==2.32.5
if %errorlevel% neq 0 (
  echo [INFO] Tentando instalacao alternativa...
  "%PYTHON_EXE%" -m pip install --user --no-cache-dir selenium openpyxl tldextract requests
  if %errorlevel% neq 0 (
    echo [ERRO] Falha critica na instalacao das dependencias
    pause & exit /b 1
  )
)

echo [INFO] Testando importacao com o mesmo Python...
"%PYTHON_EXE%" -c "import sys; print('Testando com:', sys.executable)"
"%PYTHON_EXE%" -c "import selenium, openpyxl, tldextract, requests; print('[OK] Dependencias funcionando!')"
if %errorlevel% neq 0 (
  echo [ERRO] Dependencias nao funcionam mesmo apos instalacao
  echo [INFO] Executavel Python: %PYTHON_EXE%
  pause & exit /b 1
)

echo [INFO] === EXECUCAO DO PROGRAMA ===
if not exist "main.py" (
  echo [ERRO] main.py nao encontrado nesta pasta.
  pause & exit /b 1
)

echo [OK] Iniciando o Robo Coletor de E-mails...
echo [INFO] Executando com: %PYTHON_EXE%
"%PYTHON_EXE%" main.py

if %errorlevel% neq 0 (
  echo [ERRO] O robo encontrou um erro durante a execucao.
  pause
) else (
  echo [OK] Robo finalizado com sucesso!
  pause
)