# 📐 ARQUITETURA DO SISTEMA - Component Search App

**Versão:** 2.0  
**Data:** 06/02/2026  
**Status:** Produção

---

## 📋 Índice

1. [Visão Geral](#visão-geral)
2. [Arquitetura em Camadas](#arquitetura-em-camadas)
3. [Diagrama de Sequência - Coleta](#diagrama-de-sequência-coleta)
4. [Fluxo Detalhado por Camada](#fluxo-detalhado-por-camada)
5. [Componentes Principais](#componentes-principais)
6. [Tecnologias Utilizadas](#tecnologias-utilizadas)

---

## 🎯 Visão Geral

Sistema de coleta automatizada de dados de empresas através de web scraping inteligente, com interface web para controle e monitoramento em tempo real.

### Características Principais:
- ✅ Interface Web (Flask + SocketIO)
- ✅ Dois modos de busca: Fast Search e Deep Search
- ✅ Suporte a Google e DuckDuckGo
- ✅ Coleta single-thread e multi-thread
- ✅ Extração de emails, telefones e endereços
- ✅ Banco de dados Access (pyodbc)
- ✅ Exportação para Excel

---

## 🏗️ Arquitetura em Camadas

```
┌─────────────────────────────────────────────────────────────────────────┐
│                          CAMADA 1: FRONTEND                              │
│  ┌────────────────────────────────────────────────────────────────┐    │
│  │  Dashboard Web (HTML/CSS/JavaScript + Socket.IO)               │    │
│  │  - Tela de controle (iniciar/parar coleta)                     │    │
│  │  - Configurações (browser, engine, headless, search mode)      │    │
│  │  - Logs em tempo real                                           │    │
│  │  - Estatísticas e progresso                                     │    │
│  └────────────────────────────────────────────────────────────────┘    │
│                                ▼ HTTP/WebSocket                          │
└─────────────────────────────────────────────────────────────────────────┘
                                 ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                     CAMADA 2: WEB/API LAYER                             │
│  ┌────────────────────────────────────────────────────────────────┐    │
│  │  Flask Server (dashboard_server.py)                            │    │
│  │  - Rotas HTTP: /, /api/*, /admin/*                             │    │
│  │  - Socket.IO: eventos em tempo real                            │    │
│  │  - PollingService: atualização de estatísticas                 │    │
│  └────────────────────────────────────────────────────────────────┘    │
│                                ▼                                         │
└─────────────────────────────────────────────────────────────────────────┘
                                 ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                   CAMADA 3: APPLICATION SERVICES                        │
│  ┌────────────────────────────────────────────────────────────────┐    │
│  │  Router Service (scraper_router_service.py)                    │    │
│  │  ├─ Decide: Single vs Multi Thread                             │    │
│  │  ├─ Decide: Fast vs Deep Search                                │    │
│  │  └─ Direciona para service correto                             │    │
│  │                                                                  │    │
│  │  Collection Services:                                           │    │
│  │  ├─ FastSearchSingleThreadService                              │    │
│  │  ├─ FastSearchMultiThreadService                               │    │
│  │  ├─ DeepSearchSingleThreadService                              │    │
│  │  └─ DeepSearchMultiThreadService                               │    │
│  │                                                                  │    │
│  │  Database Service (database_application_service.py)            │    │
│  │  └─ Gerencia termos, salva empresas, estatísticas              │    │
│  └────────────────────────────────────────────────────────────────┘    │
│                                ▼                                         │
└─────────────────────────────────────────────────────────────────────────┘
                                 ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                  CAMADA 4: INFRASTRUCTURE - SCRAPERS                    │
│  ┌────────────────────────────────────────────────────────────────┐    │
│  │  Collection Executor (collection_executor_service.py)          │    │
│  │  └─ Lógica central de coleta (orquestra tudo)                  │    │
│  │                                                                  │    │
│  │  Scrapers:                                                      │    │
│  │  ├─ Google Fast Search (fast_search_google_scraper.py)         │    │
│  │  ├─ Google Deep Search (deep_search_google_scraper.py)         │    │
│  │  ├─ DuckDuckGo Fast Search (fast_search_duckduckgo_scraper.py) │    │
│  │  └─ DuckDuckGo Deep Search (deep_search_duckduckgo_scraper.py) │    │
│  │                                                                  │    │
│  │  Deep Search Components:                                        │    │
│  │  ├─ ScraperCoordinator: orquestração inteligente               │    │
│  │  ├─ SiteClassifier: classifica tipo de site                    │    │
│  │  ├─ ExtractionChain: Fast Path → Smart Path → Regex            │    │
│  │  └─ Strategies: por tipo de site                               │    │
│  └────────────────────────────────────────────────────────────────┘    │
│                                ▼                                         │
└─────────────────────────────────────────────────────────────────────────┘
                                 ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                  CAMADA 5: INFRASTRUCTURE - DRIVERS                     │
│  ┌────────────────────────────────────────────────────────────────┐    │
│  │  Playwright Manager (playwright_manager.py)                    │    │
│  │  └─ Gerencia browser Chromium (headless/visible)               │    │
│  │                                                                  │    │
│  │  Extraction Services:                                           │    │
│  │  ├─ AdvancedExtractionService: regex emails/telefones          │    │
│  │  ├─ AddressExtractor: extrai endereços estruturados            │    │
│  │  └─ EmailValidationService: valida e normaliza                 │    │
│  └────────────────────────────────────────────────────────────────┘    │
│                                ▼                                         │
└─────────────────────────────────────────────────────────────────────────┘
                                 ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                    CAMADA 6: DOMAIN - REPOSITORIES                      │
│  ┌────────────────────────────────────────────────────────────────┐    │
│  │  Database Domain Service (database_domain_service.py)          │    │
│  │  └─ Coordena repositories                                       │    │
│  │                                                                  │    │
│  │  Repositories (Access Database):                               │    │
│  │  ├─ CompaniesRepository → TB_EMPRESAS                          │    │
│  │  ├─ EmailsRepository → TB_EMAILS                               │    │
│  │  ├─ PhonesRepository → TB_TELEFONES                            │    │
│  │  ├─ AddressesRepository → TB_ENDERECOS                         │    │
│  │  ├─ SpreadsheetRepository → TB_PLANILHA (para Excel)           │    │
│  │  └─ TermsRepository → TB_BASE_BUSCA                            │    │
│  └────────────────────────────────────────────────────────────────┘    │
│                                ▼                                         │
└─────────────────────────────────────────────────────────────────────────┘
                                 ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                     CAMADA 7: DATA PERSISTENCE                          │
│  ┌────────────────────────────────────────────────────────────────┐    │
│  │  Microsoft Access Database (pythonsearch.accdb)                │    │
│  │  ├─ TB_EMPRESAS: dados principais das empresas                 │    │
│  │  ├─ TB_EMAILS: emails coletados                                │    │
│  │  ├─ TB_TELEFONES: telefones coletados                          │    │
│  │  ├─ TB_ENDERECOS: endereços estruturados                       │    │
│  │  ├─ TB_PLANILHA: dados consolidados para Excel                 │    │
│  │  └─ TB_BASE_BUSCA: termos de busca                             │    │
│  │                                                                  │    │
│  │  Cache Database (pythonsearchcache.db - SQLite)                │    │
│  │  └─ Cache de requisições HTTP                                   │    │
│  │                                                                  │    │
│  │  Output Files:                                                  │    │
│  │  └─ empresas.xlsx: exportação final                            │    │
│  └────────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 📊 Diagrama de Sequência - Fluxo Completo de Coleta

### Cenário: Usuário inicia coleta via Dashboard

```
┌─────────┐  ┌──────────┐  ┌─────────┐  ┌──────────┐  ┌──────────┐  ┌─────────┐  ┌──────────┐  ┌──────────┐
│ Browser │  │  Flask   │  │ Router  │  │ Single   │  │Collection│  │ Google  │  │Playwright│  │ Database │
│  (UI)   │  │  Server  │  │ Service │  │  Thread  │  │ Executor │  │ Scraper │  │ Manager  │  │ Service  │
└────┬────┘  └────┬─────┘  └────┬────┘  └────┬─────┘  └────┬─────┘  └────┬────┘  └────┬─────┘  └────┬─────┘
     │            │              │             │             │             │             │             │
     │ 1. POST    │              │             │             │             │             │             │
     │ /api/start │              │             │             │             │             │             │
     │ {browser,  │              │             │             │             │             │             │
     │  engine,   │              │             │             │             │             │             │
     │  headless, │              │             │             │             │             │             │
     │  search}   │              │             │             │             │             │             │
     ├───────────>│              │             │             │             │             │             │
     │            │              │             │             │             │             │             │
     │            │ 2. route()   │             │             │             │             │             │
     │            ├─────────────>│             │             │             │             │             │
     │            │              │             │             │             │             │             │
     │            │              │ 3. Decide:  │             │             │             │             │
     │            │              │ SINGLE +    │             │             │             │             │
     │            │              │ FAST        │             │             │             │             │
     │            │              │             │             │             │             │             │
     │            │              │ 4. execute()│             │             │             │             │
     │            │              ├────────────>│             │             │             │             │
     │            │              │             │             │             │             │             │
     │            │              │             │ 5. Buscar   │             │             │             │
     │            │              │             │    termos   │             │             │             │
     │            │              │             │    ........>│             │             │             │
     │            │              │             │             │             │             │             │
     │            │              │             │ 6. Para cada termo:       │             │             │
     │            │              │             │ execute_                  │             │             │
     │            │              │             │ collection()              │             │             │
     │            │              │             ├──────────────────────────>│             │             │
     │            │              │             │             │             │             │             │
     │            │              │             │             │ 7. Iniciar │             │             │
     │            │              │             │             │ Playwright  │             │             │
     │            │              │             │             ├────────────────────────>│             │
     │            │              │             │             │             │             │             │
     │            │              │             │             │             │ 8. Launch  │             │
     │            │              │             │             │             │ Browser    │             │
     │            │              │             │             │             │<────────────│             │
     │            │              │             │             │             │             │             │
     │            │              │             │             │ 9. Config   │             │             │
     │            │              │             │             │    scraper  │             │             │
     │            │              │             │             ├────────────>│             │             │
     │            │              │             │             │             │             │             │
     │            │              │             │             │             │ 10. search()│             │
     │            │              │             │             │             │ google.com  │             │
     │            │              │             │             │             │<────────────│             │
     │            │              │             │             │             │             │             │
     │            │              │             │             │             │ 11. Digite  │             │
     │            │              │             │             │             │    termo    │             │
     │            │              │             │             │             │<────────────│             │
     │            │              │             │             │             │             │             │
     │            │              │             │             │             │ 12. Aguarda │             │
     │            │              │             │             │             │ resultados  │             │
     │            │              │             │             │             │<────────────│             │
     │            │              │             │             │             │             │             │
     │            │              │             │             │ 13. get_    │             │             │
     │            │              │             │             │ result_     │             │             │
     │            │              │             │             │ links()     │             │             │
     │            │              │             │             ├────────────>│             │             │
     │            │              │             │             │             │             │             │
     │            │              │             │             │             │ 14. Extract │             │
     │            │              │             │             │             │    links    │             │
     │            │              │             │             │             │    (9 links)│             │
     │            │              │             │             │<────────────│             │             │
     │            │              │             │             │             │             │             │
     │            │              │             │             │ 15. Para cada link:       │             │
     │            │              │             │             │ extract_                  │             │
     │            │              │             │             │ company_data()            │             │
     │            │              │             │             ├────────────>│             │             │
     │            │              │             │             │             │             │             │
     │            │              │             │             │             │ 16. Visita  │             │
     │            │              │             │             │             │    site     │             │
     │            │              │             │             │             │<────────────│             │
     │            │              │             │             │             │             │             │
     │            │              │             │             │             │ 17. Captura │             │
     │            │              │             │             │             │    HTML     │             │
     │            │              │             │             │             │<────────────│             │
     │            │              │             │             │             │             │             │
     │            │              │             │             │ 18. Extrai  │             │             │
     │            │              │             │             │ emails/     │             │             │
     │            │              │             │             │ telefones/  │             │             │
     │            │              │             │             │ endereço    │             │             │
     │            │              │             │             │<────────────│             │             │
     │            │              │             │             │             │             │             │
     │            │              │             │             │ 19. Salvar  │             │             │
     │            │              │             │             │    empresa  │             │             │
     │            │              │             │             ├────────────────────────────────────────>│
     │            │              │             │             │             │             │             │
     │            │              │             │             │             │             │ 20. INSERT │
     │            │              │             │             │             │             │ TB_EMPRESAS│
     │            │              │             │             │             │             │ TB_EMAILS  │
     │            │              │             │             │             │             │ TB_TELEFONES│
     │            │              │             │             │             │             │ TB_PLANILHA│
     │            │              │             │             │             │             │            │
     │            │              │             │             │<────────────────────────────────────────│
     │            │              │             │             │             │             │             │
     │            │ 21. Socket.IO: 'robot_log'               │             │             │             │
     │            │ (logs em tempo real)                     │             │             │             │
     │<───────────│              │             │             │             │             │             │
     │            │              │             │             │             │             │             │
     │            │ 22. Socket.IO: 'progress'                │             │             │             │
     │            │ {percentage, message}                    │             │             │             │
     │<───────────│              │             │             │             │             │             │
     │            │              │             │             │             │             │             │
     │            │              │             │<────────────┤             │             │             │
     │            │              │             │ 23. Retorna │             │             │             │
     │            │              │             │ resultado   │             │             │             │
     │            │              │<────────────│             │             │             │             │
     │            │<─────────────│             │             │             │             │             │
     │            │              │             │             │             │             │             │
     │ 24. JSON   │              │             │             │             │             │             │
     │ {success,  │              │             │             │             │             │             │
     │  companies,│              │             │             │             │             │             │
     │  links}    │              │             │             │             │             │             │
     │<───────────│              │             │             │             │             │             │
     │            │              │             │             │             │             │             │
```

---

## 🔄 Fluxo Detalhado por Camada

### 1️⃣ FRONTEND → API (Browser → Flask)

**Componentes:**
- `templates/index.html`: Interface principal
- `static/js/dashboard.js`: Lógica do frontend
- Socket.IO Client: Comunicação real-time

**Fluxo:**
```
Browser                          Flask Server
  │                                   │
  │ 1. Usuário clica "Iniciar"       │
  │    ├─ browser: CHROME             │
  │    ├─ engine: GOOGLE              │
  │    ├─ headless: false             │
  │    └─ search_mode: FAST           │
  │                                   │
  │ 2. POST /api/start_collection    │
  ├──────────────────────────────────>│
  │                                   │
  │ 3. Socket.IO: connect             │
  ├<─────────────────────────────────>│
  │    (canal de logs bidirecional)   │
  │                                   │
```

**Eventos Socket.IO:**
- `robot_log`: Logs em tempo real
- `progress`: Atualização de progresso (%)
- `collection_finished`: Conclusão da coleta
- `stats_update`: Atualização de estatísticas

---

### 2️⃣ API → APPLICATION SERVICES (Flask → Router)

**Arquivo:** `src/web/dashboard_server.py`

**Rotas principais:**
```python
POST /api/start_collection
  ├─ Recebe: {browser, engine, headless, search_mode, processing}
  ├─ Valida parâmetros
  └─ Chama: ScraperRouterService.route()

GET /api/statistics
  └─ Retorna estatísticas do banco

POST /api/stop_collection
  └─ Sinaliza parada via RobotController
```

**Código simplificado:**
```python
@app.route('/api/start_collection', methods=['POST'])
def start_collection():
    params = request.json
    
    # Direcionar para Router Service
    result = router_service.route(
        browser=params['browser'],
        engine=params['engine'],
        headless=params['headless'],
        search_mode=params['search_mode'],
        processing=params['processing']  # SINGLE ou MULTI
    )
    
    return jsonify(result)
```

---

### 3️⃣ ROUTER SERVICE (Decisão de Roteamento)

**Arquivo:** `src/infrastructure/scrapers/router/scraper_router_service.py`

**Lógica de Decisão:**
```
┌─────────────────────────────────────────────────────┐
│          SCRAPER ROUTER SERVICE                      │
│                                                      │
│  Entrada: browser, engine, headless, search_mode,   │
│           processing, term                          │
│                                                      │
│  ┌────────────────────────────────────────────┐    │
│  │  1. Validar parâmetros                     │    │
│  │  2. Decidir modo de processamento:         │    │
│  │     ├─ SINGLE → Single Thread              │    │
│  │     └─ MULTI → Multi Thread                │    │
│  │  3. Decidir tipo de busca:                 │    │
│  │     ├─ FAST → Fast Search Service          │    │
│  │     └─ DEEP → Deep Search Service          │    │
│  │  4. Instanciar service correto             │    │
│  │  5. Executar: service.execute()            │    │
│  └────────────────────────────────────────────┘    │
│                                                      │
│  Saída: {success, companies_found, links, ...}     │
└─────────────────────────────────────────────────────┘

Matrix de Decisão:
┌─────────────┬─────────────┬───────────────────────────────────┐
│ Processing  │ Search Mode │ Service Chamado                   │
├─────────────┼─────────────┼───────────────────────────────────┤
│ SINGLE      │ FAST        │ FastSearchSingleThreadService     │
│ SINGLE      │ DEEP        │ DeepSearchSingleThreadService     │
│ MULTI       │ FAST        │ FastSearchMultiThreadService      │
│ MULTI       │ DEEP        │ DeepSearchMultiThreadService      │
└─────────────┴─────────────┴───────────────────────────────────┘
```

---

### 4️⃣ COLLECTION SERVICES → EXECUTOR

**Arquivo (exemplo):** `fast_search_single_thread_service.py`

**Responsabilidades:**
1. Buscar termos no banco (TB_BASE_BUSCA com STATUS='PENDENTE')
2. Chamar CollectionExecutorService para cada termo
3. Gerenciar callbacks de progresso
4. Tratar exceções e logging

**Código simplificado:**
```python
class FastSearchSingleThreadService:
    def execute(self, browser, engine, headless):
        terms = self.db.get_pending_terms()
        
        for term in terms:
            result = self.executor.execute_collection_for_term(
                term=term['termo'],
                browser=browser,
                engine=engine,
                headless=headless,
                search_mode='FAST',
                progress_callback=self._on_progress
            )
            
            if result['success']:
                self.db.update_term_status(term['id'], 'CONCLUIDO')
```

---

### 5️⃣ COLLECTION EXECUTOR → SCRAPERS

**Arquivo:** `collection_executor_service.py`

**Fluxo (5 Passos):**
```
[PASSO 1/5] 🎭 Inicializar Playwright
  ├─ PlaywrightManager(headless=headless, browser=browser)
  ├─ playwright.chromium.launch()
  └─ page = context.new_page()

[PASSO 2/5] 🔧 Configurar Scraper
  ├─ Se engine=GOOGLE e search_mode=FAST:
  │    └─ FastSearchGoogleScraper(page)
  ├─ Se engine=GOOGLE e search_mode=DEEP:
  │    └─ DeepSearchGoogleScraper(page)
  └─ Idem para DUCKDUCKGO

[PASSO 3/5] 🔍 Executar Busca
  ├─ scraper.search(term)
  ├─ Aguarda resultados (wait_for_selector)
  └─ Retorna: True/False

[PASSO 4/5] 📋 Preparar Coleta
  ├─ Buscar termo_id no banco
  └─ Validar se existe

[PASSO 5/5] 📊 Coletar Dados
  ├─ Para cada página (1-3):
  │   ├─ scraper.get_result_links(blacklist)
  │   ├─ Filtrar links já visitados
  │   ├─ Para cada link:
  │   │   ├─ scraper.extract_company_data(link)
  │   │   ├─ Validar dados
  │   │   └─ _save_company_to_database()
  │   └─ scraper.go_to_next_page()
  └─ Atualizar status do termo para CONCLUIDO
```

---

### 6️⃣ SCRAPERS → PLAYWRIGHT

**Exemplo: Fast Search Google**

**Arquivo:** `fast_search_google_scraper.py`

**Métodos principais:**

```python
class FastSearchGoogleScraper:
    def __init__(self, page: Page):
        self.page = page  # Page do Playwright
    
    def search(self, term: str) -> bool:
        """
        1. Navega para google.com
        2. Preenche campo de busca
        3. Pressiona Enter
        4. Aguarda resultados (wait_for_selector)
        """
        self.page.goto("https://www.google.com")
        self.page.fill('input[name="q"]', term)
        self.page.press('input[name="q"]', 'Enter')
        self.page.wait_for_selector('div.g, div.tF2Cxc')
        return True
    
    def get_result_links(self, blacklist: List[str]) -> List[str]:
        """
        1. Extrai todos os links da página
        2. Filtra blacklist
        3. Remove duplicatas
        """
        elements = self.page.locator('div.g a[href]').all()
        links = [e.get_attribute('href') for e in elements if e.is_visible()]
        return [l for l in links if not self._is_blacklisted(l, blacklist)]
    
    def extract_company_data(self, url: str) -> CompanyModel:
        """
        1. Abre nova aba (new_page)
        2. Navega para URL
        3. Captura HTML
        4. Extrai emails, telefones, endereços (AdvancedExtractionService)
        5. Retorna CompanyModel
        """
        new_page = self.page.context.new_page()
        new_page.goto(url, timeout=5000)
        html = new_page.content()
        
        emails, phones, address = extraction_service.extract_all(html)
        
        new_page.close()
        
        return CompanyModel(
            name=new_page.title(),
            emails=';'.join(emails) + ';',
            phones=';'.join(phones) + ';',
            address=address,
            url=url
        )
```

---

### 7️⃣ EXTRACTION → SERVICES

**AdvancedExtractionService:**
- Regex otimizados para emails, telefones
- Validação de domínios suspeitos
- Normalização de telefones

**AddressExtractor:**
- Regex para endereços brasileiros
- Extração estruturada (Logradouro, Número, Bairro, Cidade, Estado, CEP)
- Validação de consistência

**EmailValidationService:**
- Validação de formato
- Filtro de domínios inválidos (example.com, test.com, etc)
- Join com separador `;`

---

### 8️⃣ DATABASE SERVICE → REPOSITORIES

**Arquivo:** `database_domain_service.py`

**Método: save_company_data()**

```python
def save_company_data(self, termo_id, site_url, domain, 
                      motor_busca, emails, telefones, 
                      nome_empresa, html_content):
    """
    1. Extrair endereço do HTML (AddressExtractor)
    2. Inserir empresa (CompaniesRepository)
    3. Se endereço válido:
       └─ Inserir endereço (AddressesRepository)
    4. Determinar status: COLETADO vs NAO_COLETADO
    5. Salvar emails (EmailsRepository)
    6. Salvar telefones (PhonesRepository)
    7. Se tiver dados: salvar na TB_PLANILHA (SpreadsheetRepository)
    """
    
    # 1. Extrair endereço
    address_model = AddressExtractor.extract_from_html(html_content)
    
    # 2. Inserir empresa
    empresa_id = self.companies_repo.insert_company(
        termo_id, site_url, domain, motor_busca, address_model
    )
    
    # 3. Inserir endereço se válido
    if address_model and address_model.is_valid():
        endereco_id = self.addresses_repo.insert_address(address_model)
    
    # 4. Status
    status = 'COLETADO' if (emails or telefones or address_model) else 'NAO_COLETADO'
    self.companies_repo.update_status(empresa_id, status, nome_empresa)
    
    # 5-6. Salvar emails e telefones
    if emails:
        self.emails_repo.insert_emails(empresa_id, emails, domain)
    if telefones:
        self.phones_repo.insert_phones(empresa_id, telefones)
    
    # 7. Salvar na planilha (para Excel)
    if emails or telefones or address_model:
        self.spreadsheet_repo.save_to_sheet(site_url, emails_str, telefones_str, endereco_str)
```

---

### 9️⃣ REPOSITORIES → DATABASE

**Exemplo: EmailsRepository**

```python
class EmailsRepository:
    def insert_emails(self, empresa_id: int, emails: List[str], domain: str):
        conn = self.access.get_connection()
        cursor = conn.cursor()
        
        for email in emails:
            cursor.execute("""
                INSERT INTO TB_EMAILS (ID_EMPRESA, EMAIL, DOMINIO_EMAIL, VALIDADO, DATA_COLETA)
                VALUES (?, ?, ?, ?, Date())
            """, (empresa_id, email, domain, -1))
        
        conn.commit()
        cursor.close()
```

**Tabelas principais:**
- `TB_EMPRESAS`: ID_EMPRESA, SITE_URL, DOMINIO, NOME_EMPRESA, STATUS_COLETA, MOTOR_BUSCA
- `TB_EMAILS`: ID_EMAIL, ID_EMPRESA (FK), EMAIL, DOMINIO_EMAIL, VALIDADO
- `TB_TELEFONES`: ID_TELEFONE, ID_EMPRESA (FK), TELEFONE, TELEFONE_FORMATADO, DDD, TIPO
- `TB_ENDERECOS`: ID_ENDERECO, LOGRADOURO, NUMERO, BAIRRO, CIDADE, ESTADO, CEP
- `TB_PLANILHA`: ID_PLANILHA, SITE, EMAIL, TELEFONE, ENDERECO, DISTANCIA_KM (para Excel)

---

## 🧩 Componentes Principais

### Frontend (HTML/JS)
```
src/web/
├── templates/
│   └── index.html           # Dashboard principal
├── static/
│   ├── css/
│   │   └── dashboard.css    # Estilos
│   └── js/
│       └── dashboard.js     # Lógica do frontend
└── dashboard_server.py      # Flask server
```

### Application Layer
```
src/application/services/
├── database_application_service.py      # Gerencia BD
├── robot_controller_application_service.py  # Start/Stop
└── scraper_adapter_service.py           # Adaptador legado
```

### Infrastructure - Scrapers
```
src/infrastructure/scrapers/
├── router/
│   └── scraper_router_service.py        # Roteamento inteligente
├── services/
│   ├── fast_search_single_thread_service.py
│   ├── fast_search_multi_thread_service.py
│   ├── deep_search_single_thread_service.py
│   ├── deep_search_multi_thread_service.py
│   └── collection_executor_service.py   # Núcleo da coleta
└── engines/
    ├── google/
    │   ├── fast_search_google_scraper.py
    │   └── deep_search_google_scraper.py
    └── duckduckgo/
        ├── fast_search_duckduckgo_scraper.py
        └── deep_search_duckduckgo_scraper.py
```

### Domain - Deep Search (Inteligente)
```
src/domain/scrapers/
├── orchestrator/
│   └── scraper_coordinator.py           # Orquestrador principal
├── classify/
│   ├── site_classifier.py               # Classifica tipo de site
│   ├── rules.py                         # Regras de classificação
│   └── site_type_enum.py                # Enum de tipos
├── extract/
│   ├── chain.py                         # Chain of Responsibility
│   ├── fast_path.py                     # Extração rápida (CSS)
│   ├── smart_path.py                    # Extração inteligente
│   └── regex_validators.py              # Validadores regex
└── strategy/
    ├── static_single.py                 # Estratégia site estático
    ├── corporate_multi.py               # Estratégia site corporativo
    └── ...                              # Outras estratégias
```

### Infrastructure - Drivers
```
src/infrastructure/
├── drivers/
│   └── playwright_manager.py            # Gerencia Playwright
├── services/
│   ├── advanced_extraction_service.py   # Regex emails/telefones
│   └── email_domain_service.py          # Validação
└── utils/
    └── address_extractor.py             # Extração de endereços
```

### Domain - Repositories
```
src/domain/services/
└── database_domain_service.py           # Coordena repositories

src/infrastructure/repositories/
├── companies_repository.py              # TB_EMPRESAS
├── emails_repository.py                 # TB_EMAILS
├── phones_repository.py                 # TB_TELEFONES
├── addresses_repository.py              # TB_ENDERECOS
├── spreadsheet_repository.py            # TB_PLANILHA
└── terms_repository.py                  # TB_BASE_BUSCA
```

---

## 🛠️ Tecnologias Utilizadas

### Backend
- **Python 3.11+**
- **Flask 3.0+**: Web server
- **Flask-SocketIO 5.3+**: WebSocket para real-time
- **Playwright 1.40+**: Automação de browser
- **BeautifulSoup4 4.12+**: Parsing HTML
- **pyodbc 4.0+**: Conexão com Access Database
- **openpyxl 3.0+**: Exportação Excel

### Frontend
- **HTML5 + CSS3**
- **JavaScript (Vanilla)**
- **Socket.IO Client**: Comunicação real-time

### Database
- **Microsoft Access (.accdb)**: Banco principal
- **SQLite**: Cache de requisições

### Automation
- **Chromium (via Playwright)**: Browser automatizado
- **Regex**: Extração de padrões (emails, telefones, endereços)

---

## 📈 Fluxo de Dados Resumido

```
1. Browser envia configurações → Flask Server
2. Flask valida e chama Router Service
3. Router decide qual Collection Service usar
4. Collection Service busca termos pendentes no banco
5. Para cada termo, chama Collection Executor
6. Executor inicializa Playwright e configura Scraper
7. Scraper busca no Google/DuckDuckGo
8. Scraper coleta links e visita cada site
9. Extraction Services extraem dados (regex + validação)
10. Database Service salva em múltiplas tabelas
11. Logs/Progress retornam via Socket.IO para Browser
12. Estatísticas atualizadas em tempo real
```

---

## 🎯 Padrões Arquiteturais Utilizados

1. **Layered Architecture (Camadas)**: Separação clara de responsabilidades
2. **Repository Pattern**: Abstração de acesso a dados
3. **Service Layer**: Lógica de negócio centralizada
4. **Strategy Pattern**: Diferentes estratégias de scraping por tipo de site
5. **Chain of Responsibility**: Tentativas sequenciais de extração (Fast → Smart → Regex)
6. **Factory Pattern**: Criação de scrapers e estratégias
7. **Dependency Injection**: Services recebem dependências via construtor
8. **Observer Pattern**: Socket.IO para notificações em tempo real

---

## 📊 Métricas e Performance

### Fast Search (Rápida)
- **Tempo médio por site:** ~1s
- **Taxa de sucesso:** ~90%
- **Uso de CPU:** Baixo
- **Uso de memória:** ~200MB

### Deep Search (Inteligente)
- **Tempo médio por site:** ~2-3s
- **Taxa de sucesso:** ~85% (após correções)
- **Uso de CPU:** Médio
- **Uso de memória:** ~300MB
- **Classificação de sites:** 10 tipos diferentes
- **Estratégias disponíveis:** 5

---

## 🔒 Considerações de Segurança

1. **Validação de entrada**: Todos os parâmetros da API são validados
2. **SQL Injection**: Uso de queries parametrizadas (pyodbc)
3. **XSS**: Flask escapa automaticamente templates
4. **CORS**: Configurado no Socket.IO
5. **Secrets**: Chaves em `config/settings.py`
6. **SSL**: Warnings desabilitados apenas para logs (não afeta segurança)

---

## 📝 Versionamento

- **v1.0**: Sistema legado (scraper único)
- **v2.0**: Arquitetura completa com Fast/Deep Search + Router + Multi-thread
- **Data**: 06/02/2026

---

## 📞 Manutenção e Suporte

Para alterações na arquitetura:
1. Atualizar este documento
2. Revisar impacto em todas as camadas
3. Testar integração end-to-end
4. Atualizar testes unitários

---

**Documento gerado em:** 06/02/2026  
**Versão:** 2.0  
**Status:** ✅ Produção
