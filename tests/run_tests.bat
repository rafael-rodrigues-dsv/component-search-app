@echo off
cd /d "%~dp0"
echo ========================================
echo  EXECUTANDO TESTES COM COBERTURA
echo ========================================
echo.

REM Instala dependencias se necessario
echo Verificando dependencias...
python -c "import pytest, coverage" >nul 2>&1
if errorlevel 1 (
    echo Instalando pytest e coverage...
    python -m pip install -r requirements-test.txt
    if errorlevel 1 (
        py -m pip install -r requirements-test.txt
        if errorlevel 1 (
            echo ERRO: Nao foi possivel instalar dependencias
            pause
            exit /b 1
        )
        set PYTHON_CMD=py
    ) else (
        set PYTHON_CMD=python
    )
) else (
    set PYTHON_CMD=python
)

echo.
echo Executando testes com cobertura...
%PYTHON_CMD% -m pytest unit/application/ --cov=../src/application --cov-report=html --cov-report=term-missing -v

if errorlevel 1 (
    echo.
    echo Tentando com unittest...
    %PYTHON_CMD% -m unittest unit.application.test_email_application_service -v
    goto :end
)

echo.
echo ========================================
echo  RELATORIO DE COBERTURA GERADO
echo ========================================

if exist htmlcov\index.html (
    echo Relatorio HTML: htmlcov\index.html
    echo Abrir relatorio? (s/n)
    set /p choice="Escolha: "
    if /i "%choice%"=="s" start htmlcov\index.html
) else (
    echo Relatorio nao foi gerado
)

:end
echo.
echo Testes concluidos!
pause