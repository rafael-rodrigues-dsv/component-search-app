"""
Gerenciador de Proxy para evitar detecção
"""
from typing import List, Optional

import requests


class ProxyManager:
    """Gerencia rotação de proxies para evitar bloqueios"""

    def __init__(self):
        self.proxies = []
        self.current_proxy_index = 0

    def load_free_proxies(self) -> List[str]:
        """Carrega lista de proxies gratuitos (básico)"""
        # Lista básica de proxies públicos (substitua por serviço pago para produção)
        free_proxies = [
            "8.8.8.8:80",
            "1.1.1.1:80",
            # Adicione mais proxies conforme necessário
        ]
        return free_proxies

    def get_next_proxy(self) -> Optional[str]:
        """Retorna próximo proxy da rotação"""
        if not self.proxies:
            return None

        proxy = self.proxies[self.current_proxy_index]
        self.current_proxy_index = (self.current_proxy_index + 1) % len(self.proxies)
        return proxy

    def test_proxy(self, proxy: str) -> bool:
        """Testa se proxy está funcionando"""
        try:
            response = requests.get(
                "http://httpbin.org/ip",
                proxies={"http": f"http://{proxy}", "https": f"http://{proxy}"},
                timeout=5
            )
            return response.status_code == 200
        except:
            return False

    def get_working_proxies(self) -> List[str]:
        """Retorna apenas proxies funcionais"""
        working = []
        for proxy in self.load_free_proxies():
            if self.test_proxy(proxy):
                working.append(proxy)
        return working
