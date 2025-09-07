"""
Testes corrigidos para GeolocationService
"""
import pytest
from unittest.mock import Mock, patch
from src.infrastructure.services.geolocation_service import GeolocationService, GeoResult


class TestGeolocationService:
    """Testes para GeolocationService"""

    def setup_method(self):
        """Setup para cada teste"""
        with patch('src.infrastructure.config.config_manager.ConfigManager'):
            self.service = GeolocationService()

    def test_extrair_endereco_do_html(self):
        """Testa extração de endereço do HTML"""
        html = "<div>Rua Augusta, 123, São Paulo</div>"
        
        with patch('src.infrastructure.utils.address_extractor.AddressExtractor.extract_from_html') as mock_extract:
            mock_extract.return_value = "Rua Augusta, 123"
            result = self.service.extrair_endereco_do_html(html)
            assert result == "Rua Augusta, 123"

    @patch('requests.Session.get')
    def test_geocodificar_endereco_sucesso(self, mock_get):
        """Testa geocodificação bem-sucedida"""
        mock_response = Mock()
        mock_response.json.return_value = [{'lat': '-23.5505', 'lon': '-46.6333'}]
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        result = self.service.geocodificar_endereco("Rua Augusta, São Paulo")
        
        assert isinstance(result, GeoResult)
        assert result.success is True
        assert result.latitude == -23.5505
        assert result.longitude == -46.6333

    @patch('requests.Session.get')
    def test_geocodificar_endereco_falha(self, mock_get):
        """Testa geocodificação com falha"""
        mock_response = Mock()
        mock_response.json.return_value = []
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        result = self.service.geocodificar_endereco("Endereço inválido")
        
        assert isinstance(result, GeoResult)
        assert result.success is False

    def test_calcular_distancia(self):
        """Testa cálculo de distância"""
        # São Paulo para Rio de Janeiro (aproximadamente)
        lat1, lon1 = -23.5505, -46.6333  # São Paulo
        lat2, lon2 = -22.9068, -43.1729  # Rio de Janeiro
        
        distancia = self.service.calcular_distancia(lat1, lon1, lat2, lon2)
        
        assert isinstance(distancia, float)
        assert 350 < distancia < 450  # Aproximadamente 400km

    @patch('requests.Session.get')
    def test_geocodificar_cep(self, mock_get):
        """Testa geocodificação por CEP"""
        # Mock ViaCEP
        mock_viacep = Mock()
        mock_viacep.json.return_value = {
            'logradouro': 'Rua Augusta',
            'bairro': 'Consolação',
            'localidade': 'São Paulo',
            'uf': 'SP'
        }
        mock_viacep.raise_for_status.return_value = None
        
        # Mock Nominatim
        mock_nominatim = Mock()
        mock_nominatim.json.return_value = [{'lat': '-23.5505', 'lon': '-46.6333'}]
        mock_nominatim.raise_for_status.return_value = None
        
        mock_get.side_effect = [mock_viacep, mock_nominatim]
        
        lat, lon = self.service.geocodificar_cep("01310-100")
        
        assert lat == -23.5505
        assert lon == -46.6333

    def test_calcular_distancia_do_endereco_sem_referencia(self):
        """Testa cálculo sem ponto de referência"""
        service = GeolocationService()
        service.lat_referencia = None
        service.lon_referencia = None
        
        result = service.calcular_distancia_do_endereco("Rua Augusta, São Paulo")
        
        assert result == ("Rua Augusta, São Paulo", None, None, None)

    @patch('requests.Session.get')
    def test_calcular_distancia_do_endereco_sucesso(self, mock_get):
        """Testa cálculo de distância bem-sucedido"""
        # Setup referência
        self.service.lat_referencia = -23.5505
        self.service.lon_referencia = -46.6333
        
        # Mock geocodificação
        mock_response = Mock()
        mock_response.json.return_value = [{'lat': '-23.5600', 'lon': '-46.6400'}]
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        result = self.service.calcular_distancia_do_endereco("Rua Teste, São Paulo")
        
        endereco, lat, lon, distancia = result
        assert endereco == "Rua Teste, São Paulo"
        assert lat is not None
        assert lon is not None
        assert distancia is not None

    def test_parse_endereco(self):
        """Testa parsing de endereço"""
        endereco = "Rua Augusta, 123, Consolação, São Paulo, SP"
        street, city, state = self.service._parse_endereco(endereco)
        
        assert "augusta" in street.lower()
        assert city == "São Paulo"
        assert state == "SP"

    def test_gerar_variantes_endereco(self):
        """Testa geração de variantes"""
        endereco = "Av. Paulista, 1000"
        variantes = self.service._gerar_variantes_endereco(endereco)
        
        assert len(variantes) <= 2
        assert any("avenida" in v.lower() for v in variantes)

    def test_normalizar_endereco(self):
        """Testa normalização de endereço"""
        endereco = "  Rua Augusta, 123  "
        resultado = self.service._normalizar_endereco(endereco)
        
        assert resultado == "Rua Augusta, 123"