"""
Simulador de Comportamento Humano para evitar detecção
"""
import random
import time
from typing import Tuple


class HumanBehaviorSimulator:
    """Simula comportamento humano realista"""

    @staticmethod
    def random_delay(min_seconds: float = 1.0, max_seconds: float = 3.0) -> None:
        """Delay aleatório com distribuição mais realista"""
        # Usa distribuição beta para simular padrões humanos
        delay = random.betavariate(2, 5) * (max_seconds - min_seconds) + min_seconds
        time.sleep(delay)

    @staticmethod
    def typing_delay() -> float:
        """Delay entre teclas durante digitação"""
        # Humanos digitam com velocidade variável
        return random.uniform(0.05, 0.25)

    @staticmethod
    def reading_delay(text_length: int) -> float:
        """Simula tempo de leitura baseado no tamanho do texto"""
        # ~200 palavras por minuto = ~3.3 palavras por segundo
        words = text_length / 5  # Aproximação: 5 chars por palavra
        reading_time = words / 3.3
        # Adiciona variação humana
        return max(0.5, reading_time * random.uniform(0.7, 1.3))

    @staticmethod
    def scroll_behavior(driver) -> None:
        """Simula scroll humano realista"""
        try:
            # Scroll gradual como humano
            total_scroll = random.randint(800, 2000)
            steps = random.randint(3, 6)
            step_size = total_scroll // steps

            for _ in range(steps):
                driver.execute_script(f"window.scrollBy(0, {step_size});")
                time.sleep(random.uniform(0.3, 0.8))

            # Às vezes volta um pouco (comportamento humano)
            if random.random() < 0.3:
                driver.execute_script(f"window.scrollBy(0, -{step_size});")
                time.sleep(random.uniform(0.2, 0.5))

        except Exception:
            pass

    @staticmethod
    def mouse_movement(driver) -> None:
        """Simula movimento de mouse aleatório"""
        try:
            from selenium.webdriver.common.action_chains import ActionChains
            actions = ActionChains(driver)

            # Movimento em curva (mais humano)
            for _ in range(random.randint(2, 4)):
                x_offset = random.randint(-50, 50)
                y_offset = random.randint(-50, 50)
                actions.move_by_offset(x_offset, y_offset)
                time.sleep(random.uniform(0.1, 0.3))

            actions.perform()
        except Exception:
            pass

    @staticmethod
    def get_search_intervals() -> Tuple[float, float]:
        """Retorna intervalos realistas entre buscas"""
        # Humanos fazem pausas maiores entre buscas
        base_min = random.uniform(5.0, 10.0)
        base_max = random.uniform(15.0, 25.0)

        # Às vezes fazem pausas muito longas (café, telefone, etc.)
        if random.random() < 0.1:  # 10% chance
            base_min *= 3
            base_max *= 3

        return base_min, base_max

    @staticmethod
    def session_break_needed(searches_count: int) -> bool:
        """Determina se precisa de pausa longa (simula cansaço humano)"""
        # Após muitas buscas, humanos fazem pausas
        if searches_count > 0 and searches_count % random.randint(15, 25) == 0:
            return True
        return False

    @staticmethod
    def take_session_break() -> None:
        """Pausa longa simulando comportamento humano"""
        break_time = random.uniform(60, 180)  # 1-3 minutos
        print(f"[INFO] Pausa de sessão: {break_time:.1f}s (simulando comportamento humano)")
        time.sleep(break_time)
