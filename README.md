# 🤖 PYTHON SEARCH APP v4.0.0 - COLETOR DE E-MAILS E CONTATOS COM DESCOBERTA GEOGRÁFICA DINÂMICA

Aplicação Python para coleta de e-mails, telefones e geolocalização de empresas usando Google/DuckDuckGo e Selenium com **Clean Architecture**, **Endereços Estruturados Normalizados** e **Descoberta Geográfica 100% Automática**.

## 📋 O que a Aplicação Faz

| Funcionalidade                 | Descrição                                                     |
|--------------------------------|---------------------------------------------------------------|
| **🌐 Detecção automática**     | Verifica Chrome e Brave instalados automaticamente            |
| **🔍 Escolha do motor**        | Google ou DuckDuckGo (usuário escolhe)                        |
| **🚀 Descoberta geográfica**   | **NOVO**: Descobre cidades e bairros automaticamente via CEP  |
| **🏛️ Perfis inteligentes**    | **NOVO**: Detecta região metropolitana/rural automaticamente  |
| **🎯 Busca inteligente**       | Termos gerados dinamicamente por localização descoberta      |
| **📧 Extração completa**       | E-mails, telefones formatados e dados da empresa              |
| **🏠 Endereços estruturados**  | TB_ENDERECOS normalizada com logradouro, número, bairro, etc  |
| **🎆 Enriquecimento CEP**      | **NOVO**: Processo separado para enriquecer via ViaCEP       |
| **📍 Geolocalização avançada** | Fallback progressivo: endereço → CEP → bairro → cidade        |
| **✅ Validação rigorosa**       | Filtra e-mails/telefones inválidos automaticamente            |
| **🚫 Controle de duplicatas**  | Evita revisitar sites e endereços duplicados                  |
| **📊 Planilha Excel**          | Formato SITE \| EMAIL \| TELEFONE \| ENDEREÇO \| DISTÂNCIA_KM |
| **🎛️ Menu otimizado**        | **NOVO**: 4 opções focadas + dashboard integrado            |
| **📊 Dashboard Web Integrado** | **NOVO**: Interface AdminLTE com métricas em tempo real     |
| **⚙️ Modo completo**           | Processamento completo de todos os resultados                |
| **🔄 Reinício opcional**      | Continuar anterior ou começar do zero                        |

## 🏗️ Arquitetura v4.0.0 - Clean Architecture + Descoberta Geográfica Dinâmica

```
📁 PythonSearchApp/
├── 🔵 src/domain/                    # CAMADA DE DOMÍNIO
│   ├── models/                       # Entidades e modelos
│   │   ├── address_model.py          # Modelo de endereço estruturado
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
│       ├── address_enrichment_service.py # **NOVO**: Enriquecimento de endereços
│       ├── database_domain_service.py    # Serviços de banco de domínio
│       ├── email_domain_service.py       # Regras de negócio e validações
│       └── geolocation_domain_service.py # Serviços de geolocalização
├── 🟢 src/application/               # CAMADA DE APLICAÇÃO
│   └── services/                     # Serviços de aplicação
│       ├── address_enrichment_application_service.py # **NOVO**: Enriquecimento de endereços
│       ├── cep_enrichment_application_service.py    # **NOVO**: Enriquecimento via CEP
│       ├── database_service.py                      # Serviço de banco de dados
│       ├── email_application_service.py             # Orquestração principal
│       ├── excel_application_service.py             # Exportação Excel
│       ├── geolocation_application_service.py      # Processamento geolocalização
│       └── user_config_service.py                   # Configuração do usuário
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
│   │   ├── access_repository.py      # Banco Access (Singleton)
│   │   └── data_repository.py        # Repositório de dados
│   ├── scrapers/                     # Web scraping
│   │   ├── duckduckgo_scraper.py     # Scraper DuckDuckGo
│   │   └── google_scraper.py         # Scraper Google
│   ├── services/                     # Serviços de infraestrutura
│   │   ├── capital_cep_validator.py      # **NOVO**: Validador de CEP de capital
│   │   ├── cities_cache_service.py       # **NOVO**: Cache local de cidades
│   │   ├── dynamic_geographic_discovery_service.py # **NOVO**: Descoberta geográfica
│   │   └── geolocation_service.py        # Serviço de geolocalização
│   ├── storage/                      # Gerenciamento de arquivos
│   │   └── data_storage.py           # Limpeza de dados
│   ├── utils/                        # Utilitários
│   │   └── address_extractor.py      # Extrator de endereços estruturados
│   └── web/                          # **NOVO**: Dashboard Web
│       ├── dashboard_server.py       # Servidor Flask com WebSocket
│       ├── templates/
│       │   └── dashboard.html        # Interface AdminLTE
│       └── static/
│           └── dashboard.css         # Estilos customizados
├── 📜 src/resources/                 # Recursos e configurações
│   └── application.yaml              # Configuração principal YAML
├── 📌 src/__version__.py               # Controle de versão dinâmico
├── ⚙️ config/
│   └── settings.py                   # Configurações legadas
├── 💾 data/                          # Dados de runtime (ignorado no Git)
│   └── pythonsearch.accdb            # Banco Access principal
├── 📊 output/                        # Arquivos de saída (ignorado no Git)
│   └── empresas.xlsx                 # Planilha Excel
├── 📜 scripts/                       # Scripts utilitários
│   ├── database/                     # Scripts de banco
│   │   ├── create_db_simple.py       # Criação do banco Access
│   │   └── load_initial_data.py      # Carregamento de dados iniciais
│   ├── monitoring/                   # Monitores
│   │   ├── advanced_monitor.py       # Monitor avançado
│   │   └── realtime_monitor.py       # Monitor em tempo real
│   ├── setup/                        # Scripts de instalação
│   ├── utils/                        # Utilitários
│   └── verification/                 # Scripts de verificação
├── 🧪 tests/                         # Testes unitários (95% coverage)
│   ├── unit/                         # Testes por camada
│   │   ├── domain/                   # Testes de domínio
│   │   ├── application/              # Testes de aplicação
│   │   └── infrastructure/           # Testes de infraestrutura
│   ├── reports/                      # Relatórios de coverage
│   └── run_tests.bat                # Script de execução de testes

├── 📋 pyproject.toml                 # Gerenciamento de dependências
└── 🚀 main.py                        # Ponto de entrada
```

## 🆕 Novidades da Versão 4.0.0

### 🚀 **Descoberta Geográfica Dinâmica**
- **100% Automática**: Descobre cidades e bairros baseado no seu CEP de referência
- **Perfis Inteligentes**: Detecta automaticamente se é região metropolitana ou rural
- **APIs Oficiais**: Integração com ViaCEP, IBGE e Nominatim
- **Cache Local**: Performance otimizada com cache SQLite de cidades brasileiras

### 🎆 **Enriquecimento CEP Separado**
- **Processo Independente**: Enriquecimento via ViaCEP agora é etapa separada
- **Controle de Tarefas**: Nova tabela TB_CEP_ENRICHMENT para rastreamento
- **Validação Inteligente**: Só processa quando há melhoria real nos dados
- **Dados Oficiais**: Sempre prioriza informações oficiais do ViaCEP

### 🎛️ **Menu Otimizado**
- **4 Opções**: Console focado em processamento + dashboard integrado
- **Estatísticas Detalhadas**: Cada opção mostra progresso específico
- **Fluxo Flexível**: Execute apenas as etapas que precisar
- **Excel Integrado**: Geração de planilha direto no dashboard

### 🏛️ **Validação de CEP de Capital**
- **Validação Dinâmica**: Verifica se CEP é de capital via APIs
- **Sugestões Inteligentes**: Mostra capital do estado para CEPs não-capital
- **Cobertura Completa**: Suporta todas as 27 capitais brasileiras

### 📊 **Dashboard Web Integrado**
- **Interface AdminLTE**: Dashboard profissional com design responsivo
- **Métricas em Tempo Real**: Estatísticas atualizadas via WebSocket
- **Três Fluxos Unificados**: Coleta, CEP Enrichment e Geolocalização
- **Boxes Informativos**: Empresas coletadas, CEPs enriquecidos, endereços geocodificados
- **Taxa de Sucesso**: Percentual de sucesso para cada processo
- **Gráficos e Progresso**: Barras de progresso e indicadores visuais
- **Inicialização Automática**: Inicia automaticamente durante processamento
- **Exportação Integrada**: Botão para gerar Excel diretamente no dashboard

---

## 🚀 Como Executar

### Pré-requisitos

- Python 3.13.0+ (baixa automaticamente se necessário)
- **Microsoft Access** (para banco de dados)
- **Pelo menos um navegador suportado:**
    - Google Chrome **OU** Brave Browser
- ChromeDriver (baixa automaticamente)

### Instalação e Execução

**1️⃣ Executar Robô (Criação Automática)**

```cmd
iniciar_robo_simples.bat
```

[![Executar Robô](https://img.shields.io/badge/▶️-Executar%20Robô-blue?style=for-the-badge)](iniciar_robo_simples.bat)

**2️⃣ Configurar CEP de Referência (Opcional)**

Edite `src/resources/application.yaml`:

```yaml
geolocation:
  reference_cep: "01310-100"  # Seu CEP de referência
```

**3️⃣ Carregar Dados Iniciais (Opcional)**

```cmd
python scripts\database\load_initial_data.py
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

### Fluxo Interativo v4.0.0

A aplicação:

1. **🌐 Verifica navegadores**: Detecta automaticamente Chrome e/ou Brave
2. **🗄️ Cria banco automaticamente**: Se não existir, cria com 14 tabelas estruturadas
3. **🚀 Descoberta geográfica**: Descobre automaticamente cidades e bairros baseado no CEP
4. **🎛️ Menu principal expandido**: Escolha da funcionalidade desejada
   - **[1] Processar coleta de dados** (e-mails e telefones)
   - **[2] Enriquecer endereços (ViaCEP)** - **NOVO**: Processamento separado
   - **[3] Processar geolocalização (Nominatim)** - **NOVO**: Geocodificação separada
   - **[4] Sair**
   - **📊 Gerar Excel**: Integrado no dashboard web
5. **📊 Dashboard web automático**: Interface AdminLTE inicia automaticamente durante processamento
6. **📈 Estatísticas detalhadas**: Cada opção mostra progresso e estatísticas específicas
7. **⚙️ Configurações automáticas**: Motor de busca e modo são configurados durante a coleta
8. **🔄 Reset opcional**: Pergunta sobre reset apenas na opção de coleta

### Configurações v4.0.0

- **Arquivo principal**: `src/resources/application.yaml`
- **Modo teste**: `mode.is_test: true/false`
- **CEP referência**: `geolocation.reference_cep`
- **Descoberta geográfica**: `geographic_discovery.*` - **NOVO**
  - **Perfis**: `profiles.metropolitan` e `profiles.rural`
  - **APIs**: `apis.viacep`, `apis.ibge`, `apis.nominatim`
  - **Detecção automática**: `auto_profile_detection.enabled`
  - **Prefixos metropolitanos**: Lista de 96 prefixos de CEP
- **Delays**: Configuráveis por motor de busca
- **ChromeDriver**: Download automático da versão compatível

## 🛠️ Tecnologias Utilizadas

| Tecnologia             | Descrição                                            | Versão        |
|------------------------|------------------------------------------------------|---------------|
| **Python**             | Linguagem de programação principal                   | 3.13.0+       |
| **PyODBC**             | Conector para Microsoft Access                       | ≥4.0.0        |
| **Microsoft Access**   | Sistema de banco de dados                            | 2016+         |
| **Selenium**           | Automação de navegadores web                         | ≥4.0.0        |
| **OpenPyXL**           | Manipulação de arquivos Excel (.xlsx)                | ≥3.0.0        |
| **TLDExtract**         | Extração e processamento de domínios                 | ≥3.0.0        |
| **Requests**           | Cliente HTTP para APIs e download de drivers         | ≥2.25.0       |
| **PyYAML**             | Parser e gerador de arquivos YAML                    | ≥6.0          |
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
| **Flask**              | Servidor web para dashboard integrado                 | ≥3.0.0        |
| **Flask-SocketIO**     | Comunicação em tempo real via WebSocket              | ≥5.3.0        |
| **AdminLTE**           | Template profissional para dashboard web             | 3.2.0 (CDN)   |
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

### 🗄️ **Banco Access v4.0.0 (Principal)**

- Dados normalizados em **14 tabelas** (incluindo TB_ENDERECOS, TB_CEP_ENRICHMENT, TB_CIDADES, TB_BAIRROS)
- **Endereços estruturados** com logradouro, número, bairro, cidade, estado, CEP
- **Descoberta geográfica dinâmica** com cache local de cidades e bairros
- **Enriquecimento CEP separado** com controle de tarefas na TB_CEP_ENRICHMENT
- **Geolocalização com fallback progressivo** usando campos estruturados
- **Singleton de conexão** para máxima performance
- **Replicação automática** entre tabelas
- Consultas avançadas e relatórios
- Auditoria completa e logs categorizados

### 📋 **Excel (Compatibilidade)**

- Formato atual mantido para usuário final
- Gerado automaticamente do banco
- Para copiar/colar onde quiser

### Formato dos Dados

- **E-mails**: `email1@domain.com;email2@domain.com;`
- **Telefones**: `(11) 99999-8888;(11) 3333-4444;`
- **Endereços Estruturados**: 
  - `LOGRADOURO`: "Rua Augusta"
  - `NUMERO`: "123"
  - `BAIRRO`: "Consolação"
  - `CIDADE`: "São Paulo"
  - `ESTADO`: "SP"
  - `CEP`: "01310-100"
- **Endereço Concatenado**: `Rua Augusta, 123, Consolação, São Paulo, SP`
- **Distâncias**: `5.2` (em quilômetros do ponto de referência)
- **Validação**: Filtra e-mails/telefones inválidos automaticamente

## 🔄 Fluxo de Trabalho Recomendado v4.0.0

### Sequência Otimizada
1. **[1] Processar coleta de dados** - Coleta e-mails, telefones e endereços
2. **[2] Enriquecer endereços (ViaCEP)** - Melhora dados de endereço com CEP
3. **[3] Processar geolocalização (Nominatim)** - Geocodifica endereços enriquecidos
4. **📊 Dashboard**: Gerar planilha Excel via interface web

### Execução Flexível
- **Independente**: Cada etapa pode ser executada separadamente
- **Estatísticas**: Progresso detalhado para cada processo
- **Continuação**: Pode parar e continuar em qualquer etapa

---

## 🎯 Especificações Técnicas

### Modo Produção

- **Descoberta dinâmica**: Cidades e bairros descobertos automaticamente via CEP
- **Termos gerados**: Baseados nas localizações descobertas dinamicamente
- **Processamento**: Sempre completo (todos os resultados)
- **Interface**: Console simplificado + dashboard web completo

### Modo Teste

- **Termos de busca**: 2 termos apenas (modo teste)
- **Execução rápida**: Para desenvolvimento e validação
- **Processamento**: Sempre completo independente do modo
- **Excel**: Gerado via dashboard web (não mais no console)

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

### 🌍 Precisão da Geolocalização com Fallback Progressivo

| Tentativa             | Precisão | Exemplo                               | API Nominatim |
|-----------------------|----------|---------------------------------------|---------------|
| **1. Endereço completo** | ±10-50m  | `street="Rua Augusta, 123" city="São Paulo"` | Estruturada |
| **2. Só CEP**         | ±10-50m  | `postalcode="01310-100"`              | Estruturada |
| **3. Bairro + Cidade** | ±2-5km   | `city="Moema, São Paulo"`             | Estruturada |
| **4. Só Cidade**      | ±10-20km | `city="São Paulo" state="SP"`         | Estruturada |
| **5. Sem dados**      | -        | Não geocodifica                       | - |

## 📝 Logs Categorizados

- `[INFO]`: Informações gerais e progresso
- `[OK]`: Operações bem-sucedidas
- `[ERRO]`: Falhas na execução
- `[DB]`: Criação de tabelas (`[DB] 1/11 - TB_ZONAS criada`)
- `[DB-DATA]`: Carregamento de dados iniciais
- `[DB-CHECK]`: Verificações de integridade
- `[DB-ERRO]`: Erros específicos de banco
- `[GEO]`: Processamento de geolocalização
- `[DEBUG]`: Informações detalhadas de debug

## 📄 Licença

**Creative Commons Attribution-NonCommercial 4.0 International (CC BY-NC 4.0)**

- ✅ **Compartilhamento livre**: Copie e redistribua em qualquer formato
- ✅ **Adaptação permitida**: Modifique, transforme e crie derivações
- ✅ **Atribuição obrigatória**: Dê crédito ao autor original
- ❌ **Uso comercial proibido**: Não pode ser usado para fins comerciais
- 🛡️ **Proteção contra patentes**: Publicado como arte anterior

Veja o arquivo [LICENSE](LICENSE) para detalhes completos.