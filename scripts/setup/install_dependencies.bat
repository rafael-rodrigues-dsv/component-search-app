@echo off
echo Instalando dependencias...
cd /d "%~dp0\..\.."

REM Ativar ambiente virtual se existir
if exist ".venv\Scripts\activate.bat" (
    echo [INFO] Ativando ambiente virtual...
    call .venv\Scripts\activate.bat
)

REM Instalar dependencias individuais para evitar .egg-info
echo Instalando dependencias principais...
python -m pip install selenium>=4.0.0 openpyxl>=3.0.0 tldextract>=3.0.0 requests>=2.25.0 pyyaml>=6.0 pyodbc>=4.0.0 pywin32>=306

echo Instalando dependencias de teste...
python -m pip install pytest>=7.0.0 pytest-cov>=4.0.0 coverage>=7.0.0

echo.
echo Dependencias instaladas com sucesso!
pause