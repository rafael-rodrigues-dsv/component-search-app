#!/usr/bin/env python3
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
    """Verifica se as dependências estão instaladas"""
    # Mapeamento: nome_pacote -> nome_import
    dependencias = {
        'selenium': 'selenium',
        'openpyxl': 'openpyxl', 
        'tldextract': 'tldextract',
        'requests': 'requests',
        'pyodbc': 'pyodbc',
        'pyyaml': 'yaml'
    }

    # Adicionar pywin32 apenas no Windows
    import platform
    if platform.system() == 'Windows':
        dependencias['pywin32'] = 'win32com.client'

    print("[INFO] Verificando dependências...")

    for nome_pacote, nome_import in dependencias.items():
        try:
            __import__(nome_import)
            print(f"[OK] {nome_pacote} instalado")
        except ImportError:
            print(f"[AVISO] {nome_pacote} não encontrado")
            return False

    print("[OK] Todas as dependências estão instaladas")
    return True


def instalar_dependencias():
    """Instala as dependências necessárias"""
    print("[INFO] Instalando dependências...")

    try:
        subprocess.run([sys.executable, '-m', 'pip', 'install', '--upgrade', 'pip'],
                       check=True, capture_output=True)

        # Instalar dependências individuais com tratamento especial para pyodbc
        deps = ['selenium>=4.0.0', 'openpyxl>=3.0.0', 'tldextract>=3.0.0',
                'requests>=2.25.0', 'pyyaml>=6.0']

        for dep in deps:
            subprocess.run([sys.executable, '-m', 'pip', 'install', dep],
                           check=True, capture_output=True)

        # Instalar pyodbc com tratamento especial
        print("[INFO] Instalando pyodbc...")
        try:
            subprocess.run([sys.executable, '-m', 'pip', 'install', 'pyodbc>=4.0.0'],
                           check=True, capture_output=True)
            print("[OK] pyodbc instalado")
        except subprocess.CalledProcessError:
            print("[AVISO] Falha na instalação do pyodbc, tentando alternativa...")
            subprocess.run([sys.executable, '-m', 'pip', 'install', '--force-reinstall', 'pyodbc'],
                           check=True, capture_output=True)
        
        # Instalar pywin32 no Windows
        import platform
        if platform.system() == 'Windows':
            print("[INFO] Instalando pywin32...")
            try:
                subprocess.run([sys.executable, '-m', 'pip', 'install', 'pywin32>=306'],
                               check=True, capture_output=True)
                print("[OK] pywin32 instalado")
            except subprocess.CalledProcessError:
                print("[AVISO] Falha na instalação do pywin32")

        print("[OK] Dependências instaladas")
        return True

    except subprocess.CalledProcessError as e:
        print(f"[ERRO] Falha na instalação: {e}")
        return False


if __name__ == "__main__":
    print("🐍 Verificador de Instalação Python")
    print("=" * 40)

    # Verificar versão
    if not verificar_versao_python():
        print("\n[ERRO] Python incompatível")
        sys.exit(1)

    # Verificar dependências
    if not verificar_dependencias():
        if not instalar_dependencias():
            sys.exit(1)

    print("\n✅ Python e dependências OK!")
