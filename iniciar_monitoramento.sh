#!/bin/bash

clear
echo "========================================"
echo "  MONITOR PYTHONSEARCHAPP - TEMPO REAL"
echo "========================================"
echo
echo "Monitora as 3 funcionalidades do robo:"
echo "  - Coleta de dados (emails/telefones)"
echo "  - Geolocalizacao das empresas"
echo "  - Exportacao de planilha Excel"
echo
echo "Escolha o tipo de monitor:"
echo
echo "[1] Monitor Simples (atualiza a cada 5s)"
echo "[2] Monitor Avancado (metricas completas)"
echo "[3] Sair"
echo

read -p "Digite sua opcao (1-3): " opcao

cd "$(dirname "$0")"

# Ativar ambiente virtual se existir
if [ -f ".venv/bin/activate" ]; then
    echo "[INFO] Ativando ambiente virtual..."
    source .venv/bin/activate
fi

case $opcao in
    1)
        echo
        echo "Iniciando Monitor Simples..."
        python scripts/monitoring/realtime_monitor.py
        ;;
    2)
        echo
        echo "Iniciando Monitor Avancado..."
        python scripts/monitoring/advanced_monitor.py
        ;;
    3)
        echo
        echo "Saindo..."
        exit 0
        ;;
    *)
        echo
        echo "Opcao invalida! Tente novamente."
        read -p "Pressione Enter para continuar..."
        ;;
esac

read -p "Pressione Enter para continuar..."