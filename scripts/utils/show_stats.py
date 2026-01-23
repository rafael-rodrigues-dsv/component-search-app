"""
Script utilitário para mostrar estatísticas do banco
"""
import sys
from pathlib import Path

# Adicionar src ao path
sys.path.append(str(Path(__file__).parent.parent.parent / "src"))

from application.services.database_application_service import DatabaseApplicationService


def show_statistics():
    """Mostra estatísticas detalhadas do banco"""
    try:
        db_service = DatabaseApplicationService()

        print("📊 ESTATÍSTICAS DO BANCO ACCESS")
        print("=" * 50)

        stats = db_service.get_statistics()

        if stats:
            print(f"🎯 TERMOS DE BUSCA:")
            print(f"   Total: {stats['termos_total']}")
            print(f"   Concluídos: {stats['termos_concluidos']}")
            print(f"   Pendentes: {stats['termos_pendentes']}")
            print(f"   Progresso: {stats['progresso_pct']}%")
            print()

            print(f"🏢 EMPRESAS:")
            print(f"   Total encontradas: {stats['empresas_total']}")
            print(f"   Com dados coletados: {stats['empresas_coletadas']}")
            print()

            print(f"📧 DADOS COLETADOS:")
            print(f"   E-mails: {stats['emails_total']}")
            print(f"   Telefones: {stats['telefones_total']}")
            print()

            # Calcular eficiência
            if stats['empresas_total'] > 0:
                eficiencia = round((stats['empresas_coletadas'] / stats['empresas_total']) * 100, 1)
                print(f"📈 EFICIÊNCIA:")
                print(f"   Taxa de coleta: {eficiencia}%")

                if stats['empresas_coletadas'] > 0:
                    media_emails = round(stats['emails_total'] / stats['empresas_coletadas'], 1)
                    media_telefones = round(stats['telefones_total'] / stats['empresas_coletadas'], 1)
                    print(f"   Média e-mails/empresa: {media_emails}")
                    print(f"   Média telefones/empresa: {media_telefones}")
        else:
            print("❌ Não foi possível obter estatísticas")

    except Exception as e:
        print(f"❌ ERRO: {e}")


if __name__ == "__main__":
    show_statistics()
    input("⏸️ ENTER para sair...")
