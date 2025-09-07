"""
Configuração de delays por motor de busca
"""
from .config_manager import ConfigManager


def get_scraper_delays(search_engine: str = "DUCKDUCKGO"):
    """Retorna delays baseados no motor de busca lendo do YAML"""
    config = ConfigManager()
    engine_key = search_engine.lower()

    if engine_key == "google":
        return {
            "page_load": (config.get("search.delays.google.page_load_min", 1.5),
                          config.get("search.delays.google.page_load_max", 2.5)),
            "scroll": (config.get("search.delays.google.scroll_min", 0.8),
                       config.get("search.delays.google.scroll_max", 1.2))
        }
    else:  # DuckDuckGo
        return {
            "page_load": (config.get("search.delays.duckduckgo.page_load_min", 0.3),
                          config.get("search.delays.duckduckgo.page_load_max", 0.8)),
            "scroll": (config.get("search.delays.duckduckgo.scroll_min", 0.1),
                       config.get("search.delays.duckduckgo.scroll_max", 0.4))
        }
