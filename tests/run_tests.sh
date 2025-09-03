#!/bin/bash

# EXECUTANDO TESTES COM COBERTURA (Linux/macOS)
set -e

cd "$(dirname "$0")"
echo "========================================"
echo "  EXECUTANDO TESTES COM COBERTURA"
echo "========================================"
echo

# Detectar Python disponível
echo "Verificando Python..."
if command -v python3 &> /dev/null; then
    echo "[OK] Python3 encontrado"
    PYTHON_CMD=python3
elif command -v python &> /dev/null; then
    echo "[OK] Python encontrado"
    PYTHON_CMD=python
else
    echo "ERRO: Python não encontrado"
    exit 1
fi

# Verificar dependências
echo "Verificando dependências..."
if ! $PYTHON_CMD -c "import pytest, coverage" &> /dev/null; then
    echo "Instalando pytest e coverage..."
    $PYTHON_CMD -m pip install pytest pytest-cov coverage
    if [ $? -ne 0 ]; then
        echo "ERRO: Não foi possível instalar dependências"
        exit 1
    fi
fi

echo
echo "Executando testes com cobertura..."
$PYTHON_CMD -m pytest unit/ --cov=../src --cov-report=html:reports/htmlcov --cov-report=term-missing --cov-report=xml:reports/coverage.xml -v

if [ $? -ne 0 ]; then
    echo
    echo "Tentando com unittest..."
    $PYTHON_CMD -m unittest discover unit/ -v
    exit $?
fi

echo
echo "========================================"
echo "  RELATÓRIOS DE COBERTURA GERADOS"
echo "========================================"
echo "HTML: reports/htmlcov/index.html"
echo "XML:  reports/coverage.xml"
echo

if [ -f "reports/htmlcov/index.html" ]; then
    echo "Abrir relatório HTML? (s/n)"
    read -r choice
    if [[ "$choice" == "s" || "$choice" == "S" ]]; then
        # Detectar sistema e abrir navegador
        if command -v xdg-open &> /dev/null; then
            xdg-open reports/htmlcov/index.html
        elif command -v open &> /dev/null; then
            open reports/htmlcov/index.html
        else
            echo "Abra manualmente: reports/htmlcov/index.html"
        fi
    fi
else
    echo "Relatório não foi gerado"
fi

echo
echo "Testes concluídos!"