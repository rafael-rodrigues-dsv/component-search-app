#!/usr/bin/env python3
"""
Script para baixar e instalar Python 3.13.7
"""
import os
import requests
import subprocess
import sys
from pathlib import Path

def baixar_python():
    """Baixa o instalador do Python 3.13.7"""
    url = "https://www.python.org/ftp/python/3.13.7/python-3.13.7-amd64.exe"
    drivers_dir = Path("drivers")
    drivers_dir.mkdir(exist_ok=True)
    
    installer_path = drivers_dir / "python-installer.exe"
    
    print("📥 Baixando Python 3.13.7...")
    print(f"🔗 URL: {url}")
    
    try:
        response = requests.get(url, stream=True, timeout=30)
        response.raise_for_status()
        
        total_size = int(response.headers.get('content-length', 0))
        downloaded = 0
        
        with open(installer_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)
                    if total_size > 0:
                        percent = (downloaded / total_size) * 100
                        print(f"\r📊 Progresso: {percent:.1f}%", end="", flush=True)
        
        print(f"\n✅ Download concluído: {installer_path}")
        return installer_path
        
    except Exception as e:
        print(f"\n❌ Erro no download: {e}")
        return None

def instalar_python(installer_path):
    """Instala o Python usando o instalador baixado"""
    print("\n🔧 Instalando Python 3.13.7...")
    
    try:
        # Instalar silenciosamente com PATH
        cmd = [
            str(installer_path),
            "/quiet",
            "InstallAllUsers=0",
            "PrependPath=1",
            "Include_test=0",
            "Include_doc=0"
        ]
        
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        
        print("✅ Python 3.13.7 instalado com sucesso!")
        print("📝 PATH atualizado automaticamente")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Erro na instalação: {e}")
        return False

def limpar_installer(installer_path):
    """Remove o arquivo do instalador"""
    try:
        os.remove(installer_path)
        print("🗑️ Instalador removido")
    except:
        pass

if __name__ == "__main__":
    print("🚀 Instalador Automático Python 3.13.7")
    print("=" * 50)
    
    # Baixar Python
    installer = baixar_python()
    if not installer:
        sys.exit(1)
    
    # Instalar Python
    if instalar_python(installer):
        limpar_installer(installer)
        print("\n🎉 Instalação concluída!")
        print("🔄 Reinicie o terminal para usar o novo Python")
    else:
        sys.exit(1)