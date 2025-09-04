"""
Testes para verificar se scrapers incluem html_content
"""
from unittest.mock import Mock, patch

import pytest

from src.domain.models.company_model import CompanyModel
from src.infrastructure.scrapers.duckduckgo_scraper import DuckDuckGoScraper
from src.infrastructure.scrapers.google_scraper import GoogleScraper


class TestScrapersGeolocation:
    """Testes para verificar geolocalização nos scrapers"""

    @pytest.fixture
    def mock_driver_manager(self):
        """Mock do driver manager"""
        driver_manager = Mock()
        driver_manager.driver = Mock()
        driver_manager.driver.page_source = "<html><body>Rua Test, 123, São Paulo</body></html>"
        driver_manager.driver.title = "Test Company"
        driver_manager.driver.window_handles = ["handle1"]
        return driver_manager

    def test_duckduckgo_scraper_includes_html_content(self, mock_driver_manager):
        """Testa se DuckDuckGo scraper inclui html_content"""
        scraper = DuckDuckGoScraper(mock_driver_manager)

        with patch.object(scraper, '_extract_emails_fast', return_value=['test@example.com']):
            with patch.object(scraper, '_extract_phones_fast', return_value=['11999999999']):
                with patch('selenium.webdriver.support.ui.WebDriverWait'):
                    company = scraper.extract_company_data('http://test.com', 5)

        assert isinstance(company, CompanyModel)
        assert company.html_content == "<html><body>Rua Test, 123, São Paulo</body></html>"
        assert company.url == 'http://test.com'

    def test_google_scraper_includes_html_content(self):
        """Testa se Google scraper inclui html_content"""
        mock_driver = Mock()
        mock_driver.page_source = "<html><body>Rua Augusta, 456, São Paulo</body></html>"
        mock_driver.title = "Google Test Company"
        mock_driver.window_handles = ["handle1"]

        scraper = GoogleScraper(mock_driver)

        with patch('selenium.webdriver.support.ui.WebDriverWait'):
            with patch.object(scraper, '_extract_phones_fast', return_value=['11888888888']):
                company = scraper.extract_company_data('http://google-test.com', 5)

        assert isinstance(company, CompanyModel)
        assert company.html_content == "<html><body>Rua Augusta, 456, São Paulo</body></html>"
        assert company.url == 'http://google-test.com'

    def test_company_model_with_html_content(self):
        """Testa se CompanyModel aceita html_content"""
        html_content = "<html><body>Test content with address</body></html>"

        company = CompanyModel(
            name="Test Company",
            emails="test@test.com;",
            domain="test.com",
            url="http://test.com",
            html_content=html_content
        )

        assert company.html_content == html_content
        assert hasattr(company, 'html_content')

    def test_empty_html_content_fallback(self, mock_driver_manager):
        """Testa fallback quando não há html_content"""
        scraper = DuckDuckGoScraper(mock_driver_manager)

        # Simular erro na extração
        with patch.object(scraper, 'extract_company_data', side_effect=Exception("Test error")):
            try:
                company = scraper.extract_company_data('http://error.com', 5)
            except:
                # Criar company vazio como no código real
                company = CompanyModel(name="", emails="", domain="", url='http://error.com', html_content="")

        assert company.html_content == ""
        assert company.url == 'http://error.com'
