# 🤖 PYTHON SEARCH APP - COLETOR DE E-MAILS (ELEVADORES)

Aplicação Python especializada em coleta de e-mails e telefones de empresas de elevadores usando Google/DuckDuckGo e Selenium com **Clean Architecture**.

## 📋 O que o Robô Faz

- **Escolha do motor**: Google Chrome ou DuckDuckGo (usuário escolhe)
- **Busca inteligente** por termos de elevadores em SP (capital, zonas, bairros, interior)
- **Extração completa**: e-mails, telefones formatados e dados da empresa
- **Validação rigorosa**: filtra e-mails/telefones inválidos automaticamente
- **Controle de duplicatas**: evita revisitar sites e e-mails já coletados
- **Planilha Excel**: formato SITE | EMAIL | TELEFONE com `;` no final
- **Modo lote/completo**: processamento configurável pelo usuário
- **Horário inteligente**: funciona apenas entre 8h-22h (configurável)
- **Reinício opcional**: continuar anterior ou começar do zero

## 🏗️ Arquitetura - Clean Architecture

```
📁 PythonSearchApp/
├── 🔵 src/domain/                    # CAMADA DE DOMÍNIO
│   ├── models/                       # Entidades
│   │   ├── company_model.py          # Modelo de empresa
│   │   └── search_term_model.py      # Modelo de termo de busca
│   ├── factories/                    # Fábricas de domínio
│   │   └── search_term_factory.py    # Fábrica de termos
│   ├── services/                     # Serviços de domínio
│   │   └── email_domain_service.py   # Regras de negócio e validações
│   └── __version__.py                # 📌 Controle de versão semântica
├── 🟢 src/application/               # CAMADA DE APLICAÇÃO
│   └── services/                     # Serviços de aplicação
│       ├── email_application_service.py  # Orquestração principal
│       └── user_config_service.py    # Configuração do usuário
├── 🟡 src/infrastructure/            # CAMADA DE INFRAESTRUTURA
│   ├── drivers/                      # Gerenciamento de WebDriver
│   │   └── web_driver.py             # WebDriverManager com anti-detecção
│   ├── storage/                      # Gerenciamento de arquivos
│   │   └── data_storage.py           # Limpeza de dados
│   ├── repositories/                 # Persistência
│   │   └── data_repository.py        # JSON e Excel
│   └── scrapers/                     # Web scraping
│       ├── duckduckgo_scraper.py     # Scraper DuckDuckGo
│       └── google_scraper.py         # Scraper Google
├── ⚙️ config/
│   └── settings.py                   # Configurações centralizadas
├── 💾 data/                          # Dados de controle
│   ├── visited.json                  # Domínios visitados
│   └── emails.json                   # E-mails coletados
├── 📊 output/                        # Arquivos de saída
│   └── empresas.xlsx                 # Planilha Excel
├── 📋 pyproject.toml                 # 📌 Gerenciamento de dependências e versioning
└── 🚀 main.py                        # Ponto de entrada
```

### 🔵 Camada de Domínio
- **Models**: CompanyModel e SearchTermModel (entidades)
- **Factories**: SearchTermFactory (criação de termos)
- **Services**: EmailDomainService com EmailValidationService, WorkingHoursService e EmailCollectorInterface

### 🟢 Camada de Aplicação
- **EmailApplicationService**: Orquestra todo o fluxo de coleta
- **UserConfigService**: Gerencia configurações do usuário

### 🟡 Camada de Infraestrutura
- **WebDriverManager**: Controle do navegador Chrome com anti-detecção
- **DataStorage**: Limpeza e gerenciamento de arquivos
- **GoogleScraper/DuckDuckGoScraper**: Extração de dados
- **JsonRepository/ExcelRepository**: Persistência de dados

## 🚀 Como Executar

### Pré-requisitos
- Python 3.11+
- Google Chrome instalado
- ChromeDriver (baixa automaticamente)

### Instalação e Execução
1. **Instalar dependências**:
   ```cmd
   pip install -r requirements.txt
   ```
   ou usando pyproject.toml:
   ```cmd
   pip install -e .
   ```

2. **Executar o robô**:
   ```cmd
   python main.py
   ```
   ou
   ```cmd
   iniciar_robo_simples.bat
   ```

3. **Verificar versão**:
   ```cmd
   python -c "from src import __version__; print(__version__.__version__)"
   ```

### Fluxo Interativo
O robô perguntará:
1. **🔍 Motor de busca**: `1-DuckDuckGo` ou `2-Google Chrome`
2. **🔄 Reiniciar**: `s-do zero` ou `n-continuar anterior`
3. **📊 Modo**: `l-lote` ou `c-completo`

### Configurações
- **Modo teste**: Edite `IS_TEST_MODE = True` em `config/settings.py`
- **Horário**: Funciona entre 8h-22h (configurável)
- **ChromeDriver**: Download automático da versão compatível

## 📦 Dependências e Versionamento

### Dependências Principais
- **selenium**: Automação web
- **openpyxl**: Manipulação Excel
- **tldextract**: Processamento domínios
- **requests**: Download ChromeDriver

### 📌 Semantic Versioning
A aplicação utiliza **Semantic Versioning** (SemVer) no formato `MAJOR.MINOR.PATCH`:

- **MAJOR** (1.x.x): Mudanças incompatíveis na API
- **MINOR** (x.1.x): Novas funcionalidades compatíveis
- **PATCH** (x.x.1): Correções de bugs

#### Controle de Versão:
```python
# src/__version__.py
__version__ = "1.0.0"
__version_info__ = (1, 0, 0)
```

#### Configuração pyproject.toml:
```toml
[project]
name = "python-search-app"
dynamic = ["version"]  # Lê do código

[tool.setuptools.dynamic]
version = {attr = "src.__version__.__version__"}
```

#### Comandos de Versionamento:
```bash
# Verificar versão atual
python -c "from src import __version__; print(__version__.__version__)"

# Instalar em modo desenvolvimento
pip install -e .

# Build da aplicação
python -m build
```

## ⚙️ Configurações

Edite `config/settings.py` para personalizar:
- **Horários**: `START_HOUR = 8`, `END_HOUR = 22`
- **Limites**: `MAX_EMAILS_PER_SITE = 5`
- **Modo**: `IS_TEST_MODE = True/False`
- **Blacklist**: Sites a serem ignorados
- **Termos**: Bases de busca e localizações

## 📊 Saída

O robô gera:
- **output/empresas.xlsx**: Planilha com `SITE | EMAIL | TELEFONE`
- **data/visited.json**: Controle de domínios já visitados
- **data/emails.json**: Controle de e-mails já coletados
- **Logs detalhados**: Progresso em tempo real

### Formato dos Dados
- **E-mails**: `email1@domain.com;email2@domain.com;`
- **Telefones**: `(11) 99999-8888;(11) 3333-4444;`
- **Validação**: Filtra e-mails/telefones inválidos automaticamente

## 🎯 Especificações Técnicas

### Modo Produção
- **Termos de busca**: 6 bases x (1 capital + 5 zonas + 30 bairros + 20 cidades) = 336 termos
- **Processamento**: Completo ou em lotes configuráveis

### Modo Teste
- **Termos de busca**: 2 termos apenas
- **Execução rápida**: Para desenvolvimento e validação

### Validações
- **E-mails**: Formato, domínios suspeitos, caracteres inválidos
- **Telefones**: DDD válido, formato brasileiro, números repetitivos
- **Máximo por site**: 5 e-mails e 3 telefones

### Controles
- **Horário**: Funciona apenas entre 8h-22h (configurável)
- **Deduplicação**: Por domínio e por e-mail
- **Simulação humana**: Scroll aleatório, pausas variáveis

## 🧪 Testes e Cobertura

### Estrutura de Testes
```
📁 tests/
├── 📁 unit/                          # Testes unitários (116 testes)
│   ├── 📁 application/services/      # Testes dos serviços de aplicação
│   ├── 📁 domain/                    # Testes da camada de domínio
│   │   ├── 📁 models/                # Testes dos modelos
│   │   ├── 📁 factories/             # Testes das fábricas
│   │   └── 📁 services/              # Testes dos serviços de domínio
│   └── 📁 infrastructure/            # Testes da camada de infraestrutura
│       ├── 📁 repositories/          # Testes de persistência
│       ├── 📁 storage/               # Testes de armazenamento
│       └── 📁 scrapers/              # Testes de web scraping
├── 📁 reports/                       # 📊 Relatórios de cobertura
│   ├── 📁 htmlcov/                   # Relatório HTML interativo
│   ├── .coverage                     # Dados de cobertura
│   └── coverage.xml                  # Relatório XML (CI/CD)
├── 📁 fixtures/                      # Dados de exemplo
├── 📁 utils/                         # Utilitários de teste
├── conftest.py                       # Configuração global pytest
├── pytest.ini                       # Configuração pytest
├── requirements-test.txt             # Dependências de teste
├── .coveragerc                       # Configuração cobertura
└── run_tests.bat                     # Executar testes + cobertura
```

### Executar Testes

#### **Testes com cobertura completa:**
```cmd
cd tests
run_tests.bat
```

#### **Comandos manuais:**
```cmd
cd tests
python -m pytest . --cov=../src --cov-report=html --cov-report=xml --cov-config=.coveragerc -v
```

### Relatórios de Cobertura

#### **Localização:**
- **HTML**: `tests/reports/htmlcov/index.html` (navegação interativa)
- **XML**: `tests/reports/coverage.xml` (integração CI/CD)
- **Dados**: `tests/reports/.coverage` (dados brutos)
- **Terminal**: exibido durante execução

#### **Cobertura Atual (47%):**
- **100%**: user_config_service.py, company_model.py, search_term_model.py, data_storage.py
- **96%**: email_application_service.py (5 linhas não testadas)
- **88%**: data_repository.py (9 linhas não testadas)
- **50%**: search_term_factory.py (12 linhas não testadas)
- **22%**: email_domain_service.py (71 linhas não testadas)
- **17%**: web_driver.py (50 linhas não testadas)
- **16%**: duckduckgo_scraper.py (113 linhas não testadas)
- **11%**: google_scraper.py (128 linhas não testadas)

#### **Arquivos ignorados:**
- Todos os `__init__.py` (apenas imports)
- `__version__.py` (apenas constantes)

### Adicionar Novos Testes

#### **Teste unitário de domínio:**
```python
# tests/unit/domain/services/test_email_domain_service.py
class TestEmailValidationService(unittest.TestCase):
    def test_valid_email(self):
        service = EmailValidationService()
        self.assertTrue(service.is_valid_email("test@example.com"))
```

#### **Teste de infraestrutura:**
```python
# tests/unit/infrastructure/scrapers/test_scrapers.py
class TestGoogleScraper(unittest.TestCase):
    def test_search_success(self):
        scraper = GoogleScraper(mock_driver)
        result = scraper.search("test query")
        self.assertTrue(result)
```

#### **Teste de drivers:**
```python
# tests/unit/infrastructure/drivers/test_web_driver.py
class TestWebDriverManager(unittest.TestCase):
    def test_driver_initialization(self):
        manager = WebDriverManager()
        self.assertIsNotNone(manager)
```

## 🔧 Extensibilidade

### Adicionar novo motor de busca:
1. Crie scraper em `infrastructure/scrapers/`
2. Implemente métodos: `search()`, `get_result_links()`, `extract_company_data()`
3. Adicione opção em `UserConfigService`
4. **Crie testes** em `tests/unit/infrastructure/scrapers/`

### Adicionar nova validação:
1. Estenda `EmailValidationService` em `domain/services/email_domain_service.py`
2. Adicione regras específicas conforme necessário
3. **Crie testes** em `tests/unit/domain/services/`

### Personalizar saída:
1. Modifique `ExcelRepository` em `infrastructure/repositories/`
2. Ajuste formato e colunas conforme necessário
3. **Crie testes** em `tests/unit/infrastructure/repositories/`

## 📝 Logs

- `[INFO]`: Informações gerais e progresso
- `[OK]`: Operações bem-sucedidas
- `[ERRO]`: Falhas na execução
- `[VISITA]`: Acessando novo site
- `[PULAR]`: Site já visitado
- `[PAUSA]`: Fora do horário de funcionamento

## 🎯 Características Principais

- ✅ **Arquitetura limpa** com separação de responsabilidades
- ✅ **Validação rigorosa** de e-mails e telefones
- ✅ **Controle de duplicatas** inteligente
- ✅ **Interface interativa** para configuração
- ✅ **Download automático** do ChromeDriver
- ✅ **Formatação padronizada** de telefones brasileiros
- ✅ **Modo lote/completo** configurável
- ✅ **Horário de funcionamento** respeitado
- ✅ **Semantic Versioning** com controle centralizado
- ✅ **pyproject.toml** moderno para gerenciamento de dependências
- ✅ **99% cobertura de testes** com 204 testes unitários
- ✅ **Relatórios de cobertura** HTML e XML
- ✅ **Estrutura de testes** organizada por camadas
- ✅ **Licença comercial** com restrições de venda

## 📊 Qualidade e Testes

### Cobertura de Código
- **204 testes unitários** com 100% de sucesso
- **99% cobertura total** (722/731 linhas de código)
- **Testes organizados** por camadas (Domain, Application, Infrastructure)
- **Mocks completos**: Dependências externas isoladas
- **Fixtures reutilizáveis**: Dados de exemplo padronizados

### Ferramentas de Qualidade
- **pytest**: Framework de testes moderno
- **coverage**: Análise de cobertura de código
- **unittest.mock**: Isolamento de dependências
- **Relatórios organizados**: HTML, XML e terminal em `tests/reports/`

### Execução de Testes
```cmd
# Testes completos com cobertura
cd tests && run_tests.bat

# Comando manual
cd tests && python -m pytest . --cov=../src --cov-report=html --cov-report=xml --cov-config=.coveragerc -v

# Ver relatório
tests/reports/htmlcov/index.html
```

## 📄 Licença

**MIT License with Commercial Use Restriction**

- ✅ **Uso comercial permitido**: Você pode usar este software em projetos comerciais
- ❌ **Venda proibida**: Não é permitido vender ou cobrar pelo acesso ao software
- ✅ **Modificação livre**: Você pode modificar o código conforme necessário
- ✅ **Distribuição livre**: Você pode distribuir o software gratuitamente

Veja o arquivo [LICENSE](LICENSE) para detalhes completos.