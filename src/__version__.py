"""Versão da aplicação PythonSearchApp"""
import yaml
from pathlib import Path

def _get_version():
    config_path = Path(__file__).parent / "resources" / "application.yaml"
    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    return config['app']['version']

__version__ = _get_version()
__version_info__ = tuple(map(int, __version__.split('.')))

# Limpar namespace
del _get_version, yaml, Path