#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Monitor de Telemetria em Tempo Real - PythonSearchApp
"""
import os
import sys
import time
from datetime import datetime
from pathlib import Path

# Adicionar diretório raiz ao path
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

from src.application.services.database_service import DatabaseService


class MonitorTempoReal:
    """Monitor de métricas em tempo real"""

    def __init__(self):
        self.db_service = DatabaseService()
        self.running = False
        self.stats_anteriores = {}
        self.processo_ativo = self._detectar_processo_ativo()

    def _detectar_processo_ativo(self):
        """Detecta qual processo está ativo baseado no estado do banco"""
        try:
            stats = self.db_service.get_statistics()
            if not stats:
                return "INICIALIZANDO"

            # Verificar se há termos pendentes (coleta ativa)
            if stats.get('termos_pendentes', 0) > 0 and stats.get('termos_concluidos', 0) > 0:
                return "COLETA"

            # Verificar se há tarefas de geolocalização pendentes
            try:
                with self.db_service.repository._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute("SELECT COUNT(*) FROM TB_GEOLOCALIZACAO WHERE STATUS_PROCESSAMENTO = 'PENDENTE'")
                    pendentes_geo = cursor.fetchone()[0]
                    if pendentes_geo > 0:
                        return "GEOLOCALIZACAO"
            except:
                pass

            # Se há dados coletados, pode exportar Excel
            if stats.get('empresas_coletadas', 0) > 0:
                return "EXCEL_DISPONIVEL"

            return "AGUARDANDO"
        except:
            return "ERRO"

    def limpar_tela(self):
        """Limpa a tela do terminal"""
        os.system('cls' if os.name == 'nt' else 'clear')

    def formatar_tempo(self, segundos):
        """Formata tempo em formato legível"""
        if segundos < 60:
            return f"{segundos:.1f}s"
        elif segundos < 3600:
            return f"{segundos / 60:.1f}m"
        else:
            return f"{segundos / 3600:.1f}h"

    def calcular_velocidade(self, stats_atual, stats_anterior):
        """Calcula velocidade de processamento"""
        if not stats_anterior:
            return 0, 0, 0

        # Diferenças
        diff_empresas = stats_atual.get('empresas_coletadas', 0) - stats_anterior.get('empresas_coletadas', 0)
        diff_emails = stats_atual.get('emails_total', 0) - stats_anterior.get('emails_total', 0)
        diff_termos = stats_atual.get('termos_concluidos', 0) - stats_anterior.get('termos_concluidos', 0)

        return diff_empresas, diff_emails, diff_termos

    def exibir_dashboard(self):
        """Exibe dashboard principal"""
        try:
            stats = self.db_service.get_statistics()
            if not stats:
                print("❌ Erro ao obter estatísticas do banco")
                return

            # Calcular velocidades
            vel_empresas, vel_emails, vel_termos = self.calcular_velocidade(stats, self.stats_anteriores)

            # Detectar processo atual
            self.processo_ativo = self._detectar_processo_ativo()

            # Cabeçalho com processo ativo
            agora = datetime.now().strftime("%H:%M:%S")
            processo_emoji = {
                "COLETA": "📊",
                "GEOLOCALIZACAO": "🌍",
                "EXCEL_DISPONIVEL": "📋",
                "AGUARDANDO": "⏸️",
                "INICIALIZANDO": "🔄",
                "ERRO": "❌"
            }
            emoji = processo_emoji.get(self.processo_ativo, "🤖")

            print("=" * 80)
            print(f"{emoji} PYTHONSEARCHAPP - MONITOR TEMPO REAL | {agora}")
            print(f"Status: {self.processo_ativo}")
            print("=" * 80)

            # Progresso específico por processo
            if self.processo_ativo == "COLETA":
                progresso = stats.get('progresso_pct', 0)
                barra_progresso = "█" * int(progresso / 2) + "░" * (50 - int(progresso / 2))
                print(f"\n📊 PROGRESSO COLETA: {progresso}%")
                print(f"[{barra_progresso}] {progresso}%")
            elif self.processo_ativo == "GEOLOCALIZACAO":
                try:
                    from src.application.services.geolocation_application_service import GeolocationApplicationService
                    geo_service = GeolocationApplicationService()
                    geo_stats = geo_service.get_geolocation_stats()
                    progresso_geo = geo_stats.get('percentual', 0)
                    barra_geo = "█" * int(progresso_geo / 2) + "░" * (50 - int(progresso_geo / 2))
                    print(f"\n🌍 PROGRESSO GEOLOCALIZAÇÃO: {progresso_geo}%")
                    print(f"[{barra_geo}] {progresso_geo}%")
                except:
                    print(f"\n🌍 GEOLOCALIZAÇÃO: Processando...")
            else:
                progresso = stats.get('progresso_pct', 0)
                barra_progresso = "█" * int(progresso / 2) + "░" * (50 - int(progresso / 2))
                print(f"\n📊 PROGRESSO GERAL: {progresso}%")
                print(f"[{barra_progresso}] {progresso}%")

            # Estatísticas Principais
            print(f"\n📈 ESTATÍSTICAS PRINCIPAIS:")
            print(f"   Termos Processados: {stats.get('termos_concluidos', 0):,} / {stats.get('termos_total', 0):,}")
            print(f"   Termos Pendentes:   {stats.get('termos_pendentes', 0):,}")
            print(f"   Empresas Visitadas: {stats.get('empresas_total', 0):,}")
            print(f"   Empresas Coletadas: {stats.get('empresas_coletadas', 0):,}")
            print(f"   E-mails Coletados:  {stats.get('emails_total', 0):,}")
            print(f"   Telefones Coletados: {stats.get('telefones_total', 0):,}")

            # Velocidade (por minuto)
            print(f"\n⚡ VELOCIDADE (últimos 5s):")
            print(f"   Empresas/min: {vel_empresas * 12:,}")
            print(f"   E-mails/min:  {vel_emails * 12:,}")
            print(f"   Termos/min:   {vel_termos * 12:,}")

            # Taxa de Sucesso
            if stats.get('empresas_total', 0) > 0:
                taxa_sucesso = (stats.get('empresas_coletadas', 0) / stats.get('empresas_total', 0)) * 100
                print(f"\n✅ TAXA DE SUCESSO: {taxa_sucesso:.1f}%")

            # Estimativa de Conclusão
            if vel_termos > 0 and stats.get('termos_pendentes', 0) > 0:
                tempo_restante = stats.get('termos_pendentes', 0) / (vel_termos * 12)  # em minutos
                print(f"⏱️  TEMPO ESTIMADO: {self.formatar_tempo(tempo_restante * 60)}")

            # Salvar stats para próxima iteração
            self.stats_anteriores = stats.copy()

            # Status específico por processo
            if self.processo_ativo == "COLETA":
                print(f"\n📊 COLETA DE DADOS EM ANDAMENTO")
            elif self.processo_ativo == "GEOLOCALIZACAO":
                print(f"\n🌍 GEOLOCALIZAÇÃO EM ANDAMENTO")
            elif self.processo_ativo == "EXCEL_DISPONIVEL":
                print(f"\n📋 DADOS PRONTOS PARA EXPORTAÇÃO EXCEL")
            elif self.processo_ativo == "AGUARDANDO":
                print(f"\n⏸️ SISTEMA AGUARDANDO PRÓXIMA OPERAÇÃO")

            print(f"\n🔄 Atualizando a cada 5 segundos... (Ctrl+C para sair)")

        except Exception as e:
            print(f"❌ Erro no monitor: {e}")

    def monitorar_logs(self):
        """Monitor de logs em tempo real (thread separada)"""
        # Implementação futura para logs em tempo real
        pass

    def iniciar(self):
        """Inicia o monitor"""
        self.running = True
        print("🚀 Iniciando Monitor de Tempo Real...")
        print("   Pressione Ctrl+C para parar")
        time.sleep(2)

        try:
            while self.running:
                self.limpar_tela()
                self.exibir_dashboard()
                time.sleep(5)  # Atualiza a cada 5 segundos

        except KeyboardInterrupt:
            print("\n\n🛑 Monitor interrompido pelo usuário")
            self.running = False
        except Exception as e:
            print(f"\n❌ Erro no monitor: {e}")
            self.running = False


def main():
    """Função principal"""
    monitor = MonitorTempoReal()
    monitor.iniciar()


if __name__ == "__main__":
    main()
