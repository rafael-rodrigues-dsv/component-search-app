"""
HTTP Fetcher - Requisições HTTP puras (sem renderização)
"""
import requests
from typing import Optional
from ..utils.scraper_logger import ScraperLogger

# ✅ Desabilitar warnings de SSL (logs limpos)
import urllib3
urllib3.disable_warnings()


class HttpFetcher:
    """
    Fetcher HTTP puro usando requests

    Usado pelo SmartPath para navegar páginas sem renderização
    """

    def __init__(self, logger: Optional[ScraperLogger] = None):
        """
        Args:
            logger: Logger opcional
        """
        self.logger = logger or ScraperLogger('HTTP_FETCHER')

        # User-Agent padrão
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        }

        # Session para reutilizar conexões
        self.session = requests.Session()
        self.session.headers.update(self.headers)

    def fetch(self, url: str, timeout: int = 5) -> Optional[str]:
        """
        Faz requisição HTTP GET

        Args:
            url: URL para requisitar
            timeout: Timeout em segundos

        Returns:
            HTML da página ou None em caso de erro
        """
        try:
            self.logger.log('web', f"Fetch HTTP: {url[:60]}...")

            response = self.session.get(
                url,
                timeout=timeout,
                allow_redirects=True,
                verify=False  # Ignorar SSL para evitar erros
            )

            # Verificar status
            if response.status_code != 200:
                self.logger.log('warning', f"Status {response.status_code}")
                return None

            # Verificar se é HTML
            content_type = response.headers.get('Content-Type', '').lower()
            if 'html' not in content_type:
                self.logger.log('warning', f"Não é HTML: {content_type}")
                return None

            html = response.text
            self.logger.log('success', f"Fetch OK: {len(html):,} chars")

            return html

        except requests.Timeout:
            self.logger.log('error', f"Timeout em {url[:40]}")
            return None

        except requests.RequestException as e:
            self.logger.log('error', f"Request error: {str(e)[:40]}")
            return None

        except Exception as e:
            self.logger.log('error', f"Fetch error: {str(e)[:40]}")
            return None

    def close(self):
        """Fecha session"""
        try:
            self.session.close()
        except:
            pass
