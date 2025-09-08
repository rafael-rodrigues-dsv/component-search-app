# 🌐 Dashboard Web Integrado

Dashboard web em tempo real para monitoramento do Python Search App.

## 🚀 Funcionalidades

- **Monitoramento em tempo real** via WebSocket
- **Interface responsiva** com design moderno
- **Gráficos dinâmicos** de progresso
- **Integração automática** com o console
- **Abertura automática** do navegador

## 📊 Métricas Monitoradas

### Coleta de Dados
- Termos processados com barra de progresso
- Empresas encontradas
- E-mails coletados
- Telefones coletados

### Enriquecimento CEP
- CEPs processados via ViaCEP
- Taxa de sucesso do enriquecimento

### Geolocalização
- Endereços geocodificados via Nominatim
- Taxa de sucesso da geocodificação

## 🔧 Tecnologias

- **Flask** - Servidor web
- **Socket.IO** - Comunicação em tempo real
- **Chart.js** - Gráficos interativos
- **CSS3** - Interface moderna com gradientes

## 🎯 Uso

O dashboard é iniciado automaticamente quando você escolhe as opções 1, 2 ou 3 no menu principal:

1. **Processar coleta de dados** → Dashboard + Coleta
2. **Enriquecer endereços** → Dashboard + Enriquecimento CEP
3. **Processar geolocalização** → Dashboard + Geocodificação

### URL de Acesso
```
http://127.0.0.1:5000
```

## 📱 Interface

- **Cards informativos** com métricas em tempo real
- **Barras de progresso** animadas
- **Gráfico de linha** com histórico dos últimos 20 pontos
- **Status de conexão** em tempo real
- **Design responsivo** para desktop e mobile

## ⚙️ Configuração

Configurações disponíveis em `src/resources/application.yaml`:

```yaml
dashboard:
  enabled: true
  port: 5000
  auto_open_browser: true
  update_interval_seconds: 2
```

## 🔄 Fluxo de Integração

1. Usuário executa `iniciar_robo_simples.bat`
2. Escolhe opção 1, 2 ou 3 no menu
3. Dashboard inicia automaticamente em thread separada
4. Navegador abre automaticamente
5. Processamento continua no console
6. Dashboard mostra progresso em tempo real
7. Dashboard para automaticamente ao finalizar