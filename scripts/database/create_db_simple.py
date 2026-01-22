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
            # TB_BASE_BUSCA com colunas extras para compatibilidade (IS_TEST, CREATED_BY, UPDATED_BY, UPDATED_AT)
            "CREATE TABLE TB_BASE_BUSCA (ID_BASE COUNTER PRIMARY KEY, TERMO_BUSCA TEXT(200), CATEGORIA TEXT(50), ATIVO BIT, DATA_CRIACAO DATE, IS_TEST BIT, CREATED_BY TEXT(100), UPDATED_BY TEXT(100), UPDATED_AT DATE)",
            # Tabela para armazenar dados do CEP de referência (CEP, cidade, estado, logradouro)
            "CREATE TABLE TB_CEP_CONFIG (ID_CEP_CONFIG COUNTER PRIMARY KEY, CEP TEXT(10), CIDADE TEXT(100), ESTADO TEXT(2), LOGRADOURO TEXT(255), DATA_ATUALIZACAO DATE)",
            "CREATE TABLE TB_ENDERECOS (ID_ENDERECO COUNTER PRIMARY KEY, LOGRADOURO TEXT(200), NUMERO TEXT(20), COMPLEMENTO TEXT(50), BAIRRO TEXT(100), CIDADE TEXT(100), ESTADO TEXT(2), CEP TEXT(10), DATA_CRIACAO DATE)",
            "CREATE TABLE TB_TERMOS_BUSCA (ID_TERMO COUNTER PRIMARY KEY, ID_BASE LONG, ID_ZONA LONG, ID_BAIRRO LONG, ID_CIDADE LONG, TERMO_COMPLETO TEXT(255), TIPO_LOCALIZACAO TEXT(20), STATUS_PROCESSAMENTO TEXT(20), DATA_CRIACAO DATE, DATA_PROCESSAMENTO DATE)",
            "CREATE TABLE TB_EMPRESAS (ID_EMPRESA COUNTER PRIMARY KEY, ID_TERMO LONG, SITE_URL TEXT(255), DOMINIO TEXT(100), NOME_EMPRESA TEXT(100), STATUS_COLETA TEXT(20), DATA_PRIMEIRA_VISITA DATE, DATA_ULTIMA_VISITA DATE, TENTATIVAS_COLETA LONG, MOTOR_BUSCA TEXT(20), ID_ENDERECO LONG, LATITUDE DOUBLE, LONGITUDE DOUBLE, DISTANCIA_KM DOUBLE)",
            "CREATE TABLE TB_EMAILS (ID_EMAIL COUNTER PRIMARY KEY, ID_EMPRESA LONG, EMAIL TEXT(200), DOMINIO_EMAIL TEXT(100), VALIDADO BIT, DATA_COLETA DATE, ORIGEM_COLETA TEXT(20))",
            "CREATE TABLE TB_TELEFONES (ID_TELEFONE COUNTER PRIMARY KEY, ID_EMPRESA LONG, TELEFONE TEXT(20), TELEFONE_FORMATADO TEXT(20), DDD TEXT(2), TIPO_TELEFONE TEXT(10), VALIDADO BIT, DATA_COLETA DATE)",
            "CREATE TABLE TB_GEOLOCALIZACAO (ID_GEO COUNTER PRIMARY KEY, ID_EMPRESA LONG, ID_ENDERECO LONG, LATITUDE DOUBLE, LONGITUDE DOUBLE, DISTANCIA_KM DOUBLE, STATUS_PROCESSAMENTO TEXT(20), DATA_PROCESSAMENTO DATE, TENTATIVAS LONG, ERRO_DESCRICAO TEXT(255))",
            "CREATE TABLE TB_PLANILHA (ID_PLANILHA COUNTER PRIMARY KEY, SITE TEXT(255), EMAIL MEMO, TELEFONE MEMO, ENDERECO TEXT(255), DISTANCIA_KM DOUBLE, DATA_ATUALIZACAO DATE)",
            "CREATE TABLE TB_CEP_ENRICHMENT (ID_CEP_ENRICHMENT COUNTER PRIMARY KEY, ID_EMPRESA LONG, ID_ENDERECO LONG, STATUS_PROCESSAMENTO TEXT(20), DATA_PROCESSAMENTO DATE, TENTATIVAS LONG, ERRO_DESCRICAO TEXT(255))",
            # Tabelas criadas para suportar processamento
        ]

        for i, sql in enumerate(sqls, 1):
            try:
                access.DoCmd.RunSQL(sql)
                table = sql.split()[2]
                print(f"[DB] {i}/{len(sqls)} - {table} criada")
            except Exception as e:
                table = sql.split()[2] if len(sql.split()) > 2 else "UNKNOWN"
                print(f"[DB-ERRO] {i}/{len(sqls)} - {table}: {str(e)[:50]}")
                # Continuar mesmo com erro
                pass

        # Apenas criamos as tabelas; população será realizada por serviços separados
        print("[INFO] Tabelas criadas. População de dados será executada separadamente pelo serviço de inicialização.")

        # Fechar Access COM agora que as tabelas foram criadas
        try:
            access.Quit()
            access = None
            print('[INFO] Access COM finalizado')
        except Exception:
            pass

    except Exception as e:
        print(f"[ERRO] Falha: {e}")


if __name__ == "__main__":
    create_simple_db()
    # Só pausar se executado diretamente (não via subprocess)
    import sys
    import os
    if 'PYTEST_CURRENT_TEST' not in os.environ and sys.stdin.isatty():
        input("[INFO] ENTER para sair...")
