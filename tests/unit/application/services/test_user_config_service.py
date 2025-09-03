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

    @patch('builtins.print')
    @patch('builtins.input')
    def test_get_search_engine_options(self, mock_input, mock_print):
        """Testa todas as opções de motor de busca"""
        # Testa opção padrão
        mock_input.return_value = ''
        self.assertEqual(UserConfigService.get_search_engine(), "GOOGLE")

        # Testa opção 1
        mock_input.return_value = '1'
        self.assertEqual(UserConfigService.get_search_engine(), "GOOGLE")

        # Testa opção 2
        mock_input.return_value = '2'
        self.assertEqual(UserConfigService.get_search_engine(), "DUCKDUCKGO")

    @patch('src.application.services.user_config_service.UserConfigService._check_browser_availability')
    @patch('builtins.print')
    @patch('builtins.input')
    def test_get_browser_both_available(self, mock_input, mock_print, mock_check):
        """Testa seleção quando ambos navegadores estão disponíveis"""
        mock_check.return_value = True  # Ambos disponíveis

        # Testa opção padrão (Chrome)
        mock_input.return_value = ''
        self.assertEqual(UserConfigService.get_browser(), "CHROME")

        # Testa opção 2 (Brave)
        mock_input.return_value = '2'
        self.assertEqual(UserConfigService.get_browser(), "BRAVE")

    @patch('src.application.services.user_config_service.UserConfigService._check_browser_availability')
    @patch('builtins.print')
    def test_get_browser_only_chrome_available(self, mock_print, mock_check):
        """Testa seleção automática quando só Chrome está disponível"""

        def side_effect(browser):
            return browser == "CHROME"

        mock_check.side_effect = side_effect

        result = UserConfigService.get_browser()
        self.assertEqual(result, "CHROME")

    @patch('src.application.services.user_config_service.UserConfigService._check_browser_availability')
    @patch('builtins.print')
    def test_get_browser_only_brave_available(self, mock_print, mock_check):
        """Testa seleção automática quando só Brave está disponível"""

        def side_effect(browser):
            return browser == "BRAVE"

        mock_check.side_effect = side_effect

        result = UserConfigService.get_browser()
        self.assertEqual(result, "BRAVE")

    @patch('src.application.services.user_config_service.UserConfigService._check_browser_availability')
    @patch('builtins.print')
    @patch('builtins.input')
    def test_get_browser_invalid_option(self, mock_input, mock_print, mock_check):
        """Testa opção inválida quando ambos estão disponíveis"""
        mock_check.return_value = True
        mock_input.side_effect = ['3', '1']  # Opção inválida, depois válida

        result = UserConfigService.get_browser()
        self.assertEqual(result, "CHROME")

    @patch('os.path.exists')
    def test_check_browser_availability_chrome(self, mock_exists):
        """Testa verificação de disponibilidade do Chrome"""
        mock_exists.return_value = True
        self.assertTrue(UserConfigService._check_browser_availability("CHROME"))

        mock_exists.return_value = False
        self.assertFalse(UserConfigService._check_browser_availability("CHROME"))

    @patch('os.path.exists')
    def test_check_browser_availability_brave(self, mock_exists):
        """Testa verificação de disponibilidade do Brave"""
        mock_exists.return_value = True
        self.assertTrue(UserConfigService._check_browser_availability("BRAVE"))

        mock_exists.return_value = False
        self.assertFalse(UserConfigService._check_browser_availability("BRAVE"))

    def test_check_browser_availability_invalid(self):
        """Testa verificação com navegador inválido"""
        self.assertFalse(UserConfigService._check_browser_availability("INVALID"))

    # Teste removido - get_restart_option não existe mais

    # Teste removido - get_restart_option não existe mais

    @patch('builtins.print')
    @patch('builtins.input')
    def test_get_processing_mode_basic(self, mock_input, mock_print):
        """Testa modos básicos de processamento"""
        # Modo padrão (completo)
        mock_input.return_value = ''
        self.assertEqual(UserConfigService.get_processing_mode(), 999999)

        # Modo completo explícito
        mock_input.return_value = 'c'
        self.assertEqual(UserConfigService.get_processing_mode(), 999999)

        # Modo lote com limite padrão
        mock_input.side_effect = ['l', '']
        self.assertEqual(UserConfigService.get_processing_mode(), 10)

        # Modo lote com limite customizado
        mock_input.side_effect = ['l', '50']
        self.assertEqual(UserConfigService.get_processing_mode(), 50)

    @patch('builtins.print')
    @patch('builtins.input')
    def test_get_processing_mode_batch_invalid_limit(self, mock_input, mock_print):
        """Testa modo lote com limite inválido"""
        mock_input.side_effect = ['l', 'abc', '25']
        self.assertEqual(UserConfigService.get_processing_mode(), 25)

    @patch('builtins.print')
    @patch('builtins.input')
    def test_get_processing_mode_batch_zero_limit(self, mock_input, mock_print):
        """Testa modo lote com limite zero"""
        mock_input.side_effect = ['l', '0', '15']
        self.assertEqual(UserConfigService.get_processing_mode(), 15)

    @patch('builtins.print')
    @patch('builtins.input')
    def test_get_processing_mode_invalid_mode(self, mock_input, mock_print):
        """Testa modo inválido"""
        mock_input.side_effect = ['x', 'c']
        self.assertEqual(UserConfigService.get_processing_mode(), 999999)

    @patch('builtins.print')
    @patch('builtins.input')
    def test_get_processing_mode_case_insensitive(self, mock_input, mock_print):
        """Testa case insensitive"""
        mock_input.side_effect = ['L', '30']
        self.assertEqual(UserConfigService.get_processing_mode(), 30)

    @patch('builtins.print')
    @patch('builtins.input')
    def test_get_processing_mode_whitespace(self, mock_input, mock_print):
        """Testa tratamento de espaços"""
        mock_input.return_value = ' c '
        self.assertEqual(UserConfigService.get_processing_mode(), 999999)

    def test_all_methods_are_static(self):
        """Verifica que todos os métodos são estáticos"""
        import inspect
        methods = ['get_search_engine', 'get_browser', 'get_processing_mode', '_check_browser_availability']
        for method in methods:
            self.assertTrue(isinstance(inspect.getattr_static(UserConfigService, method), staticmethod))

    @patch('builtins.print')
    @patch('builtins.input')
    def test_methods_return_correct_types(self, mock_input, mock_print):
        """Verifica que métodos retornam tipos corretos"""
        mock_input.return_value = '1'
        self.assertIsInstance(UserConfigService.get_search_engine(), str)
        self.assertIsInstance(UserConfigService.get_browser(), str)

        mock_input.return_value = 'c'
        self.assertIsInstance(UserConfigService.get_processing_mode(), int)


if __name__ == '__main__':
    unittest.main()
