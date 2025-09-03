# 🗄️ Modelo de Banco de Dados Access - PythonSearchApp

## 📊 Diagrama MER (Modelo Entidade-Relacionamento)

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                           MODELO DE DADOS ACCESS                                │
└─────────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────┐    ┌─────────────────────────┐    ┌─────────────────────────┐
│      TB_ZONAS           │    │     TB_BAIRROS          │    │    TB_CIDADES           │
├─────────────────────────┤    ├─────────────────────────┤    ├─────────────────────────┤
│ ID_ZONA (PK)           │    │ ID_BAIRRO (PK)         │    │ ID_CIDADE (PK)         │
│ NOME_ZONA              │    │ NOME_BAIRRO            │    │ NOME_CIDADE            │
│ UF                     │    │ UF                     │    │ UF                     │
│ ATIVO                  │    │ ATIVO                  │    │ ATIVO                  │
│ DATA_CRIACAO           │    │ DATA_CRIACAO           │    │ DATA_CRIACAO           │
└─────────────────────────┘    └─────────────────────────┘    └─────────────────────────┘

┌─────────────────────────┐
│    TB_BASE_BUSCA        │
├─────────────────────────┤
│ ID_BASE (PK)           │
│ TERMO_BUSCA            │
│ CATEGORIA              │
│ ATIVO                  │
│ DATA_CRIACAO           │
└─────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────────┐
│                              TB_TERMOS_BUSCA                                    │
├─────────────────────────────────────────────────────────────────────────────────┤
│ ID_TERMO (PK)                                                                  │
│ ID_BASE (FK) → TB_BASE_BUSCA                                                   │
│ ID_ZONA (FK) → TB_ZONAS (nullable)                                            │
│ ID_BAIRRO (FK) → TB_BAIRROS (nullable)                                        │
│ ID_CIDADE (FK) → TB_CIDADES (nullable)                                        │
│ TERMO_COMPLETO                                                                 │
│ TIPO_LOCALIZACAO (ZONA/BAIRRO/CIDADE/CAPITAL)                                │
│ STATUS_PROCESSAMENTO (PENDENTE/PROCESSANDO/CONCLUIDO/ERRO)                    │
│ DATA_CRIACAO                                                                   │
│ DATA_PROCESSAMENTO                                                             │
└─────────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────────┐
│                               TB_EMPRESAS                                       │
├─────────────────────────────────────────────────────────────────────────────────┤
│ ID_EMPRESA (PK)                                                                │
│ ID_TERMO (FK) → TB_TERMOS_BUSCA                                               │
│ SITE_URL                                                                       │
│ DOMINIO                                                                        │
│ NOME_EMPRESA (nullable)                                                        │
│ STATUS_COLETA (PENDENTE/COLETADO/ERRO/IGNORADO)                              │
│ DATA_PRIMEIRA_VISITA                                                           │
│ DATA_ULTIMA_VISITA                                                             │
│ TENTATIVAS_COLETA                                                              │
│ MOTOR_BUSCA (GOOGLE/DUCKDUCKGO)                                               │
└─────────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────────┐
│                                TB_EMAILS                                        │
├─────────────────────────────────────────────────────────────────────────────────┤
│ ID_EMAIL (PK)                                                                  │
│ ID_EMPRESA (FK) → TB_EMPRESAS                                                  │
│ EMAIL                                                                          │
│ DOMINIO_EMAIL                                                                  │
│ VALIDADO                                                                       │
│ DATA_COLETA                                                                    │
│ ORIGEM_COLETA (CONTATO/RODAPE/CABECALHO/TEXTO)                               │
└─────────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────────┐
│                               TB_TELEFONES                                      │
├─────────────────────────────────────────────────────────────────────────────────┤
│ ID_TELEFONE (PK)                                                               │
│ ID_EMPRESA (FK) → TB_EMPRESAS                                                  │
│ TELEFONE                                                                       │
│ TELEFONE_FORMATADO                                                             │
│ DDD                                                                            │
│ TIPO_TELEFONE (FIXO/CELULAR/WHATSAPP)                                        │
│ VALIDADO                                                                       │
│ DATA_COLETA                                                                    │
└─────────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────────┐
│                            TB_LOG_PROCESSAMENTO                                 │
├─────────────────────────────────────────────────────────────────────────────────┤
│ ID_LOG (PK)                                                                    │
│ ID_TERMO (FK) → TB_TERMOS_BUSCA (nullable)                                    │
│ ID_EMPRESA (FK) → TB_EMPRESAS (nullable)                                      │
│ NIVEL_LOG (INFO/WARNING/ERROR/SUCCESS)                                        │
│ MENSAGEM                                                                       │
│ DETALHES_ERRO (nullable)                                                       │
│ DATA_LOG                                                                       │
│ SESSAO_EXECUCAO                                                                │
└─────────────────────────────────────────────────────────────────────────────────┘
```

## 🔗 Relacionamentos

- **TB_TERMOS_BUSCA** ← 1:N → **TB_EMPRESAS**
- **TB_EMPRESAS** ← 1:N → **TB_EMAILS**  
- **TB_EMPRESAS** ← 1:N → **TB_TELEFONES**
- **TB_BASE_BUSCA** ← 1:N → **TB_TERMOS_BUSCA**
- **TB_ZONAS** ← 1:N → **TB_TERMOS_BUSCA**
- **TB_BAIRROS** ← 1:N → **TB_TERMOS_BUSCA**
- **TB_CIDADES** ← 1:N → **TB_TERMOS_BUSCA**

## 📋 Descrição das Tabelas

### 🏢 **TB_EMPRESAS** (Principal)
- Armazena dados das empresas coletadas
- Substitui a planilha Excel atual
- Controla status de coleta e tentativas

### 📧 **TB_EMAILS** 
- E-mails coletados por empresa
- Validação e origem da coleta
- Substitui `emails.json`

### 📞 **TB_TELEFONES**
- Telefones coletados por empresa  
- Formatação e validação automática
- Tipos: fixo, celular, WhatsApp

### 🔍 **TB_TERMOS_BUSCA**
- Termos gerados dinamicamente
- Combina base + localização
- Status de processamento

### 📍 **Tabelas de Localização**
- **TB_ZONAS**: Zonas de SP
- **TB_BAIRROS**: Bairros de SP  
- **TB_CIDADES**: Cidades do interior
- **TB_BASE_BUSCA**: Termos base de busca

### 📊 **TB_LOG_PROCESSAMENTO**
- Logs estruturados da execução
- Rastreabilidade completa
- Debug e auditoria

## 🎯 Vantagens do Modelo

✅ **Normalização**: Elimina redundância de dados  
✅ **Rastreabilidade**: Histórico completo de processamento  
✅ **Flexibilidade**: Fácil adição de novos termos/localizações  
✅ **Performance**: Consultas otimizadas com índices  
✅ **Integridade**: Relacionamentos com chaves estrangeiras  
✅ **Auditoria**: Logs detalhados de todas as operações  

## 📊 **Saída Dupla: Access + Excel**

### 🗄️ **Banco Access** (Principal)
- Dados estruturados e normalizados
- Controle completo de status e histórico
- Consultas avançadas e relatórios
- Auditoria e logs detalhados

### 📋 **Planilha Excel** (Compatibilidade)
- **Formato atual mantido**: `SITE | EMAIL | TELEFONE`
- **Gerada automaticamente** do banco Access
- **Para o usuário final**: Copiar/colar onde quiser
- **Mesmo formato**: `email1@domain.com;email2@domain.com;`

### 🔄 **Fluxo de Dados**
```
🔍 Scraping → 🗄️ Access (estruturado) → 📋 Excel (compatibilidade)
```

**Vantagens:**
✅ **Melhor controle**: Banco normalizado para o sistema  
✅ **Compatibilidade**: Excel para usuário final  
✅ **Flexibilidade**: Usuário pode exportar como quiser  
✅ **Histórico**: Tudo rastreado no Access  

## 🔧 Próximos Passos

1. **Aprovação do modelo** ✋
2. Criação do arquivo `.accdb`
3. Implementação das classes de acesso
4. Migração dos dados atuais
5. Atualização dos scrapers
6. **Geração automática do Excel** a partir do Access