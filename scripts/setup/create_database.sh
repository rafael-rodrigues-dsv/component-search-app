#!/bin/bash
echo "CRIADOR AUTOMATICO DO BANCO ACCESS"
echo "====================================="
echo ""

cd "$(dirname "$0")/../.."

echo "Instalando dependencias..."
pip install pyodbc

echo ""
echo "Criando banco Access..."
python scripts/database/create_db_simple.py

echo ""
read -p "Pressione Enter para sair..."