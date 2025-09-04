"""
Testes para ProxyManager
"""
import pytest
from unittest.mock import Mock, patch
from src.infrastructure.network.proxy_manager import ProxyManager


class TestProxyManager:
    """Testes para gerenciador de proxy"""
    
    def setup_method(self):
        """Setup para cada teste"""
        self.proxy_manager = ProxyManager()
    
    def test_init(self):
        """Testa inicialização"""
        assert self.proxy_manager.proxies == []
        assert self.proxy_manager.current_proxy_index == 0
    
    def test_load_free_proxies(self):
        """Testa carregamento de proxies gratuitos"""
        proxies = self.proxy_manager.load_free_proxies()
        assert isinstance(proxies, list)
        assert len(proxies) > 0
        assert "8.8.8.8:80" in proxies
    
    def test_get_next_proxy_empty_list(self):
        """Testa get_next_proxy com lista vazia"""
        result = self.proxy_manager.get_next_proxy()
        assert result is None
    
    def test_get_next_proxy_with_proxies(self):
        """Testa rotação de proxies"""
        self.proxy_manager.proxies = ["proxy1:80", "proxy2:80"]
        
        # Primeira chamada
        result1 = self.proxy_manager.get_next_proxy()
        assert result1 == "proxy1:80"
        assert self.proxy_manager.current_proxy_index == 1
        
        # Segunda chamada
        result2 = self.proxy_manager.get_next_proxy()
        assert result2 == "proxy2:80"
        assert self.proxy_manager.current_proxy_index == 0  # Volta ao início
    
    @patch('requests.get')
    def test_test_proxy_success(self, mock_get):
        """Testa proxy funcionando"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_get.return_value = mock_response
        
        result = self.proxy_manager.test_proxy("8.8.8.8:80")
        assert result is True
    
    @patch('requests.get')
    def test_test_proxy_failure(self, mock_get):
        """Testa proxy com falha"""
        mock_get.side_effect = Exception("Connection error")
        
        result = self.proxy_manager.test_proxy("invalid:80")
        assert result is False
    
    @patch.object(ProxyManager, 'test_proxy')
    @patch.object(ProxyManager, 'load_free_proxies')
    def test_get_working_proxies(self, mock_load, mock_test):
        """Testa obtenção de proxies funcionais"""
        mock_load.return_value = ["proxy1:80", "proxy2:80", "proxy3:80"]
        mock_test.side_effect = [True, False, True]  # proxy1 e proxy3 funcionam
        
        result = self.proxy_manager.get_working_proxies()
        assert result == ["proxy1:80", "proxy3:80"]
        assert mock_test.call_count == 3