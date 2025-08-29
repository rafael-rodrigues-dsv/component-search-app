#!/bin/bash

# COLETOR DE E-MAILS E CONTATOS (Linux/macOS)
set -e

echo "[INFO] Iniciando Coletor de E-mails e Contatos..."
echo "[INFO] Pasta: $(pwd)"

# Função para verificar versão do Python
check_python_version() {
    local python_cmd=$1
    if command -v "$python_cmd" &> /dev/null; then
        local version=$("$python_cmd" --version 2>&1 | cut -d' ' -f2)
        local major=$(echo "$version" | cut -d'.' -f1)
        local minor=$(echo "$version" | cut -d'.' -f2)
        
        if [[ "$major" -eq 3 && "$minor" -ge 11 ]] || [[ "$major" -gt 3 ]]; then
            echo "[OK] Python $version encontrado via '$python_cmd' - compatível"
            PYTHON_CMD="$python_cmd"
            return 0
        else
            echo "[ERRO] Python $version incompatível - necessário 3.11+"
            return 1
        fi
    fi
    return 1
}

# Verificar Python disponível
if check_python_version "python3" || check_python_version "python"; then
    echo "[OK] Python compatível encontrado"
else
    echo "[ERRO] Python 3.11+ não encontrado"
    echo "[INFO] Por favor, instale Python 3.11+ manualmente:"
    echo "  Ubuntu/Debian: sudo apt update && sudo apt install python3 python3-pip"
    echo "  CentOS/RHEL: sudo yum install python3 python3-pip"
    echo "  macOS: brew install python3"
    exit 1
fi

echo "[INFO] Verificando detalhes do Python..."
"$PYTHON_CMD" --version
PYTHON_EXE=$("$PYTHON_CMD" -c "import sys; print(sys.executable)")
echo "[INFO] Executável Python: $PYTHON_EXE"

echo "[INFO] Verificando e instalando dependências..."
if ! "$PYTHON_CMD" scripts/verificar_instalacao_python.py; then
    echo "[ERRO] Falha na verificação das dependências"
    exit 1
fi

echo "[INFO] Verificando ChromeDriver..."
if ! "$PYTHON_CMD" scripts/verificar_chromedriver.py; then
    echo "[ERRO] ChromeDriver não disponível"
    exit 1
fi

echo "[INFO] Executando programa..."
"$PYTHON_CMD" main.py

echo "[OK] Execução concluída!"