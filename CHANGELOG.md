# 📋 CHANGELOG

## [2.0.0] - 2024-12-19

### 🔄 BREAKING CHANGES

- **Migração completa de JSON para Microsoft Access**: Sistema de armazenamento totalmente reformulado
- **Nova arquitetura de banco de dados**: 8 tabelas normalizadas substituindo arquivos JSON
- **Criação automática de banco**: Sistema detecta e cria banco automaticamente na inicialização

### ✨ NEW FEATURES

- **DatabaseService**: Nova camada de serviço para operações de banco de dados
- **AccessRepository**: Repositório completo para Microsoft Access com 100% de cobertura de testes
- **Criação automática de estrutura**: Scripts para criar banco com dados básicos ou completos
- **Export automático para Excel**: Geração automática de planilha a partir do banco
- **Scripts multiplataforma**: Versões .bat (Windows) e .sh (Linux/macOS) para todos os utilitários

### 🏗️ ARCHITECTURE

- **Clean Architecture mantida**: Separação clara entre domínio, aplicação e infraestrutura
- **Eliminação de dependência JSON**: Remoção completa dos arquivos visited.json e emails.json
- **Padronização de nomes**: Scripts renomeados de português para inglês

### 🧪 TESTING

- **Cobertura de testes**: Aumentada de 81% para 93% (261 testes passando)
- **Novos testes de integração**: Cobertura completa das funcionalidades de banco de dados
- **Testes de repositório**: 100% de cobertura para AccessRepository

### 🔧 IMPROVEMENTS

- **Performance**: Operações de banco mais eficientes que JSON
- **Confiabilidade**: Transações ACID e controle de integridade
- **Auditoria**: Logs detalhados de todas as operações
- **Multiplataforma**: Suporte completo para Windows, Linux e macOS

### 🐛 BUG FIXES

- **Correção de paths**: Atualizadas todas as referências para novos nomes de arquivos
- **Dependências**: pyodbc adicionado corretamente ao pyproject.toml
- **Scripts de inicialização**: Paths corrigidos para scripts de verificação

### 📚 DOCUMENTATION

- **README atualizado**: Documentação completa da nova arquitetura
- **Instruções de migração**: Guia para transição da versão 1.x
- **Scripts de setup**: Documentação dos novos utilitários

---

## [1.0.0] - 2024-12-18

### ✨ INITIAL RELEASE

- **Sistema de coleta**: Extração de e-mails e telefones via Google/DuckDuckGo
- **Clean Architecture**: Implementação completa com separação de camadas
- **Armazenamento JSON**: Sistema de persistência baseado em arquivos JSON
- **Validação rigorosa**: Filtros para e-mails e telefones inválidos
- **Controle de duplicatas**: Evita revisitar sites já processados
- **Modo teste/produção**: Configurações flexíveis para desenvolvimento
- **Suporte multiplataforma**: Windows, Linux e macOS
- **Cobertura de testes**: 81% de cobertura com testes unitários