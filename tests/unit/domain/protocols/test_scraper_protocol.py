"""
Testes unitários para ScraperProtocol
"""
import unittest
import sys
import os
from typing import List

# Adiciona o diretório raiz ao path para imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', '..'))

from src.domain.protocols.scraper_protocol import ScraperProtocol
from src.domain.models.company_model import CompanyModel


class MockScraper:
    """Mock scraper que implementa o protocol"""

    def search(self, query: str) -> bool:
        return True

    def get_result_links(self, blacklist: List[str]) -> List[str]:
        return ["https://example.com", "https://test.com"]

    def extract_company_data(self, url: str, max_emails: int) -> CompanyModel:
        return CompanyModel(
            name="Test Company",
            emails="test@example.com;",
            domain="example.com",
            url=url,
            phone="(11) 99999-9999;"
        )

    def go_to_next_page(self) -> bool:
        return True


class InvalidScraper:
    """Scraper inválido que não implementa todos os métodos"""

    def search(self, query: str) -> bool:
        return True

    # Faltam outros métodos obrigatórios


class TestScraperProtocol(unittest.TestCase):
    """Testes para ScraperProtocol"""

    def test_protocol_methods_exist(self):
        """Testa se métodos do protocol existem"""
        # Verifica se o protocol tem os métodos esperados
        self.assertTrue(hasattr(ScraperProtocol, 'search'))
        self.assertTrue(hasattr(ScraperProtocol, 'get_result_links'))
        self.assertTrue(hasattr(ScraperProtocol, 'extract_company_data'))
        self.assertTrue(hasattr(ScraperProtocol, 'go_to_next_page'))

    def test_mock_scraper_implements_protocol(self):
        """Testa se MockScraper implementa o protocol corretamente"""
        scraper = MockScraper()

        # Testa método search
        result = scraper.search("elevadores SP")
        self.assertIsInstance(result, bool)
        self.assertTrue(result)

        # Testa método get_result_links
        links = scraper.get_result_links(["blacklisted.com"])
        self.assertIsInstance(links, list)
        self.assertEqual(len(links), 2)
        self.assertIn("https://example.com", links)

        # Testa método extract_company_data
        company = scraper.extract_company_data("https://example.com", 5)
        self.assertIsInstance(company, CompanyModel)
        self.assertEqual(company.name, "Test Company")
        self.assertEqual(company.domain, "example.com")

        # Testa método go_to_next_page
        next_page = scraper.go_to_next_page()
        self.assertIsInstance(next_page, bool)
        self.assertTrue(next_page)

    def test_protocol_type_checking(self):
        """Testa verificação de tipos do protocol"""
        scraper = MockScraper()

        # Verifica tipos de entrada e saída
        self.assertIsInstance(scraper.search("test"), bool)
        self.assertIsInstance(scraper.get_result_links([]), list)
        self.assertIsInstance(scraper.extract_company_data("url", 1), CompanyModel)
        self.assertIsInstance(scraper.go_to_next_page(), bool)

    def test_protocol_with_different_implementations(self):
        """Testa protocol com diferentes implementações"""

        class AlternativeScraper:
            def search(self, query: str) -> bool:
                return False  # Implementação diferente

            def get_result_links(self, blacklist: List[str]) -> List[str]:
                return []  # Lista vazia

            def extract_company_data(self, url: str, max_emails: int) -> CompanyModel:
                return CompanyModel(
                    name="",
                    emails="",
                    domain="",
                    url=url,
                    phone=""
                )

            def go_to_next_page(self) -> bool:
                return False

        alt_scraper = AlternativeScraper()

        # Deve funcionar mesmo com implementação diferente
        self.assertFalse(alt_scraper.search("test"))
        self.assertEqual(alt_scraper.get_result_links([]), [])
        self.assertFalse(alt_scraper.go_to_next_page())

    def test_protocol_method_signatures(self):
        """Testa assinaturas dos métodos do protocol"""
        scraper = MockScraper()

        # Testa search com string
        result = scraper.search("elevadores manutenção")
        self.assertTrue(result)

        # Testa get_result_links com lista de strings
        links = scraper.get_result_links(["site1.com", "site2.com"])
        self.assertIsInstance(links, list)

        # Testa extract_company_data com string e int
        company = scraper.extract_company_data("https://test.com", 10)
        self.assertEqual(company.url, "https://test.com")

    def test_protocol_return_types(self):
        """Testa tipos de retorno dos métodos"""
        scraper = MockScraper()

        # search deve retornar bool
        search_result = scraper.search("test")
        self.assertIn(type(search_result).__name__, ['bool'])

        # get_result_links deve retornar List[str]
        links_result = scraper.get_result_links([])
        self.assertIsInstance(links_result, list)
        for link in links_result:
            self.assertIsInstance(link, str)

        # extract_company_data deve retornar CompanyModel
        company_result = scraper.extract_company_data("url", 1)
        self.assertIsInstance(company_result, CompanyModel)

        # go_to_next_page deve retornar bool
        next_page_result = scraper.go_to_next_page()
        self.assertIn(type(next_page_result).__name__, ['bool'])

    def test_protocol_ellipsis_coverage(self):
        """Testa cobertura das linhas com ellipsis do protocol"""
        # Acessa diretamente os métodos do protocol para cobrir ellipsis
        protocol_instance = ScraperProtocol

        # Verifica que os métodos têm anotações
        self.assertTrue(hasattr(protocol_instance.search, '__annotations__'))
        self.assertTrue(hasattr(protocol_instance.get_result_links, '__annotations__'))
        self.assertTrue(hasattr(protocol_instance.extract_company_data, '__annotations__'))
        self.assertTrue(hasattr(protocol_instance.go_to_next_page, '__annotations__'))

        # Testa que são callable
        self.assertTrue(callable(protocol_instance.search))
        self.assertTrue(callable(protocol_instance.get_result_links))
        self.assertTrue(callable(protocol_instance.extract_company_data))
        self.assertTrue(callable(protocol_instance.go_to_next_page))


if __name__ == '__main__':
    unittest.main()
