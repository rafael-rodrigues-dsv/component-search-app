# 📁 Scripts - PythonSearchApp

## 📋 Organização

### 🗄️ **database/** - Scripts de Banco de Dados
- `create_db_simple.py` - Criador automático do banco Access
- `load_initial_data.py` - Carregador de dados completos do settings.py

### ⚙️ **setup/** - Scripts de Configuração
- `criar_banco.bat` - Automatização completa da criação do banco
- `instalar_dependencias.bat` - Instala todas as dependências Python

### 🔧 **utils/** - Utilitários
- `export_excel.py` - Exporta dados do banco para Excel
- `reset_data.py` - Reset dos dados coletados (mantém configurações)
- `show_stats.py` - Mostra estatísticas detalhadas do banco

### ✅ **verification/** - Verificação de Instalação
- `verificar_instalacao_python.py` - Verifica Python e dependências
- `verificar_instalacao_chrome.py` - Verifica Chrome e WebDriver
- `verificar_instalacao_brave.py` - Verifica Brave e WebDriver
- `verificar_chromedriver.py` - Baixa ChromeDriver automaticamente
- `baixar_python.py` - Baixa e instala Python 3.13.7

## 🚀 Como Usar

### **Primeira Configuração**
```cmd
# 0. Instalar dependências (se necessário)
scripts\setup\instalar_dependencias.bat

# 1. Criar banco Access
scripts\setup\criar_banco.bat

# 2. Carregar dados completos (opcional)
python scripts\database\load_initial_data.py
```

### **Verificação de Instalação**
```cmd
# Verificar Python
python scripts\verification\verificar_instalacao_python.py

# Verificar Chrome
python scripts\verification\verificar_instalacao_chrome.py

# Verificar Brave
python scripts\verification\verificar_instalacao_brave.py

# Baixar ChromeDriver
python scripts\verification\verificar_chromedriver.py
```

### **Utilitários Durante o Uso**
```cmd
# Ver estatísticas
python scripts\utils\show_stats.py

# Exportar para Excel
python scripts\utils\export_excel.py

# Reset dos dados
python scripts\utils\reset_data.py
```

## 📊 Fluxo Recomendado

1. **Setup inicial:** `scripts\setup\criar_banco.bat`
2. **Dados completos:** `python scripts\database\load_initial_data.py`
3. **Executar robô:** `iniciar_robo_simples.bat`
4. **Ver progresso:** `python scripts\utils\show_stats.py`
5. **Exportar dados:** `python scripts\utils\export_excel.py`

## ⚠️ Importante

- Scripts em `database/` e `utils/` são **Python** - executar com `python`
- Scripts em `setup/` são **Batch** - executar diretamente
- Todos os scripts ajustam automaticamente os caminhos relativos
- **Não mover** arquivos do `src/` - apenas scripts de automação