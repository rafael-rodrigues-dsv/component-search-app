#!/bin/bash
echo "CRIADOR DO BANCO ACCESS"
echo "========================"

cd "$(dirname "$0")/../.."

# Ativar ambiente virtual se existir
if [ -f ".venv/bin/activate" ]; then
    echo "[INFO] Ativando ambiente virtual..."
    source .venv/bin/activate
fi

echo "[INFO] Instalando dependencias..."
python -m pip install -q pyodbc pywin32

echo ""
python scripts/database/create_db_simple.py

echo ""
read -p "Pressione Enter para sair..."