"""
Testes unitários para UserConfigService
"""
import unittest
from unittest.mock import patch
import sys
import os

# Adiciona o diretório raiz ao path para imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', '..'))

from src.application.services.user_config_service import UserConfigService


class TestUserConfigService(unittest.TestCase):
    """Testes para UserConfigService"""
    
    def setUp(self):
        """Setup para cada teste"""
        self.patches = []
    
    def tearDown(self):
        """Cleanup após cada teste"""
        for patch_obj in self.patches:
            patch_obj.stop()
    
    def _mock_input(self, return_values):
        """Helper para mockar input com múltiplos valores"""
        mock_input = patch('builtins.input')
        mock_input_obj = mock_input.start()
        mock_input_obj.side_effect = return_values
        self.patches.append(mock_input)
        return mock_input_obj
    
    def _mock_print(self):
        """Helper para mockar print"""
        mock_print = patch('builtins.print')
        mock_print_obj = mock_print.start()
        self.patches.append(mock_print)
        return mock_print_obj
    
    # Testes para get_search_engine()
    
    def test_get_search_engine_default_option(self):
        """Testa seleção padrão (vazio) retorna DuckDuckGo"""
        self._mock_input([''])
        self._mock_print()
        
        result = UserConfigService.get_search_engine()
        
        self.assertEqual(result, "DUCKDUCKGO")
    
    def test_get_search_engine_option_1(self):
        """Testa seleção opção 1 retorna DuckDuckGo"""
        self._mock_input(['1'])
        self._mock_print()
        
        result = UserConfigService.get_search_engine()
        
        self.assertEqual(result, "DUCKDUCKGO")
    
    def test_get_search_engine_option_2(self):
        """Testa seleção opção 2 retorna Google"""
        self._mock_input(['2'])
        self._mock_print()
        
        result = UserConfigService.get_search_engine()
        
        self.assertEqual(result, "GOOGLE")
    
    def test_get_search_engine_invalid_then_valid(self):
        """Testa entrada inválida seguida de válida"""
        self._mock_input(['3', '1'])
        self._mock_print()
        
        result = UserConfigService.get_search_engine()
        
        self.assertEqual(result, "DUCKDUCKGO")
    
    def test_get_search_engine_multiple_invalid_then_valid(self):
        """Testa múltiplas entradas inválidas seguidas de válida"""
        self._mock_input(['abc', '0', '5', '2'])
        self._mock_print()
        
        result = UserConfigService.get_search_engine()
        
        self.assertEqual(result, "GOOGLE")
    
    def test_get_search_engine_whitespace_handling(self):
        """Testa tratamento de espaços em branco"""
        self._mock_input([' 1 '])
        self._mock_print()
        
        result = UserConfigService.get_search_engine()
        
        self.assertEqual(result, "DUCKDUCKGO")
    
    def test_get_search_engine_exception_handling(self):
        """Testa tratamento de exceções"""
        mock_input = self._mock_input([''])
        mock_input.side_effect = [KeyboardInterrupt(), '1']
        self._mock_print()
        
        result = UserConfigService.get_search_engine()
        
        self.assertEqual(result, "DUCKDUCKGO")
    
    # Testes para get_restart_option()
    
    def test_get_restart_option_default(self):
        """Testa opção padrão (vazio) retorna False"""
        self._mock_input([''])
        self._mock_print()
        
        result = UserConfigService.get_restart_option()
        
        self.assertFalse(result)
    
    def test_get_restart_option_n(self):
        """Testa opção 'n' retorna False"""
        self._mock_input(['n'])
        self._mock_print()
        
        result = UserConfigService.get_restart_option()
        
        self.assertFalse(result)
    
    def test_get_restart_option_s(self):
        """Testa opção 's' retorna True"""
        self._mock_input(['s'])
        self._mock_print()
        
        result = UserConfigService.get_restart_option()
        
        self.assertTrue(result)
    
    def test_get_restart_option_case_insensitive(self):
        """Testa que opções são case insensitive"""
        self._mock_input(['S'])
        self._mock_print()
        
        result = UserConfigService.get_restart_option()
        
        self.assertTrue(result)
    
    def test_get_restart_option_with_whitespace(self):
        """Testa tratamento de espaços"""
        self._mock_input([' N '])
        self._mock_print()
        
        result = UserConfigService.get_restart_option()
        
        self.assertFalse(result)
    
    def test_get_restart_option_invalid_then_valid(self):
        """Testa entrada inválida seguida de válida"""
        self._mock_input(['x', 's'])
        self._mock_print()
        
        result = UserConfigService.get_restart_option()
        
        self.assertTrue(result)
    
    def test_get_restart_option_exception_handling(self):
        """Testa tratamento de exceções"""
        mock_input = self._mock_input([''])
        mock_input.side_effect = [Exception(), 'n']
        self._mock_print()
        
        result = UserConfigService.get_restart_option()
        
        self.assertFalse(result)
    
    # Testes para get_processing_mode()
    
    def test_get_processing_mode_default(self):
        """Testa modo padrão (vazio) retorna completo"""
        self._mock_input([''])
        self._mock_print()
        
        result = UserConfigService.get_processing_mode()
        
        self.assertEqual(result, 999999)
    
    def test_get_processing_mode_complete(self):
        """Testa modo completo 'c'"""
        self._mock_input(['c'])
        self._mock_print()
        
        result = UserConfigService.get_processing_mode()
        
        self.assertEqual(result, 999999)
    
    def test_get_processing_mode_batch_default_limit(self):
        """Testa modo lote com limite padrão"""
        self._mock_input(['l', ''])
        self._mock_print()
        
        result = UserConfigService.get_processing_mode()
        
        self.assertEqual(result, 10)
    
    def test_get_processing_mode_batch_custom_limit(self):
        """Testa modo lote com limite customizado"""
        self._mock_input(['l', '50'])
        self._mock_print()
        
        result = UserConfigService.get_processing_mode()
        
        self.assertEqual(result, 50)
    
    def test_get_processing_mode_batch_invalid_then_valid_limit(self):
        """Testa modo lote com limite inválido seguido de válido"""
        self._mock_input(['l', 'abc', '25'])
        self._mock_print()
        
        result = UserConfigService.get_processing_mode()
        
        self.assertEqual(result, 25)
    
    def test_get_processing_mode_batch_zero_then_valid(self):
        """Testa modo lote com zero seguido de válido"""
        self._mock_input(['l', '0', '15'])
        self._mock_print()
        
        result = UserConfigService.get_processing_mode()
        
        self.assertEqual(result, 15)
    
    def test_get_processing_mode_batch_negative_then_valid(self):
        """Testa modo lote com número negativo seguido de válido"""
        self._mock_input(['l', '-5', '20'])
        self._mock_print()
        
        result = UserConfigService.get_processing_mode()
        
        self.assertEqual(result, 20)
    
    def test_get_processing_mode_invalid_mode_then_valid(self):
        """Testa modo inválido seguido de válido"""
        self._mock_input(['x', 'c'])
        self._mock_print()
        
        result = UserConfigService.get_processing_mode()
        
        self.assertEqual(result, 999999)
    
    def test_get_processing_mode_case_insensitive(self):
        """Testa que modos são case insensitive"""
        self._mock_input(['L', '30'])
        self._mock_print()
        
        result = UserConfigService.get_processing_mode()
        
        self.assertEqual(result, 30)
    
    def test_get_processing_mode_whitespace_handling(self):
        """Testa tratamento de espaços"""
        self._mock_input([' c '])
        self._mock_print()
        
        result = UserConfigService.get_processing_mode()
        
        self.assertEqual(result, 999999)
    
    def test_get_processing_mode_exception_handling(self):
        """Testa tratamento de exceções no modo"""
        mock_input = self._mock_input([''])
        mock_input.side_effect = [Exception(), 'c']
        self._mock_print()
        
        result = UserConfigService.get_processing_mode()
        
        self.assertEqual(result, 999999)
    
    def test_get_processing_mode_batch_multiple_invalid_limits(self):
        """Testa modo lote com múltiplos limites inválidos"""
        self._mock_input(['l', 'abc', '-10', '0', 'xyz', '40'])
        self._mock_print()
        
        result = UserConfigService.get_processing_mode()
        
        self.assertEqual(result, 40)
    
    # Testes de integração
    
    def test_all_methods_are_static(self):
        """Verifica que todos os métodos são estáticos"""
        import inspect
        self.assertTrue(isinstance(inspect.getattr_static(UserConfigService, 'get_search_engine'), staticmethod))
        self.assertTrue(isinstance(inspect.getattr_static(UserConfigService, 'get_restart_option'), staticmethod))
        self.assertTrue(isinstance(inspect.getattr_static(UserConfigService, 'get_processing_mode'), staticmethod))
    
    def test_methods_return_correct_types(self):
        """Verifica que métodos retornam tipos corretos"""
        self._mock_input(['1'])
        self._mock_print()
        result1 = UserConfigService.get_search_engine()
        self.assertIsInstance(result1, str)
        
        self._mock_input(['n'])
        result2 = UserConfigService.get_restart_option()
        self.assertIsInstance(result2, bool)
        
        self._mock_input(['c'])
        result3 = UserConfigService.get_processing_mode()
        self.assertIsInstance(result3, int)
    
    def test_print_calls_for_search_engine(self):
        """Verifica que mensagens corretas são exibidas para search engine"""
        self._mock_input(['1'])
        mock_print = self._mock_print()
        
        UserConfigService.get_search_engine()
        
        print_calls = [call[0][0] for call in mock_print.call_args_list if call[0]]
        self.assertTrue(any("Escolha o motor de busca" in str(call) for call in print_calls))
        self.assertTrue(any("DuckDuckGo" in str(call) for call in print_calls))
        self.assertTrue(any("Google Chrome" in str(call) for call in print_calls))
    
    def test_error_messages_displayed(self):
        """Verifica que mensagens de erro são exibidas"""
        self._mock_input(['invalid', '1'])
        mock_print = self._mock_print()
        
        UserConfigService.get_search_engine()
        
        print_calls = [call[0][0] for call in mock_print.call_args_list if call[0]]
        self.assertTrue(any("[ERRO]" in str(call) for call in print_calls))


if __name__ == '__main__':
    unittest.main()