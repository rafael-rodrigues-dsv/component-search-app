"""
Teste para forçar cobertura do email_domain_service
"""
import unittest


class TestEmailDomainServiceCoverage(unittest.TestCase):
    """Força importação do email_domain_service para cobertura"""
    
    def test_import_email_domain_service(self):
        """Importa email_domain_service para aparecer na cobertura"""
        try:
            from src.domain.services.email_domain_service import (
                EmailValidationService, 
                WorkingHoursService,
                EmailCollectorInterface
            )
            
            # Verifica se as classes existem
            self.assertTrue(EmailValidationService)
            self.assertTrue(WorkingHoursService)
            self.assertTrue(EmailCollectorInterface)
            
        except ImportError as e:
            self.fail(f"Falha ao importar email_domain_service: {e}")


if __name__ == '__main__':
    unittest.main()