@echo off
echo CRIADOR AUTOMATICO DO BANCO ACCESS
echo =====================================
echo.

cd /d "%~dp0\..\..\"

echo Instalando dependencias...
pip install pyodbc pywin32

echo.
echo Criando banco Access...
python scripts\database\create_db_simple.py