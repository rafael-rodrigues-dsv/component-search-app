@echo off
echo Instalando dependencias...
cd /d "%~dp0\..\.."

REM Instalar dependencias usando pyproject.toml
echo Instalando dependencias principais...
pip install -e .

echo Instalando dependencias de teste...
pip install -e .[test]

echo.
echo Dependencias instaladas com sucesso!
pause