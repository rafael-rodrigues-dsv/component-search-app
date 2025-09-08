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
        self.recurso_monitorado = self._escolher_recurso_monitoramento()

    def _escolher_recurso_monitoramento(self):
        """Menu para escolher qual recurso monitorar"""
        print("\n=== ESCOLHA O RECURSO PARA MONITORAR ===")
        print("[1] 📊 Coleta de Dados (termos/empresas/emails)")
        print("[2] 🏠 Enriquecimento CEP (ViaCEP)")
        print("[3] 🌍 Geolocalização (Nominatim)")
        print("[4] 📋 Visão Geral (todos os recursos)")
        
        while True:
            try:
                opcao = input("\nDigite sua opção (1-4): ").strip()
                if opcao == '1':
                    return "COLETA"
                elif opcao == '2':
                    return "CEP_ENRICHMENT"
                elif opcao == '3':
                    return "GEOLOCALIZACAO"
                elif opcao == '4':
                    return "GERAL"
                else:
                    print("Opção inválida! Digite 1, 2, 3 ou 4.")
            except KeyboardInterrupt:
                print("\nSaindo...")
                exit(0)

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



            # Cabeçalho com processo ativo
            agora = datetime.now().strftime("%H:%M:%S")
            processo_emoji = {
                "COLETA": "📊",
                "CEP_ENRICHMENT": "🏠",
                "GEOLOCALIZACAO": "🌍",
                "GERAL": "📋"
            }
            emoji = processo_emoji.get(self.recurso_monitorado, "🤖")

            print("=" * 80)
            print(f"{emoji} PYTHONSEARCHAPP - MONITOR TEMPO REAL | {agora}")
            print(f"Monitorando: {self.recurso_monitorado}")
            print("=" * 80)

            # Barra de progresso baseada na escolha do usuário
            if self.recurso_monitorado == "COLETA":
                progresso = stats.get('progresso_pct', 0)
                barra = "█" * int(progresso / 2) + "░" * (50 - int(progresso / 2))
                print(f"\n📊 PROGRESSO COLETA: {progresso}%")
                print(f"[{barra}] {progresso}%")
            elif self.recurso_monitorado == "CEP_ENRICHMENT":
                try:
                    # Usar status da TB_CEP_ENRICHMENT (CONCLUIDO + ERRO = processados)
                    from src.infrastructure.repositories.access_repository import AccessRepository
                    repo = AccessRepository()
                    with repo._get_connection() as conn:
                        cursor = conn.cursor()
                        cursor.execute("SELECT COUNT(*) FROM TB_CEP_ENRICHMENT WHERE STATUS_PROCESSAMENTO IN ('CONCLUIDO', 'ERRO')")
                        processados = cursor.fetchone()[0]
                        cursor.execute("SELECT COUNT(*) FROM TB_CEP_ENRICHMENT")
                        total = cursor.fetchone()[0]
                        progresso = (processados / max(total, 1)) * 100
                    
                    barra = "█" * int(progresso / 2) + "░" * (50 - int(progresso / 2))
                    print(f"\n🏠 PROGRESSO CEP: {progresso:.1f}%")
                    print(f"[{barra}] {processados}/{total} processados")
                except Exception as e:
                    print(f"\n🏠 CEP: Erro - {e}")
            elif self.recurso_monitorado == "GEOLOCALIZACAO":
                try:
                    # Usar status da TB_GEOLOCALIZACAO
                    from src.infrastructure.repositories.access_repository import AccessRepository
                    repo = AccessRepository()
                    with repo._get_connection() as conn:
                        cursor = conn.cursor()
                        cursor.execute("SELECT COUNT(*) FROM TB_GEOLOCALIZACAO WHERE STATUS_PROCESSAMENTO = 'CONCLUIDO'")
                        concluidos = cursor.fetchone()[0]
                        cursor.execute("SELECT COUNT(*) FROM TB_GEOLOCALIZACAO")
                        total = cursor.fetchone()[0]
                        progresso = (concluidos / max(total, 1)) * 100
                    
                    barra = "█" * int(progresso / 2) + "░" * (50 - int(progresso / 2))
                    print(f"\n🌍 PROGRESSO GEO: {progresso:.1f}%")
                    print(f"[{barra}] {concluidos}/{total} concluídas")
                except Exception as e:
                    print(f"\n🌍 GEO: Erro - {e}")
            else:  # GERAL
                progresso = stats.get('progresso_pct', 0)
                barra = "█" * int(progresso / 2) + "░" * (50 - int(progresso / 2))
                print(f"\n📋 PROGRESSO GERAL: {progresso}%")
                print(f"[{barra}] {progresso}%")

            # Estatísticas específicas por recurso monitorado
            print(f"\n📈 ESTATÍSTICAS - {self.recurso_monitorado}:")
            if self.recurso_monitorado == "COLETA":
                print(f"   Termos Processados: {stats.get('termos_concluidos', 0):,} / {stats.get('termos_total', 0):,}")
                print(f"   Termos Pendentes:   {stats.get('termos_pendentes', 0):,}")
                print(f"   Empresas Visitadas: {stats.get('empresas_total', 0):,}")
                print(f"   Empresas Coletadas: {stats.get('empresas_coletadas', 0):,}")
                print(f"   E-mails Coletados:  {stats.get('emails_total', 0):,}")
                print(f"   Telefones Coletados: {stats.get('telefones_total', 0):,}")
            elif self.recurso_monitorado == "CEP_ENRICHMENT":
                try:
                    from src.infrastructure.repositories.access_repository import AccessRepository
                    repo = AccessRepository()
                    with repo._get_connection() as conn:
                        cursor = conn.cursor()
                        cursor.execute("SELECT COUNT(*) FROM TB_CEP_ENRICHMENT WHERE STATUS_PROCESSAMENTO = 'CONCLUIDO'")
                        concluidos = cursor.fetchone()[0]
                        cursor.execute("SELECT COUNT(*) FROM TB_CEP_ENRICHMENT WHERE STATUS_PROCESSAMENTO = 'PENDENTE'")
                        pendentes = cursor.fetchone()[0]
                        cursor.execute("SELECT COUNT(*) FROM TB_CEP_ENRICHMENT WHERE STATUS_PROCESSAMENTO = 'ERRO'")
                        erros = cursor.fetchone()[0]
                        total = concluidos + pendentes + erros
                    print(f"   Total de Tarefas:   {total:,}")
                    print(f"   CEPs Enriquecidos:  {concluidos:,} (✅ sucesso)")
                    print(f"   Tentativas Falhas:  {erros:,} (⚠️ não melhorou)")
                    print(f"   Pendentes:          {pendentes:,}")
                except Exception as e:
                    print(f"   Erro ao obter dados CEP: {e}")
            elif self.recurso_monitorado == "GEOLOCALIZACAO":
                try:
                    from src.infrastructure.repositories.access_repository import AccessRepository
                    repo = AccessRepository()
                    with repo._get_connection() as conn:
                        cursor = conn.cursor()
                        cursor.execute("SELECT COUNT(*) FROM TB_GEOLOCALIZACAO WHERE STATUS_PROCESSAMENTO = 'CONCLUIDO'")
                        concluidos = cursor.fetchone()[0]
                        cursor.execute("SELECT COUNT(*) FROM TB_GEOLOCALIZACAO WHERE STATUS_PROCESSAMENTO = 'PENDENTE'")
                        pendentes = cursor.fetchone()[0]
                        cursor.execute("SELECT COUNT(*) FROM TB_GEOLOCALIZACAO WHERE STATUS_PROCESSAMENTO = 'ERRO'")
                        erros = cursor.fetchone()[0]
                        cursor.execute("SELECT AVG(DISTANCIA_KM) FROM TB_GEOLOCALIZACAO WHERE DISTANCIA_KM IS NOT NULL")
                        dist_media = cursor.fetchone()[0] or 0
                        total = concluidos + pendentes + erros
                    print(f"   Total de Tarefas:   {total:,}")
                    print(f"   Concluídas:         {concluidos:,} (✅ sucesso)")
                    print(f"   Pendentes:          {pendentes:,} (⏳ aguardando)")
                    print(f"   Erros:              {erros:,} (❌ falha)")
                    if concluidos > 0:
                        print(f"   Distância Média:    {dist_media:.1f} km")
                except Exception as e:
                    print(f"   Erro ao obter dados GEO: {e}")
            else:  # GERAL
                print(f"   Termos Processados: {stats.get('termos_concluidos', 0):,} / {stats.get('termos_total', 0):,}")
                print(f"   Empresas Visitadas: {stats.get('empresas_total', 0):,}")
                print(f"   E-mails Coletados:  {stats.get('emails_total', 0):,}")
                print(f"   Telefones Coletados: {stats.get('telefones_total', 0):,}")

            # Velocidade específica por recurso
            if self.recurso_monitorado == "COLETA":
                print(f"\n⚡ VELOCIDADE COLETA (últimos 5s):")
                print(f"   Empresas/min: {vel_empresas * 12:,}")
                print(f"   E-mails/min:  {vel_emails * 12:,}")
                print(f"   Termos/min:   {vel_termos * 12:,}")
            elif self.recurso_monitorado == "CEP_ENRICHMENT":
                print(f"\n⚡ VELOCIDADE CEP:")
                print(f"   Rate Limit: 1 req/seg (60/min)")
                print(f"   ✅ Sucesso: CEP melhora endereço")
                print(f"   ⚠️ Falha: CEP não melhora endereço")
            elif self.recurso_monitorado == "GEOLOCALIZACAO":
                print(f"\n⚡ VELOCIDADE GEO:")
                print(f"   Rate Limit: 1 req/seg (60/min)")
            else:  # GERAL
                print(f"\n⚡ VELOCIDADE GERAL (últimos 5s):")
                print(f"   Empresas/min: {vel_empresas * 12:,}")
                print(f"   E-mails/min:  {vel_emails * 12:,}")
                print(f"   Termos/min:   {vel_termos * 12:,}")

            # Taxa de Sucesso específica por recurso
            if self.recurso_monitorado == "COLETA":
                if stats.get('empresas_total', 0) > 0:
                    taxa_sucesso = (stats.get('empresas_coletadas', 0) / stats.get('empresas_total', 0)) * 100
                    print(f"\n✅ TAXA DE SUCESSO COLETA: {taxa_sucesso:.1f}%")
            elif self.recurso_monitorado == "CEP_ENRICHMENT":
                try:
                    from src.infrastructure.repositories.access_repository import AccessRepository
                    repo = AccessRepository()
                    with repo._get_connection() as conn:
                        cursor = conn.cursor()
                        cursor.execute("SELECT COUNT(*) FROM TB_CEP_ENRICHMENT WHERE STATUS_PROCESSAMENTO = 'CONCLUIDO'")
                        concluidos = cursor.fetchone()[0]
                        cursor.execute("SELECT COUNT(*) FROM TB_CEP_ENRICHMENT WHERE STATUS_PROCESSAMENTO IN ('CONCLUIDO', 'ERRO')")
                        processados = cursor.fetchone()[0]
                        if processados > 0:
                            taxa_sucesso = (concluidos / processados) * 100
                            print(f"\n✅ TAXA DE SUCESSO CEP: {taxa_sucesso:.1f}% ({concluidos}/{processados})")
                except Exception as e:
                    print(f"   Erro CEP taxa: {e}")
            elif self.recurso_monitorado == "GEOLOCALIZACAO":
                try:
                    from src.infrastructure.repositories.access_repository import AccessRepository
                    repo = AccessRepository()
                    with repo._get_connection() as conn:
                        cursor = conn.cursor()
                        cursor.execute("SELECT COUNT(*) FROM TB_GEOLOCALIZACAO WHERE STATUS_PROCESSAMENTO = 'CONCLUIDO'")
                        concluidos = cursor.fetchone()[0]
                        cursor.execute("SELECT COUNT(*) FROM TB_GEOLOCALIZACAO")
                        total = cursor.fetchone()[0]
                        if total > 0:
                            taxa_sucesso = (concluidos / total) * 100
                            print(f"\n✅ TAXA DE SUCESSO GEO: {taxa_sucesso:.1f}%")
                except Exception as e:
                    print(f"   Erro GEO taxa: {e}")

            # Estimativa de Conclusão específica por recurso
            if self.recurso_monitorado == "COLETA" and vel_termos > 0 and stats.get('termos_pendentes', 0) > 0:
                tempo_restante = stats.get('termos_pendentes', 0) / (vel_termos * 12)  # em minutos
                print(f"⏱️  TEMPO ESTIMADO COLETA: {self.formatar_tempo(tempo_restante * 60)}")
            elif self.recurso_monitorado in ["CEP_ENRICHMENT", "GEOLOCALIZACAO"]:
                try:
                    tabela = "TB_CEP_ENRICHMENT" if self.recurso_monitorado == "CEP_ENRICHMENT" else "TB_GEOLOCALIZACAO"
                    from src.infrastructure.repositories.access_repository import AccessRepository
                    repo = AccessRepository()
                    with repo._get_connection() as conn:
                        cursor = conn.cursor()
                        cursor.execute(f"SELECT COUNT(*) FROM {tabela} WHERE STATUS_PROCESSAMENTO = 'PENDENTE'")
                        pendentes = cursor.fetchone()[0]
                        if pendentes > 0:
                            # Estimativa baseada em 1 tarefa por segundo (rate limiting)
                            tempo_restante = pendentes  # em segundos
                            recurso_nome = "CEP" if self.recurso_monitorado == "CEP_ENRICHMENT" else "GEO"
                            print(f"⏱️  TEMPO ESTIMADO {recurso_nome}: {self.formatar_tempo(tempo_restante)} ({pendentes} pendentes)")
                except Exception as e:
                    print(f"   Erro estimativa: {e}")

            # Salvar stats para próxima iteração
            self.stats_anteriores = stats.copy()

            # Status baseado na escolha do usuário
            status_msgs = {
                "COLETA": "📊 MONITORANDO COLETA DE DADOS",
                "CEP_ENRICHMENT": "🏠 MONITORANDO CEP (✅ sucesso | ⚠️ não melhorou)",
                "GEOLOCALIZACAO": "🌍 MONITORANDO GEOLOCALIZAÇÃO",
                "GERAL": "📋 MONITORANDO VISÃO GERAL"
            }
            print(f"\n{status_msgs.get(self.recurso_monitorado, 'MONITORANDO')}")

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
