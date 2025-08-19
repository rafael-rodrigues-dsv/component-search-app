# 🤖 ROBO 2 - COLETOR DE E-MAILS (ELEVADORES)

Robô Python especializado em coleta de e-mails de empresas de elevadores usando DuckDuckGo, Firefox e Selenium com arquitetura em 3 camadas.

## 📋 O que o Robô Faz

- **Busca profunda** por termos de elevadores em SP (capital, zonas, bairros, interior)
- **Abre resultados** e simula navegação humana com scroll
- **Extrai até 5 e-mails válidos** por site visitado
- **Deduplica** sites e e-mails automaticamente
- **Salva em Excel** formato: NOME | EMAIL (separados por ';')
- **Respeita horário** de trabalho (8h-22h configurado)
- **Firefox visível** para monitoramento em tempo real

## 🏗️ Arquitetura - 3 Camadas

```
📁 RoboApp/
├── 🔵 src/domain/              # CAMADA DE DOMÍNIO
│   └── email_processor.py      # Entidades e regras de negócio
├── 🟡 src/infrastructure/      # CAMADA DE INFRAESTRUTURA
│   ├── web_driver.py           # Gerenciamento Firefox/Selenium
│   ├── email_scraper.py        # Web scraping de e-mails
│   └── excel_repository.py     # Persistência em Excel
├── 🟢 src/application/         # CAMADA DE APLICAÇÃO
│   └── email_robot_service.py  # Orquestração e casos de uso
├── ⚙️ config/
│   └── settings.py             # Configurações centralizadas
├── 🧪 tests/
│   └── test_email_processor.py # Testes unitários
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
- Firefox instalado
- GeckoDriver

### Instalação
1. **Baixar GeckoDriver**:
   - Acesse: https://github.com/mozilla/geckodriver/releases
   - Baixe versão Windows
   - Extraia `geckodriver.exe` na pasta do projeto

2. **Executar**:
   ```cmd
   iniciar_robo.bat
   ```

### Execução Manual
```cmd
python -m pip install -r requirements.txt
python main.py
```

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

## 📊 Saída

O robô gera:
- **empresas.xlsx**: Planilha com NOME | EMAIL (e-mails separados por ';')
- **visited.json**: Controle de domínios já visitados
- **emails.json**: Controle de e-mails já coletados
- **Logs detalhados**: Progresso em tempo real

## 🎯 Especificações Técnicas

- **Termos de busca**: 6 bases x (1 capital + 5 zonas + 30 bairros + 20 cidades) = 336 termos
- **Páginas por termo**: Capital(80), Zona(25), Bairro(12), Interior(20)
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