@echo off
echo CRIADOR DO BANCO ACCESS
echo ========================

cd /d "%~dp0\..\..\"

REM Ativar ambiente virtual se existir
if exist ".venv\Scripts\activate.bat" (
    echo [INFO] Ativando ambiente virtual...
    call .venv\Scripts\activate.bat
)

echo [INFO] Instalando dependencias...
python -m pip install -q pyodbc pywin32

echo.
python scripts\database\create_db_simple.py

echo.
pause