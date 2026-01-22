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
from src.application.services.robot_controller import request_stop, clear_stop

# Imports opcionais do Flask
try:
    from flask import Flask, render_template, jsonify
    from flask_socketio import SocketIO, emit
    FLASK_AVAILABLE = True
except ImportError:
    FLASK_AVAILABLE = False
    Flask = None
    SocketIO = None
    render_template = lambda *args, **kwargs: None
    jsonify = lambda *args, **kwargs: None
    emit = lambda *args, **kwargs: None


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
        
        # Configurar logger para exibir mensagens no terminal
        logging.basicConfig(level=logging.INFO)
        self.app.logger.setLevel(logging.INFO)

        self.socketio = SocketIO(self.app, cors_allowed_origins="*", logger=False, engineio_logger=False)
        self.db_service = DatabaseService()
        self.is_running = False
        self.server_thread = None
        self.monitor_thread = None

        # --- Captura de logs e saída padrão para o painel do dashboard ---
        import sys
        import logging as _logging

        class SocketIOLogHandler(_logging.Handler):
            """Logging handler que encaminha logs para o Socket.IO (evento 'robot_log')."""
            def __init__(self, socketio, level=_logging.INFO):
                super().__init__(level)
                self.socketio = socketio
                fmt = _logging.Formatter('%(asctime)s [%(levelname)s] %(name)s: %(message)s', '%H:%M:%S')
                self.setFormatter(fmt)

            def emit(self, record):
                try:
                    msg = self.format(record)
                    level = (record.levelname or 'INFO').lower()
                    # emitir de forma não bloqueante
                    try:
                        self.socketio.emit('robot_log', {'level': level, 'message': msg})
                    except Exception:
                        # Não usar logging interno aqui para evitar loops
                        pass
                except Exception:
                    pass

        # Bufferizado para stdout/stderr para enviar linhas completas
        class SocketIOStream:
            def __init__(self, original, socketio, level='info'):
                self._orig = original
                self._socketio = socketio
                self._level = level
                self._buf = ''

            def write(self, data):
                try:
                    self._orig.write(data)
                except Exception:
                    pass
                try:
                    if not data:
                        return
                    self._buf += str(data)
                    # enviar apenas linhas completas
                    while '\n' in self._buf:
                        line, self._buf = self._buf.split('\n', 1)
                        text = line.strip()
                        if text:
                            try:
                                self._socketio.emit('robot_log', {'level': self._level, 'message': text})
                            except Exception:
                                pass
                except Exception:
                    pass

            def flush(self):
                try:
                    if self._buf:
                        text = self._buf.strip()
                        if text:
                            try:
                                self._socketio.emit('robot_log', {'level': self._level, 'message': text})
                            except Exception:
                                pass
                        self._buf = ''
                except Exception:
                    pass

            # Support for attributes used by some code
            def isatty(self):
                try:
                    return self._orig.isatty()
                except Exception:
                    return False

        try:
            # Adicionar handler ao logger root para emitir logs via socket
            root_logger = _logging.getLogger()
            socket_handler = SocketIOLogHandler(self.socketio)
            socket_handler.setLevel(_logging.DEBUG)
            root_logger.addHandler(socket_handler)
        except Exception:
            pass

        try:
            # Redirecionar stdout/stderr para emitir via socket (mantendo saída original)
            sys.stdout = SocketIOStream(sys.stdout, self.socketio, level='info')
            sys.stderr = SocketIOStream(sys.stderr, self.socketio, level='error')
        except Exception:
            pass

        # ----------------------------------------------------------------

        self._setup_routes()
        self._setup_socketio()
    
    def _setup_routes(self):
        """Configura rotas HTTP"""
        
        @self.app.route('/')
        def dashboard():
            return render_template('dashboard/index.html')

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
                return jsonify({'success': False, 'message': str(e)}), 500

        @self.app.route('/api/config/cep', methods=['GET'])
        def get_reference_cep():
            try:
                from src.application.services.zip_code_service import ZipCodeService
                svc = ZipCodeService()
                cep_row = svc.get_reference_cep()
                if not cep_row:
                    # fallback to YAML default - format minimal structure
                    from src.infrastructure.config.config_manager import ConfigManager
                    cfg = ConfigManager()
                    cep_val = cfg.reference_cep
                    cep_row = {'cep': cep_val, 'cidade': '', 'estado': '', 'logradouro': ''}
                return jsonify({'success': True, 'data': cep_row})
            except Exception as e:
                return jsonify({'success': False, 'message': str(e)}), 500

        @self.app.route('/api/config/cep', methods=['POST'])
        def set_reference_cep():
            try:
                from flask import request
                data = request.get_json() or {}
                cep = data.get('cep')
                from src.application.services.zip_code_service import ZipCodeService
                svc = ZipCodeService()
                ok = svc.set_reference_cep(cep)
                if not ok:
                    return jsonify({'success': False, 'message': 'CEP inválido ou não encontrado'}), 400
                # Return updated row
                row = svc.get_reference_cep()
                return jsonify({'success': True, 'data': row})
            except Exception as e:
                return jsonify({'success': False, 'message': str(e)}), 500

        @self.app.route('/api/config/cep/lookup')
        def lookup_cep():
            try:
                from flask import request
                cep = request.args.get('cep')
                if not cep:
                    return jsonify({'success': False, 'message': 'CEP é obrigatório'}), 400
                # Use domain service to lookup via ViaCEP
                try:
                    from src.domain.services.address_enrichment_service import AddressEnrichmentService
                    svc = AddressEnrichmentService()
                    cep_data = svc._fetch_cep_data(cep)
                except Exception as e:
                    return jsonify({'success': False, 'message': f'Erro na consulta do CEP: {e}'}), 500
                if not cep_data:
                    return jsonify({'success': False, 'message': 'CEP não encontrado'}), 404
                # Normalize and return useful fields
                cep_clean = cep_data.get('cep') or cep
                result = {
                    'cep': cep_clean,
                    'logradouro': cep_data.get('logradouro', ''),
                    'bairro': cep_data.get('bairro', ''),
                    'cidade': cep_data.get('localidade', cep_data.get('localidade', '')),
                    'estado': cep_data.get('uf', '')
                }
                return jsonify({'success': True, 'data': result})
            except Exception as e:
                return jsonify({'success': False, 'message': str(e)}), 500

        # Páginas adicionais (configuração e execução)
        @self.app.route('/config/terms')
        def page_config_terms():
            from flask import redirect
            return redirect('/workflow')

        # Rotas de atalho para compatibilidade
        @self.app.route('/config')
        def page_config():
            from flask import redirect
            return redirect('/config/terms')

        # Rota da POC: workflow de execução (front-end mock)
        @self.app.route('/workflow')
        def workflow_index():
            try:
                return render_template('workflow/index.html')
            except Exception as e:
                return jsonify({'error': str(e)}), 500

        @self.app.route('/workflow/step/<step_name>')
        def workflow_step(step_name: str):
            """Serve templates parciais para cada passo do workflow POC.
            Aceita apenas nomes permitidos para evitar leitura arbitrária de arquivos.
            """
            try:
                allowed = {
                    'define_terms': 'workflow/_workflow_step_terms.html',
                    'define_cep': 'workflow/_workflow_step_zip_code.html',
                    'municipios': 'workflow/_workflow_step_cities.html',
                    'bairros': 'workflow/_workflow_step_neighborhood.html',
                    'termos_processados': 'workflow/_workflow_step_processed_terms.html'
                }
                tpl = allowed.get(step_name)
                if not tpl:
                    return jsonify({'error': 'Step inválido'}), 404
                return render_template(tpl)
            except Exception as e:
                return jsonify({'error': str(e)}), 500

        # Rotas alternativas com trailing slash (compatibilidade)
        @self.app.route('/config/terms/')
        def page_config_terms_slash():
            return page_config_terms()

        # Persistir rotas em data/routes.json para depuração (escreve no startup)
        try:
            routes_list = sorted([{
                'rule': r.rule,
                'methods': sorted(list(r.methods - {'HEAD', 'OPTIONS'})),
                'endpoint': r.endpoint
            } for r in self.app.url_map.iter_rules()], key=lambda x: x['rule'])
            data_dir = Path(__file__).parents[2] / 'data'
            data_dir.mkdir(parents=True, exist_ok=True)
            with open(data_dir / 'routes.json', 'w', encoding='utf-8') as _f:
                import json as _json
                _json.dump({'routes': routes_list}, _f, indent=2, ensure_ascii=False)
        except Exception:
            pass

        # Handler 404 para ajudar a depurar links locais (apenas para debug)
        @self.app.errorhandler(404)
        def page_not_found(e):
            try:
                routes = sorted([r.rule for r in self.app.url_map.iter_rules()])
                content = '<h3>404 - Not Found</h3><p>Rotas registradas:</p><ul>' + ''.join(f'<li>{r}</li>' for r in routes) + '</ul>'
                return content, 404
            except Exception:
                return '404 - Not Found', 404

        # ===== TERMOS (API de configuração) =====
        from flask import request
        from src.application.services.search_term_service import SearchTermService
        from src.infrastructure.config.config_manager import ConfigManager

        @self.app.route('/api/terms')
        def api_terms():
            try:
                config = ConfigManager()
                st_service = SearchTermService()

                # Fetch pagination parameters
                limit = int(request.args.get('limit', 10))
                offset = int(request.args.get('offset', 0))

                # Log para depuração: registrar chamadas e origem
                try:
                    client = request.remote_addr or 'unknown'
                except Exception:
                    client = 'unknown'
                self.app.logger.info(f"[API] /api/terms called from {client} - limit={limit} offset={offset}")

                # Get paginated terms
                result = st_service.get_paginated_terms(limit=limit, offset=offset)

                # Normalize output
                normalized = []
                for row in result['terms']:
                    if not isinstance(row, dict):
                        normalized.append(row)
                        continue
                    lower_map = {k.lower(): v for k, v in row.items()}
                    id_base = lower_map.get('id_base') or lower_map.get('id') or lower_map.get('idbase')
                    termo_busca = lower_map.get('termo_busca') or lower_map.get('termo') or lower_map.get('termo_completo')
                    categoria = lower_map.get('categoria') or lower_map.get('category') or lower_map.get('categ')

                    nb = {
                        'ID_BASE': id_base,
                        'TERMO_BUSCA': termo_busca,
                        'CATEGORIA': categoria
                    }
                    for k, v in row.items():
                        if k not in nb:
                            nb[k] = v
                    normalized.append(nb)

                return jsonify({
                    'terms': normalized,
                    'pagination': result['pagination']
                })
            except Exception as e:
                return jsonify({'success': False, 'message': str(e)}), 500

        @self.app.route('/api/terms', methods=['POST'])
        def api_terms_propose():
            try:
                payload = request.get_json(force=True) or {}
                termo = payload.get('termo')
                is_test = payload.get('is_test', False)
                proposto_por = payload.get('proposed_by', 'ui')
                if not termo:
                    return jsonify({'success': False, 'message': 'Campo termo é obrigatório'}), 400
                st_service = SearchTermService()
                change_id = st_service.propose_term(termo, is_test=is_test, proposto_por=proposto_por)
                # Notificar via websocket (proposta criada)
                try:
                    self.socketio.emit('term_change_proposed', {'id': change_id, 'termo': termo, 'proposto_por': proposto_por})
                except Exception:
                    pass
                return jsonify({'success': True, 'change_id': change_id})
            except Exception as e:
                import traceback as _tb
                tb = _tb.format_exc()
                print(f"[ERRO] api_terms_propose: {e}\n{tb}")
                return jsonify({'success': False, 'message': str(e), 'traceback': tb}), 500

        # Inserir termo direto (bypass change)
        @self.app.route('/api/terms/add', methods=['POST'])
        def api_terms_add():
            try:
                payload = request.get_json(force=True) or {}
                termo = payload.get('termo')
                categoria = payload.get('categoria', 'base')
                if not termo:
                    return jsonify({'success': False, 'message': 'Campo termo é obrigatório'}), 400
                # Respeitar modo de teste da aplicação para a inserção
                config = ConfigManager()
                st_service = SearchTermService()
                new_id = st_service.insert_term(termo, categoria=categoria, is_test=config.is_test_mode)
                # Emitir evento para atualizar as UIs conectadas
                try:
                    self.socketio.emit('term_change_applied', {'id': new_id, 'termo': termo, 'categoria': categoria})
                except Exception:
                    pass
                return jsonify({'success': True, 'id': new_id})
            except Exception as e:
                import traceback as _tb
                tb = _tb.format_exc()
                print(f"[ERRO] api_terms_add: {e}\n{tb}")
                return jsonify({'success': False, 'message': str(e), 'traceback': tb}), 500

        # Deletar term (marca como inativo)
        @self.app.route('/api/terms/<int:term_id>', methods=['DELETE'])
        def api_terms_delete(term_id: int):
            try:
                st_service = SearchTermService()
                # Primeiro, tentar remover como termo base (TB_BASE_BUSCA)
                try:
                    deleted_base = st_service.delete_base_term(term_id)
                    if deleted_base:
                        # Emitir evento para atualizar UIs
                        try:
                            self.socketio.emit('term_change_applied', {'id': term_id})
                        except Exception:
                            pass
                        return jsonify({'success': True})
                except Exception:
                    # não conseguir deletar como base não é fatal — tentaremos como termo dinâmico
                    pass

                # Se não foi um termo base, tentar deletar como termo em TB_TERMOS_BUSCA
                ok = st_service.delete_term_direct(term_id)
                return jsonify({'success': ok})
            except Exception as e:
                return jsonify({'success': False, 'message': str(e)}), 500

        # ===== EXECUÇÃO DO ROBÔ =====
        # Runner simples que executa EmailApplicationService.execute() em background
        class RobotRunner:
             def __init__(self, socketio):
                 self.socketio = socketio
                 self.thread = None
                 self.running = False
                 self._stop_requested = False
                 self.current_job = None

             def start(self, job_type: str = 'coleta'):
                 if self.running:
                     return False
                # Limpar sinal global de parada (caso tenha sido solicitado anteriormente)
                 try:
                     clear_stop()
                 except Exception:
                     pass
                 self._stop_requested = False
                 self.current_job = job_type
                 self.thread = threading.Thread(target=self._run, daemon=True)
                 self.thread.start()
                 self.running = True
                 return True

             def stop(self):
                 if not self.running:
                     return False
                # Sinalizar parada local e globalmente ao serviço
                 self._stop_requested = True
                 try:
                     request_stop()
                 except Exception:
                     pass
                 return True

             def _run(self):
                 try:
                     self.socketio.emit('robot_status', {'running': True, 'job': self.current_job})
                     # Escolher serviço baseado no job
                     try:
                         if self.current_job == 'coleta':
                             from src.application.services.email_application_service import EmailApplicationService
                             service = EmailApplicationService()
                             service.execute()
                         elif self.current_job == 'cep':
                             from src.application.services.cep_enrichment_application_service import CepEnrichmentApplicationService
                             service = CepEnrichmentApplicationService()
                             service.process_cep_enrichment()
                         elif self.current_job == 'geo':
                             from src.application.services.geolocation_application_service import GeolocationApplicationService
                             service = GeolocationApplicationService()
                             service.process_geolocation()
                         else:
                             # Default para coleta
                             from src.application.services.email_application_service import EmailApplicationService
                             service = EmailApplicationService()
                             service.execute()
                     except Exception as e:
                         self.socketio.emit('robot_log', {'level': 'error', 'message': str(e)})
                     finally:
                        # Se durante a execução foi solicitada parada, emitir log informativo
                         if self._stop_requested:
                             try:
                                 self.socketio.emit('robot_log', {'level': 'info', 'message': 'Parada solicitada pelo usuário'})
                             except Exception:
                                 pass
                 finally:
                     self.running = False
                     self.socketio.emit('robot_status', {'running': False, 'job': self.current_job})
                     self.current_job = None

        # Instanciar runner único
        if not hasattr(self, '_robot_runner'):
            self._robot_runner = RobotRunner(self.socketio)

        @self.app.route('/api/execute', methods=['POST'])
        def api_execute():
            try:
                payload = request.get_json(force=True) or {}
                action = payload.get('action')
                job_type = payload.get('job_type', 'coleta')
                # Ler configurações opcionais do payload
                browser = payload.get('browser')
                engine = payload.get('engine')
                # Parâmetro headless vindo da UI (True/False). Pode ser string 'true'/'false' também.
                headless = payload.get('headless', None)
                try:
                    from src.application.services.user_config_service import UserConfigService
                    if browser:
                        UserConfigService.set_browser(browser)
                    if engine:
                        UserConfigService.set_search_engine(engine)
                    # Propagar headless se informado (padrão: None = não altera)
                    if headless is not None:
                        # aceitar valores booleanos ou strings
                        if isinstance(headless, str):
                            val = headless.lower() in ('1', 'true', 'yes', 'y')
                        else:
                            val = bool(headless)
                        UserConfigService.set_headless(val)
                except Exception:
                    pass

                if action == 'start':
                    ok = self._robot_runner.start(job_type=job_type)
                    if ok:
                        return jsonify({'success': True, 'message': 'Robô iniciado'})
                    else:
                        return jsonify({'success': False, 'message': 'Robô já em execução'}), 400
                elif action == 'stop':
                    ok = self._robot_runner.stop()
                    if ok:
                        return jsonify({'success': True, 'message': 'Solicitado parada do robô'})
                    else:
                        return jsonify({'success': False, 'message': 'Robô não está em execução'}), 400
                else:
                    return jsonify({'success': False, 'message': 'Ação inválida'}), 400
            except Exception as e:
                return jsonify({'success': False, 'message': str(e)}), 500

        @self.app.route('/api/reset-search', methods=['POST'])
        def api_reset_search():
            try:
                # Resetar dados coletados e re-inicializar termos no banco
                try:
                    dbs = DatabaseService()
                    dbs.reset_data(confirm=True)
                    # Re-inicializar termos (descoberta dinâmica ou estática)
                    count = dbs.initialize_search_terms()
                except Exception as e:
                    return jsonify({'success': False, 'message': f'Falha ao resetar: {e}'}), 500

                return jsonify({'success': True, 'message': f'Reset concluído. {count} termos preparados.'})
            except Exception as e:
                return jsonify({'success': False, 'message': str(e)}), 500

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
                if not isinstance(stats, dict):
                    stats = {}

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

