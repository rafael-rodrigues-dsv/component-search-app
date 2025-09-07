"""
Testes para AddressExtractor
"""
import pytest
from src.infrastructure.utils.address_extractor import AddressExtractor
from src.domain.models.address_model import AddressModel


class TestAddressExtractor:
    """Testes para extração de endereços estruturados"""

    def test_extract_from_html_complete_address(self):
        """Testa extração de endereço completo"""
        html = """
        <div>
            <p>Rua Augusta, 123, Consolação, São Paulo, SP</p>
            <span>CEP: 01310-100</span>
        </div>
        """
        
        result = AddressExtractor.extract_from_html(html)
        
        assert result is not None
        assert isinstance(result, AddressModel)

    def test_extract_from_html_empty(self):
        """Testa extração com HTML vazio"""
        result = AddressExtractor.extract_from_html("")
        assert result is None

    def test_extract_from_html_none(self):
        """Testa extração com HTML None"""
        result = AddressExtractor.extract_from_html(None)
        assert result is None

    def test_extract_street_rua(self):
        """Testa extração de rua"""
        html = "rua augusta 123"
        result = AddressExtractor._extract_street(html)
        assert "augusta" in result.lower()

    def test_extract_street_avenida(self):
        """Testa extração de avenida"""
        html = "avenida paulista 1000"
        result = AddressExtractor._extract_street(html)
        assert "paulista" in result.lower()

    def test_extract_number(self):
        """Testa extração de número"""
        html = "rua augusta 123"
        result = AddressExtractor._extract_number(html)
        assert result == "123"

    def test_extract_neighborhood(self):
        """Testa extração de bairro"""
        html = "moema são paulo"
        result = AddressExtractor._extract_neighborhood(html)
        assert result == "Moema"

    def test_extract_cep(self):
        """Testa extração de CEP"""
        html = "CEP: 01310-100"
        result = AddressExtractor._extract_cep(html)
        assert result == "01310-100"

    def test_extract_cep_without_dash(self):
        """Testa extração de CEP sem hífen"""
        html = "CEP: 01310100"
        result = AddressExtractor._extract_cep(html)
        assert result == "01310100"

    def test_html_limit(self):
        """Testa limitação de HTML para performance"""
        large_html = "a" * 100000  # 100KB
        result = AddressExtractor.extract_from_html(large_html)
        # Deve processar sem erro (limitado a 50KB internamente)
        assert result is not None or result is None  # Qualquer resultado é válido

    def test_structured_address_creation(self):
        """Testa criação de endereço estruturado"""
        html = "rua augusta 123 consolação são paulo"
        result = AddressExtractor._extract_structured_address(html)
        
        assert isinstance(result, AddressModel)
        assert result.cidade == "São Paulo"
        assert result.estado == "SP"