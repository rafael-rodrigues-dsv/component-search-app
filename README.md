# 🤖 PYTHON SEARCH APP v3.0.0 - COLETOR DE E-MAILS E CONTATOS COM GEOLOCALIZAÇÃO

Aplicação Python para coleta de e-mails, telefones e localização de empresas usando Google/DuckDuckGo e Selenium com **Clean Architecture** e **Sistema de Controle de Geolocalização**.

## 📋 O que a Aplicação Faz

| Funcionalidade                 | Descrição                                                     |
|--------------------------------|---------------------------------------------------------------|
| **🌐 Detecção automática**     | Verifica Chrome e Brave instalados automaticamente            |
| **🔍 Escolha do motor**        | Google ou DuckDuckGo (usuário escolhe)                        |
| **🎯 Busca inteligente**       | Termos configuráveis por localização e segmento               |
| **📧 Extração completa**       | E-mails, telefones formatados e dados da empresa              |
| **📍 Geolocalização seletiva** | Extrai endereços reais do HTML e calcula distâncias precisas  |
| **✅ Validação rigorosa**       | Filtra e-mails/telefones inválidos automaticamente            |
| **🚫 Controle de duplicatas**  | Evita revisitar sites e e-mails já coletados                  |
| **📊 Planilha Excel**          | Formato SITE \| EMAIL \| TELEFONE \| ENDEREÇO \| DISTÂNCIA_KM |
| **⚙️ Modo lote/completo**      | Processamento configurável pelo usuário                       |

| **🔄 Reinício opcional**      | Continuar anterior ou começar do zero |

## 🏗️ Arquitetura v3.0.0 - Clean Architecture + Controle de Geolocalização

```
📁 PythonSearchApp/
├── 🔵 src/domain/                    # CAMADA DE DOMÍNIO
│   ├── models/                       # Entidades e modelos
│   │   ├── company_model.py          # Modelo de empresa
│   │   ├── search_term_model.py      # Modelo de termo de busca
│   │   ├── collection_result_model.py # Resultado da coleta
│   │   ├── collection_stats_model.py  # Estatísticas da coleta
│   │   ├── term_result_model.py      # Resultado por termo
│   │   ├── performance_metric_model.py # Métricas de performance
│   │   └── retry_config_model.py     # Configuração de retry
│   ├── factories/                    # Fábricas de domínio
│   │   └── search_term_factory.py    # Fábrica de termos
│   ├── protocols/                    # Interfaces e contratos
│   │   └── scraper_protocol.py       # Interface para scrapers
│   └── services/                     # Serviços de domínio
│       └── email_domain_service.py   # Regras de negócio e validações
├── 🟢 src/application/               # CAMADA DE APLICAÇÃO
│   └── services/                     # Serviços de aplicação
│       ├── email_application_service.py  # Orquestração principal
│       └── user_config_service.py    # Configuração do usuário
├── 🟡 src/infrastructure/            # CAMADA DE INFRAESTRUTURA
│   ├── config/                       # Gerenciamento de configuração
│   │   └── config_manager.py         # ConfigManager YAML/JSON
│   ├── drivers/                      # Gerenciamento de WebDriver
│   │   └── web_driver.py             # WebDriverManager com anti-detecção
│   ├── logging/                      # Sistema de logging
│   │   └── structured_logger.py      # Logger estruturado contextual
│   ├── metrics/                      # Métricas e performance
│   │   └── performance_tracker.py    # Rastreamento de performance
│   ├── network/                      # Rede e retry
│   │   └── retry_manager.py          # Gerenciador de retry com backoff
│   ├── repositories/                 # Persistência
│   │   └── access_repository.py      # Banco Access
│   ├── scrapers/                     # Web scraping
│   │   ├── duckduckgo_scraper.py     # Scraper DuckDuckGo
│   │   └── google_scraper.py         # Scraper Google
│   └── storage/                      # Gerenciamento de arquivos
│       └── data_storage.py           # Limpeza de dados
├── 🌐 src/infrastructure/services/   # Serviços de infraestrutura
│   └── geolocation_service.py        # Serviço de geolocalização
├── 📜 src/resources/                 # Recursos e configurações
│   └── application.yaml              # Configuração principal YAML
├── 📌 src/__version__.py               # Controle de versão dinâmico
├── ⚙️ config/
│   └── settings.py                   # Configurações legadas
├── 💾 data/                          # Dados de runtime (ignorado no Git)
│   └── pythonsearch.accdb            # Banco Access principal
├── 📊 output/                        # Arquivos de saída (ignorado no Git)
│   └── empresas.xlsx                 # Planilha Excel
├── 🧪 tests/                         # Testes unitários (95% coverage)
│   ├── unit/                         # Testes por camada
│   │   └── infrastructure/services/  # Testes do GeolocationService
│   ├── reports/                      # Relatórios de coverage
│   ├── run_tests.bat                # Script de execução de testes

├── 📋 pyproject.toml                 # Gerenciamento de dependências
└── 🚀 main.py                        # Ponto de entrada
```

## 🚀 Como Executar

### Pré-requisitos

- Python 3.13+ (baixa automaticamente se necessário)
- **Microsoft Access** (para banco de dados)
- **Pelo menos um navegador suportado:**
    - Google Chrome **OU** Brave Browser
- ChromeDriver (baixa automaticamente)

### Instalação e Execução

**1️⃣ Primeiro: Criar Banco Access**

```cmd
scripts\setup\create_database.bat (Windows)
scripts/setup/create_database.sh (Linux/macOS)
```

[![Criar Banco](https://img.shields.io/badge/🗄️-Criar%20Banco%20Access-orange?style=for-the-badge)](scripts/setup/create_database.bat)

**2️⃣ Carregar Dados Iniciais (Opcional)**

```cmd
python scripts\database\load_initial_data.py
```

**3️⃣ Configurar CEP de Referência (Opcional)**

Edite `config/settings.py`:

```python
# CEP de referência para cálculo de distâncias
REFERENCE_CEP = "01310-100"  # Seu CEP de referência
```

**4️⃣ Executar Robô**

```cmd
iniciar_robo_simples.bat
```

[![Executar Robô](https://img.shields.io/badge/▶️-Executar%20Robô-blue?style=for-the-badge)](iniciar_robo_simples.bat)

### 🛠️ Scripts Utilitários

```cmd
# Ver estatísticas
python scripts\utils\show_stats.py

# Exportar Excel (com geolocalização)
python scripts\utils\export_excel.py

# Reset dados
python scripts\utils\reset_data.py

# Executar todos os testes
run_tests.bat
```

### Fluxo Interativo v3.0.0

A aplicação:

1. **🌐 Verifica navegadores**: Detecta automaticamente Chrome e/ou Brave
2. **📋 Menu principal**: Escolha da funcionalidade desejada
   - **[1] Coleta de dados** (e-mails e telefones)
   - **[2] Geolocalização** das empresas
   - **[3] Exportar Excel** com dados completos
3. **⚙️ Configurações automáticas**: Motor de busca e modo são configurados durante a coleta
4. **🔄 Reset opcional**: Pergunta sobre reset apenas na opção de coleta

### Configurações

- **Modo teste**: Edite `IS_TEST_MODE = True` em `config/settings.py`
- **CEP referência**: Configure `REFERENCE_CEP` em `config/settings.py`
- **ChromeDriver**: Download automático da versão compatível

## 🛠️ Tecnologias Utilizadas

| Tecnologia             | Descrição                                            | Versão        |
|------------------------|------------------------------------------------------|---------------|
| **Python**             | Linguagem de programação principal                   | 3.13+         |
| **PyODBC**             | Conector para Microsoft Access                       | ≥4.0.0        |
| **Microsoft Access**   | Sistema de banco de dados                            | 2016+         |
| **Selenium**           | Automação de navegadores web                         | ≥4.0.0        |
| **OpenPyXL**           | Manipulação de arquivos Excel (.xlsx)                | ≥3.0.0        |
| **TLDExtract**         | Extração e processamento de domínios                 | ≥3.0.0        |
| **Requests**           | Cliente HTTP para download de drivers                | ≥2.25.0       |
| **PyYAML**             | Parser e gerador de arquivos YAML                    | ≥6.0          |
| **Requests**           | Cliente HTTP para APIs de geolocalização             | ≥2.32.4       |
| **Pytest**             | Framework de testes unitários                        | ≥7.0.0        |
| **Pytest-Cov**         | Plugin de coverage para pytest                       | ≥4.0.0        |
| **Coverage**           | Medição de cobertura de código                       | ≥7.0.0        |
| **Google Chrome**      | Navegador para automação web (opcional)              | Última versão |
| **Brave Browser**      | Navegador alternativo baseado em Chromium (opcional) | Última versão |
| **ChromeDriver**       | Driver para controle dos navegadores                 | Auto-download |
| **Nominatim API**      | Geocodificação gratuita (OpenStreetMap)              | Gratuita      |
| **ViaCEP API**         | Consulta de CEPs brasileiros                         | Gratuita      |
| **Clean Architecture** | Padrão arquitetural                                  | -             |
| **SOLID Principles**   | Princípios de design de software                     | -             |
| **Type Hints**         | Tipagem estática para Python                         | Built-in      |
| **Dataclasses**        | Classes de dados estruturadas                        | Built-in      |

## ⚙️ Configurações

Edite `config/settings.py` para personalizar:

- **Navegadores**: Detecção automática de Chrome e Brave
- **Limites**: `MAX_EMAILS_PER_SITE = 5`
- **Modo**: `IS_TEST_MODE = True/False`
- **Geolocalização**: `REFERENCE_CEP` para cálculo de distâncias
- **Blacklist**: Sites a serem ignorados
- **Termos**: Bases de busca e localizações

## 📊 Saída

A aplicação gera:

- **data/pythonsearch.accdb**: Banco Access com dados estruturados e geolocalização
- **output/empresas.xlsx**: Planilha com `SITE | EMAIL | TELEFONE | ENDEREÇO | DISTÂNCIA_KM` (ordenada por proximidade)
- **Logs detalhados**: Progresso em tempo real com informações de geolocalização

### 🗄️ **Banco Access v3.0.0 (Principal)**

- Dados normalizados em **10 tabelas** (incluindo TB_GEOLOCALIZACAO)
- **Controle de geolocalização independente** com status e histórico
- Coordenadas geográficas e cálculo de distâncias
- **Replicação automática** entre tabelas
- Consultas avançadas e relatórios
- Auditoria completa e logs detalhados

### 📋 **Excel (Compatibilidade)**

- Formato atual mantido para usuário final
- Gerado automaticamente do banco
- Para copiar/colar onde quiser

### Formato dos Dados

- **E-mails**: `email1@domain.com;email2@domain.com;`
- **Telefones**: `(11) 99999-8888;(11) 3333-4444;`
- **Endereços**: `Rua Augusta, 123, Consolação, São Paulo, SP`
- **Distâncias**: `5.2` (em quilômetros do ponto de referência)
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
- **Endereços**: Extração seletiva - só geocodifica endereços reais encontrados no HTML
- **Coordenadas**: Geocodificação via Nominatim (OpenStreetMap) com precisão ±10-50m para endereços completos
- **Distâncias**: Calculadas usando **Fórmula de Haversine** - método matemático que calcula a distância entre dois
  pontos na superfície terrestre considerando a curvatura da Terra, fornecendo precisão em quilômetros
- **Máximo por site**: 5 e-mails e 3 telefones

### Controles

- **Deduplicação**: Por domínio e por e-mail
- **Geolocalização**: Rate limiting 1s/request, só processa endereços reais do HTML
- **Simulação humana**: Scroll aleatório, pausas variáveis

### ⚡ Performance por Motor de Busca

| Motor             | Tempo/Empresa | 50 Registros  | Vantagens                                                                                                               | Desvantagens                                                                             |
|-------------------|---------------|---------------|-------------------------------------------------------------------------------------------------------------------------|------------------------------------------------------------------------------------------|
| **🦆 DuckDuckGo** | **3-5s**      | **~2.5-4min** | ✅ **4x mais rápido**<br>✅ Sem CAPTCHA<br>✅ Performance máxima<br>✅ Delays mínimos<br>✅ Ideal para grandes volumes       | ⚠️ Menos resultados por termo<br>⚠️ Qualidade variável<br>⚠️ Sem proteção anti-detecção  |
| **🔍 Google**     | **12-18s**    | **~10-15min** | ✅ **Mais resultados**<br>✅ Melhor qualidade<br>✅ Anti-detecção completa<br>✅ Comportamento humano<br>✅ Proteção CAPTCHA | ⚠️ 4x mais lento<br>⚠️ Risco de bloqueio<br>⚠️ Pausas de sessão<br>⚠️ Complexidade maior |

**Recomendação**:

- **DuckDuckGo**: Para coletas rápidas e grandes volumes (50+ empresas)
- **Google**: Para qualidade máxima e proteção contra detecção prolongada

### 🌍 Precisão da Geolocalização

| Cenário               | Precisão | Exemplo                               |
|-----------------------|----------|---------------------------------------|
| **Endereço completo** | ±10-50m  | "Rua Augusta, 123, Consolação, SP"    |
| **Cidade/bairro**     | ±2-5km   | "Moema, São Paulo" (centro do bairro) |
| **Sem endereço**      | -        | Não geocodifica (sem fallback)        |

## 📝 Logs

- `[INFO]`: Informações gerais e progresso
- `[OK]`: Operações bem-sucedidas
- `[ERRO]`: Falhas na execução
- `[VISITA]`: Acessando novo site
- `[PULAR]`: Site já visitado
- `[GEO]`: Processando geolocalização

## 📄 Licença

**Creative Commons Attribution-NonCommercial 4.0 International (CC BY-NC 4.0)**

- ✅ **Compartilhamento livre**: Copie e redistribua em qualquer formato
- ✅ **Adaptação permitida**: Modifique, transforme e crie derivações
- ✅ **Atribuição obrigatória**: Dê crédito ao autor original
- ❌ **Uso comercial proibido**: Não pode ser usado para fins comerciais
- 🛡️ **Proteção contra patentes**: Publicado como arte anterior

Veja o arquivo [LICENSE](LICENSE) para detalhes completos.