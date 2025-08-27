@echo off
setlocal enableextensions
title ROBO 2 - E-mails reais (Firefox visivel)

echo [INFO] Pasta atual esperada: %cd%
echo [OK] Pasta atual: %cd%

where py >nul 2>nul || (
  echo [INFO] Python nao encontrado. Baixando Python 3.13...
  powershell -Command "Invoke-WebRequest -Uri 'https://www.python.org/ftp/python/3.13.7/python-3.13.7-amd64.exe' -OutFile 'python-installer.exe'"
  echo [INFO] Instalando Python 3.13...
  python-installer.exe /quiet InstallAllUsers=0 PrependPath=1 Include_test=0
  del python-installer.exe
  echo [OK] Python instalado. Reinicie o terminal e execute novamente.
  pause & exit /b
)

echo [INFO] Verificando versao do Python...
py --version
echo [INFO] Verificando dependencias...
py -m pip install --user -r requirements.txt

echo [INFO] Testando importacao das dependencias...
py -c "import selenium, openpyxl, tldextract, requests; print('[OK] Todas as dependencias estao disponiveis')" || (
  echo [ERRO] Dependencias nao instaladas corretamente
  echo [INFO] Tentando instalacao global...
  py -m pip install -r requirements.txt
  pause & exit /b
)

if not exist "main.py" (
  echo [ERRO] main.py nao encontrado nesta pasta.
  pause & exit /b
)

echo [INFO] Iniciando o ROBO 2...
py "main.py"
echo [INFO] Robo finalizado.