"""
Testes unitários para SearchTermFactory
"""
import unittest
from unittest.mock import patch, MagicMock
import sys
import os

# Adiciona o diretório raiz ao path para imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', '..'))


class TestSearchTermFactory(unittest.TestCase):
    """Testes para SearchTermFactory"""
    
    def test_create_search_terms_returns_list(self):
        """Testa se retorna uma lista"""
        # Mock do módulo config.settings
        mock_settings = MagicMock()
        mock_settings.IS_TEST_MODE = True
        mock_settings.BASE_TESTES = ['elevador teste']
        mock_settings.CIDADE_BASE = 'São Paulo'
        mock_settings.UF_BASE = 'SP'
        mock_settings.CATEGORIA_BASE = 'elevadores'
        
        with patch.dict('sys.modules', {'config.settings': mock_settings}):
            from src.domain.factories.search_term_factory import SearchTermFactory
            terms = SearchTermFactory.create_search_terms()
            self.assertIsInstance(terms, list)
    
    def test_create_search_terms_test_mode_returns_terms(self):
        """Testa que modo teste retorna termos"""
        from src.domain.factories.search_term_factory import SearchTermFactory
        from src.domain.models.search_term_model import SearchTermModel
        
        terms = SearchTermFactory.create_search_terms()
        
        # Deve retornar pelo menos alguns termos
        self.assertGreater(len(terms), 0)
        # Todos devem ser SearchTermModel
        for term in terms:
            self.assertIsInstance(term, SearchTermModel)
            self.assertIsInstance(term.query, str)
            self.assertIsInstance(term.location, str)
            self.assertIsInstance(term.category, str)
            self.assertIsInstance(term.pages, int)
            self.assertEqual(terms[0].pages, 10)
    
    def test_create_search_terms_structure_validation(self):
        """Testa estrutura dos termos gerados"""
        from src.domain.factories.search_term_factory import SearchTermFactory
        
        terms = SearchTermFactory.create_search_terms()
        
        # Verifica estrutura básica
        self.assertIsInstance(terms, list)
        
        if len(terms) > 0:
            term = terms[0]
            # Verifica que tem os campos obrigatórios
            self.assertTrue(hasattr(term, 'query'))
            self.assertTrue(hasattr(term, 'location'))
            self.assertTrue(hasattr(term, 'category'))
            self.assertTrue(hasattr(term, 'pages'))
            
            # Verifica que query contém informações relevantes
            self.assertIn('São Paulo', term.query)
            self.assertEqual(term.location, 'SP')
    
    def test_create_search_terms_basic_functionality(self):
        """Testa funcionalidade básica da factory"""
        from src.domain.factories.search_term_factory import SearchTermFactory
        
        # Deve funcionar sem lançar exceção
        try:
            terms = SearchTermFactory.create_search_terms()
            self.assertIsInstance(terms, list)
        except Exception as e:
            self.fail(f"create_search_terms() lançou exceção: {e}")
    
    def test_create_search_terms_returns_valid_models(self):
        """Testa que retorna modelos válidos"""
        from src.domain.factories.search_term_factory import SearchTermFactory
        from src.domain.models.search_term_model import SearchTermModel
        
        terms = SearchTermFactory.create_search_terms()
        
        # Verifica que todos são SearchTermModel válidos
        for term in terms:
            self.assertIsInstance(term, SearchTermModel)
            self.assertIsNotNone(term.query)
            self.assertIsNotNone(term.location)
            self.assertIsNotNone(term.category)
            self.assertIsInstance(term.pages, int)
            self.assertGreater(term.pages, 0)
    
    def test_search_term_model_attributes(self):
        """Testa atributos dos modelos gerados"""
        from src.domain.factories.search_term_factory import SearchTermFactory
        
        terms = SearchTermFactory.create_search_terms()
        
        if len(terms) > 0:
            term = terms[0]
            # Verifica tipos dos atributos
            self.assertIsInstance(term.query, str)
            self.assertIsInstance(term.location, str)
            self.assertIsInstance(term.category, str)
            self.assertIsInstance(term.pages, int)
            
            # Verifica valores não vazios
            self.assertNotEqual(term.query.strip(), '')
            self.assertNotEqual(term.location.strip(), '')
            self.assertNotEqual(term.category.strip(), '')
    
    def test_uniqueness_of_terms(self):
        """Testa que os termos são únicos"""
        from src.domain.factories.search_term_factory import SearchTermFactory
        
        terms = SearchTermFactory.create_search_terms()
        
        # Verifica que não há termos duplicados
        queries = [term.query for term in terms]
        unique_queries = set(queries)
        
        self.assertEqual(len(queries), len(unique_queries), "Encontrados termos duplicados")
    
    def test_terms_contain_location_info(self):
        """Testa que os termos contêm informações de localização"""
        from src.domain.factories.search_term_factory import SearchTermFactory
        
        terms = SearchTermFactory.create_search_terms()
        
        for term in terms:
            # Deve conter informações de localização na query
            query_lower = term.query.lower()
            self.assertTrue(
                'são paulo' in query_lower or 'sp' in query_lower,
                f"Query '{term.query}' não contém informação de localização"
            )
    
    def test_factory_method_exists(self):
        """Testa que o método da factory existe e é chamavel"""
        from src.domain.factories.search_term_factory import SearchTermFactory
        
        # Verifica que o método existe
        self.assertTrue(hasattr(SearchTermFactory, 'create_search_terms'))
        self.assertTrue(callable(getattr(SearchTermFactory, 'create_search_terms')))
    
    def test_search_term_model_attributes(self):
        """Testa atributos do SearchTermModel"""
        mock_settings = MagicMock()
        mock_settings.IS_TEST_MODE = True
        mock_settings.BASE_TESTES = ['teste']
        mock_settings.CIDADE_BASE = 'São Paulo'
        mock_settings.UF_BASE = 'SP'
        mock_settings.CATEGORIA_BASE = 'elevadores'
        
        with patch.dict('sys.modules', {'config.settings': mock_settings}):
            from src.domain.factories.search_term_factory import SearchTermFactory
            
            terms = SearchTermFactory.create_search_terms()
            
            if terms:
                term = terms[0]
                self.assertTrue(hasattr(term, 'query'))
                self.assertTrue(hasattr(term, 'location'))
                self.assertTrue(hasattr(term, 'category'))
                self.assertTrue(hasattr(term, 'pages'))
                
                self.assertIsInstance(term.query, str)
                self.assertIsInstance(term.location, str)
                self.assertIsInstance(term.category, str)
                self.assertIsInstance(term.pages, int)
                self.assertEqual(term.pages, 10)
    
    def test_method_is_classmethod(self):
        """Verifica que create_search_terms é método de classe"""
        from src.domain.factories.search_term_factory import SearchTermFactory
        import inspect
        
        self.assertTrue(isinstance(inspect.getattr_static(SearchTermFactory, 'create_search_terms'), classmethod))
    
    def test_uniqueness_of_terms(self):
        """Testa unicidade dos termos gerados"""
        mock_settings = MagicMock()
        mock_settings.IS_TEST_MODE = False
        mock_settings.BASE_BUSCA = ['base1', 'base2']
        mock_settings.BASE_ZONAS = ['zona1']
        mock_settings.BASE_BAIRROS = ['bairro1']
        mock_settings.CIDADES_INTERIOR = ['cidade1']
        mock_settings.CIDADE_BASE = 'São Paulo'
        mock_settings.UF_BASE = 'SP'
        mock_settings.CATEGORIA_BASE = 'elevadores'
        
        with patch.dict('sys.modules', {'config.settings': mock_settings}):
            from src.domain.factories.search_term_factory import SearchTermFactory
            
            terms = SearchTermFactory.create_search_terms()
            
            queries = [term.query for term in terms]
            unique_queries = set(queries)
            
            self.assertEqual(len(queries), len(unique_queries))
    
    def test_terms_have_valid_pages(self):
        """Testa que os termos têm número válido de páginas"""
        from src.domain.factories.search_term_factory import SearchTermFactory
        
        terms = SearchTermFactory.create_search_terms()
        
        for term in terms:
            self.assertIsInstance(term.pages, int)
            self.assertGreaterEqual(term.pages, 1)
            self.assertLessEqual(term.pages, 100)  # Limite razoável
    
    @patch('src.domain.factories.search_term_factory.SearchTermFactory.IS_TEST_MODE', False)
    def test_production_mode_complete_coverage(self):
        """Testa modo produção com cobertura completa"""
        from src.domain.factories.search_term_factory import SearchTermFactory
        
        with patch('builtins.print') as mock_print:
            terms = SearchTermFactory.create_search_terms()
            
            # Verifica se print foi chamado
            mock_print.assert_called_with("[INFO] Modo PRODUÇÃO - processamento completo")
            
            # Deve ter muitos termos no modo produção
            self.assertGreater(len(terms), 10)
    
    @patch('src.domain.factories.search_term_factory.SearchTermFactory.IS_TEST_MODE', True)
    def test_test_mode_limited_terms(self):
        """Testa modo teste com termos limitados"""
        from src.domain.factories.search_term_factory import SearchTermFactory
        
        with patch('builtins.print') as mock_print:
            terms = SearchTermFactory.create_search_terms()
            
            # Verifica se print foi chamado
            mock_print.assert_called_with("[INFO] Modo TESTE ativado")
            
            # Deve ter poucos termos no modo teste
            self.assertLessEqual(len(terms), 5)


if __name__ == '__main__':
    unittest.main()