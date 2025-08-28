"""
Configurações do PythonSearchApp - coletor de e-mails
"""
import os

# Diretórios e arquivos
BASE_DIR = os.getcwd()
DATA_DIR = os.path.join(BASE_DIR, "data")
OUTPUT_DIR = os.path.join(BASE_DIR, "output")
OUTPUT_XLSX = os.path.join(OUTPUT_DIR, "empresas.xlsx")
VISITED_JSON = os.path.join(DATA_DIR, "visited.json")
SEEN_EMAILS_JSON = os.path.join(DATA_DIR, "emails.json")

# Horários de trabalho (24h)
START_HOUR = 8
END_HOUR = 22
OUT_OF_HOURS_WAIT_SECONDS = 120

# Coleta
MAX_EMAILS_PER_SITE = 5
SEARCH_DWELL = (1.2, 2.4)
RESULTS_PER_TERM_LIMIT = 1200

# Zonas SP
BASE_ZONAS = ["zona norte", "zona sul", "zona leste", "zona oeste", "zona central"]

# Bairros SP
BASE_BAIRROS = [
    "Moema", "Vila Mariana", "Pinheiros", "Itaim Bibi", "Brooklin", "Campo Belo",
    "Saúde", "Santo Amaro", "Morumbi", "Tatuapé", "Anália Franco", "Carrão", "Penha",
    "Vila Prudente", "Ipiranga", "Liberdade", "Sé", "Bela Vista", "Higienópolis",
    "Santana", "Tucuruvi", "Casa Verde", "Freguesia do Ó", "Lapa", "Butantã",
    "Pompéia", "Perdizes", "Barra Funda", "Mooca", "Brás"
]

# Cidades interior
CIDADES_INTERIOR = [
    "Campinas", "Guarulhos", "Santo André", "São Bernardo do Campo", "São Caetano do Sul",
    "Osasco", "Barueri", "Carapicuíba", "Mogi das Cruzes", "Suzano", "Jundiaí", "Sorocaba",
    "Ribeirão Preto", "Bauru", "São José dos Campos", "Taubaté", "Santos", "Praia Grande",
    "Americana", "Piracicaba"
]

BASE_BUSCA = [
    "empresa de elevadores", "manutenção de elevadores", "instalação de elevadores",
    "modernização de elevadores", "assistência técnica elevadores", "elevadores residenciais"
]


# Termos para testes
BASE_TESTES = [
    "empresa de elevadores", "manutenção de elevadores"
]

# Alias para compatibilidade
BASE_BUSCA_TESTES = BASE_TESTES

# Configurações de busca
UF_BASE = "SP"
CIDADE_BASE = "São Paulo"
CATEGORIA_BASE = "elevadores"

# Modo de execução
IS_TEST_MODE = True  # True para teste (poucos termos), False para produção (todos os termos)

# Delays rápidos
SCRAPER_DELAYS = {
    "page_load": (2.0, 3.0),  # Aumentado para ver melhor
    "scroll": (1.0, 1.5)     # Aumentado para ver melhor
}

# Blacklist
BLACKLIST_HOSTS = [
    "coteibem.sindiconet.com.br","reclameaqui.com.br", "facebook.com", "instagram.com", "linkedin.com", "youtube.com", "x.com", "twitter.com",
    "maps.google", "goo.gl", "waze.com", "wikipedia.org", "mercadolivre.com", "olx.com",
    "gov.br", "docplayer", "issuu.com", "uol.com.br", "noticias", "pdf"
]

# Domínios suspeitos para e-mails
SUSPICIOUS_EMAIL_DOMAINS = [
    'sentry.io', 'sentry.wixpress.com', 'sentry-next.wixpress.com',
    'example.com', 'test.com', 'localhost', '127.0.0.1'
]