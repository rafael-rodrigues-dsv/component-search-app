#!/bin/bash
echo "Instalando dependencias..."
cd "$(dirname "$0")/../.."

# Ativar ambiente virtual se existir
if [ -f ".venv/bin/activate" ]; then
    echo "[INFO] Ativando ambiente virtual..."
    source .venv/bin/activate
fi

# Instalar todas as dependencias em um unico comando
echo "Instalando dependencias do sistema..."
python -m pip install --cache-dir ~/.cache/pip "selenium>=4.0.0" "playwright>=1.40.0" "openpyxl>=3.0.0" "tldextract>=3.0.0" "requests>=2.25.0" "pyyaml>=6.0" "pyodbc>=4.0.0" "beautifulsoup4>=4.12.0" "lxml>=4.9.0" "flask>=3.0.0" "flask-socketio>=5.3.0"

echo ""
echo "✅ Dependencias instaladas com sucesso!"
