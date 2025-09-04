"""
Testes para SessionManager
"""
import pytest
from unittest.mock import Mock, patch
from src.infrastructure.network.session_manager import SessionManager


class TestSessionManager:
    """Testes para gerenciador de sessão"""
    
    def setup_method(self):
        """Setup para cada teste"""
        self.mock_driver_manager = Mock()
        self.session_manager = SessionManager(self.mock_driver_manager)
    
    def test_init(self):
        """Testa inicialização"""
        assert self.session_manager.driver_manager == self.mock_driver_manager
        assert self.session_manager.searches_in_session == 0
        assert isinstance(self.session_manager.max_session_duration, float)
        assert isinstance(self.session_manager.max_searches_per_session, int)
    
    @patch('time.time')
    def test_should_restart_session_by_duration(self, mock_time):
        """Testa reinício por duração"""
        # Simula sessão longa
        mock_time.return_value = 5000  # Tempo atual
        self.session_manager.session_start_time = 1000  # Tempo de início
        self.session_manager.max_session_duration = 3600  # 1 hora
        
        result = self.session_manager.should_restart_session()
        assert result is True
    
    def test_should_restart_session_by_searches(self):
        """Testa reinício por número de buscas"""
        self.session_manager.searches_in_session = 50
        self.session_manager.max_searches_per_session = 40
        
        result = self.session_manager.should_restart_session()
        assert result is True
    
    @patch('time.time')
    def test_should_not_restart_session(self, mock_time):
        """Testa quando não deve reiniciar"""
        mock_time.side_effect = [1000, 1500]  # 500s de diferença
        self.session_manager.session_start_time = 1000
        self.session_manager.max_session_duration = 3600
        self.session_manager.searches_in_session = 5
        self.session_manager.max_searches_per_session = 40
        
        with patch('random.random', return_value=0.1):  # > 0.05
            result = self.session_manager.should_restart_session()
            assert result is False
    
    @patch('time.sleep')
    @patch('time.time')
    def test_restart_session_success(self, mock_time, mock_sleep):
        """Testa reinício de sessão com sucesso"""
        mock_time.return_value = 2000
        self.mock_driver_manager.start_driver.return_value = True
        
        result = self.session_manager.restart_session()
        
        assert result is True
        self.mock_driver_manager.close_driver.assert_called_once()
        self.mock_driver_manager.start_driver.assert_called_once()
        assert self.session_manager.searches_in_session == 0
        assert self.session_manager.session_start_time == 2000
    
    @patch('time.sleep')
    def test_restart_session_failure(self, mock_sleep):
        """Testa falha no reinício de sessão"""
        self.mock_driver_manager.start_driver.return_value = False
        
        result = self.session_manager.restart_session()
        
        assert result is False
        self.mock_driver_manager.close_driver.assert_called_once()
        self.mock_driver_manager.start_driver.assert_called_once()
    
    @patch('time.sleep')
    def test_restart_session_exception(self, mock_sleep):
        """Testa exceção no reinício de sessão"""
        self.mock_driver_manager.close_driver.side_effect = Exception("Driver error")
        
        result = self.session_manager.restart_session()
        
        assert result is False
    
    def test_increment_search_count(self):
        """Testa incremento do contador de buscas"""
        initial_count = self.session_manager.searches_in_session
        self.session_manager.increment_search_count()
        assert self.session_manager.searches_in_session == initial_count + 1
    
    @patch('time.time')
    def test_get_session_info(self, mock_time):
        """Testa obtenção de informações da sessão"""
        mock_time.return_value = 1500  # Tempo atual
        self.session_manager.session_start_time = 1000  # Tempo de início
        self.session_manager.searches_in_session = 10
        
        info = self.session_manager.get_session_info()
        
        assert info["duration"] == 500
        assert info["searches"] == 10
        assert "max_duration" in info
        assert "max_searches" in info