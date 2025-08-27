@echo off
title Compilando Robo de E-mails

echo [INFO] Compilando PythonSearchApp para executavel...

py -m PyInstaller ^
  --onefile ^
  --noconsole ^
  --add-data "config;config" ^
  --add-data "drivers;drivers" ^
  --hidden-import selenium ^
  --hidden-import openpyxl ^
  --hidden-import tldextract ^
  --hidden-import requests ^
  --name "RoboEmails" ^
  main.py

if %errorlevel% neq 0 (
  echo [ERRO] Falha na compilacao
  pause
  exit /b
)

echo [OK] Executavel criado em: dist\RoboEmails.exe
echo [INFO] Copiando arquivos necessarios...

mkdir dist\config 2>nul
copy config\*.py dist\config\
mkdir dist\drivers 2>nul
copy drivers\*.exe dist\drivers\ 2>nul
copy requirements.txt dist\
copy README.md dist\

echo [OK] Compilacao finalizada!
echo [INFO] Pasta para distribuicao: dist\
pause