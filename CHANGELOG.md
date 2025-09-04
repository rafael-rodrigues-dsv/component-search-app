# Changelog

Todas as mudanças notáveis neste projeto serão documentadas neste arquivo.

## [2.1.0] - 2024-12-19

### ✨ Adicionado
- **Geolocalização Automática**: Sistema completo de extração de endereços e cálculo de distâncias
- **GeolocationService**: Novo serviço para geocodificação usando APIs gratuitas (Nominatim + ViaCEP)
- **Extração Seletiva de Endereços**: 
  - Cenário ideal: Endereço completo com rua, número, bairro (±10-50m precisão)
  - Cenário parcial: Cidade/bairro extraído do HTML (±2-5km precisão)
  - Sem fallback: Só geocodifica endereços reais encontrados no site
- **Cálculo de Distâncias**: Fórmula de Haversine para calcular distância em km do ponto de referência
- **Novas Colunas no Banco**:
  - TB_EMPRESAS: `ENDERECO`, `LATITUDE`, `LONGITUDE`, `DISTANCIA_KM`
  - TB_PLANILHA: `ENDERECO`, `DISTANCIA_KM`
- **Excel Ordenado por Proximidade**: Planilha agora inclui endereço e distância, ordenada por proximidade
- **Configuração de CEP de Referência**: Configurável via `application.yaml`
- **Testes Completos**: 19 novos testes para funcionalidades de geolocalização

### 🔧 Modificado
- **CompanyModel**: Adicionado campo `html_content` para captura de HTML das páginas
- **Scrapers**: DuckDuckGo e Google agora capturam HTML content para extração de endereços
- **AccessRepository**: Métodos atualizados para suportar dados de geolocalização
- **DatabaseService**: Integração com GeolocationService para processamento em tempo real
- **Excel Export**: Agora inclui colunas ENDERECO e DISTANCIA_KM, ordenado por proximidade
- **Estrutura do Projeto**: Novo diretório `src/infrastructure/services/`

### 📋 Detalhes Técnicos
- **APIs Utilizadas**: 
  - Nominatim (OpenStreetMap) - Geocodificação gratuita
  - ViaCEP - Consulta de CEPs brasileiros
- **Rate Limiting**: Implementado para APIs externas (1 segundo entre requests)
- **Geocodificação Seletiva**: Só processa endereços reais extraídos do HTML, eliminando geocodificações desnecessárias
- **Validação**: Coordenadas e distâncias validadas antes do armazenamento
- **Performance**: Processamento otimizado - só geocodifica quando há endereço real, reduzindo chamadas de API

### 🧪 Testes
- **Cobertura Atualizada**: 95% de cobertura de código
- **Novos Testes**:
  - `test_geolocation_service.py`: 9 testes para GeolocationService
  - `test_scrapers_geolocation.py`: 4 testes para integração com scrapers
  - Testes atualizados para AccessRepository, DatabaseService e CompanyModel
- **Compatibilidade**: Todos os testes existentes continuam passando

### 🗂️ Estrutura de Dados
```
TB_EMPRESAS:
- ENDERECO (TEXT): Endereço completo extraído
- LATITUDE (DOUBLE): Coordenada de latitude
- LONGITUDE (DOUBLE): Coordenada de longitude  
- DISTANCIA_KM (DOUBLE): Distância em km do ponto de referência

TB_PLANILHA:
- ENDERECO (TEXT): Endereço da empresa
- DISTANCIA_KM (DOUBLE): Distância em km
```

### 📊 Formato Excel Atualizado
```
SITE | EMAIL | TELEFONE | ENDERECO | DISTANCIA_KM
```
- Ordenado por proximidade (menor distância primeiro)
- Endereços formatados e limpos
- Distâncias em quilômetros com 2 casas decimais

---

## [2.0.0] - 2024-12-15

### ✨ Adicionado
- **Clean Architecture**: Implementação completa com separação de camadas
- **Banco Access**: Substituição completa do sistema JSON por banco Access
- **9 Tabelas Normalizadas**: Estrutura robusta para dados empresariais
- **Sistema de Termos**: Geração automática de 336+ termos de busca
- **Controle de Status**: Rastreamento completo do processamento
- **Validação Avançada**: Sistema robusto de validação de e-mails e telefones

### 🔧 Modificado
- **Arquitetura Completa**: Migração para Clean Architecture
- **Persistência**: JSON → Microsoft Access
- **Performance**: Otimizações significativas de velocidade
- **Logs Estruturados**: Sistema de logging contextual

### 🗑️ Removido
- **Sistema JSON**: Arquivos visited.json e emails.json
- **Dependências Legadas**: Limpeza de código antigo

---

## [1.x.x] - Versões Anteriores

### Funcionalidades Base
- Scraping básico com Selenium
- Suporte a Google e DuckDuckGo  
- Extração de e-mails e telefones
- Exportação para Excel
- Sistema de blacklist
- Controle de horário de funcionamento