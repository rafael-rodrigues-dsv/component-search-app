@echo off
echo Instalando dependencias...
cd /d "%~dp0\..\.."

REM Ativar ambiente virtual se existir
if exist ".venv\Scripts\activate.bat" (
    echo [INFO] Ativando ambiente virtual...
    call .venv\Scripts\activate.bat
)

REM Instalar todas as dependencias em um unico comando
echo Instalando dependencias do sistema...
python -m pip install --cache-dir "%LOCALAPPDATA%\pip\cache" selenium>=4.0.0 playwright>=1.40.0 openpyxl>=3.0.0 tldextract>=3.0.0 requests>=2.25.0 pyyaml>=6.0 pyodbc>=4.0.0 pywin32>=306 beautifulsoup4>=4.12.0 lxml>=4.9.0 flask>=3.0.0 flask-socketio>=5.3.0

echo.
echo ✅ Dependencias instaladas com sucesso!
pause