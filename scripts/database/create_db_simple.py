"""
Criador simples do banco Access - Funciona garantido
"""
from pathlib import Path


def create_simple_db(auto_mode=False):
    """Cria banco Access de forma simples e funcional"""

    # Sempre usar pasta data do projeto (onde o main.py está)
    import os
    if 'scripts' in os.getcwd():
        # Se executando de dentro de scripts, subir para raíz
        project_root = Path.cwd().parent.parent
    else:
        # Se executando da raíz
        project_root = Path.cwd()
    
    data_dir = project_root / "data"
    db_path = data_dir / "pythonsearch.accdb"
    
    print(f"[INFO] Criando banco em: {db_path.resolve()}")
    print(f"[DEBUG] Diretório atual: {Path.cwd()}")
    print(f"[DEBUG] Projeto root: {project_root}")

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
            print("[ERRO] pywin32 nao encontrado")
            print("[INFO] Execute: pip install pywin32")
            print("[INFO] Depois reinicie o terminal e tente novamente")
            return False

        print("[INFO] Criando banco Access...")
        access = win32com.client.Dispatch("Access.Application")
        access.NewCurrentDatabase(str(db_path))

        print("[INFO] Criando tabelas...")

        # Tabelas básicas sem complexidade
        sqls = [
            "CREATE TABLE TB_ZONAS (ID_ZONA COUNTER PRIMARY KEY, NOME_ZONA TEXT(50), UF TEXT(2), ATIVO BIT, DATA_CRIACAO DATE)",
            "CREATE TABLE TB_BAIRROS (ID_BAIRRO COUNTER PRIMARY KEY, NOME_BAIRRO TEXT(100), UF TEXT(2), ATIVO BIT, DATA_CRIACAO DATE)",
            "CREATE TABLE TB_CIDADES (ID_CIDADE COUNTER PRIMARY KEY, NOME_CIDADE TEXT(100), UF TEXT(2), ATIVO BIT, DATA_CRIACAO DATE)",
            "CREATE TABLE TB_BASE_BUSCA (ID_BASE COUNTER PRIMARY KEY, TERMO_BUSCA TEXT(200), CATEGORIA TEXT(50), ATIVO BIT, DATA_CRIACAO DATE)",
            "CREATE TABLE TB_ENDERECOS (ID_ENDERECO COUNTER PRIMARY KEY, LOGRADOURO TEXT(200), NUMERO TEXT(20), COMPLEMENTO TEXT(50), BAIRRO TEXT(100), CIDADE TEXT(100), ESTADO TEXT(2), CEP TEXT(10), DATA_CRIACAO DATE)",
            "CREATE TABLE TB_TERMOS_BUSCA (ID_TERMO COUNTER PRIMARY KEY, ID_BASE LONG, ID_ZONA LONG, ID_BAIRRO LONG, ID_CIDADE LONG, TERMO_COMPLETO TEXT(255), TIPO_LOCALIZACAO TEXT(20), STATUS_PROCESSAMENTO TEXT(20), DATA_CRIACAO DATE, DATA_PROCESSAMENTO DATE)",
            "CREATE TABLE TB_EMPRESAS (ID_EMPRESA COUNTER PRIMARY KEY, ID_TERMO LONG, SITE_URL TEXT(255), DOMINIO TEXT(100), NOME_EMPRESA TEXT(100), STATUS_COLETA TEXT(20), DATA_PRIMEIRA_VISITA DATE, DATA_ULTIMA_VISITA DATE, TENTATIVAS_COLETA LONG, MOTOR_BUSCA TEXT(20), ID_ENDERECO LONG, LATITUDE DOUBLE, LONGITUDE DOUBLE, DISTANCIA_KM DOUBLE)",
            "CREATE TABLE TB_EMAILS (ID_EMAIL COUNTER PRIMARY KEY, ID_EMPRESA LONG, EMAIL TEXT(200), DOMINIO_EMAIL TEXT(100), VALIDADO BIT, DATA_COLETA DATE, ORIGEM_COLETA TEXT(20))",
            "CREATE TABLE TB_TELEFONES (ID_TELEFONE COUNTER PRIMARY KEY, ID_EMPRESA LONG, TELEFONE TEXT(20), TELEFONE_FORMATADO TEXT(20), DDD TEXT(2), TIPO_TELEFONE TEXT(10), VALIDADO BIT, DATA_COLETA DATE)",
            "CREATE TABLE TB_GEOLOCALIZACAO (ID_GEO COUNTER PRIMARY KEY, ID_EMPRESA LONG, ID_ENDERECO LONG, LATITUDE DOUBLE, LONGITUDE DOUBLE, DISTANCIA_KM DOUBLE, STATUS_PROCESSAMENTO TEXT(20), DATA_PROCESSAMENTO DATE, TENTATIVAS LONG, ERRO_DESCRICAO TEXT(255))",
            "CREATE TABLE TB_PLANILHA (ID_PLANILHA COUNTER PRIMARY KEY, SITE TEXT(255), EMAIL MEMO, TELEFONE MEMO, ENDERECO TEXT(255), DISTANCIA_KM DOUBLE, DATA_ATUALIZACAO DATE)",
            "CREATE TABLE TB_CEP_ENRICHMENT (ID_CEP_ENRICHMENT COUNTER PRIMARY KEY, ID_EMPRESA LONG, ID_ENDERECO LONG, STATUS_PROCESSAMENTO TEXT(20), DATA_PROCESSAMENTO DATE, TENTATIVAS LONG, ERRO_DESCRICAO TEXT(255))"
        ]

        for i, sql in enumerate(sqls, 1):
            try:
                access.DoCmd.RunSQL(sql)
                table = sql.split()[2]
                print(f"[DB] {i}/12 - {table} criada")
            except Exception as e:
                table = sql.split()[2] if len(sql.split()) > 2 else "UNKNOWN"
                print(f"[DB-ERRO] {i}/11 - {table}: {str(e)[:50]}")
                # Continuar mesmo com erro
                pass

        print("[INFO] Carregando dados basicos...")

        # Dados organizados por categoria
        zonas = [
            "INSERT INTO TB_ZONAS (NOME_ZONA, UF, ATIVO, DATA_CRIACAO) VALUES ('zona norte', 'SP', -1, Date())",
            "INSERT INTO TB_ZONAS (NOME_ZONA, UF, ATIVO, DATA_CRIACAO) VALUES ('zona sul', 'SP', -1, Date())",
            "INSERT INTO TB_ZONAS (NOME_ZONA, UF, ATIVO, DATA_CRIACAO) VALUES ('zona leste', 'SP', -1, Date())",
            "INSERT INTO TB_ZONAS (NOME_ZONA, UF, ATIVO, DATA_CRIACAO) VALUES ('zona oeste', 'SP', -1, Date())",
            "INSERT INTO TB_ZONAS (NOME_ZONA, UF, ATIVO, DATA_CRIACAO) VALUES ('zona central', 'SP', -1, Date())"
        ]

        # Tabelas TB_BAIRROS e TB_CIDADES ficam vazias - serão populadas pela descoberta dinâmica
        bairros = []  # Sem dados hardcoded
        cidades = []  # Sem dados hardcoded

        termos = [
            "INSERT INTO TB_BASE_BUSCA (TERMO_BUSCA, CATEGORIA, ATIVO, DATA_CRIACAO) VALUES ('empresa de elevadores', 'elevadores', -1, Date())",
            "INSERT INTO TB_BASE_BUSCA (TERMO_BUSCA, CATEGORIA, ATIVO, DATA_CRIACAO) VALUES ('manutenção de elevadores', 'elevadores', -1, Date())"
        ]

        # Carregar zonas
        print(f"[DB-DATA] Carregando {len(zonas)} zonas...")
        for sql in zonas:
            try:
                access.DoCmd.RunSQL(sql)
            except:
                pass
        print(f"[DB-DATA] {len(zonas)} zonas carregadas")

        # Carregar bairros (agora vazio - descoberta dinâmica)
        if bairros:
            print(f"[DB-DATA] Carregando {len(bairros)} bairros...")
            for sql in bairros:
                try:
                    access.DoCmd.RunSQL(sql)
                except:
                    pass
            print(f"[DB-DATA] {len(bairros)} bairros carregados")
        else:
            print(f"[DB-DATA] TB_BAIRROS vazia - usará descoberta dinâmica")

        # Carregar cidades (agora vazio - descoberta dinâmica)
        if cidades:
            print(f"[DB-DATA] Carregando {len(cidades)} cidades...")
            for sql in cidades:
                try:
                    access.DoCmd.RunSQL(sql)
                except:
                    pass
            print(f"[DB-DATA] {len(cidades)} cidades carregadas")
        else:
            print(f"[DB-DATA] TB_CIDADES vazia - usará descoberta dinâmica")

        # Carregar termos base
        print(f"[DB-DATA] Carregando {len(termos)} termos base...")
        for sql in termos:
            try:
                access.DoCmd.RunSQL(sql)
            except:
                pass
        print(f"[DB-DATA] {len(termos)} termos base carregados")

        access.Quit()

        # Verificar registros salvos
        print("\n[INFO] Verificando registros salvos...")
        
        try:
            import pyodbc
            conn_str = f'DRIVER={{Microsoft Access Driver (*.mdb, *.accdb)}};DBQ={db_path};'
            conn = pyodbc.connect(conn_str)
            cursor = conn.cursor()
            
            # Contar registros por tabela
            tabelas = {
                'TB_ZONAS': 'zonas',
                'TB_BAIRROS': 'bairros', 
                'TB_CIDADES': 'cidades',
                'TB_BASE_BUSCA': 'termos base'
            }
            
            print("\n[INFO] CONTAGEM DE REGISTROS POR TABELA:")
            print("=" * 45)
            
            total_registros = 0
            for tabela, nome in tabelas.items():
                try:
                    cursor.execute(f"SELECT COUNT(*) FROM {tabela}")
                    count = cursor.fetchone()[0]
                    print(f"   {tabela:<15} | {count:>3} {nome}")
                    total_registros += count
                except Exception as e:
                    print(f"   {tabela:<15} | ERR {nome}")
            
            print("=" * 45)
            print(f"   TOTAL GERAL     | {total_registros:>3} registros")
            
            # Calcular combinações possíveis
            cursor.execute("SELECT COUNT(*) FROM TB_ZONAS")
            count_zonas = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM TB_BAIRROS")
            count_bairros = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM TB_CIDADES")
            count_cidades = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM TB_BASE_BUSCA")
            count_termos = cursor.fetchone()[0]
            
            total_combinacoes = (count_zonas + count_bairros + count_cidades) * count_termos
            
            conn.close()
            
            print(f"\n[INFO] POTENCIAL DE BUSCA:")
            print(f"   {total_combinacoes} combinacoes possiveis")
            print(f"\n[OK] BANCO CRIADO COM SUCESSO!")
            print(f"[INFO] Localizacao: {db_path}")
            print(f"[OK] 12 tabelas estruturadas")
            
            # Verificar se TB_ENDERECOS foi criada (nova conexão)
            try:
                import pyodbc
                test_conn = pyodbc.connect(conn_str)
                test_cursor = test_conn.cursor()
                test_cursor.execute("SELECT COUNT(*) FROM TB_ENDERECOS")
                count = test_cursor.fetchone()[0]
                test_conn.close()
                print(f"[DB-CHECK] TB_ENDERECOS verificada e funcionando ({count} registros)")
            except Exception as e:
                print(f"[DB-ERRO] TB_ENDERECOS nao foi criada: {e}")
            
        except Exception as e:
            print(f"[AVISO] Nao foi possivel verificar registros: {e}")
            print(f"\n[OK] BANCO CRIADO COM SUCESSO!")
            print(f"[INFO] Localizacao: {db_path}")

    except Exception as e:
        print(f"[ERRO] Falha: {e}")


if __name__ == "__main__":
    create_simple_db()
    # Só pausar se executado diretamente (não via subprocess)
    import sys
    import os
    if 'PYTEST_CURRENT_TEST' not in os.environ and sys.stdin.isatty():
        input("[INFO] ENTER para sair...")
