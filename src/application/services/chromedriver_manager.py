"""
Gerenciador do ChromeDriver
"""
import os
import zipfile
import requests

class ChromeDriverManager:
    """Gerencia download e instalação do ChromeDriver"""
    
    @staticmethod
    def ensure_chromedriver() -> bool:
        """Verifica e instala ChromeDriver se necessário"""
        if os.path.exists("drivers/chromedriver.exe"):
            return True
        
        print("[INFO] ChromeDriver não encontrado. Baixando automaticamente...")
        
        try:
            chrome_version = ChromeDriverManager._get_chrome_version()
            download_url = ChromeDriverManager._get_download_url(chrome_version)
            
            if not download_url:
                print("[ERRO] Não foi possível encontrar versão compatível do ChromeDriver")
                return False
            
            return ChromeDriverManager._download_and_install(download_url)
            
        except Exception as e:
            print(f"[ERRO] Falha ao baixar ChromeDriver: {e}")
            return False
    
    @staticmethod
    def _get_chrome_version() -> str:
        """Detecta versão do Chrome"""
        try:
            import winreg
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Google\Chrome\BLBeacon")
            version, _ = winreg.QueryValueEx(key, "version")
            return version.split('.')[0]
        except:
            return "119"  # Versão padrão
    
    @staticmethod
    def _get_download_url(chrome_version: str) -> str:
        """Busca URL de download compatível"""
        api_url = "https://googlechromelabs.github.io/chrome-for-testing/known-good-versions-with-downloads.json"
        response = requests.get(api_url, timeout=10)
        data = response.json()
        
        for version_info in reversed(data['versions']):
            if version_info['version'].startswith(chrome_version):
                for download in version_info['downloads'].get('chromedriver', []):
                    if download['platform'] == 'win64':
                        return download['url']
        return None
    
    @staticmethod
    def _download_and_install(download_url: str) -> bool:
        """Baixa e instala ChromeDriver"""
        print("[INFO] Baixando ChromeDriver...")
        response = requests.get(download_url, timeout=30)
        
        with open("chromedriver.zip", 'wb') as f:
            f.write(response.content)
        
        with zipfile.ZipFile("chromedriver.zip", 'r') as zip_ref:
            os.makedirs('drivers', exist_ok=True)
            
            for file_info in zip_ref.filelist:
                if file_info.filename.endswith('chromedriver.exe'):
                    with zip_ref.open(file_info) as source, open('drivers/chromedriver.exe', 'wb') as target:
                        target.write(source.read())
                    break
        
        os.remove("chromedriver.zip")
        print("[OK] ChromeDriver instalado com sucesso")
        return True