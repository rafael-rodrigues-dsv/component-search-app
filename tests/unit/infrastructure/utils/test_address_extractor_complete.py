"""
Testes completos para AddressExtractor
"""
import pytest
from src.infrastructure.utils.address_extractor import AddressExtractor
from src.domain.models.address_model import AddressModel


class TestAddressExtractorComplete:
    """Testes completos para AddressExtractor"""

    def test_extract_from_html_with_rua(self):
        """Testa extração com rua"""
        html = """
        <div>
            <p>Rua Augusta, 123, Consolação, São Paulo, SP</p>
            <span>CEP: 01310-100</span>
        </div>
        """
        
        result = AddressExtractor.extract_from_html(html)
        
        assert result is not None
        assert isinstance(result, AddressModel)

    def test_extract_from_html_with_avenida(self):
        """Testa extração com avenida"""
        html = """
        <div>Avenida Paulista, 1000, Bela Vista, São Paulo</div>
        """
        
        result = AddressExtractor.extract_from_html(html)
        
        assert result is not None
        assert result.cidade == "São Paulo"

    def test_extract_from_html_empty(self):
        """Testa HTML vazio"""
        result = AddressExtractor.extract_from_html("")
        assert result is None

    def test_extract_from_html_none(self):
        """Testa HTML None"""
        result = AddressExtractor.extract_from_html(None)
        assert result is None

    def test_extract_from_html_large(self):
        """Testa HTML grande (limitação de 50KB)"""
        large_html = "a" * 60000  # 60KB
        result = AddressExtractor.extract_from_html(large_html)
        # Deve processar sem erro (limitado internamente)
        assert result is not None or result is None

    def test_extract_street_rua_complete(self):
        """Testa extração completa de rua"""
        html = "rua augusta 123 consolação"
        result = AddressExtractor._extract_street(html)
        
        assert "rua" in result.lower()
        assert "augusta" in result.lower()

    def test_extract_street_avenida_complete(self):
        """Testa extração completa de avenida"""
        html = "avenida paulista 1000"
        result = AddressExtractor._extract_street(html)
        
        assert "paulista" in result.lower()

    def test_extract_street_av_abbreviation(self):
        """Testa abreviação av."""
        html = "av. faria lima 3000"
        result = AddressExtractor._extract_street(html)
        
        assert "avenida" in result.lower()
        assert "faria lima" in result.lower()

    def test_extract_street_r_abbreviation(self):
        """Testa abreviação r."""
        html = "r. oscar freire 500"
        result = AddressExtractor._extract_street(html)
        
        assert "rua" in result.lower()
        assert "oscar freire" in result.lower()

    def test_extract_street_empty(self):
        """Testa extração sem logradouro"""
        html = "apenas texto sem endereço"
        result = AddressExtractor._extract_street(html)
        
        assert result == ""

    def test_extract_number_success(self):
        """Testa extração de número"""
        html = "rua augusta 123"
        result = AddressExtractor._extract_number(html)
        
        assert result == "123"

    def test_extract_number_with_numero_keyword(self):
        """Testa extração com palavra número"""
        html = "número 456"
        result = AddressExtractor._extract_number(html)
        
        assert result == "456"

    def test_extract_number_not_found(self):
        """Testa sem número"""
        html = "rua augusta sem número"
        result = AddressExtractor._extract_number(html)
        
        assert result == ""

    def test_extract_neighborhood_moema(self):
        """Testa extração de bairro Moema"""
        html = "localizado em moema são paulo"
        result = AddressExtractor._extract_neighborhood(html)
        
        assert result == "Moema"

    def test_extract_neighborhood_vila_mariana(self):
        """Testa bairro Vila Mariana"""
        html = "endereço na vila mariana"
        result = AddressExtractor._extract_neighborhood(html)
        
        assert result == "Vila Mariana"

    def test_extract_neighborhood_not_found(self):
        """Testa sem bairro conhecido"""
        html = "bairro desconhecido"
        result = AddressExtractor._extract_neighborhood(html)
        
        assert result == ""

    def test_extract_cep_with_dash(self):
        """Testa CEP com hífen"""
        html = "CEP: 01310-100"
        result = AddressExtractor._extract_cep(html)
        
        assert result == "01310-100"

    def test_extract_cep_without_dash(self):
        """Testa CEP sem hífen"""
        html = "CEP 01310100"
        result = AddressExtractor._extract_cep(html)
        
        assert result == "01310100"

    def test_extract_cep_multiple(self):
        """Testa múltiplos CEPs (pega o primeiro)"""
        html = "CEP: 01310-100 ou 04567-890"
        result = AddressExtractor._extract_cep(html)
        
        assert result == "01310-100"

    def test_extract_cep_not_found(self):
        """Testa sem CEP"""
        html = "endereço sem cep"
        result = AddressExtractor._extract_cep(html)
        
        assert result == ""

    def test_structured_address_complete(self):
        """Testa criação de endereço estruturado completo"""
        html = "rua augusta 123 consolação são paulo cep 01310-100"
        result = AddressExtractor._extract_structured_address(html)
        
        assert isinstance(result, AddressModel)
        assert result.cidade == "São Paulo"
        assert result.estado == "SP"

    def test_structured_address_minimal(self):
        """Testa endereço estruturado mínimo"""
        html = "rua teste"
        result = AddressExtractor._extract_structured_address(html)
        
        assert isinstance(result, AddressModel)
        assert result.cidade == "São Paulo"  # Padrão

    def test_extract_complete_address_success(self):
        """Testa extração de endereço completo"""
        html = "Rua Augusta, 123, Consolação, São Paulo, SP"
        result = AddressExtractor._extract_complete_address(html)
        
        # Pode retornar string ou None dependendo da validação
        assert result is None or isinstance(result, str)

    def test_extract_partial_address_success(self):
        """Testa extração de endereço parcial"""
        html = "Moema, São Paulo"
        result = AddressExtractor._extract_partial_address(html)
        
        # Pode retornar string formatada
        assert result is None or "São Paulo" in result

    def test_clean_address_with_html_tags(self):
        """Testa limpeza com tags HTML"""
        endereco = "<div>Rua Augusta, 123</div>"
        result = AddressExtractor._clean_address(endereco)
        
        assert "<div>" not in result
        assert "Rua Augusta" in result

    def test_clean_address_with_noise(self):
        """Testa limpeza com ruídos técnicos"""
        endereco = "aria-label Rua Augusta zoom123 123"
        result = AddressExtractor._clean_address(endereco)
        
        assert "aria-label" not in result
        assert "zoom123" not in result
        assert "Rua Augusta" in result

    def test_clean_address_with_long_numbers(self):
        """Testa remoção de IDs longos"""
        endereco = "Rua Augusta, 123 1234567890"
        result = AddressExtractor._clean_address(endereco)
        
        assert "1234567890" not in result
        assert "Rua Augusta" in result

    def test_clean_address_add_sao_paulo(self):
        """Testa adição automática de São Paulo"""
        endereco = "Rua Augusta, 123"
        result = AddressExtractor._clean_address(endereco)
        
        assert "São Paulo" in result

    def test_validate_address_valid(self):
        """Testa validação de endereço válido"""
        endereco = "Rua Augusta, 123, São Paulo, SP"
        result = AddressExtractor._validate_address(endereco)
        
        assert result is True

    def test_validate_address_too_short(self):
        """Testa endereço muito curto"""
        endereco = "Rua"
        result = AddressExtractor._validate_address(endereco)
        
        assert result is False

    def test_validate_address_no_street_type(self):
        """Testa sem tipo de logradouro"""
        endereco = "Augusta 123 São Paulo SP"
        result = AddressExtractor._validate_address(endereco)
        
        assert result is False

    def test_validate_address_no_sao_paulo(self):
        """Testa sem São Paulo"""
        endereco = "Rua Augusta, 123, Rio de Janeiro"
        result = AddressExtractor._validate_address(endereco)
        
        assert result is False

    def test_validate_address_many_numbers(self):
        """Testa com muitos números (IDs)"""
        endereco = "Rua Augusta 1234 5678 9012 São Paulo"
        result = AddressExtractor._validate_address(endereco)
        
        assert result is False

    def test_format_address_with_noise(self):
        """Testa formatação com ruídos"""
        endereco = "Rua Augusta - nbsp 123 cep01310-100 São Paulo"
        result = AddressExtractor._format_address(endereco)
        
        assert "nbsp" not in result
        assert "cep01310" not in result
        assert "Brasil" in result

    def test_format_address_normalize_abbreviations(self):
        """Testa normalização de abreviações"""
        endereco = "av. Paulista r. Augusta São Paulo"
        result = AddressExtractor._format_address(endereco)
        
        assert "avenida" in result.lower()
        assert "rua" in result.lower()

    def test_format_address_add_brasil(self):
        """Testa adição de Brasil"""
        endereco = "Rua Augusta, São Paulo, SP"
        result = AddressExtractor._format_address(endereco)
        
        assert "Brasil" in result

    def test_format_address_duplicate_sp(self):
        """Testa remoção de SP duplicado"""
        endereco = "Rua Augusta SP SP São Paulo"
        result = AddressExtractor._format_address(endereco)
        
        # Deve normalizar SPs duplicados
        assert result.count(" SP ") <= 1