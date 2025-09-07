@echo off
title Instalador PyODBC
echo [INFO] Instalando PyODBC e drivers necessarios...

REM Ativar ambiente virtual se existir
if exist ".venv\Scripts\activate.bat" (
    echo [INFO] Ativando ambiente virtual...
    call .venv\Scripts\activate.bat
)

REM Verificar se pip funciona
python -m pip --version >nul 2>nul || (
    echo [ERRO] pip nao encontrado
    pause
    exit /b 1
)

echo [INFO] Atualizando pip...
python -m pip install --upgrade pip

echo [INFO] Instalando pyodbc...
python -m pip install pyodbc>=4.0.0

echo [INFO] Verificando instalacao...
python -c "import pyodbc; print('[OK] pyodbc instalado com sucesso')" || (
    echo [ERRO] Falha na instalacao do pyodbc
    echo [INFO] Tentando instalacao alternativa...
    python -m pip install --force-reinstall pyodbc
)

echo [INFO] Testando conexao com Access...
python -c "import pyodbc; drivers = [x for x in pyodbc.drivers() if 'Access' in x or 'Microsoft' in x]; print(f'[INFO] Drivers encontrados: {drivers}')"

echo [OK] Instalacao concluida!
pause