@echo off
cd /d "%~dp0"
echo ========================================
echo  RELATORIO DE COBERTURA COMPLETA
echo ========================================
echo.

REM Instala dependencias
python -m pip install pytest pytest-cov coverage >nul 2>&1

REM Executa testes com cobertura completa
echo Gerando relatorio de cobertura...
python -m pytest unit/ --cov=../src --cov-report=html --cov-report=term --cov-report=xml -v

echo.
echo ========================================
echo  RELATORIOS GERADOS
echo ========================================
echo HTML: htmlcov\index.html
echo XML:  coverage.xml
echo.

if exist htmlcov\index.html (
    echo Abrir relatorio HTML? (s/n)
    set /p choice="Escolha: "
    if /i "%choice%"=="s" start htmlcov\index.html
)

pause