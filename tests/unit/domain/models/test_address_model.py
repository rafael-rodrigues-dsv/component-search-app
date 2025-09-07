"""
Testes para AddressModel
"""
import pytest
from src.domain.models.address_model import AddressModel


class TestAddressModel:
    """Testes para o modelo de endereço estruturado"""

    def test_address_model_creation(self):
        """Testa criação do modelo de endereço"""
        address = AddressModel(
            logradouro="Rua Augusta",
            numero="123",
            bairro="Consolação",
            cidade="São Paulo",
            estado="SP",
            cep="01310-100"
        )
        
        assert address.logradouro == "Rua Augusta"
        assert address.numero == "123"
        assert address.bairro == "Consolação"
        assert address.cidade == "São Paulo"
        assert address.estado == "SP"
        assert address.cep == "01310-100"

    def test_to_full_address(self):
        """Testa conversão para endereço completo"""
        address = AddressModel(
            logradouro="Rua Augusta",
            numero="123",
            bairro="Consolação",
            cidade="São Paulo",
            estado="SP"
        )
        
        result = address.to_full_address()
        assert result == "Rua Augusta, 123, Consolação, São Paulo, SP"

    def test_to_full_address_without_number(self):
        """Testa conversão sem número"""
        address = AddressModel(
            logradouro="Rua Augusta",
            bairro="Consolação",
            cidade="São Paulo",
            estado="SP"
        )
        
        result = address.to_full_address()
        assert result == "Rua Augusta, Consolação, São Paulo, SP"

    def test_is_valid_with_logradouro(self):
        """Testa validação com logradouro"""
        address = AddressModel(logradouro="Rua Augusta")
        assert address.is_valid() is True

    def test_is_valid_with_bairro(self):
        """Testa validação com bairro"""
        address = AddressModel(bairro="Consolação")
        assert address.is_valid() is True

    def test_is_valid_with_cidade(self):
        """Testa validação com cidade"""
        address = AddressModel(cidade="São Paulo")
        assert address.is_valid() is True

    def test_is_valid_empty(self):
        """Testa validação com endereço vazio"""
        address = AddressModel(logradouro="", numero="", bairro="", cidade="", estado="", cep="")
        assert address.is_valid() is False

    def test_defaults(self):
        """Testa valores padrão"""
        address = AddressModel()
        assert address.cidade == "São Paulo"
        assert address.estado == "SP"
        assert address.logradouro == ""
        assert address.numero == ""
        assert address.bairro == ""
        assert address.cep == ""