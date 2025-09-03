#!/usr/bin/env python3
"""
Script para verificar se tudo está instalado corretamente para Chrome
"""
import os


def verificar_instalacao():
    print("🔍 Verificando instalação para Chrome...")

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

    # 3. Teste básico do WebDriver Chrome
    try:
        from selenium import webdriver
        from selenium.webdriver.chrome.service import Service
        from selenium.webdriver.chrome.options import Options

        options = Options()
        options.add_argument("--headless")  # Teste sem abrir janela
        service = Service("chromedriver.exe")

        driver = webdriver.Chrome(service=service, options=options)
        driver.get("https://www.google.com")
        driver.quit()

        print("✅ Chrome WebDriver funcionando")

    except Exception as e:
        print(f"❌ Erro no WebDriver: {e}")
        print("   Verifique se o Chrome está instalado")
        return False

    print("\n🎉 Tudo instalado corretamente para Chrome!")
    print("Execute: python main.py")
    return True


if __name__ == "__main__":
    verificar_instalacao()
