"""
Testes de segurança para ConfigManager
"""
import pytest
from pathlib import Path
from src.infrastructure.config.config_manager import ConfigManager


class TestConfigManagerSecurity:
    """Testes de segurança para o gerenciador de configuração"""
    
    def test_validate_path_prevents_traversal(self):
        """Testa se path traversal é prevenido"""
        with pytest.raises(ValueError, match="Caminho não permitido"):
            ConfigManager("../../../etc/passwd")
    
    def test_validate_path_prevents_absolute_outside(self):
        """Testa se caminhos absolutos fora do projeto são rejeitados"""
        with pytest.raises(ValueError, match="Caminho não permitido"):
            ConfigManager("/etc/passwd")
    
    def test_validate_path_allows_relative_inside(self):
        """Testa se caminhos relativos dentro do projeto são permitidos"""
        # Este deve funcionar (mesmo que o arquivo não exista)
        try:
            config = ConfigManager("src/resources/test.yaml")
            # Se chegou aqui, o path foi aceito
            assert isinstance(config.config_path, Path)
        except FileNotFoundError:
            # Arquivo não existe, mas path foi validado
            pass
    
    def test_validate_path_allows_current_directory(self):
        """Testa se arquivos no diretório atual são permitidos"""
        try:
            config = ConfigManager("test.yaml")
            assert isinstance(config.config_path, Path)
        except FileNotFoundError:
            # Arquivo não existe, mas path foi validado
            pass