#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para verificar instalação do Python
"""
import subprocess
import sys


def verificar_versao_python():
    """Verifica se a versão do Python é compatível"""
    version = sys.version_info

    print(f"[INFO] Python {version.major}.{version.minor}.{version.micro} encontrado")
    print(f"[INFO] Executável: {sys.executable}")

    # Verificar versão mínima 3.13.7
    if version.major == 3 and version.minor == 13 and version.micro >= 7:
        print("[OK] Versão compatível")
        return True
    elif version.major == 3 and version.minor > 13:
        print("[OK] Versão compatível")
        return True
    elif version.major > 3:
        print("[OK] Versão compatível")
        return True
    else:
        print(f"[ERRO] Versão muito antiga - mínimo necessário: 3.13.7")
        return False


def verificar_dependencias():
    """Verifica se as dependências estão instaladas e retorna lista de faltantes"""
    dependencias = {
        'selenium': 'selenium',
        'playwright': 'playwright.sync_api',
        'openpyxl': 'openpyxl',
        'tldextract': 'tldextract',
        'requests': 'requests',
        'pyodbc': 'pyodbc',
        'pyyaml': 'yaml',
        'flask': 'flask',
        'flask-socketio': 'flask_socketio'
    }

    # Adicionar pywin32 apenas no Windows
    import platform
    if platform.system() == 'Windows':
        dependencias['pywin32'] = 'win32com.client'

    print("[INFO] Verificando dependências...")

    faltantes = []
    for nome_pacote, nome_import in dependencias.items():
        try:
            __import__(nome_import)
            print(f"[OK] {nome_pacote} instalado")
        except ImportError:
            print(f"[AVISO] {nome_pacote} não encontrado")
            faltantes.append(nome_pacote)

    if not faltantes:
        print("[OK] Todas as dependências estão instaladas")
        return True, []

    return False, faltantes


def instalar_dependencias(faltantes):
    """Instala apenas as dependências faltantes"""
    if not faltantes:
        print("[OK] Nenhuma dependência para instalar")
        return True

    print(f"[INFO] Instalando {len(faltantes)} dependência(s) faltante(s): {', '.join(faltantes)}")

    # Mapeamento para versões específicas
    versoes = {
        'selenium': 'selenium>=4.0.0',
        'playwright': 'playwright>=1.40.0',
        'openpyxl': 'openpyxl>=3.0.0',
        'tldextract': 'tldextract>=3.0.0',
        'requests': 'requests>=2.25.0',
        'pyyaml': 'pyyaml>=6.0',
        'flask': 'flask>=3.0.0',
        'flask-socketio': 'flask-socketio>=5.3.0',
        'pyodbc': 'pyodbc>=4.0.0',
        'pywin32': 'pywin32>=306'
    }

    try:
        # Atualizar pip silenciosamente
        subprocess.run([sys.executable, '-m', 'pip', 'install', '--upgrade', 'pip'],
                       check=True, capture_output=True)

        # Instalar apenas os pacotes faltantes
        pacotes = [versoes.get(dep, dep) for dep in faltantes]

        print(f"[INFO] Instalando pacotes: {', '.join(pacotes)}")

        # Tentar instalação em lote primeiro
        try:
            subprocess.run(
                [sys.executable, '-m', 'pip', 'install'] + pacotes,
                check=True,
                capture_output=False,  # Mostrar progresso
                timeout=300
            )
            print("[OK] Dependências instaladas com sucesso")
            return True

        except subprocess.CalledProcessError as e:
            # Se falhar, tentar um por um
            print("[AVISO] Instalação em lote falhou, tentando individualmente...")
            for pacote in pacotes:
                try:
                    print(f"[INFO] Instalando {pacote}...")
                    subprocess.run(
                        [sys.executable, '-m', 'pip', 'install', pacote],
                        check=True,
                        capture_output=True
                    )
                    print(f"[OK] {pacote} instalado")
                except subprocess.CalledProcessError as e_individual:
                    print(f"[ERRO] Falha ao instalar {pacote}: {e_individual}")

                    # Tratamento especial para pyodbc
                    if 'pyodbc' in pacote:
                        print("[INFO] Tentando reinstalar pyodbc...")
                        try:
                            subprocess.run(
                                [sys.executable, '-m', 'pip', 'install', '--force-reinstall', 'pyodbc'],
                                check=True,
                                capture_output=False
                            )
                            print("[OK] pyodbc reinstalado")
                        except:
                            print("[AVISO] pyodbc pode precisar de configuração manual")
                            continue
                    else:
                        return False

            print("[OK] Dependências instaladas")
            return True

    except subprocess.CalledProcessError as e:
        print(f"[ERRO] Falha na instalação: {e}")
        return False
    except Exception as e:
        print(f"[ERRO] Erro inesperado: {e}")
        return False


def instalar_playwright_browser():
    """Instala browser Chromium do Playwright se necessário"""
    try:
        print("\n[INFO] Verificando Playwright...")

        result = subprocess.run(
            [sys.executable, '-m', 'playwright', 'install', '--help'],
            capture_output=True,
            timeout=5
        )

        if result.returncode != 0:
            print("[INFO] Playwright não configurado, pulando instalação do browser...")
            return True

        print("[INFO] Verificando browser Chromium...")
        check_result = subprocess.run(
            [sys.executable, '-c',
             "from playwright.sync_api import sync_playwright; "
             "p = sync_playwright().start(); "
             "p.chromium.launch(); "
             "p.stop()"],
            capture_output=True,
            timeout=10
        )

        if check_result.returncode == 0:
            print("[OK] Browser Chromium já instalado")
            return True

        print("[INFO] Instalando browser Chromium do Playwright (primeira vez, ~100MB)...")
        print("[INFO] Isso pode levar 1-2 minutos...")

        install_result = subprocess.run(
            [sys.executable, '-m', 'playwright', 'install', 'chromium'],
            capture_output=False,
            timeout=300
        )

        if install_result.returncode == 0:
            print("[OK] Browser Chromium instalado com sucesso!")
            return True
        else:
            print("[AVISO] Falha ao instalar Chromium, mas Playwright funcionará quando necessário")
            return True

    except subprocess.TimeoutExpired:
        print("[AVISO] Timeout ao verificar Playwright, continuando...")
        return True
    except Exception as e:
        print(f"[AVISO] Erro ao verificar Playwright: {e}")
        print("[INFO] Playwright será configurado quando necessário")
        return True


if __name__ == "__main__":
    print("🐍 Verificador de Instalação Python")
    print("=" * 40)

    # Verificar versão
    if not verificar_versao_python():
        print("\n[ERRO] Python incompatível")
        sys.exit(1)

    # Verificar dependências
    todas_instaladas, faltantes = verificar_dependencias()

    if not todas_instaladas:
        if not instalar_dependencias(faltantes):
            print("\n[ERRO] Falha na instalação de dependências")
            sys.exit(1)

    # Verificar e instalar browser Playwright
    instalar_playwright_browser()

    print("\n✅ Python e dependências OK!")
