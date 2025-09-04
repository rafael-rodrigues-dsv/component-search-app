"""
Testes para HumanBehaviorSimulator
"""
from unittest.mock import Mock, patch

import pytest

from src.infrastructure.network.human_behavior import HumanBehaviorSimulator


class TestHumanBehaviorSimulator:
    """Testes para simulador de comportamento humano"""

    def setup_method(self):
        """Setup para cada teste"""
        self.simulator = HumanBehaviorSimulator()

    @patch('time.sleep')
    def test_random_delay(self, mock_sleep):
        """Testa delay aleatório"""
        self.simulator.random_delay(1.0, 3.0)
        mock_sleep.assert_called_once()
        # Verifica se o delay está no range esperado
        call_args = mock_sleep.call_args[0][0]
        assert 1.0 <= call_args <= 3.0

    def test_typing_delay(self):
        """Testa delay de digitação"""
        delay = self.simulator.typing_delay()
        assert isinstance(delay, float)
        assert 0.05 <= delay <= 0.25

    def test_reading_delay(self):
        """Testa delay de leitura"""
        # Texto curto
        delay_short = self.simulator.reading_delay(10)
        assert delay_short >= 0.5

        # Texto longo
        delay_long = self.simulator.reading_delay(1000)
        assert delay_long > delay_short

    def test_scroll_behavior(self):
        """Testa comportamento de scroll"""
        mock_driver = Mock()

        self.simulator.scroll_behavior(mock_driver)

        # Verifica se execute_script foi chamado
        assert mock_driver.execute_script.called

        # Verifica se foram feitas múltiplas chamadas de scroll
        call_count = mock_driver.execute_script.call_count
        assert call_count >= 3  # Pelo menos 3 steps

    def test_scroll_behavior_exception(self):
        """Testa scroll com exceção"""
        mock_driver = Mock()
        mock_driver.execute_script.side_effect = Exception("Script error")

        # Não deve levantar exceção
        self.simulator.scroll_behavior(mock_driver)

    @patch('selenium.webdriver.common.action_chains.ActionChains')
    def test_mouse_movement(self, mock_action_chains):
        """Testa movimento de mouse"""
        mock_driver = Mock()
        mock_actions = Mock()
        mock_action_chains.return_value = mock_actions

        self.simulator.mouse_movement(mock_driver)

        mock_action_chains.assert_called_once_with(mock_driver)
        assert mock_actions.move_by_offset.called
        mock_actions.perform.assert_called_once()

    def test_mouse_movement_exception(self):
        """Testa movimento de mouse com exceção"""
        mock_driver = Mock()

        # Não deve levantar exceção
        self.simulator.mouse_movement(mock_driver)

    def test_get_search_intervals(self):
        """Testa intervalos de busca"""
        min_interval, max_interval = self.simulator.get_search_intervals()

        assert isinstance(min_interval, float)
        assert isinstance(max_interval, float)
        assert min_interval < max_interval
        assert min_interval >= 5.0

    def test_session_break_needed(self):
        """Testa necessidade de pausa de sessão"""
        # Poucas buscas - não precisa pausa
        assert not self.simulator.session_break_needed(5)

        # Muitas buscas - pode precisar pausa
        result = self.simulator.session_break_needed(20)
        assert isinstance(result, bool)

    @patch('time.sleep')
    def test_take_session_break(self, mock_sleep):
        """Testa pausa de sessão"""
        self.simulator.take_session_break()

        mock_sleep.assert_called_once()
        # Verifica se o tempo está no range esperado (60-180s)
        call_args = mock_sleep.call_args[0][0]
        assert 60 <= call_args <= 180
