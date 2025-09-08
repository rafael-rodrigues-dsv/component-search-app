#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Configurações do Dashboard Web
"""
from dataclasses import dataclass
from typing import Optional

@dataclass
class DashboardConfig:
    """Configurações do dashboard web"""
    
    # Servidor
    host: str = '127.0.0.1'
    port: int = 5000
    debug: bool = False
    
    # Comportamento
    auto_open_browser: bool = True
    update_interval_seconds: int = 2
    max_chart_points: int = 20
    
    # Segurança
    secret_key: str = 'pythonsearch_dashboard_2024'
    cors_origins: str = "*"
    
    # Performance
    max_connections: int = 100
    connection_timeout: int = 30
    
    @classmethod
    def from_yaml_config(cls, config_manager) -> 'DashboardConfig':
        """Cria configuração a partir do ConfigManager"""
        try:
            dashboard_config = config_manager.get('dashboard', {})
            
            return cls(
                port=dashboard_config.get('port', 5000),
                auto_open_browser=dashboard_config.get('auto_open_browser', True),
                update_interval_seconds=dashboard_config.get('update_interval_seconds', 2)
            )
        except:
            return cls()  # Configuração padrão