# 🏗️ Arquitetura v3.0.0 - PythonSearchApp

## 📋 Visão Geral

O PythonSearchApp v3.0.0 segue os princípios da **Clean Architecture** com separação clara de responsabilidades em camadas bem definidas e **Sistema de Controle de Geolocalização** independente.

## 🔵 Camadas da Arquitetura

### 1. **Domain Layer** (Domínio)

```
src/domain/
├── models/           # Entidades e modelos de dados
├── services/         # Regras de negócio puras
├── protocols/        # Interfaces e contratos
└── factories/        # Criação de objetos complexos
```

**Responsabilidades:**

- Regras de negócio centrais
- Validações de domínio
- Modelos de dados puros
- Interfaces para infraestrutura

### 2. **Application Layer** (Aplicação)

```
src/application/
└── services/         # Orquestração e casos de uso
    ├── email_application_service.py    # Serviço principal
    ├── geolocation_application_service.py # 🆕 Controle de geolocalização
    ├── database_service.py             # Gerenciamento do banco
    └── user_config_service.py          # Configurações do usuário
```

**Responsabilidades:**

- Orquestração de casos de uso
- Coordenação entre camadas
- Lógica de aplicação específica
- Gerenciamento de transações

### 3. **Infrastructure Layer** (Infraestrutura)

```
src/infrastructure/
├── config/           # Gerenciamento de configuração
├── drivers/          # WebDriver e automação
├── logging/          # Sistema de logging
├── metrics/          # Métricas e performance
├── network/          # Rede e retry
├── repositories/     # Acesso a dados
├── scrapers/         # Web scraping
└── storage/          # Gerenciamento de arquivos
```

**Responsabilidades:**

- Acesso a dados externos
- Integração com APIs
- Persistência de dados
- Infraestrutura técnica

## 🗄️ Arquitetura de Dados

### **Banco Access v3.0.0 (10 Tabelas)**

```
TB_ZONAS ←─┐
TB_BAIRROS ←─┼─→ TB_TERMOS_BUSCA ←─→ TB_EMPRESAS ←─┬─→ TB_EMAILS
TB_CIDADES ←─┘                                      ├─→ TB_TELEFONES
TB_BASE_BUSCA ←─┘                                     └─→ TB_GEOLOCALIZACAO 🆕
                                                           └─→ TB_PLANILHA
```

### **🆕 NOVIDADE: TB_GEOLOCALIZACAO**

**Tabela de Controle de Geolocalização:**
- `ID_GEO` - Chave primária da tarefa
- `ID_EMPRESA` - Referência à empresa
- `ENDERECO` - Endereço a ser geocodificado
- `LATITUDE, LONGITUDE, DISTANCIA_KM` - Resultados
- `STATUS_PROCESSAMENTO` - PENDENTE/CONCLUIDO/ERRO
- `DATA_PROCESSAMENTO, TENTATIVAS, ERRO_DESCRICAO` - Controle detalhado

### **Fluxo de Dados v3.0.0**

1. **Configuração** → Tabelas base (zonas, bairros, cidades, termos)
2. **Geração** → Combinação automática de termos de busca
3. **Coleta** → Scraping e coleta de dados + criação de tarefas de geolocalização
4. **Geolocalização** → Processamento independente com controle de status
5. **Replicação** → Coordenadas propagadas automaticamente
6. **Exportação** → Excel com dados completos

## 🔄 Fluxo de Execução

### **1. Inicialização**

```python
main.py → DatabaseService.initialize_search_terms()
       → EmailApplicationService()
```

### **2. Processamento v3.0.0**

```python
# COLETA (Opção 1)
EmailApplicationService.execute()
├── Obter termos do banco
├── Para cada termo:
│   ├── Executar busca (Google/DuckDuckGo)
│   ├── Extrair links dos resultados
│   ├── Para cada link:
│   │   ├── Verificar se já visitado
│   │   ├── Extrair dados (emails/telefones/endereço)
│   │   ├── Salvar empresa no banco
│   │   └── 🆕 Criar tarefa de geolocalização (se houver endereço)
│   └── Atualizar status do termo
└── Finalizar coleta

# GEOLOCALIZAÇÃO (Opção 2)
GeolocationApplicationService.process_geolocation()
├── Obter tarefas PENDENTES de TB_GEOLOCALIZACAO
├── Para cada tarefa:
│   ├── Geocodificar endereço
│   ├── Calcular distância
│   ├── Atualizar TB_GEOLOCALIZACAO (CONCLUIDO/ERRO)
│   ├── 🆕 Replicar para TB_EMPRESAS
│   └── 🆕 Replicar para TB_PLANILHA
└── Finalizar geolocalização
```

### **3. Finalização**

```python
DatabaseService.export_to_excel()
DatabaseService.get_statistics()
```

## 🎯 Padrões Utilizados

### **Repository Pattern**

- `AccessRepository` - Acesso ao banco Access
- Abstração da persistência de dados
- Facilita testes e manutenção

### **Service Layer Pattern**

- `DatabaseService` - Lógica de banco de dados
- `EmailApplicationService` - Orquestração principal
- Separação de responsabilidades

### **Factory Pattern**

- `SearchTermFactory` - Criação de termos de busca
- Encapsula lógica de criação complexa

### **Strategy Pattern**

- `ScraperProtocol` - Interface para scrapers
- `GoogleScraper` / `DuckDuckGoScraper` - Implementações

## 🔧 Configuração e Extensibilidade

### **Configuração Centralizada**

```yaml
# src/resources/application.yaml
app:
  name: "PythonSearchApp"
  version: "1.2.0"

search:
  engines:
    google:
      enabled: true
    duckduckgo:
      enabled: true
```

### **Pontos de Extensão**

1. **Novos Scrapers** - Implementar `ScraperProtocol`
2. **Novos Repositórios** - Criar novos repositórios de dados
3. **Novas Validações** - Estender `EmailValidationService`
4. **Novas Métricas** - Adicionar ao `PerformanceTracker`

## 📊 Benefícios da Arquitetura

### **Testabilidade**

- Camadas isoladas e testáveis
- Mocks e stubs fáceis de implementar
- Cobertura de testes alta (99%+)

### **Manutenibilidade**

- Responsabilidades bem definidas
- Baixo acoplamento entre camadas
- Código limpo e organizado

### **Extensibilidade**

- Fácil adição de novos recursos
- Padrões consistentes
- Interfaces bem definidas

### **Performance**

- Banco de dados normalizado
- Índices otimizados
- Métricas de performance integradas

## 🆕 **Benefícios da Nova Arquitetura v3.0.0**

### **Separação de Processos**
- ✅ Coleta e geolocalização são independentes
- ✅ Controle granular de cada etapa
- ✅ Processamento sob demanda

### **Controle Total**
- ✅ Status individual de cada tarefa
- ✅ Histórico de tentativas e erros
- ✅ Auditoria completa do processamento

### **Replicação Automática**
- ✅ Dados propagados automaticamente
- ✅ Consistência entre tabelas
- ✅ Integridade referencial mantida

## 🚀 Evolução Futura

### **Possíveis Melhorias**

1. **Processamento em Lote** - Múltiplas tarefas simultâneas
2. **API REST** - Exposição via API
3. **Interface Web** - Dashboard de monitoramento
4. **Cache Inteligente** - Redis/Memcached
5. **Notificações** - Email/Slack/Teams
6. **Fila de Processamento** - RabbitMQ/Celery