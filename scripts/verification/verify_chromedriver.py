#!/usr/bin/env python3
"""
Script para verificar e instalar ChromeDriver
"""
import os
import sys
import zipfile
from pathlib import Path

import requests


def verificar_chrome_instalado():
    """Verifica se o Google Chrome está instalado"""
    try:
        import winreg
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Google\Chrome\BLBeacon")
        version, _ = winreg.QueryValueEx(key, "version")
        print(f"[OK] Google Chrome {version} encontrado")
        return version.split('.')[0]
    except:
        print("[ERRO] Google Chrome não encontrado")
        return None


def verificar_chromedriver():
    """Verifica se ChromeDriver existe"""
    chromedriver_path = Path("drivers/chromedriver.exe")

    if chromedriver_path.exists():
        print(f"[OK] ChromeDriver encontrado: {chromedriver_path}")
        return True
    else:
        print("[AVISO] ChromeDriver não encontrado")
        return False


def get_download_url(chrome_version):
    """Busca URL de download compatível"""
    print(f"[INFO] Buscando ChromeDriver para Chrome {chrome_version}...")

    try:
        api_url = "https://googlechromelabs.github.io/chrome-for-testing/known-good-versions-with-downloads.json"
        response = requests.get(api_url, timeout=10)
        data = response.json()

        for version_info in reversed(data['versions']):
            if version_info['version'].startswith(chrome_version):
                for download in version_info['downloads'].get('chromedriver', []):
                    if download['platform'] == 'win64':
                        print(f"[OK] Versão compatível encontrada: {version_info['version']}")
                        return download['url']

        print(f"[ERRO] Nenhuma versão compatível encontrada para Chrome {chrome_version}")
        return None

    except Exception as e:
        print(f"[ERRO] Falha ao buscar versão: {e}")
        return None


def baixar_chromedriver(download_url):
    """Baixa e instala ChromeDriver"""
    print("📥 Baixando ChromeDriver...")
    print(f"🔗 URL: {download_url}")

    try:
        response = requests.get(download_url, stream=True, timeout=30)
        response.raise_for_status()

        total_size = int(response.headers.get('content-length', 0))
        downloaded = 0

        zip_path = "chromedriver.zip"

        with open(zip_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)
                    if total_size > 0:
                        percent = (downloaded / total_size) * 100
                        print(f"\r📊 Progresso: {percent:.1f}%", end="", flush=True)

        print(f"\n✅ Download concluído")

        # Extrair ChromeDriver
        print("📦 Extraindo ChromeDriver...")
        drivers_dir = Path("drivers")
        drivers_dir.mkdir(exist_ok=True)

        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            for file_info in zip_ref.filelist:
                if file_info.filename.endswith('chromedriver.exe'):
                    with zip_ref.open(file_info) as source:
                        with open(drivers_dir / 'chromedriver.exe', 'wb') as target:
                            target.write(source.read())
                    break

        # Limpar arquivo zip
        os.remove(zip_path)
        print("✅ ChromeDriver instalado com sucesso!")
        return True

    except Exception as e:
        print(f"\n❌ Erro no download: {e}")
        return False


if __name__ == "__main__":
    print("🚗 Verificador de ChromeDriver")
    print("=" * 40)

    # Verificar Chrome
    chrome_version = verificar_chrome_instalado()
    if not chrome_version:
        print("\n❌ Google Chrome deve estar instalado")
        sys.exit(1)

    # Verificar ChromeDriver
    if verificar_chromedriver():
        print("\n✅ ChromeDriver já está instalado!")
        sys.exit(0)

    # Baixar ChromeDriver
    download_url = get_download_url(chrome_version)
    if not download_url:
        sys.exit(1)

    if baixar_chromedriver(download_url):
        print("\n🎉 ChromeDriver instalado com sucesso!")
    else:
        sys.exit(1)
