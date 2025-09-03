@echo off
cd /d "%~dp0"
echo ========================================
echo  EXECUTANDO TESTES COM COBERTURA
echo ========================================
echo.

REM Detectar Python disponivel
echo Verificando Python...
py --version >nul 2>&1 && (
    echo [OK] Python encontrado via 'py'
    set PYTHON_CMD=py
    goto :check_deps
)
python --version >nul 2>&1 && (
    echo [OK] Python encontrado via 'python'
    set PYTHON_CMD=python
    goto :check_deps
)
echo ERRO: Python nao encontrado
pause
exit /b 1

:check_deps
echo Verificando dependencias...
%PYTHON_CMD% -c "import pytest, coverage" >nul 2>&1
if errorlevel 1 (
    echo Instalando pytest e coverage...
    %PYTHON_CMD% -m pip install pytest pytest-cov coverage
    if errorlevel 1 (
        echo ERRO: Nao foi possivel instalar dependencias
        pause
        exit /b 1
    )
)

echo.
echo Executando testes com cobertura...
%PYTHON_CMD% -m pytest unit/ --cov=../src --cov-report=html:reports/htmlcov --cov-report=term-missing --cov-report=xml:reports/coverage.xml -v

if errorlevel 1 (
    echo.
    echo Tentando com unittest...
    %PYTHON_CMD% -m unittest discover unit/ -v
    goto :end
)

echo.
echo ========================================
echo  RELATORIOS DE COBERTURA GERADOS
echo ========================================
echo HTML: reports\htmlcov\index.html
echo XML:  reports\coverage.xml
echo.

if exist reports\htmlcov\index.html (
    echo Abrir relatorio HTML? (s/n)
    set /p choice="Escolha: "
    if /i "%choice%"=="s" start reports\htmlcov\index.html
) else (
    echo Relatorio nao foi gerado
)

:end
echo.
echo Testes concluidos!
pause