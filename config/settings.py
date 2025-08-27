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
TIME_BETWEEN_OUT_OF_HOURS = 120

# Coleta
MAX_EMAILS_PER_SITE = 5
SCROLL_STEPS = (6, 10)
SCROLL_PAUSE = (0.8, 2.0)
SITE_DWELL_TIME = (6, 12)
SEARCH_DWELL = (1.2, 2.4)
RESULTS_PER_TERM_LIMIT = 1200

# Páginas por tipo
PAGES_CAPITAL = 80
PAGES_ZONA = 25
PAGES_BAIRRO = 12
PAGES_INTERIOR = 20

# Zonas SP
ZONAS_SP = ["zona norte", "zona sul", "zona leste", "zona oeste", "zona central"]

# Bairros SP
BAIRROS_SP = [
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

# Termos elevadores
BASE_ELEVADORES = [
    "empresa de elevadores", "manutenção de elevadores", "instalação de elevadores",
    "modernização de elevadores", "assistência técnica elevadores", "elevadores residenciais"
]

# Termos para testes
BASE_TESTES = [
    "empresa de elevadores", "manutenção de elevadores"
]

# Configurações de busca
SEARCH_LOCATION = "SP"
SEARCH_CATEGORY = "elevadores"

# Modo de execução
IS_TEST_MODE = True  # True para teste (poucos termos), False para produção (todos os termos)

# Blacklist
BLACKLIST_HOSTS = [
    "facebook.com", "instagram.com", "linkedin.com", "youtube.com", "x.com", "twitter.com",
    "maps.google", "goo.gl", "waze.com", "wikipedia.org", "mercadolivre.com", "olx.com",
    "gov.br", "docplayer", "issuu.com", "uol.com.br", "noticias", "pdf"
]