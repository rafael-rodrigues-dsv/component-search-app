# 🏗️ Arquitetura - PythonSearchApp

## 📋 Visão Geral

O PythonSearchApp segue os princípios da **Clean Architecture** com separação clara de responsabilidades em camadas bem definidas.

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

### **Banco Access (Principal)**
```
TB_ZONAS ←─┐
TB_BAIRROS ←─┼─→ TB_TERMOS_BUSCA ←─→ TB_EMPRESAS ←─┬─→ TB_EMAILS
TB_CIDADES ←─┘                                      └─→ TB_TELEFONES
TB_BASE_BUSCA ←─┘
```

### **Fluxo de Dados**
1. **Configuração** → Tabelas base (zonas, bairros, cidades, termos)
2. **Geração** → Combinação automática de termos de busca
3. **Processamento** → Scraping e coleta de dados
4. **Armazenamento** → Dados estruturados no Access
5. **Exportação** → Excel para compatibilidade

## 🔄 Fluxo de Execução

### **1. Inicialização**
```python
main.py → DatabaseService.initialize_search_terms()
       → EmailApplicationService()
```

### **2. Processamento**
```python
EmailApplicationService.execute()
├── Obter termos do banco
├── Para cada termo:
│   ├── Executar busca (Google/DuckDuckGo)
│   ├── Extrair links dos resultados
│   ├── Para cada link:
│   │   ├── Verificar se já visitado
│   │   ├── Extrair dados (emails/telefones)
│   │   └── Salvar no banco
│   └── Atualizar status do termo
└── Exportar para Excel
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

## 🚀 Evolução Futura

### **Possíveis Melhorias**
1. **API REST** - Exposição via API
2. **Interface Web** - Dashboard de monitoramento
3. **Processamento Paralelo** - Múltiplas threads
4. **Cache Inteligente** - Redis/Memcached
5. **Notificações** - Email/Slack/Teams