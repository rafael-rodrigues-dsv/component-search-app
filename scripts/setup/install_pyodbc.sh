#!/bin/bash
echo "[INFO] Instalando PyODBC e drivers necessarios..."

# Ativar ambiente virtual se existir
if [ -f ".venv/bin/activate" ]; then
    echo "[INFO] Ativando ambiente virtual..."
    source .venv/bin/activate
fi

# Verificar se pip funciona
if ! python -m pip --version >/dev/null 2>&1; then
    echo "[ERRO] pip nao encontrado"
    exit 1
fi

echo "[INFO] Atualizando pip..."
python -m pip install --upgrade pip

echo "[INFO] Instalando pyodbc..."
python -m pip install "pyodbc>=4.0.0"

echo "[INFO] Verificando instalacao..."
if python -c "import pyodbc; print('[OK] pyodbc instalado com sucesso')" 2>/dev/null; then
    echo "[OK] pyodbc funcionando"
else
    echo "[ERRO] Falha na instalacao do pyodbc"
    echo "[INFO] Tentando instalacao alternativa..."
    python -m pip install --force-reinstall pyodbc
fi

echo "[INFO] Testando conexao..."
python -c "import pyodbc; drivers = [x for x in pyodbc.drivers() if 'Access' in x or 'Microsoft' in x]; print(f'[INFO] Drivers encontrados: {drivers}')"

echo "[OK] Instalacao concluida!"