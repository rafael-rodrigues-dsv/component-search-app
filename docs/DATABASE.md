# 🗄️ Documentação do Banco de Dados

## 📊 Modelo de Dados Access

### **Visão Geral**
O PythonSearchApp utiliza Microsoft Access como banco de dados principal, com 8 tabelas normalizadas que controlam todo o fluxo de coleta de dados.

## 📋 Estrutura das Tabelas

### **1. TB_ZONAS**
Armazena as zonas de São Paulo para busca.

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `ID_ZONA` | COUNTER (PK) | Identificador único |
| `NOME_ZONA` | TEXT(50) | Nome da zona (ex: "zona norte") |
| `UF` | TEXT(2) | Estado (sempre "SP") |
| `ATIVO` | BIT | Se a zona está ativa para busca |
| `DATA_CRIACAO` | DATE | Data de criação do registro |

**Dados Padrão:** zona norte, zona sul, zona leste, zona oeste, zona central

### **2. TB_BAIRROS**
Armazena os bairros de São Paulo para busca.

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `ID_BAIRRO` | COUNTER (PK) | Identificador único |
| `NOME_BAIRRO` | TEXT(100) | Nome do bairro |
| `UF` | TEXT(2) | Estado (sempre "SP") |
| `ATIVO` | BIT | Se o bairro está ativo |
| `DATA_CRIACAO` | DATE | Data de criação |

**Dados Padrão:** Moema, Vila Mariana, Pinheiros, Itaim Bibi, Brooklin, etc. (30 bairros)

### **3. TB_CIDADES**
Armazena cidades do interior de SP para busca.

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `ID_CIDADE` | COUNTER (PK) | Identificador único |
| `NOME_CIDADE` | TEXT(100) | Nome da cidade |
| `UF` | TEXT(2) | Estado (sempre "SP") |
| `ATIVO` | BIT | Se a cidade está ativa |
| `DATA_CRIACAO` | DATE | Data de criação |

**Dados Padrão:** Campinas, Guarulhos, Santo André, São Bernardo, etc. (20 cidades)

### **4. TB_BASE_BUSCA**
Armazena os termos base para construção das buscas.

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `ID_BASE` | COUNTER (PK) | Identificador único |
| `TERMO_BUSCA` | TEXT(200) | Termo base (ex: "empresa de elevadores") |
| `CATEGORIA` | TEXT(50) | Categoria do termo |
| `ATIVO` | BIT | Se o termo está ativo |
| `DATA_CRIACAO` | DATE | Data de criação |

**Dados Padrão:** empresa de elevadores, manutenção de elevadores, instalação de elevadores, etc.

### **5. TB_TERMOS_BUSCA** ⭐
Tabela central que combina termos base com localizações.

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `ID_TERMO` | COUNTER (PK) | Identificador único |
| `ID_BASE` | LONG (FK) | Referência ao termo base |
| `ID_ZONA` | LONG (FK) | Referência à zona (nullable) |
| `ID_BAIRRO` | LONG (FK) | Referência ao bairro (nullable) |
| `ID_CIDADE` | LONG (FK) | Referência à cidade (nullable) |
| `TERMO_COMPLETO` | TEXT(255) | Termo final para busca |
| `TIPO_LOCALIZACAO` | TEXT(20) | CAPITAL/ZONA/BAIRRO/CIDADE |
| `STATUS_PROCESSAMENTO` | TEXT(20) | PENDENTE/PROCESSANDO/CONCLUIDO/ERRO |
| `DATA_CRIACAO` | DATE | Data de criação |
| `DATA_PROCESSAMENTO` | DATE | Data do processamento |

**Exemplo de Registros:**
- "empresa de elevadores São Paulo SP" (CAPITAL)
- "empresa de elevadores zona norte São Paulo SP" (ZONA)
- "empresa de elevadores Moema São Paulo SP" (BAIRRO)
- "empresa de elevadores Campinas SP" (CIDADE)

### **6. TB_EMPRESAS** ⭐
Armazena as empresas encontradas durante a busca.

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `ID_EMPRESA` | COUNTER (PK) | Identificador único |
| `ID_TERMO` | LONG (FK) | Termo que encontrou a empresa |
| `SITE_URL` | TEXT(255) | URL completa do site |
| `DOMINIO` | TEXT(100) | Domínio extraído (ex: "empresa.com.br") |
| `NOME_EMPRESA` | TEXT(100) | Nome da empresa (se encontrado) |
| `STATUS_COLETA` | TEXT(20) | PENDENTE/COLETADO/ERRO/IGNORADO/SEM_DADOS |
| `DATA_PRIMEIRA_VISITA` | DATE | Primeira vez que foi encontrada |
| `DATA_ULTIMA_VISITA` | DATE | Última tentativa de coleta |
| `TENTATIVAS_COLETA` | LONG | Número de tentativas |
| `MOTOR_BUSCA` | TEXT(20) | GOOGLE/DUCKDUCKGO |

### **7. TB_EMAILS**
Armazena os e-mails coletados de cada empresa.

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `ID_EMAIL` | COUNTER (PK) | Identificador único |
| `ID_EMPRESA` | LONG (FK) | Empresa proprietária do e-mail |
| `EMAIL` | TEXT(200) | E-mail completo |
| `DOMINIO_EMAIL` | TEXT(100) | Domínio do e-mail |
| `VALIDADO` | BIT | Se passou na validação |
| `DATA_COLETA` | DATE | Data da coleta |
| `ORIGEM_COLETA` | TEXT(20) | CONTATO/RODAPE/CABECALHO/TEXTO |

### **8. TB_TELEFONES**
Armazena os telefones coletados de cada empresa.

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `ID_TELEFONE` | COUNTER (PK) | Identificador único |
| `ID_EMPRESA` | LONG (FK) | Empresa proprietária do telefone |
| `TELEFONE` | TEXT(20) | Telefone original encontrado |
| `TELEFONE_FORMATADO` | TEXT(20) | Telefone formatado (ex: "(11) 99999-9999") |
| `DDD` | TEXT(2) | DDD extraído |
| `TIPO_TELEFONE` | TEXT(10) | FIXO/CELULAR/WHATSAPP |
| `VALIDADO` | BIT | Se passou na validação |
| `DATA_COLETA` | DATE | Data da coleta |

## 🔗 Relacionamentos

```
TB_BASE_BUSCA (1) ──→ (N) TB_TERMOS_BUSCA
TB_ZONAS (1) ──→ (N) TB_TERMOS_BUSCA
TB_BAIRROS (1) ──→ (N) TB_TERMOS_BUSCA  
TB_CIDADES (1) ──→ (N) TB_TERMOS_BUSCA
TB_TERMOS_BUSCA (1) ──→ (N) TB_EMPRESAS
TB_EMPRESAS (1) ──→ (N) TB_EMAILS
TB_EMPRESAS (1) ──→ (N) TB_TELEFONES
```

## 📊 Consultas Úteis

### **Progresso da Coleta**
```sql
SELECT 
    COUNT(*) as Total_Termos,
    SUM(IIF(STATUS_PROCESSAMENTO = 'CONCLUIDO', 1, 0)) as Concluidos,
    SUM(IIF(STATUS_PROCESSAMENTO = 'PENDENTE', 1, 0)) as Pendentes
FROM TB_TERMOS_BUSCA;
```

### **Empresas com Mais E-mails**
```sql
SELECT 
    e.DOMINIO,
    e.NOME_EMPRESA,
    COUNT(em.ID_EMAIL) as Total_Emails
FROM TB_EMPRESAS e
LEFT JOIN TB_EMAILS em ON e.ID_EMPRESA = em.ID_EMPRESA
GROUP BY e.DOMINIO, e.NOME_EMPRESA
ORDER BY Total_Emails DESC;
```

### **Relatório de Coleta por Motor de Busca**
```sql
SELECT 
    MOTOR_BUSCA,
    COUNT(*) as Total_Empresas,
    SUM(IIF(STATUS_COLETA = 'COLETADO', 1, 0)) as Com_Dados
FROM TB_EMPRESAS
GROUP BY MOTOR_BUSCA;
```

### **Exportação para Excel (Formato Atual)**
```sql
SELECT DISTINCT 
    e.SITE_URL as SITE,
    (SELECT STRING_AGG(EMAIL, ';') FROM TB_EMAILS WHERE ID_EMPRESA = e.ID_EMPRESA) + ';' as EMAIL,
    (SELECT STRING_AGG(TELEFONE_FORMATADO, ';') FROM TB_TELEFONES WHERE ID_EMPRESA = e.ID_EMPRESA) + ';' as TELEFONE
FROM TB_EMPRESAS e
WHERE e.STATUS_COLETA = 'COLETADO';
```

## 🔄 Operações de Manutenção

### **Reset Completo (Manter Configurações)**
```sql
DELETE FROM TB_TELEFONES;
DELETE FROM TB_EMAILS;
DELETE FROM TB_EMPRESAS;
UPDATE TB_TERMOS_BUSCA SET STATUS_PROCESSAMENTO = 'PENDENTE', DATA_PROCESSAMENTO = NULL;
```

### **Reprocessar Termos com Erro**
```sql
UPDATE TB_TERMOS_BUSCA 
SET STATUS_PROCESSAMENTO = 'PENDENTE', DATA_PROCESSAMENTO = NULL
WHERE STATUS_PROCESSAMENTO = 'ERRO';
```

### **Limpar Dados de Teste**
```sql
DELETE FROM TB_TERMOS_BUSCA WHERE TERMO_COMPLETO LIKE '%teste%';
```

## 📈 Índices Recomendados

Para melhor performance, criar índices em:
- `TB_EMPRESAS.DOMINIO`
- `TB_EMPRESAS.STATUS_COLETA`
- `TB_EMAILS.EMAIL`
- `TB_TERMOS_BUSCA.STATUS_PROCESSAMENTO`

## 🔧 Backup e Manutenção

### **Backup Diário**
- Copiar `data/pythonsearch.accdb` para local seguro
- Manter histórico de 30 dias

### **Compactação**
- Usar "Compactar e Reparar" do Access mensalmente
- Monitora tamanho do arquivo (limite ~2GB)

### **Monitoramento**
- Verificar integridade dos relacionamentos
- Validar consistência dos dados
- Monitorar performance das consultas