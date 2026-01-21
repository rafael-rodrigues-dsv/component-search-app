"""
Script de debug para imprimir termos retornados por SearchTermRepository
Uso: python scripts\debug_print_terms.py
"""
import sys
from pprint import pprint

sys.path.append('.')
try:
    from src.infrastructure.repositories.search_term_repository import SearchTermRepository
except Exception as e:
    print('Erro ao importar SearchTermRepository:', e)
    raise

repo = SearchTermRepository()
print('list_active_terms(is_test=True):')
try:
    pprint(repo.list_active_terms(is_test=True))
except Exception as e:
    print('Erro ao executar list_active_terms(is_test=True):', e)

print('\nlist_active_terms(is_test=False):')
try:
    pprint(repo.list_active_terms(is_test=False))
except Exception as e:
    print('Erro ao executar list_active_terms(is_test=False):', e)

print('\nget_pending_terms():')
try:
    from src.infrastructure.repositories.access_repository import AccessRepository
    ar = AccessRepository()
    pprint(ar.get_pending_terms())
except Exception as e:
    print('Erro ao executar get_pending_terms():', e)
