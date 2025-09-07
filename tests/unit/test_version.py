"""
Testes para __version__.py
"""
def test_version_exists():
    """Testa se a versão existe"""
    from src.__version__ import __version__
    assert __version__ is not None
    assert isinstance(__version__, str)
    assert len(__version__) > 0