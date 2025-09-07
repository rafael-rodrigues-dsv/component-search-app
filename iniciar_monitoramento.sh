#!/bin/bash

clear
echo "========================================"
echo "  MONITOR PYTHONSEARCHAPP - TEMPO REAL"
echo "========================================"
echo
echo "Monitora as 5 funcionalidades do robo:"
echo "  - Coleta de dados (emails/telefones)"
echo "  - Enriquecimento CEP (ViaCEP)"
echo "  - Geolocalizacao (Nominatim)"
echo "  - Exportacao Excel"
echo "  - Estatisticas completas"
echo
echo "Iniciando Monitor em Tempo Real..."
echo

cd "$(dirname "$0")"

# Ativar ambiente virtual se existir
if [ -f ".venv/bin/activate" ]; then
    echo "[INFO] Ativando ambiente virtual..."
    source .venv/bin/activate
fi

echo
echo "Iniciando Monitor..."
python scripts/monitoring/realtime_monitor.py

read -p "Pressione Enter para continuar..."