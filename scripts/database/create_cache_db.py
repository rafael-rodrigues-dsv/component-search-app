"""
Criador do banco de cache SQLite unificado
Todas as tabelas de cache em um único arquivo cache.db
"""
import sqlite3
from pathlib import Path


def create_cache_db():
    """Cria banco SQLite de cache unificado"""

    # Determinar pasta do projeto
    import os
    if 'scripts' in os.getcwd():
        project_root = Path.cwd().parent.parent
    else:
        project_root = Path.cwd()

    cache_dir = project_root / "data" / "cache"
    db_path = cache_dir / "cache.db"

    print("=" * 60)
    print("🗄️  CRIANDO BANCO DE CACHE UNIFICADO")
    print("=" * 60)
    print(f"[INFO] Caminho: {db_path.resolve()}")
    print(f"[DEBUG] Diretório atual: {Path.cwd()}")
    print(f"[DEBUG] Projeto root: {project_root}")
    print()

    # Criar diretório se não existir
    cache_dir.mkdir(parents=True, exist_ok=True)

    # Se banco existe, perguntar se quer recriar
    if db_path.exists():
        response = input(f"⚠️  Cache existe. Recriar? Isso apagará todos os dados em cache! (s/N): ")
        if response.lower() != 's':
            print("[INFO] Operação cancelada pelo usuário")
            return False
        db_path.unlink()
        print("[INFO] Cache antigo removido")

    try:
        print("\n[INFO] Criando banco cache.db...")
        conn = sqlite3.connect(db_path)

        print("[INFO] Criando tabelas de cache...\n")

        # Lista de tabelas com suas definições SQL
        tables = [
            {
                'name': 'cep_cache',
                'description': 'Cache de dados de CEP (BrasilAPI)',
                'sql': """
                    CREATE TABLE IF NOT EXISTS cep_cache (
                        cep TEXT PRIMARY KEY,
                        cidade TEXT,
                        uf TEXT,
                        bairro TEXT,
                        logradouro TEXT,
                        complemento TEXT,
                        source TEXT,
                        timestamp INTEGER,
                        hit_count INTEGER DEFAULT 1
                    )
                """,
                'indexes': [
                    "CREATE INDEX IF NOT EXISTS idx_cep_uf ON cep_cache(uf)",
                    "CREATE INDEX IF NOT EXISTS idx_cep_timestamp ON cep_cache(timestamp)"
                ]
            },
            {
                'name': 'geocoding_cache',
                'description': 'Cache de geocodificação (Nominatim)',
                'sql': """
                    CREATE TABLE IF NOT EXISTS geocoding_cache (
                        address_hash TEXT PRIMARY KEY,
                        address TEXT,
                        latitude REAL,
                        longitude REAL,
                        source TEXT,
                        timestamp INTEGER,
                        hit_count INTEGER DEFAULT 1
                    )
                """,
                'indexes': [
                    "CREATE INDEX IF NOT EXISTS idx_geocoding_timestamp ON geocoding_cache(timestamp)"
                ]
            },
            {
                'name': 'distance_cache',
                'description': 'Cache de distâncias calculadas (Haversine)',
                'sql': """
                    CREATE TABLE IF NOT EXISTS distance_cache (
                        origin_lat REAL,
                        origin_lon REAL,
                        dest_lat REAL,
                        dest_lon REAL,
                        distance_km REAL,
                        timestamp INTEGER,
                        hit_count INTEGER DEFAULT 1,
                        PRIMARY KEY (origin_lat, origin_lon, dest_lat, dest_lon)
                    )
                """,
                'indexes': [
                    "CREATE INDEX IF NOT EXISTS idx_distance_origin ON distance_cache(origin_lat, origin_lon)",
                    "CREATE INDEX IF NOT EXISTS idx_distance_timestamp ON distance_cache(timestamp)"
                ]
            },
            {
                'name': 'cities_brazil',
                'description': 'Cache de cidades brasileiras (IBGE + coordenadas)',
                'sql': """
                    CREATE TABLE IF NOT EXISTS cities (
                        id TEXT PRIMARY KEY,
                        name TEXT,
                        state TEXT,
                        population INTEGER,
                        is_capital BOOLEAN,
                        region_type TEXT,
                        latitude REAL,
                        longitude REAL
                    )
                """,
                'indexes': [
                    "CREATE INDEX IF NOT EXISTS idx_cities_state ON cities(state)",
                    "CREATE INDEX IF NOT EXISTS idx_cities_population ON cities(population DESC)",
                    "CREATE INDEX IF NOT EXISTS idx_cities_coords ON cities(latitude, longitude)",
                    "CREATE INDEX IF NOT EXISTS idx_cities_search ON cities(name, state)"
                ]
            }
        ]

        # Criar cada tabela
        for i, table in enumerate(tables, 1):
            try:
                # Criar tabela
                conn.execute(table['sql'])
                print(f"[CACHE] {i}/{len(tables)} - ✅ {table['name']}")
                print(f"         └─ {table['description']}")

                # Criar índices
                for idx_sql in table.get('indexes', []):
                    conn.execute(idx_sql)

            except Exception as e:
                print(f"[CACHE] {i}/{len(tables)} - ❌ {table['name']}: {str(e)[:80]}")

        conn.commit()

        # Estatísticas do banco criado
        print("\n" + "=" * 60)
        print("📊 ESTATÍSTICAS DO CACHE")
        print("=" * 60)

        cursor = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
        )
        tables_created = cursor.fetchall()
        print(f"✅ Total de tabelas: {len(tables_created)}")
        for table in tables_created:
            print(f"   ├─ {table[0]}")

        cursor = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='index' ORDER BY name"
        )
        indexes_created = cursor.fetchall()
        print(f"\n📌 Total de índices: {len(indexes_created)}")
        for idx in indexes_created[:5]:  # Mostrar primeiros 5
            print(f"   ├─ {idx[0]}")
        if len(indexes_created) > 5:
            print(f"   └─ ... e mais {len(indexes_created) - 5} índices")

        # Tamanho do arquivo
        file_size = db_path.stat().st_size
        print(f"\n💾 Tamanho do arquivo: {file_size:,} bytes (~{file_size/1024:.1f} KB)")

        conn.close()

        print("\n" + "=" * 60)
        print("✅ CACHE UNIFICADO CRIADO COM SUCESSO!")
        print("=" * 60)
        print(f"\n📁 Localização: {db_path.resolve()}")
        print("\n💡 Benefícios:")
        print("   ✓ Todos os caches em um único arquivo")
        print("   ✓ Gerenciamento simplificado")
        print("   ✓ Backups mais fáceis")
        print("   ✓ Menos overhead de I/O")
        print()

        return True

    except Exception as e:
        print(f"\n❌ [ERRO] Falha ao criar cache: {e}")
        import traceback
        traceback.print_exc()
        return False


def get_cache_stats(db_path: Path = None):
    """Exibe estatísticas do cache"""

    if db_path is None:
        import os
        if 'scripts' in os.getcwd():
            project_root = Path.cwd().parent.parent
        else:
            project_root = Path.cwd()
        db_path = project_root / "data" / "cache" / "cache.db"

    if not db_path.exists():
        print(f"❌ Cache não encontrado em: {db_path}")
        return

    try:
        conn = sqlite3.connect(db_path)

        print("\n" + "=" * 60)
        print("📊 ESTATÍSTICAS DO CACHE")
        print("=" * 60)

        # Estatísticas por tabela
        tables = ['cep_cache', 'geocoding_cache', 'distance_cache', 'cities']

        for table in tables:
            try:
                cursor = conn.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]

                # Tentar pegar hit_count se existir
                try:
                    cursor = conn.execute(f"SELECT SUM(hit_count), AVG(hit_count) FROM {table}")
                    total_hits, avg_hits = cursor.fetchone()
                    print(f"\n📦 {table}:")
                    print(f"   ├─ Entradas: {count:,}")
                    print(f"   ├─ Total hits: {total_hits or 0:,}")
                    print(f"   └─ Média hits/entrada: {avg_hits or 0:.2f}")
                except:
                    print(f"\n📦 {table}:")
                    print(f"   └─ Entradas: {count:,}")

            except Exception as e:
                print(f"\n📦 {table}: ⚠️ {str(e)[:50]}")

        conn.close()

        # Tamanho do arquivo
        file_size = db_path.stat().st_size
        print(f"\n💾 Tamanho total: {file_size:,} bytes (~{file_size/1024/1024:.2f} MB)")
        print("=" * 60)

    except Exception as e:
        print(f"❌ Erro ao ler estatísticas: {e}")


if __name__ == "__main__":
    import sys

    # Verificar se é para mostrar stats
    if len(sys.argv) > 1 and sys.argv[1] == '--stats':
        get_cache_stats()
    else:
        # Criar cache
        success = create_cache_db()

        if success:
            # Mostrar stats após criar
            print("\n")
            get_cache_stats()

    # Pausar se executado diretamente
    import os
    if 'PYTEST_CURRENT_TEST' not in os.environ and sys.stdin.isatty():
        input("\n[INFO] Pressione ENTER para sair...")
