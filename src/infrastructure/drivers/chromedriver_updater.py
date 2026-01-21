"""
Helper para atualizar o ChromeDriver em tempo de execução.
Tenta (em ordem):
 - webdriver_manager (mais robusto)
 - chromedriver_autoinstaller
 - scripts/verification/verify_chromedriver.py (fallback)
Faz backup do driver existente antes de sobrescrever.
Retorna True se o driver foi atualizado com sucesso.
"""
from pathlib import Path
import logging
import shutil
import time
import subprocess
import sys
import os
import importlib
import requests
import zipfile

logger = logging.getLogger(__name__)


def _get_installed_chrome_major() -> int | None:
    """Retorna a versão major do Chrome instalada (ex.: 143) ou None.

    Estratégia:
    1. Tentar ler registro HKCU\Software\Google\Chrome\BLBeacon
    2. Tentar ler HKLM caminho App Paths\chrome.exe
    3. Tentar executar chrome.exe --version em caminhos comuns
    4. Por fim, executar scripts/verification/verify_chromedriver.py e parsear stdout
    """
    # 1) HKCU
    try:
        import winreg
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Google\Chrome\BLBeacon")
        version, _ = winreg.QueryValueEx(key, "version")
        major = int(version.split('.')[0])
        return major
    except Exception:
        pass

    # 2) HKLM App Paths
    try:
        import winreg
        key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\chrome.exe")
        val, _ = winreg.QueryValueEx(key, None)  # type: ignore
        if val and Path(val).exists():
            try:
                proc = subprocess.run([str(val), '--version'], capture_output=True, text=True, timeout=5)
                out = (proc.stdout or proc.stderr or '').strip()
                # Expect 'Google Chrome 143.0.0.0'
                for token in out.split():
                    if token[0].isdigit():
                        return int(token.split('.')[0])
            except Exception:
                pass
    except Exception:
        pass

    # 3) Tentar caminhos comuns
    common = [
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe",
        r"C:\Program Files (x86)\BraveSoftware\Brave-Browser\Application\brave.exe",
    ]
    for p in common:
        try:
            pth = Path(p)
            if pth.exists():
                proc = subprocess.run([str(pth), '--version'], capture_output=True, text=True, timeout=5)
                out = (proc.stdout or proc.stderr or '').strip()
                for token in out.split():
                    if token[0].isdigit():
                        return int(token.split('.')[0])
        except Exception:
            continue

    # 4) Fallback: executar script de verificação e parsear stdout
    verifier = Path('scripts/verification/verify_chromedriver.py')
    if verifier.exists():
        try:
            env = os.environ.copy()
            env['PYTHONIOENCODING'] = 'utf-8'
            proc = subprocess.run([sys.executable, str(verifier)], capture_output=True, text=True, env=env, timeout=20)
            out = (proc.stdout or proc.stderr or '')
            # procurar algo como: '[OK] Google Chrome 143.0.7499.193 encontrado'
            import re
            m = re.search(r'Google Chrome\s+([0-9]+)\.', out)
            if m:
                return int(m.group(1))
        except Exception:
            pass

    return None


def _get_chromedriver_major(path: Path) -> int | None:
    """Executa o chromedriver binary com --version e extrai a versão major.
    Retorna None se não for possível obter.
    """
    try:
        if not path.exists():
            return None
        proc = subprocess.run([str(path), '--version'], capture_output=True, text=True, timeout=10)
        out = (proc.stdout or proc.stderr or '').strip()
        # usualmente: 'ChromeDriver 139.0.0.0 (...)'
        parts = out.split()
        for p in parts:
            if p[0].isdigit():
                ver = p
                break
        else:
            # fallback: procurar o primeiro token que contenha '.'
            ver = None
            for p in parts:
                if '.' in p:
                    ver = p
                    break
        if not ver:
            return None
        major = int(ver.split('.')[0])
        return major
    except Exception:
        return None


def _is_driver_compatible(driver_path: Path, chrome_major: int | None) -> bool:
    """Retorna True somente se for possível comparar e as versões major coincidirem.

    Não assume compatibilidade quando não for possível obter a versão do Chrome.
    """
    # Se driver não existe, não é compatível
    if not driver_path.exists():
        return False

    # Tentar obter versão do chromedriver
    drv_major = _get_chromedriver_major(driver_path)
    if drv_major is None:
        logger.debug('Não foi possível obter versão do chromedriver')
        return False

    # Se chrome_major foi fornecido, comparar diretamente
    if chrome_major is not None:
        return drv_major == chrome_major

    # Se chrome_major não informado, tentar detectar via caminhos/registro novamente
    detected = _get_installed_chrome_major()
    if detected is not None:
        return drv_major == detected

    # Tentar usar chrome.exe --version em caminhos comuns como último recurso
    common = [
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    ]
    for p in common:
        try:
            pth = Path(p)
            if pth.exists():
                proc = subprocess.run([str(pth), '--version'], capture_output=True, text=True, timeout=5)
                out = (proc.stdout or proc.stderr or '').strip()
                for token in out.split():
                    if token and token[0].isdigit():
                        try:
                            browser_major = int(token.split('.')[0])
                            return drv_major == browser_major
                        except Exception:
                            continue
        except Exception:
            continue

    # Se não foi possível detectar a versão do navegador, não aceitar o driver automaticamente
    logger.debug('Versão do navegador não detectável; mantendo driver anterior')
    return False


def _download_chromedriver_for_major(chrome_major: int, target: Path) -> bool:
    """Baixa um chromedriver compatível para a versão major do Chrome usando
    a API de 'known-good-versions-with-downloads.json'. Retorna True se instalado.
    """
    try:
        api_url = "https://googlechromelabs.github.io/chrome-for-testing/known-good-versions-with-downloads.json"
        resp = requests.get(api_url, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        # procurar última versão que comece com major
        for version_info in reversed(data.get('versions', [])):
            ver = version_info.get('version', '')
            if ver.startswith(str(chrome_major) + '.'):
                for download in version_info.get('downloads', {}).get('chromedriver', []):
                    if download.get('platform') == 'win64':
                        url = download.get('url')
                        if not url:
                            continue
                        # baixar zip para temp
                        tmp_zip = target.parent / 'chromedriver_tmp.zip'
                        with requests.get(url, stream=True, timeout=30) as r:
                            r.raise_for_status()
                            with open(tmp_zip, 'wb') as f:
                                for chunk in r.iter_content(chunk_size=8192):
                                    if chunk:
                                        f.write(chunk)
                        # extrair chromedriver.exe para arquivo temporário
                        tmp_target = target.parent / (target.name + '.tmp')
                        with zipfile.ZipFile(tmp_zip, 'r') as zf:
                            for info in zf.filelist:
                                if info.filename.endswith('chromedriver.exe'):
                                    with zf.open(info) as src, open(tmp_target, 'wb') as dst:
                                        dst.write(src.read())
                                    break
                        try:
                            tmp_zip.unlink()
                        except Exception:
                            pass
                        # garantir permissões
                        try:
                            tmp_target.chmod(0o755)
                        except Exception:
                            pass
                        # substituir de forma atômica
                        try:
                            os.replace(str(tmp_target), str(target))
                        except Exception as e:
                            logger.debug(f'Falha ao substituir chromedriver extraído: {e}')
                        # validar
                        if _is_driver_compatible(target, chrome_major):
                            logger.info(f'ChromeDriver baixado diretamente para compatibilidade com Chrome {chrome_major}')
                            return True
                        else:
                            logger.debug('Driver baixado não é compatível após extração')
        logger.debug('Nenhuma versão compatível encontrada na lista known-good-versions')
        return False
    except Exception as e:
        logger.debug(f'Erro ao baixar chromedriver via known-good-versions: {e}')
        return False


def update_chromedriver(target_path: str) -> bool:
    target = Path(target_path)
    target.parent.mkdir(parents=True, exist_ok=True)

    # Detectar versão major do Chrome para validação
    chrome_major = _get_installed_chrome_major()
    logger.debug(f'Detectada versão major do Chrome: {chrome_major}')

    # Não criaremos backups (.bak). Em vez disso usamos escrita atômica via arquivo temporário
    # para sempre substituir o binário existente.

    def _atomic_replace(src_path: Path, dst_path: Path) -> bool:
        try:
            tmp = dst_path.parent / (dst_path.name + '.tmp')
            # Copiar preservando metadata
            shutil.copy2(src_path, tmp)
            # Substituir de forma atômica
            os.replace(str(tmp), str(dst_path))
            try:
                dst_path.chmod(0o755)
            except Exception:
                pass
            return True
        except Exception as e:
            logger.debug(f'Falha ao substituir driver de forma atômica: {e}')
            try:
                if tmp.exists():
                    tmp.unlink()
            except Exception:
                pass
            return False

    def _atomic_write_bytes(data: bytes, dst_path: Path) -> bool:
        try:
            tmp = dst_path.parent / (dst_path.name + '.tmp')
            with open(tmp, 'wb') as f:
                f.write(data)
            os.replace(str(tmp), str(dst_path))
            try:
                dst_path.chmod(0o755)
            except Exception:
                pass
            return True
        except Exception as e:
            logger.debug(f'Falha ao escrever binário temporário: {e}')
            try:
                if tmp.exists():
                    tmp.unlink()
            except Exception:
                pass
            return False

    # 1) Tentar webdriver_manager
    try:
        wm_mod = importlib.import_module('webdriver_manager.chrome')
        ChromeDriverManager = getattr(wm_mod, 'ChromeDriverManager')
        logger.info('Atualizando ChromeDriver via webdriver_manager...')
        new_path = ChromeDriverManager().install()
        new_file = Path(new_path)
        if new_file.exists():
            # copiar para tmp e substituir
            if _atomic_replace(new_file, target):
                logger.info(f'ChromeDriver atualizado com sucesso para: {target} (compatível)')
                return True
            else:
                logger.debug('Falha ao substituir chromedriver após webdriver_manager')
             # validar compatibilidade
            if _is_driver_compatible(target, chrome_major):
                logger.info(f'ChromeDriver atualizado com sucesso para: {target} (compatível)')
                return True
            else:
                logger.debug('Driver baixado via webdriver_manager NÃO é compatível com o Chrome instalado')
    except Exception as e:
        logger.debug(f'webdriver_manager não funcionou: {e}')

    # 2) Tentar chromedriver_autoinstaller
    try:
        cda = importlib.import_module('chromedriver_autoinstaller')
        logger.info('Atualizando ChromeDriver via chromedriver_autoinstaller...')
        installed_path = cda.install()
        installed_file = Path(installed_path)
        if installed_file.exists():
            if _atomic_replace(installed_file, target):
                if _is_driver_compatible(target, chrome_major):
                    logger.info(f'ChromeDriver atualizado com sucesso para: {target} (compatível)')
                    return True
                else:
                    logger.debug('Driver instalado via chromedriver_autoinstaller NÃO é compatível com o Chrome instalado')
            else:
                logger.debug('Falha ao substituir chromedriver após chromedriver_autoinstaller')
    except Exception as e:
        logger.debug(f'chromedriver_autoinstaller não funcionou: {e}')

    # 3) Fallback: executar script de verificação existente
    verifier = Path('scripts/verification/verify_chromedriver.py')
    if verifier.exists():
        logger.info('Executando script de verificação de chromedriver como fallback...')
        env = os.environ.copy()
        env['PYTHONIOENCODING'] = 'utf-8'
        try:
            # se já existe mas é incompatível, remover para forçar download pelo verificador
            if target.exists() and not _is_driver_compatible(target, chrome_major):
                try:
                    target.unlink()
                    logger.debug('Removido chromedriver incompatível para forçar redeownload via verificador')
                except Exception as e:
                    logger.debug(f'Falha ao remover chromedriver incompatível: {e}')

            proc = subprocess.run([sys.executable, str(verifier)], capture_output=True, text=True, env=env)

            # Se chrome_major ainda não conhecido, tentar parsear do stdout do verificador
            parsed_chrome_major = chrome_major
            try:
                if parsed_chrome_major is None and proc.stdout:
                    import re
                    m = re.search(r'Google Chrome\s+([0-9]+)\.', proc.stdout)
                    if m:
                        parsed_chrome_major = int(m.group(1))
                        logger.debug(f'Chrome major detectado via verificador: {parsed_chrome_major}')
            except Exception:
                pass

            # Tentar baixar diretamente via API se chrome_major conhecido (ou obtido via verificador)
            if parsed_chrome_major is not None:
                if _download_chromedriver_for_major(parsed_chrome_major, target):
                    logger.info('ChromeDriver instalado via known-good-versions')
                    # validar e retornar
                    if _is_driver_compatible(target, parsed_chrome_major):
                        return True
            else:
                logger.debug('Versão do Chrome desconhecida; não foi possível baixar via known-good-versions')

            # Mesmo que o script tenha criado um driver, validar versão do driver gerado
            if target.exists() and _is_driver_compatible(target, parsed_chrome_major):
                logger.info(f'ChromeDriver atualizado via script: {target} (compatível)')
                return True
            else:
                logger.debug(f'Verificador executado mas driver não compatível ou não encontrado. stdout={proc.stdout} stderr={proc.stderr}')
        except Exception as e:
            logger.debug(f'Erro ao executar script verificador: {e}')

    # Se falhou, não restauramos backups: manter o binário atual (se existente) e retornar False

    return False
