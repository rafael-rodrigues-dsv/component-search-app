"""
Testes unitários para RetryConfigModel
"""
import unittest

from src.domain.models.retry_config_model import RetryConfigModel


class TestRetryConfigModel(unittest.TestCase):
    """Testes para RetryConfigModel"""
    
    def test_retry_config_default_values(self):
        """Testa valores padrão"""
        config = RetryConfigModel()
        
        self.assertEqual(config.max_attempts, 3)
        self.assertEqual(config.base_delay, 1.0)
        self.assertEqual(config.backoff_factor, 2.0)
        self.assertEqual(config.max_delay, 60.0)
    
    def test_retry_config_custom_values(self):
        """Testa valores customizados"""
        config = RetryConfigModel(
            max_attempts=5,
            base_delay=2.5,
            backoff_factor=1.5,
            max_delay=120.0
        )
        
        self.assertEqual(config.max_attempts, 5)
        self.assertEqual(config.base_delay, 2.5)
        self.assertEqual(config.backoff_factor, 1.5)
        self.assertEqual(config.max_delay, 120.0)
    
    def test_retry_config_types(self):
        """Testa tipos dos campos"""
        config = RetryConfigModel()
        
        self.assertIsInstance(config.max_attempts, int)
        self.assertIsInstance(config.base_delay, float)
        self.assertIsInstance(config.backoff_factor, float)
        self.assertIsInstance(config.max_delay, float)
    
    def test_retry_config_zero_values(self):
        """Testa valores zero"""
        config = RetryConfigModel(
            max_attempts=0,
            base_delay=0.0,
            backoff_factor=0.0,
            max_delay=0.0
        )
        
        self.assertEqual(config.max_attempts, 0)
        self.assertEqual(config.base_delay, 0.0)
        self.assertEqual(config.backoff_factor, 0.0)
        self.assertEqual(config.max_delay, 0.0)
    
    def test_retry_config_equality(self):
        """Testa igualdade entre instâncias"""
        config1 = RetryConfigModel(max_attempts=3, base_delay=1.0)
        config2 = RetryConfigModel(max_attempts=3, base_delay=1.0)
        
        self.assertEqual(config1, config2)
    
    def test_retry_config_inequality(self):
        """Testa desigualdade entre instâncias"""
        config1 = RetryConfigModel(max_attempts=3)
        config2 = RetryConfigModel(max_attempts=5)
        
        self.assertNotEqual(config1, config2)


if __name__ == '__main__':
    unittest.main()