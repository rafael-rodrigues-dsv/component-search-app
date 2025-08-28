#!/usr/bin/env python3
"""
Script para baixar ChromeDriver automaticamente
"""
import os
import zipfile

import requests


def get_chrome_version():
    """Detecta versão do Chrome instalado"""
    try:
        import winreg
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Google\Chrome\BLBeacon")
        version, _ = winreg.QueryValueEx(key, "version")
        return version.split('.')[0]  # Retorna major version
    except:
        return "119"  # Versão padrão se não conseguir detectar

def baixar_chromedriver():
    """Baixa ChromeDriver automaticamente"""
    print("🔍 Detectando versão do Chrome...")
    
    chrome_version = get_chrome_version()
    print(f"📋 Chrome versão detectada: {chrome_version}")
    
    # URL da API do ChromeDriver
    api_url = f"https://googlechromelabs.github.io/chrome-for-testing/known-good-versions-with-downloads.json"
    
    try:
        print("📡 Buscando versão compatível do ChromeDriver...")
        response = requests.get(api_url, timeout=10)
        data = response.json()
        
        # Procura versão compatível
        download_url = None
        for version_info in reversed(data['versions']):
            if version_info['version'].startswith(chrome_version):
                for download in version_info['downloads'].get('chromedriver', []):
                    if download['platform'] == 'win64':
                        download_url = download['url']
                        break
                if download_url:
                    break
        
        if not download_url:
            print("❌ Não foi possível encontrar versão compatível")
            print("🔗 Baixe manualmente em: https://chromedriver.chromium.org/")
            return False
        
        print(f"⬇️ Baixando ChromeDriver...")
        print(f"🔗 URL: {download_url}")
        
        # Baixa o arquivo
        response = requests.get(download_url, timeout=30)
        zip_path = "chromedriver.zip"
        
        with open(zip_path, 'wb') as f:
            f.write(response.content)
        
        # Extrai o arquivo
        print("📦 Extraindo arquivo...")
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            # Procura o chromedriver.exe dentro do zip
            for file_info in zip_ref.filelist:
                if file_info.filename.endswith('chromedriver.exe'):
                    # Extrai apenas o chromedriver.exe
                    with zip_ref.open(file_info) as source, open('chromedriver.exe', 'wb') as target:
                        target.write(source.read())
                    break
        
        # Remove o arquivo zip
        os.remove(zip_path)
        
        if os.path.exists('chromedriver.exe'):
            print("✅ ChromeDriver baixado com sucesso!")
            print("📁 Arquivo salvo como: chromedriver.exe")
            return True
        else:
            print("❌ Erro ao extrair ChromeDriver")
            return False
            
    except Exception as e:
        print(f"❌ Erro ao baixar: {e}")
        print("🔗 Baixe manualmente em: https://chromedriver.chromium.org/")
        return False

if __name__ == "__main__":
    print("🚀 Baixador automático do ChromeDriver")
    print("=" * 50)
    
    if os.path.exists('chromedriver.exe'):
        print("✅ chromedriver.exe já existe na pasta")
        resposta = input("Deseja baixar novamente? (s/n): ")
        if resposta.lower() != 's':
            exit()
    
    if baixar_chromedriver():
        print("\n🎉 Pronto! Agora execute: python main.py")
    else:
        print("\n❌ Falha no download. Baixe manualmente.")