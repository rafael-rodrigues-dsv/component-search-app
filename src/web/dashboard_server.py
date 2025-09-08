#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Dashboard Web Server - Monitoramento em tempo real
"""
import json
import threading
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional

from src.application.services.database_service import DatabaseService

# Imports opcionais do Flask
try:
    from flask import Flask, render_template, jsonify
    from flask_socketio import SocketIO, emit
    FLASK_AVAILABLE = True
except ImportError:
    FLASK_AVAILABLE = False
    Flask = None
    SocketIO = None


class DashboardServer:
    """Servidor web para dashboard de monitoramento"""
    
    def __init__(self, port: int = 5000):
        if not FLASK_AVAILABLE:
            raise ImportError("Flask não está instalado. Execute: pip install flask flask-socketio")
        
        self.port = port
        self.app = Flask(__name__, 
                        template_folder=str(Path(__file__).parent / "templates"),
                        static_folder=str(Path(__file__).parent / "static"))
        self.app.config['SECRET_KEY'] = 'pythonsearch_dashboard_2024'
        
        # Desabilitar logs do Flask
        import logging
        logging.getLogger('werkzeug').setLevel(logging.ERROR)
        self.app.logger.setLevel(logging.ERROR)
        
        self.socketio = SocketIO(self.app, cors_allowed_origins="*", logger=False, engineio_logger=False)
        self.db_service = DatabaseService()
        self.is_running = False
        self.server_thread = None
        self.monitor_thread = None
        
        self._setup_routes()
        self._setup_socketio()
    
    def _setup_routes(self):
        """Configura rotas HTTP"""
        
        @self.app.route('/')
        def dashboard():
            return render_template('dashboard.html')
        
        @self.app.route('/api/export-excel')
        def export_excel():
            try:
                from src.application.services.excel_application_service import ExcelApplicationService
                excel_service = ExcelApplicationService()
                result = excel_service.export_excel()
                return jsonify(result)
            except Exception as e:
                return jsonify({'success': False, 'message': str(e)}), 500
        
        @self.app.route('/api/stats')
        def get_stats():
            try:
                stats = self.db_service.get_statistics()
                
                # Estatísticas de CEP
                try:
                    from src.application.services.cep_enrichment_application_service import CepEnrichmentApplicationService
                    cep_service = CepEnrichmentApplicationService()
                    cep_stats = cep_service.get_cep_enrichment_stats()
                except:
                    cep_stats = {'total': 0, 'concluidos': 0, 'percentual': 0}
                
                # Estatísticas de geolocalização
                try:
                    from src.application.services.geolocation_application_service import GeolocationApplicationService
                    geo_service = GeolocationApplicationService()
                    geo_stats = geo_service.get_geolocation_stats()
                except:
                    geo_stats = {'total_com_endereco': 0, 'geocodificadas': 0, 'percentual': 0}
                
                # Estatísticas detalhadas de empresas
                empresas_stats = self.db_service.get_company_collection_stats()
                
                return jsonify({
                    'timestamp': datetime.now().isoformat(),
                    'coleta': {
                        'termos_total': stats.get('termos_total', 0),
                        'termos_concluidos': stats.get('termos_concluidos', 0),
                        'progresso_pct': stats.get('progresso_pct', 0),
                        'empresas_total': stats.get('empresas_total', 0),
                        'empresas_visitadas': empresas_stats.get('visitadas', 0),
                        'empresas_coletadas': empresas_stats.get('coletadas', 0),
                        'empresas_nao_coletadas': empresas_stats.get('nao_coletadas', 0),
                        'taxa_coleta_pct': empresas_stats.get('taxa_coleta_pct', 0),
                        'emails_total': stats.get('emails_total', 0),
                        'telefones_total': stats.get('telefones_total', 0)
                    },
                    'cep': {
                        'total': cep_stats.get('total', 0),
                        'concluidos': cep_stats.get('concluidos', 0),
                        'pendentes': cep_stats.get('pendentes', 0),
                        'erros': cep_stats.get('erros', 0),
                        'percentual': cep_stats.get('percentual', 0)
                    },
                    'geo': {
                        'total': geo_stats.get('total_com_endereco', 0),
                        'geocodificadas': geo_stats.get('geocodificadas', 0),
                        'pendentes': geo_stats.get('pendentes', 0),
                        'erros': geo_stats.get('erros', 0),
                        'percentual': geo_stats.get('percentual', 0)
                    }
                })
            except Exception as e:
                return jsonify({'error': str(e)}), 500
    
    def _setup_socketio(self):
        """Configura WebSocket events"""
        
        @self.socketio.on('connect')
        def handle_connect():
            emit('status', {'message': 'Conectado ao dashboard'})
        
        @self.socketio.on('disconnect')
        def handle_disconnect():
            pass
    
    def _monitor_loop(self):
        """Loop de monitoramento em background"""
        while self.is_running:
            try:
                stats = self.db_service.get_statistics()
                
                # Estatísticas de CEP
                try:
                    from src.application.services.cep_enrichment_application_service import CepEnrichmentApplicationService
                    cep_service = CepEnrichmentApplicationService()
                    cep_stats = cep_service.get_cep_enrichment_stats()
                except:
                    cep_stats = {'total': 0, 'concluidos': 0, 'percentual': 0}
                
                # Estatísticas de geolocalização
                try:
                    from src.application.services.geolocation_application_service import GeolocationApplicationService
                    geo_service = GeolocationApplicationService()
                    geo_stats = geo_service.get_geolocation_stats()
                except:
                    geo_stats = {'total_com_endereco': 0, 'geocodificadas': 0, 'percentual': 0}
                
                # Estatísticas detalhadas de empresas
                empresas_stats = self.db_service.get_company_collection_stats()
                
                data = {
                    'timestamp': datetime.now().isoformat(),
                    'coleta': {
                        'termos_total': stats.get('termos_total', 0),
                        'termos_concluidos': stats.get('termos_concluidos', 0),
                        'progresso_pct': stats.get('progresso_pct', 0),
                        'empresas_total': stats.get('empresas_total', 0),
                        'empresas_visitadas': empresas_stats.get('visitadas', 0),
                        'empresas_coletadas': empresas_stats.get('coletadas', 0),
                        'empresas_nao_coletadas': empresas_stats.get('nao_coletadas', 0),
                        'taxa_coleta_pct': empresas_stats.get('taxa_coleta_pct', 0),
                        'emails_total': stats.get('emails_total', 0),
                        'telefones_total': stats.get('telefones_total', 0)
                    },
                    'cep': {
                        'total': cep_stats.get('total', 0),
                        'concluidos': cep_stats.get('concluidos', 0),
                        'pendentes': cep_stats.get('pendentes', 0),
                        'erros': cep_stats.get('erros', 0),
                        'percentual': cep_stats.get('percentual', 0)
                    },
                    'geo': {
                        'total': geo_stats.get('total_com_endereco', 0),
                        'geocodificadas': geo_stats.get('geocodificadas', 0),
                        'pendentes': geo_stats.get('pendentes', 0),
                        'erros': geo_stats.get('erros', 0),
                        'percentual': geo_stats.get('percentual', 0)
                    }
                }
                
                self.socketio.emit('stats_update', data)
                time.sleep(2)  # Atualiza a cada 2 segundos
                
            except Exception as e:
                print(f"[ERRO] Monitor dashboard: {e}")
                time.sleep(5)
    
    def start(self):
        """Inicia o servidor web em thread separada"""
        if self.is_running:
            return
        
        self.is_running = True
        
        # Desabilitar logs do Flask
        import logging
        log = logging.getLogger('werkzeug')
        log.setLevel(logging.ERROR)
        
        # Thread do servidor Flask
        self.server_thread = threading.Thread(
            target=lambda: self.socketio.run(
                self.app, 
                host='127.0.0.1', 
                port=self.port, 
                debug=False,
                use_reloader=False,
                log_output=False
            ),
            daemon=True
        )
        
        # Thread de monitoramento
        self.monitor_thread = threading.Thread(
            target=self._monitor_loop,
            daemon=True
        )
        
        self.server_thread.start()
        self.monitor_thread.start()
        
        print(f"[OK] Dashboard iniciado em http://127.0.0.1:{self.port}")
    
    def stop(self):
        """Para o servidor"""
        self.is_running = False
        if self.server_thread:
            self.server_thread.join(timeout=1)
        if self.monitor_thread:
            self.monitor_thread.join(timeout=1)


# Instância global do servidor
_dashboard_server = None


def start_dashboard(port: int = 5000) -> Optional[DashboardServer]:
    """Inicia o dashboard web"""
    global _dashboard_server
    
    if not FLASK_AVAILABLE:
        print("[AVISO] Flask não instalado. Dashboard web desabilitado.")
        print("[INFO] Para habilitar: pip install flask flask-socketio")
        return None
    
    if _dashboard_server is None:
        _dashboard_server = DashboardServer(port)
    
    _dashboard_server.start()
    return _dashboard_server


def stop_dashboard():
    """Para o dashboard web"""
    global _dashboard_server
    
    if _dashboard_server:
        _dashboard_server.stop()
        _dashboard_server = None