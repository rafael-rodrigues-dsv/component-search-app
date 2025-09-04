"""
Configuração global para testes pytest
"""
import os
import sys

# Adiciona o diretório raiz ao path para imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# Configurações globais de teste
import pytest


@pytest.fixture(scope="session")
def test_config():
    """Configuração global para testes"""
    return {
        "test_mode": True,
        "mock_external_calls": True
    }
