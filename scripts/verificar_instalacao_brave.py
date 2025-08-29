#!/usr/bin/env python3
"""
Script para verificar se tudo está instalado corretamente para Brave Browser
"""
import os


def verificar_instalacao():
    print("🔍 Verificando instalação para Brave Browser...")
    
    # 1. Verificar ChromeDriver
    if os.path.exists("chromedriver.exe"):
        print("✅ chromedriver.exe encontrado")
    else:
        print("❌ chromedriver.exe NÃO encontrado")
        print("   Baixe em: https://chromedriver.chromium.org/")
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
    
    # 3. Verificar Brave Browser instalado
    brave_paths = [
        "C:/Program Files/BraveSoftware/Brave-Browser/Application/brave.exe",
        "C:/Program Files (x86)/BraveSoftware/Brave-Browser/Application/brave.exe"
    ]
    brave_found = False
    brave_path = None
    
    for path in brave_paths:
        if os.path.exists(path):
            brave_found = True
            brave_path = path
            break
    
    if brave_found:
        print("✅ Brave Browser encontrado")
    else:
        print("❌ Brave Browser NÃO encontrado")
        print("   Baixe em: https://brave.com/download/")
        return False
    
    # 4. Teste básico do WebDriver com Brave
    try:
        from selenium import webdriver
        from selenium.webdriver.chrome.service import Service
        from selenium.webdriver.chrome.options import Options
        
        options = Options()
        options.add_argument("--headless")  # Teste sem abrir janela
        options.binary_location = brave_path  # Usar Brave ao invés de Chrome
        service = Service("chromedriver.exe")
        
        driver = webdriver.Chrome(service=service, options=options)
        driver.get("https://www.google.com")
        driver.quit()
        
        print("✅ Brave WebDriver funcionando")
        
    except Exception as e:
        print(f"❌ Erro no WebDriver: {e}")
        print("   Verifique se o Brave está instalado corretamente")
        return False
    
    print("\n🎉 Tudo instalado corretamente para Brave Browser!")
    print("Execute: python main.py")
    return True

if __name__ == "__main__":
    verificar_instalacao()