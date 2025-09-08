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
        
        local patch=$(echo "$version" | cut -d'.' -f3)
        
        if [[ "$major" -eq 3 && "$minor" -gt 13 ]] || [[ "$major" -gt 3 ]]; then
            echo "[OK] Python $version encontrado via '$python_cmd' - compatível"
            PYTHON_CMD="$python_cmd"
            return 0
        elif [[ "$major" -eq 3 && "$minor" -eq 13 && "$patch" -ge 7 ]]; then
            echo "[OK] Python $version encontrado via '$python_cmd' - compatível"
            PYTHON_CMD="$python_cmd"
            return 0
        else
            echo "[ERRO] Python $version incompatível - necessário 3.13.7+"
            return 1
        fi
    fi
    return 1
}

# Verificar Python disponível
if check_python_version "python3" || check_python_version "python"; then
    echo "[OK] Python compatível encontrado"
else
    echo "[INFO] Python 3.13.7+ não encontrado. Tentando instalação automática..."
    
    # Detectar sistema operacional
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        if command -v brew &> /dev/null; then
            echo "[INFO] Instalando Python via Homebrew..."
            brew install python@3.13 || brew install python3
        else
            echo "[INFO] Homebrew não encontrado. Instale manualmente:"
            echo "  1. Instale Homebrew: /bin/bash -c \"\$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)\""
            echo "  2. Execute: brew install python3"
            exit 1
        fi
    elif [[ -f /etc/debian_version ]]; then
        # Ubuntu/Debian
        echo "[INFO] Instalando Python via apt..."
        sudo apt update && sudo apt install -y python3 python3-pip python3-venv
    elif [[ -f /etc/redhat-release ]]; then
        # CentOS/RHEL/Fedora
        echo "[INFO] Instalando Python via yum/dnf..."
        if command -v dnf &> /dev/null; then
            sudo dnf install -y python3 python3-pip
        else
            sudo yum install -y python3 python3-pip
        fi
    else
        echo "[ERRO] Sistema não suportado para instalação automática"
        echo "[INFO] Instale Python 3.13.7+ manualmente e execute novamente"
        exit 1
    fi
    
    # Verificar se instalação funcionou
    if check_python_version "python3" || check_python_version "python"; then
        echo "[OK] Python instalado com sucesso!"
    else
        echo "[ERRO] Falha na instalação do Python"
        exit 1
    fi
fi

echo "[INFO] Verificando detalhes do Python..."
"$PYTHON_CMD" --version
PYTHON_EXE=$("$PYTHON_CMD" -c "import sys; print(sys.executable)")
echo "[INFO] Executável Python: $PYTHON_EXE"

# Verificar se banco de dados existe
if [ ! -f "data/pythonsearch.accdb" ]; then
    echo "[AVISO] Banco de dados não encontrado em data/pythonsearch.accdb"
    echo "[INFO] Recriando ambiente virtual do zero..."
    
    # Deletar ambiente virtual anterior se existir
    if [ -d ".venv" ]; then
        echo "[INFO] Removendo ambiente virtual anterior..."
        rm -rf .venv
    fi
    
    # Criar novo ambiente virtual
    echo "[INFO] Criando novo ambiente virtual..."
    "$PYTHON_CMD" -m venv .venv
else
    echo "[OK] Banco de dados encontrado"
    
    # Criar ambiente virtual se não existir
    if [ ! -d ".venv" ]; then
        echo "[INFO] Criando ambiente virtual..."
        "$PYTHON_CMD" -m venv .venv
    fi
fi

if [ -f ".venv/bin/activate" ]; then
    echo "[INFO] Ativando ambiente virtual..."
    source .venv/bin/activate
fi

echo "[INFO] Verificando e instalando dependências..."
if ! "$PYTHON_CMD" scripts/verification/verify_python_installation.py; then
    echo "[ERRO] Falha na verificação das dependências"
    exit 1
fi

echo "[INFO] Verificando dependências do dashboard web..."
if ! "$PYTHON_CMD" -c "import flask, flask_socketio" &> /dev/null; then
    echo "[INFO] Instalando Flask para dashboard web..."
    "$PYTHON_CMD" -m pip install flask>=3.0.0 flask-socketio>=5.3.0 --quiet
    echo "[OK] Flask instalado com sucesso!"
fi

echo "[INFO] Verificando ChromeDriver..."
if ! "$PYTHON_CMD" scripts/verification/verify_chromedriver.py; then
    echo "[ERRO] ChromeDriver não disponível"
    exit 1
fi

echo "[INFO] Executando programa..."
if "$PYTHON_CMD" main.py; then
    echo "[OK] Execução concluída!"
else
    echo "[ERRO] Programa falhou"
    read -p "Pressione Enter para sair..."
    exit 1
fi