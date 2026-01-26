#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Dashboard Web Server - Monitoramento em tempo real
"""
import threading
from datetime import datetime
from pathlib import Path
from typing import Optional

from src.application.services.database_application_service import DatabaseApplicationService
from src.application.services.robot_controller_application_service import request_stop, clear_stop
from src.infrastructure.services.dashboard_polling_service import DashboardPollingService

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
        self.db_service = DatabaseApplicationService()
        # Simple UI-reset flag: on server start this is True and will be cleared on first client check.
        # Clients should call GET /api/ui/reset on init; if {'reset': true} is returned they must clear persisted UI prefs.
        self.ui_reset_required = True
        self.is_running = False
        # In-memory admin tasks store (task_id -> status/result)
        self._admin_tasks = {}
        # Guard to avoid concurrent admin resets
        self._admin_reset_lock = threading.Lock()
        self._admin_reset_running = False
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
            try:
                from src.infrastructure.config.config_manager import ConfigManager
                cfg = ConfigManager()
                show_cep = bool(cfg.cep_enrichment_widget_enabled)
                show_geo = bool(cfg.geolocation_widget_enabled)
            except Exception:
                show_cep = True
                show_geo = True

            # Try to provide initial stats payload directly in the rendered page for instant UI
            initial_stats = None
            try:
                from src.infrastructure.cache.dashboard_cache import DashboardCache
                cache = DashboardCache.get_instance()
                initial_stats = cache.get('stats')
            except Exception:
                initial_stats = None

            if not initial_stats:
                try:
                    from src.infrastructure.services.dashboard_polling_service import DashboardPollingService
                    qb = DashboardPollingService(db_service=self.db_service)
                    initial_stats = qb._quick_build_payload()
                    if initial_stats:
                        try:
                            from src.infrastructure.cache.dashboard_cache import DashboardCache
                            DashboardCache.get_instance().set('stats', initial_stats)
                        except Exception:
                            pass
                except Exception:
                    initial_stats = None

            return render_template('dashboard/index.html', show_cep=show_cep, show_geo=show_geo, initial_stats=initial_stats)

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
                # First try the in-memory cache (immediate)
                try:
                    from src.infrastructure.cache.dashboard_cache import DashboardCache
                    cache = DashboardCache.get_instance()
                    cached = cache.get('stats')
                    if cached and isinstance(cached, dict) and 'coleta' in cached:
                        return jsonify(cached)
                except Exception:
                    cached = None

                # No cache available: build a quick payload (fast path) using DB-only queries
                try:
                    from src.infrastructure.services.dashboard_polling_service import DashboardPollingService
                    quick_builder = DashboardPollingService(db_service=self.db_service)
                    payload = quick_builder._quick_build_payload()
                    if payload:
                        try:
                            # Save to cache for subsequent fast reads
                            from src.infrastructure.cache.dashboard_cache import DashboardCache
                            DashboardCache.get_instance().set('stats', payload)
                        except Exception:
                            pass
                        return jsonify(payload)
                except Exception:
                    pass

                # Fallback: compute the full stats (may be slightly slower) but ensures correctness
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
                from src.application.services.zip_code_application_service import ZipCodeApplicationService
                svc = ZipCodeApplicationService()
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
                raio_km = data.get('raio_km')
                from src.application.services.zip_code_application_service import ZipCodeApplicationService
                svc = ZipCodeApplicationService()
                # Do not allow updating CEP while robot is running
                try:
                    if hasattr(self, '_robot_runner') and getattr(self._robot_runner, 'running', False):
                        return jsonify({'success': False, 'message': 'Robô em execução. Não é possível atualizar o CEP enquanto o robô estiver ativo.'}), 400
                except Exception:
                    pass

                # Persist CEP and read back the persisted row (with full address). This returns row or raises on error
                try:
                    row = svc.set_and_get_reference(cep, raio_km=raio_km)
                except Exception as e:
                    # network errors or external service errors may surface here
                    return jsonify({'success': False, 'message': f'Erro ao validar/consultar ViaCEP: {e}'}), 502

                if not row:
                    return jsonify({'success': False, 'message': 'CEP inválido ou não encontrado'}), 400

                # If frontend requests a reset+reinitialize, run it in background and return a task id
                reset_flag = bool(data.get('reset', False) or data.get('reset_and_seed', False))

                # Ensure we return the freshest persisted row (svc.get_reference_cep reads DB)
                try:
                    current_row = svc.get_reference_cep()
                except Exception:
                    current_row = row

                if reset_flag:
                    try:
                        # Prevent concurrent admin resets even for synchronous calls
                        try:
                            with self._admin_reset_lock:
                                if getattr(self, '_admin_reset_running', False):
                                    return jsonify({'success': False, 'message': 'Reset já em execução'}), 409
                                # mark as running for this synchronous operation
                                self._admin_reset_running = True
                        except Exception:
                            return jsonify({'success': False, 'message': 'Não foi possível iniciar reset (lock error)'}), 500

                        # Execute synchronously similar to main: delete/reset and run initial load
                        try:
                            from src.application.services.initialize_database_service import InitializeDatabaseService
                            init_svc = InitializeDatabaseService()
                            # This will perform delete of tables (preserving TB_CEP_CONFIG per implementation) and run initial sequence
                            results = init_svc.reset_and_initialize()
                            return jsonify({'success': True, 'data': current_row, 'reseed': results})
                        finally:
                            # clear running flag so next admin reset can start
                            try:
                                with self._admin_reset_lock:
                                    self._admin_reset_running = False
                            except Exception:
                                self._admin_reset_running = False
                    except Exception as e:
                        return jsonify({'success': False, 'message': f'Falha no reprocessamento: {e}'}), 500

                return jsonify({'success': True, 'data': current_row})
            except Exception as e:
                return jsonify({'success': False, 'message': str(e)}), 500

        @self.app.route('/api/config/cep/lookup')
        def lookup_cep():
            try:
                from flask import request
                cep = request.args.get('cep')
                if not cep:
                    return jsonify({'success': False, 'message': 'CEP é obrigatório'}), 400

                import re
                cep_clean = re.sub(r'\D', '', cep or '')
                if len(cep_clean) != 8:
                    return jsonify({'success': False, 'message': 'CEP inválido (deve conter 8 dígitos)'}), 400

                # Format CEP as 12345-678
                formatted = f"{cep_clean[:5]}-{cep_clean[5:]}"

                # Try to fetch full address using domain AddressEnrichmentService (ViaCEP)
                try:
                    from src.domain.services.address_enrichment_service import AddressEnrichmentService
                    svc = AddressEnrichmentService()
                    # _fetch_cep_data returns the ViaCEP raw dict or None
                    cep_data = svc._fetch_cep_data(formatted)
                    if not cep_data:
                        return jsonify({'success': False, 'message': 'CEP não encontrado via ViaCEP'}), 404

                    # Normalize response keys expected by frontend
                    resp = {
                        'cep': cep_data.get('cep') or formatted,
                        'logradouro': cep_data.get('logradouro') or '',
                        'bairro': cep_data.get('bairro') or cep_data.get('complemento') or '',
                        'cidade': cep_data.get('localidade') or cep_data.get('cidade') or '',
                        'estado': cep_data.get('uf') or cep_data.get('estado') or ''
                    }

                    return jsonify({'success': True, 'data': resp})
                except Exception as e:
                    # Domain service may raise on network/ssl errors; return 502 to indicate upstream failure
                    return jsonify({'success': False, 'message': f'Erro ao consultar ViaCEP: {e}'}), 502

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

        # ===== TERMOS (TB_TERMOS_BUSCA) - API paginada para o workflow =====
        from flask import request
        from src.application.services.terms_application_service import TermsApplicationService

        @self.app.route('/api/terms')
        def api_terms():
            try:
                svc = TermsApplicationService()

                # Pagination parameters from front (limit=page_size, offset=offset)
                limit = int(request.args.get('limit', 10))
                offset = int(request.args.get('offset', 0))

                # Compute page number expected by TermsApplicationService
                page_size = max(1, int(limit))
                page = (int(offset) // page_size) + 1

                # Logging
                try:
                    client = request.remote_addr or 'unknown'
                except Exception:
                    client = 'unknown'
                self.app.logger.info(f"[API] /api/terms (TB_TERMOS_BUSCA) called from {client} - limit={limit} offset={offset}")

                data = svc.list_paginated(page=page, page_size=page_size)
                items = data.get('items', [])
                total = int(data.get('total', 0) or 0)

                # Normalize to expected frontend keys: TERMO_COMPLETO, STATUS_PROCESSAMENTO, TIPO_LOCALIDADE, ID_TERMO
                normalized = []
                for r in items:
                    if isinstance(r, dict):
                        lower = {k.lower(): v for k, v in r.items()}
                        normalized.append({
                            'ID_TERMO': lower.get('id_termo') or lower.get('id') or lower.get('id_termo'),
                            'TERMO_COMPLETO': lower.get('termo_completo') or lower.get('termo') or lower.get('termo_busca') or lower.get('termo_text'),
                            'TIPO_LOCALIDADE': lower.get('tipo_localizacao') or lower.get('tipo') or '',
                            'STATUS_PROCESSAMENTO': lower.get('status_processamento') or lower.get('status') or ''
                        })
                    else:
                        # If it's a model instance, try to call to_api_dict
                        try:
                            normalized.append(r.to_api_dict())
                        except Exception:
                            normalized.append(r)

                total_pages = (total + page_size - 1) // page_size if page_size > 0 else 1
                current_page = page

                return jsonify({
                    'terms': normalized,
                    'pagination': {
                        'total_pages': total_pages,
                        'current_page': current_page,
                        'has_next': current_page < total_pages,
                        'has_previous': current_page > 1
                    }
                })
            except Exception as e:
                return jsonify({'success': False, 'message': str(e)}), 500

        @self.app.route('/api/terms', methods=['POST'])
        def api_terms_propose_or_add():
            """Endpoint simples para adicionar um termo diretamento em TB_TERMOS_BUSCA (POC).
            Aceita JSON: { 'termo': 'texto', 'categoria': 'cat' }
            """
            try:
                payload = request.get_json(force=True) or {}
                termo = payload.get('termo')
                categoria = payload.get('categoria', '')
                if not termo:
                    return jsonify({'success': False, 'message': 'Campo termo é obrigatório'}), 400

                svc = TermsApplicationService()
                new_id = svc.add_term(termo, tipo_localizacao=categoria)

                # Emitir evento para atualizar as UIs conectadas
                try:
                    self.socketio.emit('term_change_applied', {'id': new_id, 'termo': termo, 'categoria': categoria})
                except Exception:
                    pass

                return jsonify({'success': True, 'id': new_id})
            except Exception as e:
                import traceback as _tb
                tb = _tb.format_exc()
                print(f"[ERRO] api_terms_propose_or_add: {e}\n{tb}")
                return jsonify({'success': False, 'message': str(e), 'traceback': tb}), 500

        # Deletar term (POC para TB_TERMOS_BUSCA)
        @self.app.route('/api/terms/<int:term_id>', methods=['DELETE'])
        def api_terms_delete(term_id: int):
            try:
                svc = TermsApplicationService()
                ok = svc.delete_term(term_id)
                try:
                    self.socketio.emit('term_change_applied', {'id': term_id})
                except Exception:
                    pass
                return jsonify({'success': bool(ok)})
            except Exception as e:
                return jsonify({'success': False, 'message': str(e)}), 500

        # --- Novos endpoints paginados para repositórios migrados ---
        @self.app.route('/api/companies')
        def api_companies():
            try:
                from flask import request
                from src.application.services.companies_application_service import CompaniesApplicationService
                svc = CompaniesApplicationService
                term_id = request.args.get('term_id')
                limit = int(request.args.get('limit', 10))
                offset = int(request.args.get('offset', 0))
                client = request.remote_addr or 'unknown'
                self.app.logger.info(f"[API] /api/companies called from {client} - term_id={term_id} limit={limit} offset={offset}")
                data = svc.get_paginated_companies_for_term(id_termo=int(term_id) if term_id else None, limit=limit, offset=offset)
                return jsonify(data)
            except Exception as e:
                return jsonify({'success': False, 'message': str(e)}), 500

        @self.app.route('/api/emails')
        def api_emails():
            try:
                from flask import request
                from src.application.services.email_application_service import EmailApplicationService
                svc = EmailApplicationService()
                empresa_id = request.args.get('empresa_id')
                limit = int(request.args.get('limit', 10))
                offset = int(request.args.get('offset', 0))
                data = svc.get_paginated_emails(empresa_id=int(empresa_id) if empresa_id else None, limit=limit, offset=offset)
                return jsonify(data)
            except Exception as e:
                return jsonify({'success': False, 'message': str(e)}), 500

        @self.app.route('/api/phones')
        def api_phones():
            try:
                from flask import request
                from src.application.services.phones_application_service import PhonesApplicationService
                svc = PhonesApplicationService()
                empresa_id = request.args.get('empresa_id')
                limit = int(request.args.get('limit', 10))
                offset = int(request.args.get('offset', 0))
                data = svc.get_paginated_phones(empresa_id=int(empresa_id) if empresa_id else None, limit=limit, offset=offset)
                return jsonify(data)
            except Exception as e:
                return jsonify({'success': False, 'message': str(e)}), 500

        @self.app.route('/api/cep/tasks')
        def api_cep_tasks():
            try:
                from src.application.services.cep_enrichment_application_service import CepEnrichmentApplicationService
                from flask import request
                svc = CepEnrichmentApplicationService
                limit = int(request.args.get('limit', 10))
                offset = int(request.args.get('offset', 0))
                return jsonify(svc.get_paginated_tasks(limit=limit, offset=offset))
            except Exception as e:
                return jsonify({'success': False, 'message': str(e)}), 500

        @self.app.route('/api/geo/list')
        def api_geo_list():
            try:
                from src.application.services.geolocation_application_service import GeolocationApplicationService
                from flask import request
                svc = GeolocationApplicationService
                limit = int(request.args.get('limit', 10))
                offset = int(request.args.get('offset', 0))
                return jsonify(svc.get_paginated_geolocations(limit=limit, offset=offset))
            except Exception as e:
                return jsonify({'success': False, 'message': str(e)}), 500

        @self.app.route('/api/spreadsheet')
        def api_spreadsheet():
            try:
                from src.application.services.spreadsheet_application_service import SpreadsheetApplicationService
                from flask import request
                svc = SpreadsheetApplicationService()
                limit = request.args.get('limit')
                offset = int(request.args.get('offset', 0))
                rows = svc.list_rows(limit=int(limit) if limit else None, offset=offset)
                total = svc.count()
                return jsonify({'rows': rows, 'pagination': {'total': total, 'limit': int(limit) if limit else None, 'offset': offset}})
            except Exception as e:
                return jsonify({'success': False, 'message': str(e)}), 500

        @self.app.route('/api/zones')
        def api_zones():
            try:
                from src.application.services.zones_application_service import ZonesApplicationService
                from flask import request
                svc = ZonesApplicationService()
                limit = int(request.args.get('limit', 10))
                offset = int(request.args.get('offset', 0))
                return jsonify(svc.get_paginated_zones(limit=limit, offset=offset))
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
                    try:
                        # sinaliza início
                        try:
                            self.socketio.emit('robot_status', {'running': True, 'job': self.current_job})
                        except Exception:
                            pass

                        # Escolher serviço baseado no job
                        if self.current_job == 'coleta':
                            from src.application.services.email_application_service import EmailApplicationService
                            service = EmailApplicationService()
                            try:
                                ok = service.execute()
                                if not ok:
                                    try:
                                        import traceback
                                        tb = traceback.format_exc()
                                    except Exception:
                                        tb = None
                                    try:
                                        self.socketio.emit('robot_log', {'level': 'error', 'message': 'EmailApplicationService.execute returned False', 'trace': tb})
                                    except Exception:
                                        pass
                            except Exception as e:
                                import traceback
                                tb = traceback.format_exc()
                                try:
                                    self.socketio.emit('robot_log', {'level': 'error', 'message': str(e), 'trace': tb})
                                except Exception:
                                    pass

                        elif self.current_job == 'cep':
                            from src.application.services.cep_enrichment_application_service import CepEnrichmentApplicationService
                            service = CepEnrichmentApplicationService()
                            try:
                                try:
                                    self.socketio.emit('robot_log', {'level': 'info', 'message': '[CEP] Iniciando enriquecimento CEP (via RobotRunner)'} )
                                except Exception:
                                    pass
                                result = service.process_cep_enrichment()
                                try:
                                    summary = f"[CEP] Resultado: processed={result.get('processadas', 0)} enriched={result.get('enriquecidas', 0)} total={result.get('total', 0)}"
                                    self.socketio.emit('robot_log', {'level': 'info', 'message': summary})
                                except Exception:
                                    pass
                            except Exception as e:
                                import traceback
                                tb = traceback.format_exc()
                                try:
                                    self.socketio.emit('robot_log', {'level': 'error', 'message': str(e), 'trace': tb})
                                except Exception:
                                    pass

                        elif self.current_job == 'geo':
                            from src.application.services.geolocation_application_service import GeolocationApplicationService
                            service = GeolocationApplicationService()
                            try:
                                service.process_geolocation()
                            except Exception as e:
                                import traceback
                                tb = traceback.format_exc()
                                try:
                                    self.socketio.emit('robot_log', {'level': 'error', 'message': str(e), 'trace': tb})
                                except Exception:
                                    pass

                        else:
                            # Default para coleta
                            from src.application.services.email_application_service import EmailApplicationService
                            service = EmailApplicationService
                            try:
                                ok = service.execute()
                                if not ok:
                                    try:
                                        self.socketio.emit('robot_log', {'level': 'error', 'message': 'Default EmailApplicationService.execute returned False'})
                                    except Exception:
                                        pass
                            except Exception as e:
                                import traceback
                                tb = traceback.format_exc()
                                try:
                                    self.socketio.emit('robot_log', {'level': 'error', 'message': str(e), 'trace': tb})
                                except Exception:
                                    pass

                        # Se durante a execução foi solicitada parada, emitir log informativo
                        if self._stop_requested:
                            try:
                                self.socketio.emit('robot_log', {'level': 'info', 'message': 'Parada solicitada pelo usuário'})
                            except Exception:
                                pass

                    except Exception as e:
                        import traceback
                        tb = traceback.format_exc()
                        try:
                            self.socketio.emit('robot_log', {'level': 'error', 'message': str(e), 'trace': tb})
                        except Exception:
                            pass
                finally:
                    # garantir flags e status
                    self.running = False
                    try:
                        self.socketio.emit('robot_status', {'running': False, 'job': self.current_job})
                    except Exception:
                        pass
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
                    from src.application.services.user_config_application_service import UserConfigApplicationService
                    if browser:
                        UserConfigApplicationService.set_browser(browser)
                    if engine:
                        UserConfigApplicationService.set_search_engine(engine)
                    # Propagar headless se informado (padrão: None = não altera)
                    if headless is not None:
                        # aceitar valores booleanos ou strings
                        if isinstance(headless, str):
                            val = headless.lower() in ('1', 'true', 'yes', 'y')
                        else:
                            val = bool(headless)
                        UserConfigApplicationService.set_headless(val)
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
                    dbs = DatabaseApplicationService()
                    dbs.reset_data(confirm=True)
                    # Re-inicializar termos (descoberta dinâmica ou estática)
                    count = dbs.initialize_search_terms()
                except Exception as e:
                    return jsonify({'success': False, 'message': f'Falha ao resetar: {e}'}), 500

                return jsonify({'success': True, 'message': f'Reset concluído. {count} termos preparados.'})
            except Exception as e:
                return jsonify({'success': False, 'message': str(e)}), 500

        # Endpoint administrativo: reset parcial (preserva TB_CEP_CONFIG e TB_TERMOS_BUSCA) e re-inicializa
        @self.app.route('/api/admin/reset-and-initialize', methods=['POST'])
        def api_admin_reset_and_initialize():
            try:
                from flask import request
                # Prevent running while robot is active
                try:
                    if hasattr(self, '_robot_runner') and getattr(self._robot_runner, 'running', False):
                        return jsonify({'success': False, 'message': 'Robô em execução. Pare o robô antes de resetar.'}), 409
                except Exception:
                    pass

                # Prevent concurrent admin resets
                try:
                    with self._admin_reset_lock:
                        if getattr(self, '_admin_reset_running', False):
                            return jsonify({'success': False, 'message': 'Reset já em execução'}), 409
                        self._admin_reset_running = True
                except Exception:
                    return jsonify({'success': False, 'message': 'Não foi possível iniciar reset (lock error)'}), 500

                # Create task record
                import uuid, traceback
                task_id = str(uuid.uuid4())
                self._admin_tasks[task_id] = {'status': 'pending', 'started_at': datetime.now().isoformat(), 'progress': 0, 'message': None}

                def _background_task():
                    try:
                        self._admin_tasks[task_id]['status'] = 'running'
                        self._admin_tasks[task_id]['message'] = 'Executando reset e inicialização'
                        try:
                            self.socketio.emit('reset_status', {'task_id': task_id, 'status': 'running', 'message': self._admin_tasks[task_id]['message']})
                        except Exception:
                            pass

                        from src.application.services.initialize_database_service import InitializeDatabaseService
                        init_svc = InitializeDatabaseService()
                        result = init_svc.reset_and_initialize()

                        self._admin_tasks[task_id]['status'] = 'done'
                        self._admin_tasks[task_id]['result'] = result
                        self._admin_tasks[task_id]['message'] = 'Concluído'
                        try:
                            self.socketio.emit('reset_status', {'task_id': task_id, 'status': 'done', 'result': result})
                        except Exception:
                            pass
                        # Emit a higher-level event to notify clients to refresh all workflow grids
                        try:
                            self.socketio.emit('reprocess_complete', {'task_id': task_id, 'result': result})
                        except Exception:
                            pass
                    except Exception as e:
                        tb = traceback.format_exc()
                        self._admin_tasks[task_id]['status'] = 'failed'
                        self._admin_tasks[task_id]['message'] = str(e)
                        self._admin_tasks[task_id]['traceback'] = tb
                        try:
                            self.socketio.emit('reset_status', {'task_id': task_id, 'status': 'failed', 'message': str(e)})
                        except Exception:
                            pass
                    finally:
                        # clear running flag so next admin reset can start
                        try:
                            with self._admin_reset_lock:
                                self._admin_reset_running = False
                        except Exception:
                            self._admin_reset_running = False

                thread = threading.Thread(target=_background_task, daemon=True)
                thread.start()

                return jsonify({'success': True, 'task_id': task_id}), 202
            except Exception as e:
                # ensure flag cleared on unexpected failure before return
                try:
                    with self._admin_reset_lock:
                        self._admin_reset_running = False
                except Exception:
                    self._admin_reset_running = False
                return jsonify({'success': False, 'message': str(e)}), 500

        @self.app.route('/api/admin/reset-status')
        def api_admin_reset_status():
            try:
                from flask import request
                task_id = request.args.get('task_id')
                if not task_id:
                    return jsonify({'success': False, 'message': 'task_id required'}), 400
                tasks = getattr(self, '_admin_tasks', {})
                if task_id not in tasks:
                    return jsonify({'success': False, 'message': 'task not found'}), 404
                return jsonify({'success': True, 'task': tasks[task_id]})
            except Exception as e:
                return jsonify({'success': False, 'message': str(e)}), 500

        # ===== WORKFLOW: Municípios (lista paginada via TB_CIDADES) =====
        @self.app.route('/api/workflow/cities')
        def api_workflow_cities():
            try:
                from flask import request
                uf = request.args.get('uf') or None
                try:
                    limit = int(request.args.get('limit', 10))
                except Exception:
                    limit = 10
                try:
                    offset = int(request.args.get('offset', 0))
                except Exception:
                    offset = 0

                # Use application service to read TB_CIDADES directly (no cache fallback)
                from src.application.services.cities_application_service import CitiesApplicationService
                svc = CitiesApplicationService()
                result = svc.get_paginated_cities(uf=uf, limit=limit, offset=offset)

                normalized = []
                for r in result.get('cities', []):
                    if isinstance(r, dict):
                        lower = {k.lower(): v for k, v in r.items()}
                        nome = lower.get('nome') or lower.get('name') or lower.get('nome_cidade') or ''
                        idv = lower.get('id') or lower.get('id_cidade') or None
                        uf_val = (lower.get('uf') or '').strip() if isinstance(lower.get('uf'), str) else ''
                    else:
                        try:
                            nome = r.name
                            idv = getattr(r, 'id', None)
                            uf_val = getattr(r, 'uf', '')
                        except Exception:
                            nome = ''
                            idv = None
                            uf_val = ''
                    normalized.append({'id': idv, 'name': nome, 'uf': uf_val})

                return jsonify({'cities': normalized, 'pagination': result.get('pagination', {})})
            except Exception as e:
                return jsonify({'success': False, 'message': str(e)}), 500

        @self.app.route('/api/workflow/neighborhoods')
        def api_workflow_neighborhoods():
            try:
                from flask import request
                uf = request.args.get('uf') or None
                try:
                    limit = int(request.args.get('limit', 10))
                except Exception:
                    limit = 10
                try:
                    offset = int(request.args.get('offset', 0))
                except Exception:
                    offset = 0

                from src.application.services.neighborhoods_application_service import NeighborhoodsApplicationService
                svc = NeighborhoodsApplicationService()
                result = svc.get_paginated_neighborhoods(uf=uf, limit=limit, offset=offset)

                normalized = []
                for r in result.get('neighborhoods', []):
                    if isinstance(r, dict):
                        lower = {k.lower(): v for k, v in r.items()}
                        nome = lower.get('nome') or lower.get('name') or lower.get('nome_bairro') or ''
                        idv = lower.get('id') or lower.get('id_bairro') or None
                        uf_val = (lower.get('uf') or '').strip() if isinstance(lower.get('uf'), str) else ''
                        city_name = (lower.get('cidade') or lower.get('city') or lower.get('nome_cidade') or '')
                        if isinstance(city_name, str):
                            city_name = city_name.strip()
                    else:
                        try:
                            nome = getattr(r, 'name', '')
                            idv = getattr(r, 'id', None)
                            uf_val = getattr(r, 'uf', '')
                            city_name = getattr(r, 'city', '')
                        except Exception:
                            nome = ''
                            idv = None
                            uf_val = ''
                            city_name = ''
                    normalized.append({'id': idv, 'name': nome, 'uf': uf_val, 'city': city_name})

                return jsonify({'neighborhoods': normalized, 'pagination': result.get('pagination', {})})
            except Exception as e:
                return jsonify({'success': False, 'message': str(e)}), 500

        # ===== WORKFLOW: Termos Processados (TB_TERMOS_BUSCA) =====
        @self.app.route('/api/workflow/processed_terms')
        def api_workflow_processed_terms():
            try:
                from flask import request
                try:
                    limit = int(request.args.get('limit', 10))
                except Exception:
                    limit = 10
                try:
                    offset = int(request.args.get('offset', 0))
                except Exception:
                    offset = 0

                from src.application.services.processed_terms_application_service import ProcessedTermsApplicationService
                svc = ProcessedTermsApplicationService()
                data = svc.get_paginated_processed_terms(limit=limit, offset=offset)

                # Expecting {'terms': [...], 'pagination': {...}}
                return jsonify(data)
            except Exception as e:
                return jsonify({'success': False, 'message': str(e)}), 500

        # ===== Base terms (TB_BASE_BUSCA) - paginated endpoint for workflow Define os Termos =====
        @self.app.route('/api/workflow/base_terms')
        def api_workflow_base_terms():
            try:
                from flask import request
                try:
                    limit = int(request.args.get('limit', 10))
                except Exception:
                    limit = 10
                try:
                    offset = int(request.args.get('offset', 0))
                except Exception:
                    offset = 0

                from src.application.services.base_search_application_service import BaseSearchApplicationService
                svc = BaseSearchApplicationService()
                # compute page number
                page_size = max(1, int(limit))
                page = (int(offset) // page_size) + 1
                data = svc.list_paginated(page=page, page_size=page_size)
                items = data.get('items', [])
                total = int(data.get('total', 0) or 0)

                # Return as-is; frontend's renderTerms is tolerant to different key names
                return jsonify({
                    'terms': items,
                    'pagination': {
                        'total_pages': (total + page_size - 1) // page_size if page_size > 0 else 1,
                        'current_page': page,
                        'has_next': page * page_size < total,
                        'has_previous': page > 1
                    }
                })
            except Exception as e:
                return jsonify({'success': False, 'message': str(e)}), 500

        @self.app.route('/api/workflow/base_terms', methods=['POST'])
        def api_workflow_base_terms_add():
            try:
                from flask import request
                payload = request.get_json(force=True) or {}
                term = payload.get('term') or payload.get('termo') or payload.get('termo_busca')
                category = payload.get('category') or payload.get('categoria') or ''
                is_test = bool(payload.get('is_test', False))
                if not term:
                    return jsonify({'success': False, 'message': 'Campo term é obrigatório'}), 400
                from src.application.services.base_search_application_service import BaseSearchApplicationService
                svc = BaseSearchApplicationService()
                new_id = svc.add_term(term, category=category, is_test=is_test)
                # Emit socket event so UI updates
                try:
                    self.socketio.emit('base_term_changed', {'action': 'add', 'id': new_id, 'term': term})
                except Exception:
                    pass
                return jsonify({'success': True, 'id': new_id})
            except Exception as e:
                return jsonify({'success': False, 'message': str(e)}), 500

        @self.app.route('/api/workflow/base_terms/<int:id_base>', methods=['DELETE'])
        def api_workflow_base_terms_delete(id_base: int):
            try:
                from src.application.services.base_search_application_service import BaseSearchApplicationService
                svc = BaseSearchApplicationService()
                ok = svc.delete_term(id_base)
                try:
                    self.socketio.emit('base_term_changed', {'action': 'delete', 'id': id_base})
                except Exception:
                    pass
                return jsonify({'success': bool(ok)})
            except Exception as e:
                return jsonify({'success': False, 'message': str(e)}), 500

        # DEBUG endpoint: diagnostics for term deletion (temporary)
        @self.app.route('/api/debug/terms_delete_diag')
        def api_debug_terms_delete():
            try:
                from flask import request
                term_id = request.args.get('term_id')
                if not term_id:
                    return jsonify({'success': False, 'message': 'term_id required'}), 400
                tid = int(term_id)
                from src.infrastructure.repositories.access_repository import AccessRepository
                from src.infrastructure.repositories.terms_repository import TermsRepository
                access = AccessRepository()
                tr = TermsRepository()
                before = access.execute_query('SELECT ID_TERMO, STATUS_PROCESSAMENTO FROM TB_TERMOS_BUSCA WHERE ID_TERMO = ?', [tid])
                exc = None
                try:
                    deleted = tr.delete(tid)
                except Exception as e:
                    deleted = False
                    import traceback as _tb
                    exc = str(e) + '\n' + _tb.format_exc()
                after = access.execute_query('SELECT ID_TERMO, STATUS_PROCESSAMENTO FROM TB_TERMOS_BUSCA WHERE ID_TERMO = ?', [tid])
                return jsonify({'success': True, 'term_id': tid, 'before': before, 'after': after, 'deleted': bool(deleted), 'exception': exc})
            except Exception as e:
                return jsonify({'success': False, 'message': str(e)}), 500

        @self.app.route('/api/ui/reset')
        def api_ui_reset():
            try:
                # Return True once after server startup; then clear the flag so subsequent calls return False
                if getattr(self, 'ui_reset_required', False):
                    try:
                        # clear the flag so only the first caller(s) see reset
                        self.ui_reset_required = False
                    except Exception:
                        pass
                    return jsonify({'reset': True})
                return jsonify({'reset': False})
            except Exception as e:
                return jsonify({'success': False, 'message': str(e)}), 500

        @self.app.route('/api/robot/status')
        def api_robot_status():
            try:
                running = False
                job = None
                try:
                    if hasattr(self, '_robot_runner'):
                        running = bool(getattr(self._robot_runner, 'running', False))
                        job = getattr(self._robot_runner, 'current_job', None)
                except Exception:
                    pass
                return jsonify({'success': True, 'running': running, 'job': job})
            except Exception as e:
                return jsonify({'success': False, 'message': str(e)}), 500

        # Start polling service (cache updater)
        try:
            self._polling_service = DashboardPollingService(
                db_service=self.db_service,
                socketio=self.socketio,
                poll_interval=2.0,
                robot_running_check=lambda: bool(getattr(self, '_robot_runner', None) and getattr(self._robot_runner, 'running', False))
            )
            # Try synchronous population so /api/stats can return immediately when client requests
            try:
                self._polling_service.refresh_once()
            except Exception:
                pass
        except Exception:
            self._polling_service = None

        print(f"[OK] Dashboard iniciado em http://127.0.0.1:{self.port}")

        # finally start poller thread (non-blocking) so live updates continue
        try:
            if self._polling_service:
                self._polling_service.start()
        except Exception:
            pass

    def _setup_socketio(self):
        """Configura WebSocket events"""
        
        @self.socketio.on('connect')
        def handle_connect():
            emit('status', {'message': 'Conectado ao dashboard'})
            # Ao conectar, enviar imediatamente o snapshot em cache (se houver)
            try:
                from src.infrastructure.cache.dashboard_cache import DashboardCache
                cache = DashboardCache.get_instance()
                stats = cache.get('stats')
                if stats and isinstance(stats, dict):
                    try:
                        emit('stats_update', stats)
                    except Exception:
                        # emitir via self.socketio se emit falhar no contexto do handler
                        try:
                            self.socketio.emit('stats_update', stats)
                        except Exception:
                            pass
            except Exception:
                pass

        @self.socketio.on('disconnect')
        def handle_disconnect():
            pass
    
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
        
        self.server_thread.start()

        print(f"[OK] Dashboard iniciado em http://127.0.0.1:{self.port}")
    
    def stop(self):
        """Para o servidor"""
        self.is_running = False
        if self.server_thread:
            self.server_thread.join(timeout=1)


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

