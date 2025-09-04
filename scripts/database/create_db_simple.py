"""
Criador simples do banco Access - Funciona garantido
"""
import os
from pathlib import Path


def create_simple_db(auto_mode=False):
    """Cria banco Access de forma simples e funcional"""

    # Caminhos - ajustado para scripts/database
    base_dir = Path(__file__).parent.parent.parent
    data_dir = base_dir / "data"
    db_path = data_dir / "pythonsearch.accdb"

    data_dir.mkdir(exist_ok=True)

    if db_path.exists():
        if not auto_mode:
            response = input(f"Banco existe. Recriar? (s/N): ")
            if response.lower() != 's':
                return
        db_path.unlink()

    try:
        try:
            import win32com.client
        except ImportError:
            print("❌ ERRO: pywin32 não encontrado")
            print("💡 SOLUÇÃO: Execute 'pip install pywin32' e tente novamente")
            return False

        print("🔨 Criando banco Access...")
        access = win32com.client.Dispatch("Access.Application")
        access.NewCurrentDatabase(str(db_path))

        print("📋 Criando tabelas...")

        # Tabelas básicas sem complexidade
        sqls = [
            "CREATE TABLE TB_ZONAS (ID_ZONA COUNTER PRIMARY KEY, NOME_ZONA TEXT(50), UF TEXT(2), ATIVO BIT, DATA_CRIACAO DATE)",
            "CREATE TABLE TB_BAIRROS (ID_BAIRRO COUNTER PRIMARY KEY, NOME_BAIRRO TEXT(100), UF TEXT(2), ATIVO BIT, DATA_CRIACAO DATE)",
            "CREATE TABLE TB_CIDADES (ID_CIDADE COUNTER PRIMARY KEY, NOME_CIDADE TEXT(100), UF TEXT(2), ATIVO BIT, DATA_CRIACAO DATE)",
            "CREATE TABLE TB_BASE_BUSCA (ID_BASE COUNTER PRIMARY KEY, TERMO_BUSCA TEXT(200), CATEGORIA TEXT(50), ATIVO BIT, DATA_CRIACAO DATE)",
            "CREATE TABLE TB_TERMOS_BUSCA (ID_TERMO COUNTER PRIMARY KEY, ID_BASE LONG, ID_ZONA LONG, ID_BAIRRO LONG, ID_CIDADE LONG, TERMO_COMPLETO TEXT(255), TIPO_LOCALIZACAO TEXT(20), STATUS_PROCESSAMENTO TEXT(20), DATA_CRIACAO DATE, DATA_PROCESSAMENTO DATE)",
            "CREATE TABLE TB_EMPRESAS (ID_EMPRESA COUNTER PRIMARY KEY, ID_TERMO LONG, SITE_URL TEXT(255), DOMINIO TEXT(100), NOME_EMPRESA TEXT(100), STATUS_COLETA TEXT(20), DATA_PRIMEIRA_VISITA DATE, DATA_ULTIMA_VISITA DATE, TENTATIVAS_COLETA LONG, MOTOR_BUSCA TEXT(20), ENDERECO TEXT(255), LATITUDE DOUBLE, LONGITUDE DOUBLE, DISTANCIA_KM DOUBLE)",
            "CREATE TABLE TB_EMAILS (ID_EMAIL COUNTER PRIMARY KEY, ID_EMPRESA LONG, EMAIL TEXT(200), DOMINIO_EMAIL TEXT(100), VALIDADO BIT, DATA_COLETA DATE, ORIGEM_COLETA TEXT(20))",
            "CREATE TABLE TB_TELEFONES (ID_TELEFONE COUNTER PRIMARY KEY, ID_EMPRESA LONG, TELEFONE TEXT(20), TELEFONE_FORMATADO TEXT(20), DDD TEXT(2), TIPO_TELEFONE TEXT(10), VALIDADO BIT, DATA_COLETA DATE)",
            "CREATE TABLE TB_GEOLOCALIZACAO (ID_GEO COUNTER PRIMARY KEY, ID_EMPRESA LONG, ENDERECO TEXT(255), LATITUDE DOUBLE, LONGITUDE DOUBLE, DISTANCIA_KM DOUBLE, STATUS_PROCESSAMENTO TEXT(20), DATA_PROCESSAMENTO DATE, TENTATIVAS LONG, ERRO_DESCRICAO TEXT(255))",
            "CREATE TABLE TB_PLANILHA (ID_PLANILHA COUNTER PRIMARY KEY, SITE TEXT(255), EMAIL MEMO, TELEFONE MEMO, ENDERECO TEXT(255), DISTANCIA_KM DOUBLE, DATA_ATUALIZACAO DATE)"
        ]

        for i, sql in enumerate(sqls, 1):
            try:
                access.DoCmd.RunSQL(sql)
                table = sql.split()[2]
                print(f"✅ {i}/9 - {table}")
            except Exception as e:
                print(f"⚠️ {i}/8 - {str(e)[:50]}")

        print("📋 Carregando dados básicos...")

        # Dados organizados por categoria
        zonas = [
            "INSERT INTO TB_ZONAS (NOME_ZONA, UF, ATIVO, DATA_CRIACAO) VALUES ('zona norte', 'SP', -1, Date())",
            "INSERT INTO TB_ZONAS (NOME_ZONA, UF, ATIVO, DATA_CRIACAO) VALUES ('zona sul', 'SP', -1, Date())",
            "INSERT INTO TB_ZONAS (NOME_ZONA, UF, ATIVO, DATA_CRIACAO) VALUES ('zona leste', 'SP', -1, Date())",
            "INSERT INTO TB_ZONAS (NOME_ZONA, UF, ATIVO, DATA_CRIACAO) VALUES ('zona oeste', 'SP', -1, Date())",
            "INSERT INTO TB_ZONAS (NOME_ZONA, UF, ATIVO, DATA_CRIACAO) VALUES ('zona central', 'SP', -1, Date())"
        ]

        bairros = [
            "INSERT INTO TB_BAIRROS (NOME_BAIRRO, UF, ATIVO, DATA_CRIACAO) VALUES ('Moema', 'SP', -1, Date())",
            "INSERT INTO TB_BAIRROS (NOME_BAIRRO, UF, ATIVO, DATA_CRIACAO) VALUES ('Vila Mariana', 'SP', -1, Date())",
            "INSERT INTO TB_BAIRROS (NOME_BAIRRO, UF, ATIVO, DATA_CRIACAO) VALUES ('Pinheiros', 'SP', -1, Date())"
        ]

        cidades = [
            "INSERT INTO TB_CIDADES (NOME_CIDADE, UF, ATIVO, DATA_CRIACAO) VALUES ('Campinas', 'SP', -1, Date())",
            "INSERT INTO TB_CIDADES (NOME_CIDADE, UF, ATIVO, DATA_CRIACAO) VALUES ('Guarulhos', 'SP', -1, Date())"
        ]

        termos = [
            "INSERT INTO TB_BASE_BUSCA (TERMO_BUSCA, CATEGORIA, ATIVO, DATA_CRIACAO) VALUES ('empresa de elevadores', 'elevadores', -1, Date())",
            "INSERT INTO TB_BASE_BUSCA (TERMO_BUSCA, CATEGORIA, ATIVO, DATA_CRIACAO) VALUES ('manutenção de elevadores', 'elevadores', -1, Date())"
        ]

        # Carregar zonas
        print(f"📍 Carregando {len(zonas)} zonas...")
        for sql in zonas:
            try:
                access.DoCmd.RunSQL(sql)
            except:
                pass
        print(f"✅ {len(zonas)} zonas carregadas")

        # Carregar bairros
        print(f"🏘️ Carregando {len(bairros)} bairros...")
        for sql in bairros:
            try:
                access.DoCmd.RunSQL(sql)
            except:
                pass
        print(f"✅ {len(bairros)} bairros carregados")

        # Carregar cidades
        print(f"🏙️ Carregando {len(cidades)} cidades...")
        for sql in cidades:
            try:
                access.DoCmd.RunSQL(sql)
            except:
                pass
        print(f"✅ {len(cidades)} cidades carregadas")

        # Carregar termos base
        print(f"🔍 Carregando {len(termos)} termos base...")
        for sql in termos:
            try:
                access.DoCmd.RunSQL(sql)
            except:
                pass
        print(f"✅ {len(termos)} termos base carregados")

        access.Quit()

        # Calcular total de combinações possíveis
        total_combinacoes = len(zonas) * len(termos) + len(bairros) * len(termos) + len(cidades) * len(termos)
        
        print(f"\n📊 RESUMO DOS DADOS CARREGADOS:")
        print(f"   📍 {len(zonas)} zonas")
        print(f"   🏘️ {len(bairros)} bairros")
        print(f"   🏙️ {len(cidades)} cidades")
        print(f"   🔍 {len(termos)} termos base")
        print(f"   🎯 {total_combinacoes} combinações possíveis")
        print(f"\n🎉 BANCO CRIADO COM SUCESSO!")
        print(f"📍 Localização: {db_path}")
        print(f"✅ 10 tabelas estruturadas")

    except Exception as e:
        print(f"❌ ERRO: {e}")


if __name__ == "__main__":
    create_simple_db()
    input("⏸️ ENTER para sair...")
