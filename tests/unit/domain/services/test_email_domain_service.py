"""
Testes completos para email_domain_service
"""
import unittest
from unittest.mock import patch, MagicMock
import sys
import os

# Adiciona o diretório raiz ao path para imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', '..'))

from src.domain.services.email_domain_service import (
    EmailValidationService, 
    WorkingHoursService,
    EmailCollectorInterface
)


class TestEmailValidationService(unittest.TestCase):
    """Testes para EmailValidationService"""
    
    def setUp(self):
        self.service = EmailValidationService()
    
    def test_is_valid_email_valid_cases(self):
        """Testa e-mails válidos"""
        valid_emails = [
            "contact@empresa.com.br",
            "info@site.org"
        ]
        for email in valid_emails:
            self.assertTrue(self.service.is_valid_email(email))
    
    def test_is_valid_email_invalid_cases(self):
        """Testa e-mails inválidos"""
        invalid_emails = [
            "invalid-email",
            "@domain.com",
            "user@",
            "user@domain",
            "noreply@example.com",
            "admin@localhost"
        ]
        for email in invalid_emails:
            self.assertFalse(self.service.is_valid_email(email))
    
    def test_is_valid_phone_valid_cases(self):
        """Testa telefones válidos"""
        valid_phones = [
            "21987654321"
        ]
        for phone in valid_phones:
            self.assertTrue(self.service.is_valid_phone(phone))
    
    def test_is_valid_phone_invalid_cases(self):
        """Testa telefones inválidos"""
        invalid_phones = [
            "123456789",
            "00999998888",
            "11111111111",
            "abc123def"
        ]
        for phone in invalid_phones:
            self.assertFalse(self.service.is_valid_phone(phone))
    
    def test_extract_domain_from_url(self):
        """Testa extração de domínio"""
        test_cases = [
            ("https://www.example.com/page", "example.com"),
            ("http://subdomain.site.com.br", "site.com.br"),
            ("https://domain.org", "domain.org")
        ]
        for url, expected in test_cases:
            self.assertEqual(self.service.extract_domain_from_url(url), expected)
    
    def test_validate_and_join_emails(self):
        """Testa validação e junção de e-mails"""
        emails = ["contact@site.org", "invalid-email", "info@empresa.com.br"]
        result = self.service.validate_and_join_emails(emails)
        self.assertEqual(result, "contact@site.org;info@empresa.com.br;")
    
    def test_validate_and_join_phones(self):
        """Testa validação e junção de telefones"""
        phones = ["21987654321", "invalid", "11987654321"]
        result = self.service.validate_and_join_phones(phones)
        self.assertIn("(21) 98765-4321", result)
        self.assertIn("(11) 98765-4321", result)
    
    def test_is_valid_email_long_email(self):
        """Testa rejeição de e-mail muito longo"""
        long_email = "a" * 95 + "@test.com"  # > 100 caracteres
        self.assertFalse(self.service.is_valid_email(long_email))
    
    def test_is_valid_email_suspicious_chars(self):
        """Testa rejeição de e-mails com caracteres suspeitos"""
        suspicious_emails = [
            "test@1.5x.com",
            "test@2x.com", 
            "test;email@domain.com",
            "test|email@domain.com",
            "test%20@domain.com"
        ]
        for email in suspicious_emails:
            self.assertFalse(self.service.is_valid_email(email))
    
    def test_is_valid_email_multiple_at(self):
        """Testa rejeição de e-mail com múltiplos @"""
        self.assertFalse(self.service.is_valid_email("test@@domain.com"))
        self.assertFalse(self.service.is_valid_email("test@domain@com"))
    
    def test_is_valid_email_starts_ends_suspicious(self):
        """Testa rejeição de e-mails que começam/terminam com caracteres suspeitos"""
        suspicious_emails = [
            ";test@domain.com",
            "test@domain.com;",
            "%test@domain.com",
            "test@domain.com%"
        ]
        for email in suspicious_emails:
            self.assertFalse(self.service.is_valid_email(email))
    
    @patch('config.settings.SUSPICIOUS_EMAIL_DOMAINS', ['suspicious.com', 'bad.org'])
    def test_is_valid_email_suspicious_domains(self):
        """Testa rejeição de domínios suspeitos"""
        self.assertFalse(self.service.is_valid_email("test@suspicious.com"))
        self.assertFalse(self.service.is_valid_email("test@bad.org"))
    
    def test_is_valid_phone_ddd_validation(self):
        """Testa validação de DDD"""
        # DDD inválido (< 11)
        self.assertFalse(self.service.is_valid_phone("10987654321"))
        # DDD válido (99 é válido)
        self.assertTrue(self.service.is_valid_phone("99987654321"))
    
    def test_is_valid_phone_11_digits_validation(self):
        """Testa validação de celular com 11 dígitos"""
        # 11 dígitos mas terceiro não é 9
        self.assertFalse(self.service.is_valid_phone("11887654321"))
    
    def test_is_valid_phone_repetitive_patterns(self):
        """Testa rejeição de padrões repetitivos"""
        repetitive_phones = [
            "11111111111",
            "22222222222", 
            "1234567890",
            "9999999999"
        ]
        for phone in repetitive_phones:
            self.assertFalse(self.service.is_valid_phone(phone))
    
    def test_format_phone_10_digits(self):
        """Testa formatação de telefone fixo (10 dígitos)"""
        result = self.service.format_phone("1133334444")
        self.assertEqual(result, "(11) 3333-4444")
    
    def test_format_phone_invalid_length(self):
        """Testa formatação de telefone com tamanho inválido"""
        result = self.service.format_phone("123456789")
        self.assertEqual(result, "123456789")  # Retorna sem formatação
    
    def test_validate_and_join_emails_duplicates(self):
        """Testa remoção de duplicatas em e-mails"""
        emails = ["contact@site.org", "contact@site.org", "info@site.org"]
        result = self.service.validate_and_join_emails(emails)
        # Verifica se contém ambos e-mails sem duplicatas
        self.assertIn("contact@site.org", result)
        self.assertIn("info@site.org", result)
        self.assertEqual(result.count("contact@site.org"), 1)
    
    def test_validate_and_join_phones_duplicates(self):
        """Testa remoção de duplicatas em telefones"""
        phones = ["11987654321", "11987654321", "21987654321"]
        result = self.service.validate_and_join_phones(phones)
        # Deve conter apenas um de cada
        self.assertEqual(result.count("(11) 98765-4321"), 1)
        self.assertEqual(result.count("(21) 98765-4321"), 1)
    
    def test_extract_domain_no_suffix(self):
        """Testa extração quando não há sufixo válido"""
        result = self.service.extract_domain_from_url("invalid-url")
        self.assertEqual(result, "invalid-url")


class TestWorkingHoursService(unittest.TestCase):
    """Testes para WorkingHoursService"""
    
    def setUp(self):
        self.service = WorkingHoursService(8, 22)
    
    @patch('src.domain.services.email_domain_service.datetime')
    def test_is_working_hours_true(self, mock_datetime):
        """Testa horário de trabalho válido"""
        mock_datetime.now.return_value.hour = 10
        self.assertTrue(self.service.is_working_time())
    
    @patch('src.domain.services.email_domain_service.datetime')
    def test_is_working_hours_false(self, mock_datetime):
        """Testa horário fora do trabalho"""
        mock_datetime.now.return_value.hour = 23
        self.assertFalse(self.service.is_working_time())
    
    @patch('src.domain.services.email_domain_service.datetime')
    def test_is_working_hours_boundary(self, mock_datetime):
        """Testa horários limite"""
        # Hora 8 (início)
        mock_datetime.now.return_value.hour = 8
        self.assertTrue(self.service.is_working_time())
        
        # Hora 22 (fim) - deve ser False pois é < 22
        mock_datetime.now.return_value.hour = 22
        self.assertFalse(self.service.is_working_time())


class TestEmailCollectorInterface(unittest.TestCase):
    """Testes para EmailCollectorInterface"""
    
    def test_interface_methods_exist(self):
        """Testa se métodos da interface existem"""
        # Testa se a interface tem o método abstrato
        self.assertTrue(hasattr(EmailCollectorInterface, 'collect_emails'))
    
    def test_collect_emails_not_implemented(self):
        """Testa se método abstrato levanta TypeError ao instanciar"""
        with self.assertRaises(TypeError):
            EmailCollectorInterface()


if __name__ == '__main__':
    unittest.main()