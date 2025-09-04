#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Monitor Avançado com Métricas de Geolocalização
"""
import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path

# Adicionar diretório raiz ao path
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

from src.application.services.database_service import DatabaseService


class MonitorAvancado:
    """Monitor avançado com métricas detalhadas"""

    def __init__(self):
        self.db_service = DatabaseService()
        self.running = False
        self.historico = []
        self.inicio_monitoramento = time.time()
        self.processos_ativos = self._detectar_processos_ativos()

    def _detectar_processos_ativos(self):
        """Detecta quais processos estão ativos ou disponíveis"""
        processos = {'coleta': False, 'geolocalizacao': False, 'excel': False}

        try:
            stats = self.db_service.get_statistics()
            if stats:
                # Coleta ativa se há termos pendentes
                processos['coleta'] = stats.get('termos_pendentes', 0) > 0

                # Geolocalização disponível se há tarefas pendentes
                try:
                    with self.db_service.repository._get_connection() as conn:
                        cursor = conn.cursor()
                        cursor.execute("SELECT COUNT(*) FROM TB_GEOLOCALIZACAO WHERE STATUS_PROCESSAMENTO = 'PENDENTE'")
                        pendentes_geo = cursor.fetchone()[0]
                        processos['geolocalizacao'] = pendentes_geo > 0
                except:
                    pass

                # Excel disponível se há dados coletados
                processos['excel'] = stats.get('empresas_coletadas', 0) > 0
        except:
            pass

        return processos

    def limpar_tela(self):
        os.system('cls' if os.name == 'nt' else 'clear')

    def obter_metricas_geo(self):
        """Obtém métricas específicas de geolocalização"""
        try:
            with self.db_service.repository._get_connection() as conn:
                cursor = conn.cursor()

                # Empresas com geolocalização
                cursor.execute("SELECT COUNT(*) FROM TB_EMPRESAS WHERE LATITUDE IS NOT NULL AND LONGITUDE IS NOT NULL")
                empresas_geocodificadas = cursor.fetchone()[0]

                # Tarefas de geolocalização pendentes
                cursor.execute("SELECT COUNT(*) FROM TB_GEOLOCALIZACAO WHERE STATUS_PROCESSAMENTO = 'PENDENTE'")
                empresas_endereco_sem_geo = cursor.fetchone()[0]

                # Distância média
                cursor.execute("SELECT AVG(DISTANCIA_KM) FROM TB_EMPRESAS WHERE DISTANCIA_KM IS NOT NULL")
                distancia_media = cursor.fetchone()[0] or 0

                # Empresas por faixa de distância
                cursor.execute("SELECT COUNT(*) FROM TB_EMPRESAS WHERE DISTANCIA_KM <= 5")
                empresas_5km = cursor.fetchone()[0]

                cursor.execute("SELECT COUNT(*) FROM TB_EMPRESAS WHERE DISTANCIA_KM > 5 AND DISTANCIA_KM <= 15")
                empresas_15km = cursor.fetchone()[0]

                cursor.execute("SELECT COUNT(*) FROM TB_EMPRESAS WHERE DISTANCIA_KM > 15")
                empresas_mais_15km = cursor.fetchone()[0]

                return {
                    'geocodificadas': empresas_geocodificadas,
                    'endereco_sem_geo': empresas_endereco_sem_geo,
                    'distancia_media': round(distancia_media, 1),
                    'empresas_5km': empresas_5km,
                    'empresas_15km': empresas_15km,
                    'empresas_mais_15km': empresas_mais_15km
                }
        except Exception as e:
            print(f"Erro ao obter métricas geo: {e}")
            return {}

    def obter_metricas_performance(self):
        """Obtém métricas de performance por motor de busca"""
        try:
            with self.db_service.repository._get_connection() as conn:
                cursor = conn.cursor()

                # Por motor de busca
                cursor.execute("""
                               SELECT MOTOR_BUSCA,
                                      COUNT(*)                                                    as total,
                                      SUM(CASE WHEN STATUS_COLETA = 'COLETADO' THEN 1 ELSE 0 END) as coletadas
                               FROM TB_EMPRESAS
                               WHERE MOTOR_BUSCA IS NOT NULL
                               GROUP BY MOTOR_BUSCA
                               """)

                motores = {}
                for row in cursor.fetchall():
                    motor, total, coletadas = row
                    taxa_sucesso = (coletadas / total * 100) if total > 0 else 0
                    motores[motor] = {
                        'total': total,
                        'coletadas': coletadas,
                        'taxa_sucesso': round(taxa_sucesso, 1)
                    }

                return motores
        except Exception as e:
            print(f"Erro ao obter métricas performance: {e}")
            return {}

    def calcular_tempo_execucao(self):
        """Calcula tempo total de execução"""
        tempo_execucao = time.time() - self.inicio_monitoramento
        horas = int(tempo_execucao // 3600)
        minutos = int((tempo_execucao % 3600) // 60)
        segundos = int(tempo_execucao % 60)
        return f"{horas:02d}:{minutos:02d}:{segundos:02d}"

    def exibir_dashboard_completo(self):
        """Dashboard completo com todas as métricas"""
        try:
            # Obter dados
            stats = self.db_service.get_statistics()
            metricas_geo = self.obter_metricas_geo()
            metricas_perf = self.obter_metricas_performance()

            if not stats:
                print("❌ Erro ao conectar com banco de dados")
                return

            agora = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
            tempo_exec = self.calcular_tempo_execucao()

            # Detectar processos ativos
            self.processos_ativos = self._detectar_processos_ativos()

            # Status dos processos
            status_processos = []
            if self.processos_ativos['coleta']:
                status_processos.append("📊 COLETA")
            if self.processos_ativos['geolocalizacao']:
                status_processos.append("🌍 GEO")
            if self.processos_ativos['excel']:
                status_processos.append("📋 EXCEL")

            status_str = " | ".join(status_processos) if status_processos else "⏸️ AGUARDANDO"

            # Cabeçalho
            print("=" * 100)
            print(f"🚀 PYTHONSEARCHAPP - MONITOR AVANÇADO | {agora} | Tempo: {tempo_exec}")
            print(f"Processos: {status_str}")
            print("=" * 100)

            # Progresso Principal
            progresso = stats.get('progresso_pct', 0)
            barra = "█" * int(progresso / 2) + "░" * (50 - int(progresso / 2))
            print(f"\n📊 PROGRESSO GERAL: {progresso}%")
            print(f"[{barra}] {progresso}%")

            # Estatísticas em Colunas
            print(f"\n📈 ESTATÍSTICAS PRINCIPAIS:")
            print(f"┌─────────────────────┬─────────────────────┬─────────────────────┐")
            print(f"│ TERMOS              │ EMPRESAS            │ DADOS COLETADOS     │")
            print(f"├─────────────────────┼─────────────────────┼─────────────────────┤")
            print(f"│ Total: {stats.get('termos_total', 0):,}".ljust(
                20) + f"│ Visitadas: {stats.get('empresas_total', 0):,}".ljust(
                20) + f"│ E-mails: {stats.get('emails_total', 0):,}".ljust(20) + "│")
            print(f"│ Concluídos: {stats.get('termos_concluidos', 0):,}".ljust(
                20) + f"│ Coletadas: {stats.get('empresas_coletadas', 0):,}".ljust(
                20) + f"│ Telefones: {stats.get('telefones_total', 0):,}".ljust(20) + "│")
            print(f"│ Pendentes: {stats.get('termos_pendentes', 0):,}".ljust(
                20) + f"│ Taxa: {((stats.get('empresas_coletadas', 0) / max(stats.get('empresas_total', 1), 1)) * 100):.1f}%".ljust(
                20) + f"│ Geocodificadas: {metricas_geo.get('geocodificadas', 0):,}".ljust(20) + "│")
            print(f"└─────────────────────┴─────────────────────┴─────────────────────┘")

            # Métricas por Processo Ativo
            print(f"\n🔍 STATUS DOS PROCESSOS:")

            # Coleta
            if self.processos_ativos['coleta']:
                print(f"   📊 COLETA: EM ANDAMENTO ({stats.get('termos_pendentes', 0)} termos pendentes)")
            else:
                print(f"   📊 COLETA: CONCLUÍDA")

            # Geolocalização
            if self.processos_ativos['geolocalizacao']:
                print(f"   🌍 GEOLOCALIZAÇÃO: DISPONÍVEL ({metricas_geo.get('endereco_sem_geo', 0)} tarefas pendentes)")
            else:
                print(f"   🌍 GEOLOCALIZAÇÃO: CONCLUÍDA")

            # Excel
            if self.processos_ativos['excel']:
                print(f"   📋 EXCEL: DISPONÍVEL ({stats.get('empresas_coletadas', 0)} empresas prontas)")
            else:
                print(f"   📋 EXCEL: SEM DADOS")

            # Métricas de Geolocalização (se houver dados)
            if metricas_geo and metricas_geo.get('geocodificadas', 0) > 0:
                print(f"\n🌍 GEOLOCALIZAÇÃO:")
                print(f"   Empresas Geocodificadas: {metricas_geo.get('geocodificadas', 0):,}")
                print(f"   Tarefas Pendentes: {metricas_geo.get('endereco_sem_geo', 0):,}")
                print(f"   Distância Média: {metricas_geo.get('distancia_media', 0)} km")
                print(
                    f"   Até 5km: {metricas_geo.get('empresas_5km', 0):,} | 5-15km: {metricas_geo.get('empresas_15km', 0):,} | +15km: {metricas_geo.get('empresas_mais_15km', 0):,}")

            # Performance por Motor
            if metricas_perf:
                print(f"\n⚡ PERFORMANCE POR MOTOR:")
                for motor, dados in metricas_perf.items():
                    print(f"   {motor}: {dados['coletadas']:,}/{dados['total']:,} ({dados['taxa_sucesso']}%)")

            # Salvar histórico para gráficos futuros
            self.historico.append({
                'timestamp': time.time(),
                'stats': stats,
                'geo': metricas_geo
            })

            # Manter apenas últimas 100 entradas
            if len(self.historico) > 100:
                self.historico = self.historico[-100:]

            print(f"\n🔄 Atualizando a cada 10 segundos... (Ctrl+C para sair)")

        except Exception as e:
            print(f"❌ Erro no dashboard: {e}")

    def salvar_relatorio(self):
        """Salva relatório detalhado em arquivo"""
        try:
            agora = datetime.now()
            nome_arquivo = f"relatorio_{agora.strftime('%Y%m%d_%H%M%S')}.json"

            relatorio = {
                'timestamp': agora.isoformat(),
                'tempo_execucao': self.calcular_tempo_execucao(),
                'estatisticas': self.db_service.get_statistics(),
                'metricas_geo': self.obter_metricas_geo(),
                'metricas_performance': self.obter_metricas_performance(),
                'processos_ativos': self.processos_ativos,
                'historico': self.historico
            }

            with open(nome_arquivo, 'w', encoding='utf-8') as f:
                json.dump(relatorio, f, indent=2, ensure_ascii=False)

            print(f"\n💾 Relatório salvo: {nome_arquivo}")

        except Exception as e:
            print(f"❌ Erro ao salvar relatório: {e}")

    def iniciar(self):
        """Inicia o monitor avançado"""
        self.running = True
        print("🚀 Iniciando Monitor Avançado...")
        print("   Pressione Ctrl+C para parar e salvar relatório")
        time.sleep(2)

        try:
            while self.running:
                self.limpar_tela()
                self.exibir_dashboard_completo()
                time.sleep(10)  # Atualiza a cada 10 segundos

        except KeyboardInterrupt:
            print("\n\n🛑 Monitor interrompido pelo usuário")
            self.salvar_relatorio()
            self.running = False
        except Exception as e:
            print(f"\n❌ Erro no monitor: {e}")
            self.running = False


def main():
    monitor = MonitorAvancado()
    monitor.iniciar()


if __name__ == "__main__":
    main()
