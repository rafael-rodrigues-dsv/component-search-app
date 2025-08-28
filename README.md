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
│   └── services/                     # Serviços de domínio
│       └── email_domain_service.py   # Regras de negócio e validações
├── 🟢 src/application/               # CAMADA DE APLICAÇÃO
│   └── services/                     # Serviços de aplicação
│       ├── email_application_service.py  # Orquestração principal
│       └── user_config_service.py    # Configuração do usuário
├── 🟡 src/infrastructure/            # CAMADA DE INFRAESTRUTURA
│   ├── drivers/                      # Gerenciamento de drivers
│   │   └── chromedriver_manager.py   # Download automático ChromeDriver
│   ├── storage/                      # Gerenciamento de arquivos
│   │   └── data_manager.py           # Limpeza de dados
│   ├── repositories/                 # Persistência
│   │   └── data_repository.py        # JSON e Excel
│   ├── scrapers/                     # Web scraping
│   │   ├── duckduckgo_scraper.py     # Scraper DuckDuckGo
│   │   └── google_scraper.py         # Scraper Google
│   └── web_driver.py                 # Selenium WebDriver
├── ⚙️ config/
│   └── settings.py                   # Configurações centralizadas
├── 💾 data/                          # Dados de controle
│   ├── visited.json                  # Domínios visitados
│   └── emails.json                   # E-mails coletados
├── 📊 output/                        # Arquivos de saída
│   └── empresas.xlsx                 # Planilha Excel
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
- **ChromeDriverManager**: Download automático do ChromeDriver
- **DataManager**: Limpeza e gerenciamento de arquivos
- **GoogleScraper/DuckDuckGoScraper**: Extração de dados
- **JsonRepository/ExcelRepository**: Persistência de dados
- **WebDriverManager**: Controle do navegador Chrome

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

2. **Executar o robô**:
   ```cmd
   python main.py
   ```
   ou
   ```cmd
   iniciar_robo_simples.bat
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

## 📦 Dependências

- **selenium**: Automação web
- **openpyxl**: Manipulação Excel
- **tldextract**: Processamento domínios
- **requests**: Download ChromeDriver

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
├── 📁 unit/                          # Testes unitários
│   ├── 📁 application/services/      # Testes dos serviços de aplicação
│   ├── 📁 domain/                    # Testes da camada de domínio
│   │   ├── 📁 models/                # Testes dos modelos
│   │   ├── 📁 factories/             # Testes das fábricas
│   │   └── 📁 services/              # Testes dos serviços de domínio
│   └── 📁 infrastructure/            # Testes da camada de infraestrutura
├── 📁 integration/                   # Testes de integração
├── 📁 fixtures/                      # Dados de exemplo
├── 📁 utils/                         # Utilitários de teste
├── conftest.py                       # Configuração global pytest
├── pytest.ini                       # Configuração pytest
├── requirements-test.txt             # Dependências de teste
├── .coveragerc                       # Configuração cobertura
├── run_tests.bat                     # Executar testes
└── run_coverage.bat                  # Relatório completo
```

### Executar Testes

#### **Testes básicos:**
```cmd
cd tests
run_tests.bat
```

#### **Cobertura completa:**
```cmd
cd tests
run_coverage.bat
```

#### **Comandos manuais:**
```cmd
cd tests
python -m pytest . --cov=../src --cov-report=html -v
```

### Relatórios de Cobertura

#### **Localização:**
- **HTML**: `tests/htmlcov/index.html` (navegação interativa)
- **XML**: `tests/coverage.xml` (integração CI/CD)
- **Terminal**: exibido durante execução

#### **Interpretação:**
- **Verde**: linhas cobertas pelos testes
- **Vermelho**: linhas não cobertas
- **Percentual**: % de cobertura por arquivo
- **Missing**: números das linhas não testadas

#### **Exemplo de saída:**
```
Name                                   Stmts   Miss  Cover   Missing
------------------------------------------------------------------
src/application/email_application_service.py  95      5    95%   45-47, 89
------------------------------------------------------------------
TOTAL                                         95      5    95%
```

### Adicionar Novos Testes

#### **Teste unitário de domínio:**
```python
# tests/unit/domain/test_email_service.py
class TestEmailValidationService(unittest.TestCase):
    def test_valid_email(self):
        service = EmailValidationService()
        self.assertTrue(service.is_valid_email("test@example.com"))
```

#### **Teste de infraestrutura:**
```python
# tests/unit/infrastructure/test_scrapers.py
class TestGoogleScraper(unittest.TestCase):
    def test_search_success(self):
        scraper = GoogleScraper(mock_driver)
        result = scraper.search("test query")
        self.assertTrue(result)
```

#### **Teste de integração:**
```python
# tests/integration/test_full_flow.py
class TestFullFlow(unittest.TestCase):
    def test_complete_email_collection(self):
        # Teste do fluxo completo
        pass
```

## 🔧 Extensibilidade

### Adicionar novo motor de busca:
1. Crie scraper em `infrastructure/scrapers/`
2. Implemente métodos: `search()`, `get_result_links()`, `extract_company_data()`
3. Adicione opção em `UserConfigService`
4. **Crie testes** em `tests/unit/infrastructure/`

### Adicionar nova validação:
1. Estenda `EmailValidationService` em `domain/email_service.py`
2. Adicione regras específicas conforme necessário
3. **Crie testes** em `tests/unit/domain/`

### Personalizar saída:
1. Modifique `ExcelRepository` em `infrastructure/repositories/`
2. Ajuste formato e colunas conforme necessário
3. **Crie testes** em `tests/unit/infrastructure/`

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
- ✅ **Testes unitários** com cobertura completa
- ✅ **Relatórios de cobertura** HTML e XML
- ✅ **Estrutura de testes** organizada por camadas

## 📊 Qualidade e Testes

### Cobertura de Código
- **EmailApplicationService**: 95%+ de cobertura
- **Testes unitários**: Todas as camadas (Domain, Application, Infrastructure)
- **Mocks completos**: Dependências externas isoladas
- **Fixtures reutilizáveis**: Dados de exemplo padronizados

### Ferramentas de Qualidade
- **pytest**: Framework de testes moderno
- **coverage**: Análise de cobertura de código
- **unittest.mock**: Isolamento de dependências
- **Relatórios HTML**: Visualização interativa da cobertura

### Execução de Testes
```cmd
# Testes rápidos
cd tests && run_tests.bat

# Cobertura completa
cd tests && run_coverage.bat

# Comando manual
python -m pytest tests/ --cov=src --cov-report=html -v
```