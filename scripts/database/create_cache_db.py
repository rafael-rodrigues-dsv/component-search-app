"""
Criador do banco de cache SQLite unificado
Todas as tabelas de cache em um único arquivo pythonsearchcache.db
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
    db_path = cache_dir / "pythonsearchcache.db"

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
        print("\n[INFO] Criando banco pythonsearchcache.db...")
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
            },
            {
                'name': 'neighborhoods_cache',
                'description': 'Cache de bairros por cidade (Nominatim OSM)',
                'sql': """
                    CREATE TABLE IF NOT EXISTS neighborhoods_cache (
                        city TEXT NOT NULL,
                        state TEXT NOT NULL,
                        neighborhood TEXT NOT NULL,
                        source TEXT DEFAULT 'nominatim',
                        timestamp INTEGER,
                        PRIMARY KEY (city, state, neighborhood)
                    )
                """,
                'indexes': [
                    "CREATE INDEX IF NOT EXISTS idx_neighborhoods_city_state ON neighborhoods_cache(city, state)",
                    "CREATE INDEX IF NOT EXISTS idx_neighborhoods_timestamp ON neighborhoods_cache(timestamp)"
                ]
            },
            {
                'name': 'municipalities_coordinates',
                'description': 'Coordenadas pré-calculadas dos municípios IBGE (lookup instantâneo)',
                'sql': """
                    CREATE TABLE IF NOT EXISTS municipalities_coordinates (
                        city TEXT NOT NULL,
                        state TEXT NOT NULL,
                        latitude REAL NOT NULL,
                        longitude REAL NOT NULL,
                        ibge_code TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        PRIMARY KEY (city, state)
                    )
                """,
                'indexes': [
                    "CREATE INDEX IF NOT EXISTS idx_city_state ON municipalities_coordinates(city, state)",
                    "CREATE INDEX IF NOT EXISTS idx_ibge_code ON municipalities_coordinates(ibge_code)"
                ]
            },
            {
                'name': 'states_ibge',
                'description': 'Estados brasileiros (IBGE) - 27 UFs',
                'sql': """
                    CREATE TABLE IF NOT EXISTS states_ibge (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        code TEXT UNIQUE NOT NULL,
                        name TEXT NOT NULL,
                        ibge_code TEXT UNIQUE,
                        region TEXT,
                        capital_city TEXT,
                        capital_lat REAL,
                        capital_lon REAL,
                        total_cities INTEGER DEFAULT 0,
                        created_at INTEGER,
                        updated_at INTEGER
                    )
                """,
                'indexes': [
                    "CREATE INDEX IF NOT EXISTS idx_states_code ON states_ibge(code)",
                    "CREATE INDEX IF NOT EXISTS idx_states_region ON states_ibge(region)"
                ]
            },
            {
                'name': 'cities_ibge',
                'description': 'Municípios brasileiros completo (IBGE) - 5.571 cidades',
                'sql': """
                    CREATE TABLE IF NOT EXISTS cities_ibge (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        ibge_code TEXT UNIQUE NOT NULL,
                        name TEXT NOT NULL,
                        state_code TEXT NOT NULL,
                        state_name TEXT,
                        population INTEGER DEFAULT 0,
                        latitude REAL,
                        longitude REAL,
                        is_capital INTEGER DEFAULT 0,
                        area_km2 REAL,
                        geo_source TEXT DEFAULT 'IBGE',
                        geo_quality TEXT DEFAULT 'HIGH',
                        created_at INTEGER,
                        updated_at INTEGER,
                        FOREIGN KEY (state_code) REFERENCES states_ibge(code)
                    )
                """,
                'indexes': [
                    "CREATE INDEX IF NOT EXISTS idx_cities_state ON cities_ibge(state_code)",
                    "CREATE INDEX IF NOT EXISTS idx_cities_population ON cities_ibge(population DESC)",
                    "CREATE INDEX IF NOT EXISTS idx_cities_coordinates ON cities_ibge(latitude, longitude)",
                    "CREATE INDEX IF NOT EXISTS idx_cities_ibge_code ON cities_ibge(ibge_code)",
                    "CREATE INDEX IF NOT EXISTS idx_cities_capital ON cities_ibge(is_capital)"
                ]
            },
            {
                'name': 'neighborhoods_ibge',
                'description': 'Bairros/Distritos brasileiros (IBGE)',
                'sql': """
                    CREATE TABLE IF NOT EXISTS neighborhoods_ibge (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        ibge_code TEXT,
                        name TEXT NOT NULL,
                        city_ibge_code TEXT NOT NULL,
                        city_name TEXT,
                        state_code TEXT,
                        latitude REAL,
                        longitude REAL,
                        geo_source TEXT DEFAULT 'IBGE',
                        geo_quality TEXT DEFAULT 'MEDIUM',
                        created_at INTEGER,
                        updated_at INTEGER,
                        FOREIGN KEY (city_ibge_code) REFERENCES cities_ibge(ibge_code)
                    )
                """,
                'indexes': [
                    "CREATE INDEX IF NOT EXISTS idx_neighborhoods_city ON neighborhoods_ibge(city_ibge_code)",
                    "CREATE INDEX IF NOT EXISTS idx_neighborhoods_state ON neighborhoods_ibge(state_code)",
                    "CREATE INDEX IF NOT EXISTS idx_neighborhoods_name ON neighborhoods_ibge(name)"
                ]
            },
            {
                'name': 'distance_matrix',
                'description': 'Matriz de distâncias entre cidades (pré-calculada)',
                'sql': """
                    CREATE TABLE IF NOT EXISTS distance_matrix (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        origin_city_ibge TEXT NOT NULL,
                        dest_city_ibge TEXT NOT NULL,
                        distance_km REAL NOT NULL,
                        calculation_method TEXT DEFAULT 'HAVERSINE',
                        is_same_state INTEGER DEFAULT 0,
                        created_at INTEGER,
                        UNIQUE(origin_city_ibge, dest_city_ibge)
                    )
                """,
                'indexes': [
                    "CREATE INDEX IF NOT EXISTS idx_distance_origin ON distance_matrix(origin_city_ibge)",
                    "CREATE INDEX IF NOT EXISTS idx_distance_dest ON distance_matrix(dest_city_ibge)",
                    "CREATE INDEX IF NOT EXISTS idx_distance_km ON distance_matrix(distance_km)",
                    "CREATE INDEX IF NOT EXISTS idx_distance_same_state ON distance_matrix(is_same_state)"
                ]
            },
            {
                'name': 'neighborhoods_geonames',
                'description': 'Bairros brasileiros do GeoNames (offline após carga inicial)',
                'sql': """
                    CREATE TABLE IF NOT EXISTS neighborhoods_geonames (
                        geonameid INTEGER PRIMARY KEY,
                        name TEXT NOT NULL,
                        asciiname TEXT,
                        latitude REAL NOT NULL,
                        longitude REAL NOT NULL,
                        feature_class TEXT,
                        feature_code TEXT,
                        country_code TEXT,
                        admin1_code TEXT,
                        admin2_code TEXT,
                        city_name TEXT,
                        state_code TEXT,
                        population INTEGER DEFAULT 0,
                        elevation INTEGER,
                        timezone TEXT,
                        created_at INTEGER DEFAULT (strftime('%s', 'now'))
                    )
                """,
                'indexes': [
                    "CREATE INDEX IF NOT EXISTS idx_geonames_city ON neighborhoods_geonames(city_name, state_code)",
                    "CREATE INDEX IF NOT EXISTS idx_geonames_state ON neighborhoods_geonames(state_code)",
                    "CREATE INDEX IF NOT EXISTS idx_geonames_coords ON neighborhoods_geonames(latitude, longitude)",
                    "CREATE INDEX IF NOT EXISTS idx_geonames_feature ON neighborhoods_geonames(feature_code)",
                    "CREATE INDEX IF NOT EXISTS idx_geonames_admin2 ON neighborhoods_geonames(admin2_code)"
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


def create_cache_auto(cache_path: Path = None) -> bool:
    """
    Cria banco de cache automaticamente (sem interação do usuário)
    Usado pela aplicação principal para garantir que o cache existe
    Executa sempre os DDLs (idempotente com CREATE TABLE IF NOT EXISTS)
    """
    try:
        if cache_path is None:
            import os
            if 'scripts' in os.getcwd():
                project_root = Path.cwd().parent.parent
            else:
                project_root = Path.cwd()
            cache_path = project_root / "data" / "cache" / "pythonsearchcache.db"


        # Criar diretório se não existir
        cache_path.parent.mkdir(parents=True, exist_ok=True)

        conn = sqlite3.connect(cache_path)

        # Lista de tabelas com suas definições SQL
        tables = [
            {
                'name': 'cep_cache',
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
            },
            {
                'name': 'neighborhoods_cache',
                'sql': """
                    CREATE TABLE IF NOT EXISTS neighborhoods_cache (
                        city TEXT NOT NULL,
                        state TEXT NOT NULL,
                        neighborhood TEXT NOT NULL,
                        source TEXT DEFAULT 'nominatim',
                        timestamp INTEGER,
                        PRIMARY KEY (city, state, neighborhood)
                    )
                """,
                'indexes': [
                    "CREATE INDEX IF NOT EXISTS idx_neighborhoods_city_state ON neighborhoods_cache(city, state)",
                    "CREATE INDEX IF NOT EXISTS idx_neighborhoods_timestamp ON neighborhoods_cache(timestamp)"
                ]
            },
            {
                'name': 'municipalities_coordinates',
                'sql': """
                    CREATE TABLE IF NOT EXISTS municipalities_coordinates (
                        city TEXT NOT NULL,
                        state TEXT NOT NULL,
                        latitude REAL NOT NULL,
                        longitude REAL NOT NULL,
                        ibge_code TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        PRIMARY KEY (city, state)
                    )
                """,
                'indexes': [
                    "CREATE INDEX IF NOT EXISTS idx_city_state ON municipalities_coordinates(city, state)",
                    "CREATE INDEX IF NOT EXISTS idx_ibge_code ON municipalities_coordinates(ibge_code)"
                ]
            },
            {
                'name': 'states_ibge',
                'sql': """
                    CREATE TABLE IF NOT EXISTS states_ibge (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        code TEXT UNIQUE NOT NULL,
                        name TEXT NOT NULL,
                        ibge_code TEXT UNIQUE,
                        region TEXT,
                        capital_city TEXT,
                        capital_lat REAL,
                        capital_lon REAL,
                        total_cities INTEGER DEFAULT 0,
                        created_at INTEGER,
                        updated_at INTEGER
                    )
                """,
                'indexes': [
                    "CREATE INDEX IF NOT EXISTS idx_states_code ON states_ibge(code)",
                    "CREATE INDEX IF NOT EXISTS idx_states_region ON states_ibge(region)"
                ]
            },
            {
                'name': 'cities_ibge',
                'sql': """
                    CREATE TABLE IF NOT EXISTS cities_ibge (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        ibge_code TEXT UNIQUE NOT NULL,
                        name TEXT NOT NULL,
                        state_code TEXT NOT NULL,
                        state_name TEXT,
                        population INTEGER DEFAULT 0,
                        latitude REAL,
                        longitude REAL,
                        is_capital INTEGER DEFAULT 0,
                        area_km2 REAL,
                        geo_source TEXT DEFAULT 'IBGE',
                        geo_quality TEXT DEFAULT 'HIGH',
                        created_at INTEGER,
                        updated_at INTEGER,
                        FOREIGN KEY (state_code) REFERENCES states_ibge(code)
                    )
                """,
                'indexes': [
                    "CREATE INDEX IF NOT EXISTS idx_cities_state ON cities_ibge(state_code)",
                    "CREATE INDEX IF NOT EXISTS idx_cities_population ON cities_ibge(population DESC)",
                    "CREATE INDEX IF NOT EXISTS idx_cities_coordinates ON cities_ibge(latitude, longitude)",
                    "CREATE INDEX IF NOT EXISTS idx_cities_ibge_code ON cities_ibge(ibge_code)",
                    "CREATE INDEX IF NOT EXISTS idx_cities_capital ON cities_ibge(is_capital)"
                ]
            },
            {
                'name': 'neighborhoods_ibge',
                'sql': """
                    CREATE TABLE IF NOT EXISTS neighborhoods_ibge (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        ibge_code TEXT,
                        name TEXT NOT NULL,
                        city_ibge_code TEXT NOT NULL,
                        city_name TEXT,
                        state_code TEXT,
                        latitude REAL,
                        longitude REAL,
                        geo_source TEXT DEFAULT 'IBGE',
                        geo_quality TEXT DEFAULT 'MEDIUM',
                        created_at INTEGER,
                        updated_at INTEGER,
                        FOREIGN KEY (city_ibge_code) REFERENCES cities_ibge(ibge_code)
                    )
                """,
                'indexes': [
                    "CREATE INDEX IF NOT EXISTS idx_neighborhoods_city ON neighborhoods_ibge(city_ibge_code)",
                    "CREATE INDEX IF NOT EXISTS idx_neighborhoods_state ON neighborhoods_ibge(state_code)",
                    "CREATE INDEX IF NOT EXISTS idx_neighborhoods_name ON neighborhoods_ibge(name)"
                ]
            },
            {
                'name': 'distance_matrix',
                'sql': """
                    CREATE TABLE IF NOT EXISTS distance_matrix (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        origin_city_ibge TEXT NOT NULL,
                        dest_city_ibge TEXT NOT NULL,
                        distance_km REAL NOT NULL,
                        calculation_method TEXT DEFAULT 'HAVERSINE',
                        is_same_state INTEGER DEFAULT 0,
                        created_at INTEGER,
                        UNIQUE(origin_city_ibge, dest_city_ibge)
                    )
                """,
                'indexes': [
                    "CREATE INDEX IF NOT EXISTS idx_distance_origin ON distance_matrix(origin_city_ibge)",
                    "CREATE INDEX IF NOT EXISTS idx_distance_dest ON distance_matrix(dest_city_ibge)",
                    "CREATE INDEX IF NOT EXISTS idx_distance_km ON distance_matrix(distance_km)",
                    "CREATE INDEX IF NOT EXISTS idx_distance_same_state ON distance_matrix(is_same_state)"
                ]
            },
            {
                'name': 'neighborhoods_geonames',
                'sql': """
                    CREATE TABLE IF NOT EXISTS neighborhoods_geonames (
                        geonameid INTEGER PRIMARY KEY,
                        name TEXT NOT NULL,
                        asciiname TEXT,
                        latitude REAL NOT NULL,
                        longitude REAL NOT NULL,
                        feature_class TEXT,
                        feature_code TEXT,
                        country_code TEXT,
                        admin1_code TEXT,
                        admin2_code TEXT,
                        city_name TEXT,
                        state_code TEXT,
                        population INTEGER DEFAULT 0,
                        elevation INTEGER,
                        timezone TEXT,
                        created_at INTEGER DEFAULT (strftime('%s', 'now'))
                    )
                """,
                'indexes': [
                    "CREATE INDEX IF NOT EXISTS idx_geonames_city ON neighborhoods_geonames(city_name, state_code)",
                    "CREATE INDEX IF NOT EXISTS idx_geonames_state ON neighborhoods_geonames(state_code)",
                    "CREATE INDEX IF NOT EXISTS idx_geonames_coords ON neighborhoods_geonames(latitude, longitude)",
                    "CREATE INDEX IF NOT EXISTS idx_geonames_feature ON neighborhoods_geonames(feature_code)",
                    "CREATE INDEX IF NOT EXISTS idx_geonames_admin2 ON neighborhoods_geonames(admin2_code)"
                ]
            }
        ]

        # Criar cada tabela
        print(f"[CACHE-AUTO] Criando {len(tables)} tabelas...")
        for i, table in enumerate(tables, 1):
            try:
                conn.execute(table['sql'])
                for idx_sql in table.get('indexes', []):
                    conn.execute(idx_sql)
                print(f"[CACHE-AUTO] {i}/{len(tables)} - {table['name']} criada ✅")
            except Exception as e:
                print(f"[CACHE-AUTO] {i}/{len(tables)} - {table['name']} erro: {e}")

        conn.commit()
        conn.close()

        print(f"[CACHE-AUTO] ✅ Todas as tabelas criadas com sucesso!")
        return True

    except Exception as e:
        print(f"[ERRO] Falha ao criar cache automaticamente: {e}")
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
        db_path = project_root / "data" / "cache" / "pythonsearchcache.db"

    if not db_path.exists():
        print(f"❌ Cache não encontrado em: {db_path}")
        return

    try:
        conn = sqlite3.connect(db_path)

        print("\n" + "=" * 60)
        print("📊 ESTATÍSTICAS DO CACHE")
        print("=" * 60)

        # Estatísticas por tabela
        tables = ['cep_cache', 'geocoding_cache', 'distance_cache', 'cities', 'neighborhoods_cache']

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
