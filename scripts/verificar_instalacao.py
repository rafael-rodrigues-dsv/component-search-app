#!/usr/bin/env python3
"""
Script para verificar se tudo está instalado corretamente
"""
import os


def verificar_instalacao():
    print("🔍 Verificando instalação...")
    
    # 1. Verificar GeckoDriver
    if os.path.exists("geckodriver.exe"):
        print("✅ geckodriver.exe encontrado")
    else:
        print("❌ geckodriver.exe NÃO encontrado")
        print("   Baixe em: https://github.com/mozilla/geckodriver/releases")
        return False
    
    # 2. Verificar dependências Python
    try:
        import selenium
        print("✅ selenium instalado")
    except ImportError:
        print("❌ selenium não instalado - Execute: pip install selenium")
        return False
    
    try:
        import openpyxl
        print("✅ openpyxl instalado")
    except ImportError:
        print("❌ openpyxl não instalado - Execute: pip install openpyxl")
        return False
    
    try:
        import tldextract
        print("✅ tldextract instalado")
    except ImportError:
        print("❌ tldextract não instalado - Execute: pip install tldextract")
        return False
    
    # 3. Teste básico do WebDriver
    try:
        from selenium import webdriver
        from selenium.webdriver.firefox.service import Service
        from selenium.webdriver.firefox.options import Options
        
        options = Options()
        options.add_argument("--headless")  # Teste sem abrir janela
        service = Service("geckodriver.exe")
        
        driver = webdriver.Firefox(service=service, options=options)
        driver.get("https://www.google.com")
        driver.quit()
        
        print("✅ Firefox WebDriver funcionando")
        
    except Exception as e:
        print(f"❌ Erro no WebDriver: {e}")
        print("   Verifique se o Firefox está instalado")
        return False
    
    print("\n🎉 Tudo instalado corretamente!")
    print("Execute: python main.py")
    return True

if __name__ == "__main__":
    verificar_instalacao()