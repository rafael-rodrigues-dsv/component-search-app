#!/bin/bash
echo "Instalando dependencias..."
cd "$(dirname "$0")/../.."

# Ativar ambiente virtual se existir
if [ -f ".venv/bin/activate" ]; then
    echo "[INFO] Ativando ambiente virtual..."
    source .venv/bin/activate
fi

# Instalar dependencias individuais para evitar .egg-info
echo "Instalando dependencias principais..."
python -m pip install "selenium>=4.0.0" "openpyxl>=3.0.0" "tldextract>=3.0.0" "requests>=2.25.0" "pyyaml>=6.0" "pyodbc>=4.0.0"

echo "Instalando dependencias de teste..."
python -m pip install "pytest>=7.0.0" "pytest-cov>=4.0.0" "coverage>=7.0.0"

echo ""
echo "Dependencias instaladas com sucesso!"