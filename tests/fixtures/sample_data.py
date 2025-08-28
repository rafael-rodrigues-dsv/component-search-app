"""
Dados de exemplo para testes
"""
from src.domain.models.company_model import CompanyModel
from src.domain.models.search_term_model import SearchTermModel

# Dados de exemplo para testes
SAMPLE_COMPANY = CompanyModel(
    name="Empresa Teste",
    emails="test@example.com;admin@example.com;",
    domain="example.com",
    url="https://example.com",
    search_term="empresa de elevadores",
    address="Rua Teste, 123",
    phone="(11) 99999-9999;"
)

SAMPLE_SEARCH_TERM = SearchTermModel(
    query="empresa de elevadores São Paulo",
    location="SP",
    category="elevadores",
    pages=5
)

SAMPLE_URLS = [
    "https://example1.com",
    "https://example2.com",
    "https://example3.com"
]

SAMPLE_EMAILS = [
    "valid@example.com",
    "test@company.com.br",
    "contato@elevadores.net"
]

SAMPLE_PHONES = [
    "(11) 99999-8888",
    "(11) 3333-4444",
    "(21) 98765-4321"
]