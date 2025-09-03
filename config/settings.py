"""
Configurações do PythonSearchApp - coletor de e-mails
"""
import os
from src.infrastructure.config.config_manager import ConfigManager

# Inicializa gerenciador de configuração
config = ConfigManager()

# Diretórios e arquivos
BASE_DIR = os.getcwd()
DATA_DIR = os.path.join(BASE_DIR, "data")
OUTPUT_DIR = os.path.join(BASE_DIR, "output")
OUTPUT_XLSX = os.path.join(OUTPUT_DIR, "empresas.xlsx")
VISITED_JSON = os.path.join(DATA_DIR, "visited.json")
SEEN_EMAILS_JSON = os.path.join(DATA_DIR, "emails.json")

# Horários removidos - aplicação funciona 24h

# Coleta - via configuração
MAX_EMAILS_PER_SITE = config.max_emails_per_site
SEARCH_DWELL = config.search_dwell_delay
RESULTS_PER_TERM_LIMIT = config.results_per_term_limit

# Constantes de validação - via configuração
COMPLETE_MODE_THRESHOLD = config.complete_mode_threshold
MAX_PHONES_PER_SITE = config.max_phones_per_site

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
    "Campinas", "Guarulhos", "Santo André","São Bernardo do Campo", "São Caetano do Sul",
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



# Delays rápidos - via configuração
SCRAPER_DELAYS = {
    "page_load": config.page_load_delay,
    "scroll": config.scroll_delay
}

# Blacklist
BLACKLIST_HOSTS = [
    # Redes sociais
    "facebook.com", "instagram.com", "linkedin.com", "youtube.com", "x.com", "twitter.com",
    "tiktok.com", "pinterest.com", "snapchat.com", "whatsapp.com", "telegram.org",
    "discord.com", "reddit.com", "tumblr.com", "flickr.com", "vimeo.com",
    
    # Portais de notícias
    "uol.com.br", "globo.com", "folha.uol.com.br", "estadao.com.br", "g1.globo.com",
    "r7.com", "band.uol.com.br", "sbt.com.br", "cnn.com.br", "bbc.com",
    "terra.com.br", "ig.com.br", "msn.com", "yahoo.com", "bol.uol.com.br",
    "exame.com", "valor.com.br", "infomoney.com.br", "istoedinheiro.com.br",
    "cartacapital.com.br", "veja.abril.com.br", "epoca.globo.com", "noticias",
    
    # Blogs e plataformas de conteúdo
    "medium.com", "wordpress.com", "blogspot.com", "blogger.com", "wix.com",
    "squarespace.com", "weebly.com", "ghost.org", "substack.com",
    
    # Marketplaces e classificados
    "mercadolivre.com", "olx.com", "enjoei.com.br", "webmotors.com.br",
    "imovelweb.com.br", "zapimoveis.com.br", "vivareal.com.br", "booking.com",
    "airbnb.com", "trivago.com", "decolar.com", "submarino.com.br", "americanas.com",
    
    # Mapas e navegação
    "maps.google", "goo.gl", "waze.com", "openstreetmap.org", "here.com",
    
    # Sites governamentais e institucionais
    "gov.br", "prefeitura", "camara", "senado", "tse.jus.br", "receita.fazenda.gov.br",
    
    # Documentos e arquivos
    "docplayer", "issuu.com", "scribd.com", "slideshare.net", "pdf", "academia.edu",
    
    # Enciclopédias e referências
    "wikipedia.org", "wikimedia.org", "britannica.com", "dicionario",
    
    # Reclamações e avaliações
    "reclameaqui.com.br", "consumidor.gov.br", "procon", "trustpilot.com",
    
    # Outros sites não comerciais
    "coteibem.sindiconet.com.br", "sindiconet.com.br", "condominio", "sindico",
    "forum", "faq", "suporte", "help", "support", "wiki", "manual"
]

# Domínios suspeitos para e-mails
SUSPICIOUS_EMAIL_DOMAINS = [
    'sentry.io', 'sentry.wixpress.com', 'sentry-next.wixpress.com',
    'example.com', 'test.com', 'localhost', '127.0.0.1'
]