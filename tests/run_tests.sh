#!/bin/bash

# EXECUTANDO TESTES COM COBERTURA (Linux/macOS)
set -e

cd "$(dirname "$0")"
echo "========================================"
echo "  EXECUTANDO TESTES COM COBERTURA"
echo "========================================"
echo

# Função para verificar Python
check_python() {
    local python_cmd=$1
    if command -v "$python_cmd" &> /dev/null; then
        if $python_cmd -c "import pytest, coverage" &> /dev/null; then
            echo "[OK] $python_cmd com pytest e coverage encontrado"
            PYTHON_CMD=$python_cmd
            return 0
        fi
    fi
    return 1
}

# Verificar dependências
echo "Verificando dependências..."
if check_python "python3"; then
    :
elif check_python "python"; then
    :
else
    echo "Instalando pytest e coverage..."
    if command -v python3 &> /dev/null; then
        python3 -m pip install -r requirements-test.txt
        PYTHON_CMD=python3
    elif command -v python &> /dev/null; then
        python -m pip install -r requirements-test.txt
        PYTHON_CMD=python
    else
        echo "ERRO: Python não encontrado"
        exit 1
    fi
fi

echo
echo "Executando testes com cobertura..."
$PYTHON_CMD -m pytest . --cov=../src --cov-report=html --cov-report=term-missing --cov-report=xml --cov-config=.coveragerc -v

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