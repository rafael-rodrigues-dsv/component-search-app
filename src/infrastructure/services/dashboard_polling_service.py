"""
Polling service que atualiza o DashboardCache periodicamente.
"""
import threading
from typing import Optional, Callable
from datetime import datetime

from src.infrastructure.cache.dashboard_cache import DashboardCache


class DashboardPollingService:
    def __init__(self, db_service=None, socketio=None, poll_interval: float = 2.0, robot_running_check: Optional[Callable[[], bool]] = None):
        self._stop = threading.Event()
        self._thread: Optional[threading.Thread] = None
        self.poll_interval = float(poll_interval)
        self.db_service = db_service
        self.socketio = socketio
        self.cache = DashboardCache.get_instance()
        # callable that returns True if robot is running
        self.robot_running_check = robot_running_check

    def start(self):
        if self._thread and self._thread.is_alive():
            return
        self._stop.clear()
        # start polling loop thread
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()
        # spawn an immediate non-blocking refresh so UI gets updated as soon as possible
        t = threading.Thread(target=self.refresh_once, daemon=True)
        t.start()

    def stop(self):
        self._stop.set()
        if self._thread:
            self._thread.join(timeout=1.0)

    def refresh_once(self, fast: bool = True):
        """Try to compute payload once and populate cache (used at startup for immediate response).

        If fast=True, use a lightweight payload that queries only the DB stats (avoid CEP/GEO heavy calls).
        """
        try:
            payload = self._build_payload() if not fast else self._quick_build_payload()
            if not payload:
                return False
            # validate payload structure
            if not isinstance(payload, dict) or 'coleta' not in payload:
                return False

            # avoid overwriting with empty/zero payload when there is existing cache
            existing = self.cache.get('stats')
            if existing and isinstance(existing, dict):
                # if payload seems empty (all zeros) and existing is non-empty, keep existing
                def is_empty(p):
                    try:
                        c = p.get('coleta', {})
                        return int(c.get('termos_total', 0) or 0) == 0 and int(p.get('cep', {}).get('total', 0) or 0) == 0 and int(p.get('geo', {}).get('total_com_endereco', 0) or 0) == 0
                    except Exception:
                        return False
                if is_empty(payload) and not is_empty(existing):
                    return False
                # skip identical payloads
                try:
                    if payload == existing:
                        return True
                except Exception:
                    pass

            try:
                self.cache.set('stats', payload)
            except Exception:
                pass
            # emit immediate snapshot
            if self.socketio:
                try:
                    self.socketio.emit('stats_update', payload)
                except Exception:
                    pass
            return True
        except Exception:
            return False

    def _is_robot_running(self) -> bool:
        if callable(self.robot_running_check):
            try:
                return bool(self.robot_running_check())
            except Exception:
                return False
        # fallback: try db_service method
        try:
            if self.db_service and hasattr(self.db_service, 'is_robot_running'):
                return bool(self.db_service.is_robot_running())
        except Exception:
            pass
        return False

    def _build_payload(self) -> Optional[dict]:
        """Construct the same payload structure used by /api/stats.
        Returns None on failure so cache is not overwritten with partial data.
        """
        try:
            stats = {}
            try:
                if self.db_service and hasattr(self.db_service, 'get_statistics'):
                    stats = self.db_service.get_statistics() or {}
            except Exception:
                stats = {}

            # Gather CEP stats
            cep_stats = {'total': 0, 'concluidos': 0, 'pendentes': 0, 'erros': 0, 'percentual': 0}
            try:
                from src.application.services.cep_enrichment_application_service import CepEnrichmentApplicationService
                cep_svc = CepEnrichmentApplicationService()
                cep_stats_raw = cep_svc.get_cep_enrichment_stats() or {}
                # normalize fields
                cep_stats.update({
                    'total': int(cep_stats_raw.get('total', 0) or 0),
                    'concluidos': int(cep_stats_raw.get('concluidos', 0) or 0),
                    'pendentes': int(cep_stats_raw.get('pendentes', 0) or 0),
                    'erros': int(cep_stats_raw.get('erros', 0) or 0),
                    'percentual': float(cep_stats_raw.get('percentual', 0) or 0)
                })
            except Exception:
                pass

            # Gather GEO stats
            geo_stats = {'total_com_endereco': 0, 'geocodificadas': 0, 'pendentes': 0, 'erros': 0, 'percentual': 0}
            try:
                from src.application.services.geolocation_application_service import GeolocationApplicationService
                geo_svc = GeolocationApplicationService()
                geo_stats_raw = geo_svc.get_geolocation_stats() or {}
                geo_stats.update({
                    'total_com_endereco': int(geo_stats_raw.get('total_com_endereco', 0) or 0),
                    'geocodificadas': int(geo_stats_raw.get('geocodificadas', 0) or 0),
                    'pendentes': int(geo_stats_raw.get('pendentes', 0) or 0),
                    'erros': int(geo_stats_raw.get('erros', 0) or 0),
                    'percentual': float(geo_stats_raw.get('percentual', 0) or 0)
                })
            except Exception:
                pass

            # Company stats via db_service
            empresas_stats = {}
            try:
                if self.db_service and hasattr(self.db_service, 'get_company_collection_stats'):
                    empresas_stats = self.db_service.get_company_collection_stats() or {}
            except Exception:
                empresas_stats = {}

            payload = {
                'timestamp': datetime.now().isoformat(),
                'coleta': {
                    'termos_total': int(stats.get('termos_total', 0) or 0),
                    'termos_concluidos': int(stats.get('termos_concluidos', 0) or 0),
                    'progresso_pct': float(stats.get('progresso_pct', 0) or 0),
                    'empresas_total': int(stats.get('empresas_total', 0) or 0),
                    'empresas_visitadas': int(empresas_stats.get('visitadas', 0) or 0),
                    'empresas_coletadas': int(empresas_stats.get('coletadas', 0) or 0),
                    'empresas_nao_coletadas': int(empresas_stats.get('nao_coletadas', 0) or 0),
                    'taxa_coleta_pct': float(empresas_stats.get('taxa_coleta_pct', 0) or 0),
                    'emails_total': int(stats.get('emails_total', 0) or 0),
                    'telefones_total': int(stats.get('telefones_total', 0) or 0)
                },
                'cep': cep_stats,
                'geo': geo_stats
            }

            return payload
        except Exception:
            return None

    def _quick_build_payload(self) -> Optional[dict]:
        """Build a minimal payload quickly using only database statistics (fast path).
        This avoids invoking CEP/GEO services at startup which may be slow.
        """
        try:
            stats = {}
            try:
                if self.db_service and hasattr(self.db_service, 'get_statistics'):
                    stats = self.db_service.get_statistics() or {}
            except Exception:
                stats = {}

            empresas_stats = {}
            try:
                if self.db_service and hasattr(self.db_service, 'get_company_collection_stats'):
                    empresas_stats = self.db_service.get_company_collection_stats() or {}
            except Exception:
                empresas_stats = {}

            payload = {
                'timestamp': datetime.now().isoformat(),
                'coleta': {
                    'termos_total': int(stats.get('termos_total', 0) or 0),
                    'termos_concluidos': int(stats.get('termos_concluidos', 0) or 0),
                    'progresso_pct': float(stats.get('progresso_pct', 0) or 0),
                    'empresas_total': int(stats.get('empresas_total', 0) or 0),
                    'empresas_visitadas': int(empresas_stats.get('visitadas', 0) or 0),
                    'empresas_coletadas': int(empresas_stats.get('coletadas', 0) or 0),
                    'empresas_nao_coletadas': int(empresas_stats.get('nao_coletadas', 0) or 0),
                    'taxa_coleta_pct': float(empresas_stats.get('taxa_coleta_pct', 0) or 0),
                    'emails_total': int(stats.get('emails_total', 0) or 0),
                    'telefones_total': int(stats.get('telefones_total', 0) or 0)
                },
                # provide placeholders for cep/geo so front can render consistently
                'cep': {'total': 0, 'concluidos': 0, 'pendentes': 0, 'erros': 0, 'percentual': 0},
                'geo': {'total_com_endereco': 0, 'geocodificadas': 0, 'pendentes': 0, 'erros': 0, 'percentual': 0}
            }
            return payload
        except Exception:
            return None

    def _loop(self):
        # Loop: when robot is running, poll frequently (poll_interval).
        # When robot is not running, poll less frequently to reduce Access locking.
        idle_multiplier = 5.0
        interval = self.poll_interval * idle_multiplier
        while not self._stop.is_set():
            try:
                running = self._is_robot_running()
                interval = self.poll_interval if running else (self.poll_interval * idle_multiplier)

                payload = None
                try:
                    payload = self._build_payload()
                except Exception:
                    payload = None

                if payload:
                    # avoid overwriting with empty payload when existing has data
                    existing = self.cache.get('stats')
                    def is_empty(p):
                        try:
                            c = p.get('coleta', {})
                            return int(c.get('termos_total', 0) or 0) == 0 and int(p.get('cep', {}).get('total', 0) or 0) == 0 and int(p.get('geo', {}).get('total_com_endereco', 0) or 0) == 0
                        except Exception:
                            return False
                    if existing and is_empty(payload) and not is_empty(existing):
                        # skip overwrite
                        pass
                    else:
                        try:
                            if payload != existing:
                                self.cache.set('stats', payload)
                        except Exception:
                            pass
                        if self.socketio:
                            try:
                                self.socketio.emit('stats_update', payload)
                            except Exception:
                                pass
                # Emit lightweight heartbeat/tick event so clients can update 'Última atualização'
                try:
                    if self.socketio:
                        try:
                            self.socketio.emit('stats_tick', {'timestamp': datetime.now().isoformat(), 'running': bool(running)})
                        except Exception:
                            pass
                        # Also send the cached snapshot to ensure clients update UI (progress/labels)
                        try:
                            cached = None
                            try:
                                cached = self.cache.get('stats')
                            except Exception:
                                cached = None
                            if cached and isinstance(cached, dict):
                                try:
                                    self.socketio.emit('stats_update', cached)
                                except Exception:
                                    pass
                        except Exception:
                            pass
                except Exception:
                    pass
            except Exception:
                pass
            self._stop.wait(interval)
