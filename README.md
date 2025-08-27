# 🤖 ROBO 2 - COLETOR DE E-MAILS (ELEVADORES)

Robô Python especializado em coleta de e-mails de empresas de elevadores usando DuckDuckGo, Firefox e Selenium com arquitetura em 3 camadas.

## 📋 O que o Robô Faz

- **Busca profunda** por termos de elevadores em SP (capital, zonas, bairros, interior)
- **Abre resultados** e simula navegação humana com scroll
- **Extrai dados completos**: nome, telefone, e-mails, endereço e site
- **Controle inteligente**: evita revisitar sites já processados
- **Duplo salvamento**: Excel formatado + CSV para import
- **Pasta organizada**: salva em C:/Arquivos/
- **Chrome visível** para monitoramento em tempo real
- **Opção de reiniciar** do zero ou continuar anterior

## 🏗️ Arquitetura - 3 Camadas

```
📁 RoboApp/
├── 🔵 src/domain/              # CAMADA DE DOMÍNIO
│   └── email_processor.py      # Entidades e regras de negócio
├── 🟡 src/infrastructure/      # CAMADA DE INFRAESTRUTURA
│   ├── web_driver.py           # Gerenciamento Chrome/Selenium
│   ├── scrapers/               # Web scraping
│   └── repositories/           # Persistência Excel/CSV/JSON
├── 🟢 src/application/         # CAMADA DE APLICAÇÃO
│   └── email_robot_service.py  # Orquestração e casos de uso
├── ⚙️ config/
│   └── settings.py             # Configurações centralizadas
├── 📜 scripts/                 # Scripts utilitários
│   ├── verificar_instalacao.py
│   ├── verificar_instalacao_chrome.py
│   └── baixar_chromedriver.py
├── 💾 drivers/                 # Drivers de navegação
│   └── chromedriver.exe        # ChromeDriver
├── 💾 drivers/                 # Drivers de navegação
│   └── chromedriver.exe        # ChromeDriver
├── 💾 data/                    # Dados de controle
│   ├── visited.json            # Domínios visitados
│   └── emails.json             # E-mails coletados
├── 📊 output/                  # Arquivos de saída
│   └── empresas.xlsx           # Planilha Excel
└── 🚀 main.py                  # Ponto de entrada
```

### 🔵 Camada de Domínio
- **Company**: Entidade empresa com e-mails
- **SearchTerm**: Termos de busca estruturados
- **EmailValidationService**: Validação de e-mails
- **WorkingHoursService**: Controle de horário
- **SearchTermBuilder**: Constrói termos para elevadores

### 🟡 Camada de Infraestrutura
- **WebDriverManager**: Controla Firefox
- **DuckDuckGoScraper**: Busca e extração no DuckDuckGo
- **JsonRepository**: Controle de visitados/e-mails
- **ExcelRepository**: Persistência em Excel

### 🟢 Camada de Aplicação
- **EmailCollectorService**: Orquestra coleta completa
- **Fluxo inteligente**: Busca → Extração → Deduplicação → Salvamento

## 🚀 Como Executar

### Pré-requisitos
- Python 3.11+
- Google Chrome instalado
- ChromeDriver (baixa automaticamente)

### Instalação
1. **ChromeDriver Automático**:
   - O robô detecta sua versão do Chrome
   - Baixa ChromeDriver compatível automaticamente
   - Nenhuma configuração manual necessária

2. **Executar**:
   ```cmd
   iniciar_robo.bat
   ```

### Execução Manual
```cmd
python -m pip install -r requirements.txt
python main.py
```

### Modo Teste
Para execução rápida com poucos termos:
1. Edite `config/settings.py`
2. Altere `IS_TEST_MODE = True`
3. Execute `python main.py`

- **Teste**: 2 termos apenas
- **Produção**: 336 termos completos

## 📦 Dependências

- **selenium**: Automação web
- **openpyxl**: Manipulação Excel
- **tldextract**: Processamento domínios

## 🧪 Testes

```cmd
python -m pytest tests/
```

## ⚙️ Configurações

Edite `config/settings.py` para personalizar:
- Timeouts
- Caminhos de arquivos
- URLs
- Dimensões do navegador

### Modo de Execução
- `IS_TEST_MODE = True` - Ativa modo teste (poucos termos)
- `IS_TEST_MODE = False` - Modo produção (todos os termos)

## 📊 Saída

O robô gera:
- **output/empresas.xlsx**: Planilha com SITE | EMAIL
- **data/visited.json**: Controle de domínios já visitados
- **data/emails.json**: Controle de e-mails já coletados
- **Logs detalhados**: Progresso em tempo real

## 🎯 Especificações Técnicas

### Modo Produção
- **Termos de busca**: 6 bases x (1 capital + 5 zonas + 30 bairros + 20 cidades) = 336 termos
- **Páginas por termo**: Capital(80), Zona(25), Bairro(12), Interior(20)

### Modo Teste
- **Termos de busca**: 2 termos apenas (BASE_TESTES)
- **Execução rápida**: Para desenvolvimento e validação

### Geral
- **E-mails por site**: Máximo 5 e-mails válidos
- **Simulação humana**: Scroll aleatório, pausas variáveis
- **Horário**: Funciona apenas entre 8h-22h
- **Deduplicação**: Por domínio e por e-mail

## 🔧 Extensibilidade

Para adicionar novos provedores de e-mail:
1. Crie novo scraper em `infrastructure/`
2. Implemente interface `EmailProcessorInterface`
3. Registre no `EmailRobotService`

## 📝 Logs

- `[INFO]`: Informações gerais
- `[OK]`: Operações bem-sucedidas  
- `[ERRO]`: Falhas na execução